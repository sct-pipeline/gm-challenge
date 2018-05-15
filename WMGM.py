#!/usr/bin/env python
##############################################################
#
# This script will execute commands for Spinal Cord Toolbox (SCT) to process the data and compute metrics for assessing
# the quality of the image.
#
# Two NIfTI files are required: an initial scan (image 1) and a re-scan without repositioning (image 2).
#
# The script should be launched using SCT's python:
#
#    cd $SCT_DIR
#    source python/bin/activate
#    cd PATH_TO_DATA
#    python PATH_OF_THIS_SCRIPT/WMGM.py <image 1> <image 2>
#
# Author: Stephanie Alley, Julien Cohen-Adad
# Copyright: see:
#
##############################################################

import sys, os, shutil, subprocess
import numpy as np
import pandas as pd


class Param:
    def __init__(self):
        parameters = sys.argv[:]

        self.dir_data = os.path.dirname(parameters[1])

        self.file_1 = parameters[1]
        self.file_2 = parameters[2]

        self.filename_1 = os.path.basename(parameters[1])
        self.filename_2 = os.path.basename(parameters[2])

        self.volume_1 = self.filename_1.split(os.extsep)[0]
        self.volume_2 = self.filename_2.split(os.extsep)[0]
        self.ext = '.'.join(self.filename_1.split(os.extsep)[1:])

def err(output):
    status = output.communicate()

    if output.returncode != 0:
        print(status[0])

