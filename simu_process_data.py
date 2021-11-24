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


import os
import argparse
import glob
from subprocess import call
import pandas


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


def compute_metrics(file_1, file_2, file_wm, file_gm, path_out):
    # Compute SNR using both methods
    call(f'sct_image -i {file_1} {file_2} -concat t -o {path_out}data_concat.nii.gz'.split(' '))
    call(f'sct_compute_snr -i {path_out}data_concat.nii.gz -method diff -m {file_wm} -o {path_out}snr_diff.txt'.
         split(' '))
    snr_diff = float(open(f'{path_out}snr_diff.txt', 'r').readline())
    call(f'sct_compute_snr -i {path_out}data_concat.nii.gz -method single -m {file_wm} -m-noise {file_wm} '
         f'-rayleigh 0 -o {path_out}snr_single.txt'.split(' '))
    snr_single = float(open(f'{path_out}snr_single.txt', 'r').readline())
    # Compute average value in WM and GM on a slice-by-slice basis
    call(f'sct_extract_metric -i {file_1} -f {file_wm} -method bin -o {path_out}signal_wm.csv'.split(' '))
    call(f'sct_extract_metric -i {file_2} -f {file_wm} -method bin -o {path_out}signal_wm.csv -append 1'.split(' '))
    call(f'sct_extract_metric -i {file_1} -f {file_gm} -method bin -o {path_out}signal_gm.csv'.split(' '))
    call(f'sct_extract_metric -i {file_2} -f {file_gm} -method bin -o {path_out}signal_gm.csv -append 1'.split(' '))
    # Compute contrast slicewise and average across slices
    pd_gm = pandas.read_csv(f'{path_out}signal_gm.csv')
    pd_wm = pandas.read_csv(f'{path_out}signal_wm.csv')
    pd_contrast = abs(pd_gm['BIN()'] - pd_wm['BIN()']) / pandas.DataFrame([pd_gm['BIN()'], pd_wm['BIN()']]).min()
    contrast = pd_contrast.mean()
    # Build dict
    dict_out = {
        'SNR_single': snr_single,
        'SNR_diff': float(open(f'{path_out}snr_diff.txt', 'r').readline()),
        'Contrast': contrast,
        'CNR': contrast * snr_single,
        }
    return dict_out


def main():
    path_output = 'simu_results/'
    file_output = "results_all.csv"  # csv output

    # Get list of files in folder1
    folder1, folder2 = folder_data
    fname_csv_list = sorted(glob.glob(os.path.join(folder1, "*.csv")))

    # initialize dataframe
    results_all = pandas.DataFrame(columns={'WM',
                                            'GM',
                                            'Noise',
                                            'Smooth',
                                            'SNR',
                                            'Contrast',
                                            'CNR'})

    file_wm = os.path.join(folder1, 'mask_wm.nii.gz')
    file_gm = os.path.join(folder1, 'mask_gm.nii.gz')

    # loop and process
    os.makedirs(path_output, exist_ok=True)
    for fname_csv in fname_csv_list:
        # get file name
        metadata = pandas.read_csv(fname_csv, index_col=0).to_dict()['0']
        file_data = metadata["File"]
        # get fname of each nifti file
        fname1 = os.path.join(folder1, file_data)
        fname2 = os.path.join(folder2, file_data)
        # display
        print("\nData #1: " + fname1)
        print("Data #2: " + fname2)
        # process pair of data
        results = compute_metrics(fname1, fname2, file_wm, file_gm, path_output)
        # append to dataframe
        results_all = results_all.append({'WM': metadata['WM'],
                                          'GM': metadata['GM'],
                                          'Noise': metadata['Noise'],
                                          'Smooth': metadata['Smooth'],
                                          'SNR_single': results['SNR_single'],
                                          'SNR_diff': results['SNR_diff'],
                                          'Contrast': results['Contrast'],
                                          'CNR': results['CNR']},ignore_index=True)
    results_all.to_csv(file_output)


if __name__ == "__main__":
    args = get_parameters()
    folder_data = args.input
    file_seg = args.seg
    file_gmseg = args.gmseg
    register = args.register
    verbose = args.verbose
    main()
