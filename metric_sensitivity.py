#!/usr/bin/env python

import sys, os, shutil, subprocess, argparse
import numpy as np
import pandas as pd

def get_parameters():
    parser = argparse.ArgumentParser(description='Measure metric sensitivity for GM challenge')
    parser.add_argument('image_1')
    parser.add_argument('image_2')
    args = parser.parse_args()
    return args

def main():
    image_1 = os.path.basename(args.image_1)
    image_2 = os.path.basename(args.image_2)

    # Initialize data frame for reporting results
    results = pd.DataFrame(np.nan, index=['SNR', 'Contrast'], columns=['Metric Value'])

    ########## Compute metrics

    #------- SNR -------
    # Concatenate image 1 and image 2 to generate the proper input to sct_compute_snr
    subprocess.check_output(["sct_image", "-i", os.path.join(image_1 + ',' + image_2), "-concat", "t",
         "-o", "t2s_concat.nii.gz"], stdin=None, stderr=subprocess.STDOUT)

    # Calculate the SNR
    snr = subprocess.Popen(
        ["sct_compute_snr", "-i", "t2s_concat.nii.gz", "-m", "mask_cord.nii.gz", "-vol",
         "0,1"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    snr.wait()

    if snr.returncode != 0:
        print(snr.communicate()[0])

    snr_output = snr.communicate()[0]
    snr_results = snr_output.split("SNR_diff =")

    results.loc['SNR'] = snr_results[1].strip()

    #------- Contrast -------
    # Generate a white matter mask
    subprocess.check_output(["sct_maths", "-i", "mask_cord.nii.gz", "-sub",
                             "mask_gm.nii.gz", "-o", "mask_wm.nii.gz"], stdin=None, stderr=subprocess.STDOUT)

    # Compute the mean signal value in both the white matter and gray matter of image 1
    subprocess.check_output(["sct_extract_metric", "-i", image_1, "-f",
                             "mask_wm.nii.gz", "-method", "max", "-o", "mean_wm.txt"], stdin=None, stderr=subprocess.STDOUT)

    subprocess.check_output(["sct_extract_metric", "-i", image_1, "-f",
                             "mask_gm.nii.gz", "-method", "max", "-o", "mean_gm.txt"], stdin=None, stderr=subprocess.STDOUT)

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

    image_name = image_1.split(os.extsep)[0]

    if os.path.isfile(os.path.join(image_name + '_metric_sensitivity.txt')):
        os.remove(os.path.join(image_name + '_metric_sensitivity.txt'))

    # Write metric values to a text file
    results.columns = ['']

    results_to_return = open(os.path.join(image_name + '_metric_sensitivity.txt'), 'w')
    results_to_return.write('The following metric values were calculated:\n')
    results_to_return.write(results.__repr__())
    results_to_return.close()

if __name__ == "__main__":
    args = get_parameters()
    main()