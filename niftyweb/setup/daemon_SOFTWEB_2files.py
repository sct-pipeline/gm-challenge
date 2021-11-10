#! /usr/bin/env python
# -*- coding: UTF-8 -*-

#/*============================================================================
#
#  NifTK: A software platform for medical image computing.
#
# Some doc (added by Julien Cohen-Adad):
# This soft will look at the presence of a file data_dir/PROGRAM-parameters.txt,
# which is supposed to be copied on the station through the Niftyweb interface.
# If the file is found, the data is processed. Once processed successfully, the
# file is renamed: data_dir/PROGRAM-parameters-done.txt (so that the process 
# does not run another time).
#
#
#  Copyright (c) University College London (UCL). All rights reserved.
#
#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.
#
#  See LICENSE.txt in the top level directory for details.
#
#============================================================================*/

#

# Import needed libraries
import sys
import shlex
import subprocess
import platform
import os
import shutil
import glob
from glob import glob
import re
import zipfile
import tempfile
import atexit
import numpy as np
import hashlib
from datetime import datetime, date, time
import datetime
import json
import requests

###### DEFAULT OPTIONS #######
dir_data=os.path.join('/home','niftyweb_sct','data_tmp')
URL='http://cmictig.cs.ucl.ac.uk/softweb/'
PATH='/home/niftyweb_sct/gm_challenge'+os.pathsep+'/home/niftyweb_sct/bin'+os.pathsep+os.environ.get('PATH')

# Begin of cleanup function
def cleanup():
	"""
	###########################################################################
	# Function  : Clean temp working directory
	###########################################################################
	"""

	global 	file_processed
	global  idname
	global  program
	global  lock_file

	removeFile(lock_file)

	# If the program crash we need to remove the file from the queue
	if os.path.isfile(file_processed):
		os.rename(file_processed, idname+"-"+program+"-parameters-error-global.txt")

	return
# End of cleanup function

# Begin of check_program_exists function
def check_program_exists(program):
	"""
	#####################################################################################
	# def check_program_exists(program)
	# Function   : Checks if a command exists by exploring path directories
	# Param      : program, command name like 'ls' or 'cat' or 'echo' or anything.
	#####################################################################################
	"""
	global PATH

	fpath, fname = os.path.split(program)
	result=0
	final_path=''
	if fpath:
		print "OTHER"
		if os.path.isfile(program) and os.access(program, os.X_OK):
			result=1
			final_path=program
		if os.path.isfile(program+".sh") and os.access(program+".sh", os.X_OK):
			result=1
			final_path=program+".sh"
		if os.path.isfile(program+".py") and os.access(program+".py", os.X_OK):
			result=1
			final_path=program+".py"
		if os.path.isfile(program+".bat") and os.access(program+".bat", os.X_OK):
			result=1
			final_path=program+".bat"
		if os.path.isfile(program+".exe") and os.access(program+".exe", os.X_OK):
			result=1
			final_path=program+".exe"
		final_path=os.path.abspath(final_path)
		print "final_path="+final_path

	if result == 0:
		for path in PATH.split(os.pathsep):
			path = path.strip('"')
			exe_file = os.path.join(path, fname)
			if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
				result=1
				final_path=exe_file
			if os.path.isfile(exe_file+".sh") and os.access(exe_file+".sh", os.X_OK):
				result=1
				final_path=exe_file+".sh"
			if os.path.isfile(exe_file+".py") and os.access(exe_file+".py", os.X_OK):
				result=1
				final_path=exe_file+".py"
			if os.path.isfile(exe_file+".bat") and os.access(exe_file+".bat", os.X_OK):
				result=1
				final_path=exe_file+".bat"
			if os.path.isfile(exe_file+".exe") and os.access(exe_file+".exe", os.X_OK):
				result=1
				final_path=exe_file+".exe"

	if result == 0:
		exit_program("Didn't find "+program,999)

	return final_path
# End of check_program_exists function

# Begin of execute_command_or_else_stop function
def execute_command_or_else_stop(command_line,output='OFF',echo='OFF'):
	"""
	#####################################################################################
	# def execute_command_or_else_stop(command_line,echo='OFF')
	# Function   : This is a bit drastic, can be used to execute any command
	#              and stops if the exit code of the command is non-zero.
	# Param      : command_line, a string containing a command. We simply 'eval' it.
	# Param      : output, if 'on' the method will return the execution output.
	# Param      : echo, if 'on' we only print the instruction, it's like a dry run.
	# Return	 : the execution output
	#####################################################################################
	"""

	# Before we remove white spaces, newlines and tabs
	pat = re.compile(r'\s+')
	command_line=pat.sub(' ',command_line)
	out=''

	# We can run in a dry mode
	if  echo == 'ON':
		writeLog('Echoing: execute_command_or_else_stop ('+command_line+')')
	else:
		writeLog('Evaluating: execute_command_or_else_stop ('+command_line+')')
		args = shlex.split(command_line)

		if output == 'OFF':
			p = subprocess.Popen(args)
			p.wait()
		else:
			p = subprocess.Popen(args,
							stdout=subprocess.PIPE,
							stderr=subprocess.PIPE)
			out, err = p.communicate()
			print out

		if p.returncode != 0 :
			writeLog('The command ('+command_line+') failed. '+str(p.returncode))

	return	p.returncode