def main():
    program = 'WMGM'
    dir_data = param.dir_data
    file_1 = param.file_1
    file_2 = param.file_2
    volume_1 = param.volume_1
    volume_2 = param.volume_2
    ext = param.ext

    if not dir_data:
        dir_data = os.getcwd()

    output_dir = os.path.join(dir_data + '/' + program)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    shutil.copy2(file_1, output_dir)
    shutil.copy2(file_2, output_dir)

    os.chdir(output_dir)

    ########## Pre-processing
    
    # Register image 2 to image 1
    register = subprocess.Popen(
        ["sct_register_multimodal", "-i", file_2, "-d", file_1, "-param", "step=1,type=im,algo=rigid", "-x", "nn", "-o",
         os.path.join(volume_2 + '_reg' + '.' + ext)], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    register.wait()
    err(register)

    # Segment spinal cord
    seg_sc_v1 = subprocess.Popen(["sct_deepseg_sc", "-i", os.path.join(volume_1 + '.' + ext), "-c", "t2s", "-qc", "./qc"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    seg_sc_v1.wait()
    err(seg_sc_v1)

    seg_sc_v2 = subprocess.Popen(
        ["sct_deepseg_sc", "-i", os.path.join(volume_2 + '_reg' + '.' + ext), "-c", "t2s", "-qc", "./qc"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    seg_sc_v2.wait()
    err(seg_sc_v2)

    # Segment gray matter
    seg_gm_v1 = subprocess.Popen(["sct_deepseg_gm", "-i", os.path.join(volume_1 + '.' + ext)], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    seg_gm_v1.wait()
    err(seg_gm_v1)

    seg_gm_v2 = subprocess.Popen(["sct_deepseg_gm", "-i", os.path.join(volume_2 + '_reg' + '.' + ext)], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    seg_gm_v2.wait()
    err(seg_gm_v2)

    # Generate white matter segmentation
    seg_wm_v1 = subprocess.Popen(["sct_maths", "-i", os.path.join(volume_1 + '_seg' + '.' + ext), "-sub",
                             os.path.join(volume_1 + '_gmseg' + '.' + ext), "-o",
                             os.path.join(volume_1 + '_wmseg' + '.' + ext)], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    seg_wm_v1.wait()
    err(seg_wm_v1)

    seg_wm_v2 = subprocess.Popen(["sct_maths", "-i", os.path.join(volume_2 + '_reg' + '_seg' + '.' + ext), "-sub",
                             os.path.join(volume_2 + '_reg' + '_gmseg' + '.' + ext), "-o",
                             os.path.join(volume_2 + '_reg' + '_wmseg' + '.' + ext)], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    seg_wm_v2.wait()
    err(seg_wm_v2)

    ########## Analysis: compute metrics

    # Initialize data frame for reporting results
    results = pd.DataFrame(np.nan, index=['SNR', 'Contrast', 'Sharpness'], columns=['Metric Value'])

    #------- SNR -------
    # Concatenate image 1 and image 2 to generate the proper input to sct_compute_snr
    concat = subprocess.Popen(
        ["sct_image", "-i", os.path.join(volume_1 + '.' + ext + ',' + volume_2 + '_reg' + '.' + ext), "-concat", "t",
         "-o", "t2s_concat.nii.gz"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    concat.wait()
    err(concat)

    # Calculate the SNR
    snr = subprocess.Popen(
        ["sct_compute_snr", "-i", "t2s_concat.nii.gz", "-m", os.path.join(volume_1 + '_seg' + '.' + ext), "-vol",
         "0,1"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    snr.wait()

    if snr.returncode != 0:
        print(snr.communicate()[0])

    snr_output = snr.communicate()[0]
    snr_results = snr_output.split("SNR_diff =")

    results.loc['SNR'] = snr_results[1].strip()

    #------- Contrast -------
    # Compute the mean signal value in both the white matter and gray matter of image 1
    mean_wm = subprocess.Popen(["sct_extract_metric", "-i", os.path.join(volume_1 + '.' + ext), "-f",
                             os.path.join(volume_1 + '_wmseg' + '.' + ext), "-method", "max", "-o", "mean_wm.txt"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    mean_wm.wait()
    err(mean_wm)

    mean_gm = subprocess.Popen(["sct_extract_metric", "-i", os.path.join(volume_1 + '.' + ext), "-f",
                             os.path.join(volume_1 + '_gmseg' + '.' + ext), "-method", "max", "-o", "mean_gm.txt"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    mean_gm.wait()
    err(mean_gm)

    # Extract the mean signal value for the white matter and the gray matter
    with open("mean_wm.txt") as file:
        output_wm = file.readlines()

    mean_wm_results = output_wm[-1].split(",")

    with open("mean_gm.txt") as file:
        output_gm = file.readlines()

    mean_gm_results = output_gm[-1].split(",")

    # Calculate the contrast value
    contrast = abs(float(mean_wm_results[3]) - float(mean_gm_results[3])) / min([float(mean_wm_results[3]), float(mean_gm_results[3])])

    results.loc['Contrast'] = contrast

    #------- Sharpness -------
    # Compute the Laplacian of image 1
    laplacian = subprocess.Popen(["sct_maths", "-i", os.path.join(volume_1 + '.' + ext), "-laplacian", "3", "-o",
                             os.path.join(volume_1 + '_lap' + '.' + ext)], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    laplacian.wait()
    err(laplacian)

    # Compute the mean Laplacian of the spinal cord for image 1
    mean_lap = subprocess.Popen(["sct_extract_metric", "-i", os.path.join(volume_1 + '_lap' + '.' + ext), "-f",
                             os.path.join(volume_1 + '_seg' + '.' + ext), "-method", "max", "-o", "sharpness.txt"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    mean_lap.wait()
    err(mean_lap)

    # Extract the mean Laplacian value of the cord
    with open("sharpness.txt") as file:
        output_sharp = file.readlines()

    sharpness = output_sharp[-1].split(",")

    results.loc['Sharpness'] = sharpness[3]

    if os.path.isfile('WMGM.txt'):
        os.remove('WMGM.txt')

    # Write metric values to a text file
    results.columns = ['']

    results_to_return = open('WMGM.txt', 'w')
    results_to_return.write('The following metric values were calculated:\n')
    results_to_return.write(results.__repr__())
    results_to_return.close()

if __name__ == "__main__":
    param = Param()
    main()
