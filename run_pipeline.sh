#!/bin/bash
#
# Batch script that loops across subjects and process them. It assumes that the
# "data/" folder is local.
#
# Usage:
#   ./run_pipeline.sh
#
# Add the flag "-x" after "!/bin/bash" for full verbose of commands.
# Julien Cohen-Adad 2018-10-10

# defines parameters
PATH_DATA='data'

# Exit if user presses CTRL+C (Linux) or CMD+C (OSX)
trap "echo Caught Keyboard Interrupt within script. Exiting now.; exit" INT

# Build color coding (cosmetic stuff)
Color_Off='\033[0m'  # Text Reset
Green='\033[0;92m'  # Green
Red='\033[0;91m'  # Red
On_Black='\033[40m'  # Black

# Get local path
export PATH_GMCHALLENGE=`pwd`

# Go to path data folder that encloses all subjects' folders
cd ${PATH_DATA}

# Get list of all subject folders from current directory
SUBJECTS=`ls -d */`

# Loop across subjects
for subject in ${SUBJECTS[@]}; do
  # Display stuff
  printf "${Green}${On_Black}\n========================\n\
PROCESSING SUBJECT: ${subject%?}\n========================\n\
  ${Color_Off}"
  # Go to subject folder
  cd ${subject}
  # Run process
  echo ${SCT_DIR}/python/bin/python ${PATH_GMCHALLENGE}/process_data.py
  # Go back to parent folder
  cd ..
done