# End of execute_command_or_else_stop function

# Begin of exit_program function
def exit_program(text,val=950):
	"""
	#####################################################################################
	# def exit_program(text,val=100)
	# Function   : Exit with a message, status.
	# Param      : text, message before exit, it will be displayed throught stderr.
	# Param      : val, termination value
	#####################################################################################
	"""

	writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] "+text)
	if isinstance(val,int):
		exit(val)
	else:
		exit(950)

	return
# End of exit_program function

# Begin of writeLog function
def writeLog(text,filename=''):
	"""
	###########################################################################
	# def writeLog(log)
	# Function  : write text in a file
	# Param	    : text, text to add in the filename
	# Return    :
	###########################################################################
	"""

	global program
	global log_file

	if filename=='':
		fo = open(log_file, "a")
		print text
	else:
		fo = open(filename, "w")
	fo.write(text+'\n')
	fo.close()

	# Every 10 Mb clean the log file and zip it
	if filename=='' and os.path.getsize(log_file) > 10*1024*1024:
		zip_file=os.path.join(dir_data,'log-'+program+'-'+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+'.zip')
		zipf = zipfile.ZipFile(zip_file, 'w')
		zipf.write(log_file)
		zipf.close()
		fo = open(log_file, "w")
		fo.write('')
		fo.close()
# End of writeLog function

# Begin of writeLock function
def writeLock(text,filename):
	"""
	###########################################################################
	# def writeLog(log)
	# Function  : we update the content of the lock file
	# Param	    : text, text to add in the filename
	# Return    :
	###########################################################################
	"""

	tmp=os.path.join(dir_data,'tmplock-'+program)
	writeLog(text,tmp)
	shutil.copyfile(tmp,filename)
	removeFile(tmp)
# End of writeLock function

# Begin of removeFile function
def removeFile(filename):
	"""
	###########################################################################
	# def removeFile(filename)
	# Function  : remove a file if it exists
	# Param	    : filename, file to be removed
	# Return    :
	###########################################################################
	"""

	if os.path.isfile(filename):
		os.unlink (filename)

	return
# End of removeFile function

# Begin of readFileParameters function
def readFileParameters(text_file):
	"""
	###########################################################################
	# def readFileParameters(text_file)
	# Function  : read the content and put in one string
	# Param	    : text_file, file with the content
	# Return    :
	###########################################################################
	"""
	global URL

	content=" "
	files_list=" "
	files=False
	with open(text_file) as fp:
		for line in fp:
			if "FILES" in line :
				files=True

			if ("URL-TIG:" in line) :
				URL=line.strip('URL-TIG:').strip()

			if not ("PARAMETERS" in line) and not ("URL-TIG:" in line) and not files:
				content+=" -"+line.rstrip('\n')

			if not ("FILES" in line) and files:
				files_list+=" "+os.path.join(dir_data,line.rstrip('\n'))

	content=files_list+" "+content
	return content
# End of readFileParameters function

