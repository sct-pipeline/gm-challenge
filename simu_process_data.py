#!/usr/bin/env python
#
# Process data from two phantom folders pairwise. This script will look for csv files in each phantom folder (generated
# by simu_create_phantom.py), and will process data pairwise between folder1 and folder2.
#
# USAGE:
#   python simu_process_data.py -i phantom1 phantom2 -s phantom1/mask_cord.nii.gz -g phantom1/mask_gm.nii.gz -r 0
#
# OUTPUT:
#   results_simu.csv: quantitative results in CSV format
#
# Authors: Julien Cohen-Adad


import sys, os, shutil, argparse, pickle, io, glob
from subprocess import call
import numpy as np
import pandas as pd
import pandas as pd


def get_parameters():
    parser = argparse.ArgumentParser(description='Compute metrics to assess the quality of spinal cord images. This '
                                                 'script requires two input files of scan-rescan acquisitions, which '
                                                 'will be used to compute the SNR. Other metrics (contrast, sharpness) '
                                                 'will be computed from the first file.')
    parser.add_argument("-i", "--input",
                        help="List here the two folders to process. They should contain the exact same file names.",
                        nargs='+',
                        required=True)
    parser.add_argument("-s", "--seg",
                        help="Spinal cord segmentation for the first dataset.",
                        required=False)
    parser.add_argument("-g", "--gmseg",
                        help="Gray matter segmentation for the first dataset.",
                        required=False)
    parser.add_argument("-r", "--register",
                        help="Perform registration between scan #1 and scan #2. Default=0 (data already registered).",
                        type=int,
                        default=0,
                        required=False)
    parser.add_argument("-v", "--verbose",
                        help="Verbose {0,1}. Default=1",
                        type=int,
                        default=1,
                        required=False)
    args = parser.parse_args()
    return args


def compute_metrics(file_1, file_2):
    # Compute SNR using both methods
    call(f'sct_image -i {file_1} {file_2} -concat t -o data_concat.nii.gz'.split(' '))
    # call(f'sct_compute_snr -i data_concat.nii.gz -method diff -m ${file_1}_wmseg_erode.nii.gz -o snr_diff.txt'
    return 0


def main():
    # output_dir = "./output_wmgm"  # TODO: be able to set with argument
    file_output = "results_all.csv"  # csv output
    # fdata2 = "data2.nii.gz"

    # Get list of files in folder1
    folder1, folder2 = folder_data
    fname_csv_list = sorted(glob.glob(os.path.join(folder1, "*.csv")))

    # initialize dataframe
    results_all = pd.DataFrame(columns={'WM',
                                        'GM',
                                        'Noise',
                                        'Smooth',
                                        'SNR',
                                        'Contrast',
                                        'Sharpness'})

    # loop and process
    i = 0
    for fname_csv in fname_csv_list:
        # get file name
        metadata = pd.read_csv(fname_csv, index_col=0).to_dict()['0']
        file_data = metadata["File"]
        # get fname of each nifti file
        fname1 = os.path.join(folder1, file_data)
        fname2 = os.path.join(folder2, file_data)
        # display
        print("\nData #1: " + fname1)
        print("Data #2: " + fname2)
        # process pair of data
        results = compute_metrics(fname1, fname2)
        # append to dataframe
        results_all = results_all.append({'WM': metadata['WM'],
                                          'GM': metadata['GM'],
                                          'Noise': metadata['Noise'],
                                          'Smooth': metadata['Smooth'],
                                          'SNR_single': results.loc['SNR_single'][0],
                                          'SNR_diff': results.loc['SNR_diff'][0],
                                          'Contrast': results.loc['Contrast'][0]}, ignore_index=True)
    results_all.to_csv(file_output)


if __name__ == "__main__":
    args = get_parameters()
    folder_data = args.input
    file_seg = args.seg
    file_gmseg = args.gmseg
    register = args.register
    verbose = args.verbose
    main()
