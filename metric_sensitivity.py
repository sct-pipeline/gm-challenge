#!/usr/bin/env python

import sys, os, shutil, subprocess, argparse
import numpy as np
import pandas as pd

def get_parameters():
    parser = argparse.ArgumentParser(description='Measure metric sensitivity for GM challenge')
    parser.add_argument('file_1')
    parser.add_argument('file_2')
    parser.add_argument('phantom_cord_seg')
    parser.add_argument('phantom_gm_seg')
    parser.add_argument('phantom_wm_seg')
    args = parser.parse_args()

    return args

def main():
    program = 'metric_sensitivity'
    file_1 = args.file_1
    file_2 = args.file_2
    phantom_cord_seg = args.phantom_cord_seg
    phantom_gm_seg = args.phantom_gm_seg
    phantom_wm_seg = args.phantom_wm_seg
    filename_1 = os.path.basename(file_1)
    filename_2 = os.path.basename(file_2)

    output_dir = os.path.dirname(file_1) + '/' + program

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    shutil.copy2(file_1, output_dir)
    shutil.copy2(file_2, output_dir)

    os.chdir(output_dir)

    ########## Compute metrics

    # Initialize data frame for reporting results
    results = pd.DataFrame(np.nan, index=['SNR', 'Contrast'], columns=['Metric Value'])

    #------- SNR -------
    # Concatenate image 1 and image 2 to generate the proper input to sct_compute_snr
    subprocess.check_output(
        ["sct_image", "-i", os.path.join(filename_1 + ',' + filename_2), "-concat", "t",
         "-o", "t2s_phantom_concat.nii.gz"], stdin=None, stderr=subprocess.STDOUT)

    # Calculate the SNR
    snr = subprocess.Popen(
        ["sct_compute_snr", "-i", "t2s_phantom_concat.nii.gz", "-m", phantom_cord_seg, "-vol",
         "0,1"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    snr.wait()

    if snr.returncode != 0:
        print(snr.communicate()[0])

    snr_output = snr.communicate()[0]
    snr_results = snr_output.split("SNR_diff =")

    results.loc['SNR'] = snr_results[1].strip()

    #------- Contrast -------
    # Compute the mean signal value in both the white matter and gray matter of image 1
    subprocess.check_output(["sct_extract_metric", "-i", filename_1, "-f",
                             phantom_wm_seg, "-method", "max", "-o", "mean_wm.txt"], stdin=None, stderr=subprocess.STDOUT)

    subprocess.check_output(["sct_extract_metric", "-i", filename_1, "-f",
                             phantom_gm_seg, "-method", "max", "-o", "mean_gm.txt"], stdin=None, stderr=subprocess.STDOUT)

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

    if os.path.isfile('metric_sensitivity.txt'):
        os.remove('metric_sensitivity.txt')

    # Write metric values to a text file
    results.columns = ['']

    results_to_return = open('metric_sensitivity.txt', 'w')
    results_to_return.write('The following metric values were calculated:\n')
    results_to_return.write(results.__repr__())
    results_to_return.close()

if __name__ == "__main__":
    args = get_parameters()
    main()