# Begin of uploadResults function
def uploadResults(idname,init,finish,initsql):
	"""
	###########################################################################
	# def uploadResults(idname)
	# Function  : upload the results to TIG's website
	# Param	    : idname, id
	# Param	    : filename to be uploaded at the server
	# Return    :
	###########################################################################
	"""
	global URL
	global program

	error=True
	filename=idname+'_'+program+'.txt'
	result_file=os.path.join(dir_data,filename)
	if not os.path.isfile(result_file):
		filename=idname+'_'+program+'.nii.gz'
		result_file=os.path.join(dir_data,filename)

	if not os.path.isfile(result_file):
		filename=idname+'_'+program+'.zip'
		result_file=os.path.join(dir_data,filename)

	# We look for the result file
	if os.path.isfile(result_file):
		# Copy the result into the server
		files = {'file': open(result_file, 'rb')}
		#chunk=0
		#if os.path.getsize(result_file) > 1024*1024:
		#	chunk=1
		#data = {'program': program, 'id': filename, 'chunk' : chunk }
		data = {'program': program , 'id': filename}
		writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Sending "+idname+"'s results to: "+URL+"file.php ")
		writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] File size: "+"{:.3f}".format(os.path.getsize(result_file)/(1024*1024))+ "Mb")
		r = requests.post(URL+'file.php', data=data, files=files)
		writeLog(r.text)
		decoded=json.loads(r.text.strip())
		# We analyze what happend during the upload process
		if  r.status_code != 200 or decoded['result']!="OK":
			writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Upload fails: "+str(r.status_code)+os.linesep+"ID:"+idname+os.linesep+"RESPONSE:"+r.text)
			error=True
		else:
			if "WMGM" in program:
				# We send the second file, only if we are using WMGM program
				filenamezip=idname+'_'+program+'.zip'
				result_file=os.path.join(dir_data,filenamezip)
				files = {'file': open(result_file, 'rb')}
				data = {'program': program , 'id': filenamezip}
				writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Sending "+idname+"'s results to: "+URL+"file.php ")
				writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] File size: "+"{:.3f}".format(os.path.getsize(result_file)/(1024*1024))+ "Mb")
				r = requests.post(URL+'file.php', data=data, files=files)
				writeLog(r.text)
				decoded=json.loads(r.text.strip())
				# We analyze what happend during the upload process
				if  r.status_code != 200 or decoded['result']!="OK":
					writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Upload 2 fails: "+str(r.status_code)+os.linesep+"ID:"+idname+os.linesep+"RESPONSE:"+r.text)
					error=True
				else:
					# Upload succesfully
					# We confirm that the file is done and ready to send to the user
					writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Uploaded succesfully")

			data = {'program': program , 'id': idname, 'filename': filename , 'tmpname' : decoded['id'] , 'init' : init , 'finish' : finish, 'initsql' : initsql }
			r = requests.post(URL+'file_done.php', data=data)
			writeLog(r.text)
			error=r.status_code == requests.codes.ok
			decoded=json.loads(r.text.strip())
			# We analyze what happen with the confirmation
			if  r.status_code != 200 or decoded['result']!="OK":
				writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Notification fails: "+str(r.status_code)+os.linesep+"ID:"+idname+os.linesep+"RESPONSE:"+r.text)
				error=True
			else:
				writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Upload notified")
				error=False
	else:
		writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Upload fails, no such file:"+result_file)

	return error
# End of uploadResults function

############################################################################################################
############################################################################################################
############################################################################################################
############################################################################################################

# Program starts
# Register cleanup function as a function to be executed at termination
atexit.register(cleanup)
program=''
file_processed=''
arg=len(sys.argv)
argv=sys.argv
lock_file=''
if arg <= 1:
	print 'Error, you should define a program to be executed'
	exit(-1)

# Prepare the needed name files
program=argv[1].strip().upper()
print "Program: " + program
lock_file=os.path.join(dir_data,'lock-'+program)
print "lock_file: " + lock_file
log_file=os.path.abspath('log-'+program+'.txt')

# Check if the program to execute exists
execute=check_program_exists(program)

# If exists a queue of this program
print "Check if a queue of this program already exists..."
if not os.path.isfile(lock_file) or ("CHALLENGE" in program):
	print "--> Nope!"
	# Change to the data directory
	os.chdir(dir_data)

	# Take the files that need to be processed sorted by date
	files_to_be_processed=glob('*'+program+'-parameters.txt')
	files_to_be_processed.sort(key=lambda x: os.path.getmtime(x))
	print "List of files to process:"
	print files_to_be_processed

	# While there are files to be processed
	while len(files_to_be_processed)>0:
		# Create or update the lock to avoid mutliple executions
		file_processed=files_to_be_processed[0]
		writeLock("FILE processed: "+file_processed+"\n",lock_file)

		# Read the parameters
		parameters=readFileParameters(file_processed)

		# We get the idname
		idname=file_processed.split("-"+program)[0]

		# Start the execution
		writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Start: "+file_processed)
		init=datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y");
		initsql=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S");
		exit_value=execute_command_or_else_stop(execute+" "+idname+" "+parameters, output='ON')
		writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Finish: "+file_processed)
		finish=datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y")

		# If it has finished successfuly we upload the results to the server
		if exit_value == 0 :
			error=uploadResults(idname,init,finish,initsql)
			if not error:
				writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Results upload: "+file_processed)
				os.rename(file_processed, idname+"-"+program+"-parameters-done.txt")
				writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Finish succesfully, "+idname+" is done")
			else:
				writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Error uploading results: "+file_processed)
				os.rename(file_processed, idname+"-"+program+"-parameters-error-uploading.txt")
		else:
			writeLog("["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] Error computing results: "+file_processed)
			os.rename(file_processed, idname+"-"+program+"-parameters-error-computing.txt")

		# Update the list of files to be processed
		os.chdir(dir_data)
		files_to_be_processed=glob('*'+program+'-parameters.txt')
		files_to_be_processed.sort(key=lambda x: os.path.getmtime(x))

	# Finished, then we can remove the lock file
	removeFile(lock_file)
	idname=''
else:
	print "--> Yup! ["+datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")+"] "+program+" is already running !!!!"
	lock_file=''

exit(0)
# Program finishes
