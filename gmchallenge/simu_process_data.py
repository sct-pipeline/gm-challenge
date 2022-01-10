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

# TODO: fix wrong SNR_diff value

import os
import argparse
import glob
from subprocess import call
import pandas
import tqdm

from gmchallenge import compute_cnr


def get_parser():
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
    return parser


def run(cmd):
    """Wrapper to run Unix commands"""
    call(cmd.split(' '), stdout=open(os.devnull, "w"))


def compute_metrics(file_1, file_2, file_wm, file_gm, path_out):
    # Compute SNR using both methods
    run(f'sct_image -i {file_1} {file_2} -concat t -o {path_out}data_concat.nii.gz')
    run(f'sct_compute_snr -i {path_out}data_concat.nii.gz -method diff -m {file_wm} -o {path_out}snr_diff.txt')
    run(f'sct_compute_snr -i {path_out}data_concat.nii.gz -method single -m {file_wm} -m-noise {file_wm} -rayleigh 0 '
        f'-o {path_out}snr_single.txt')
    snr_single = float(open(f'{path_out}snr_single.txt', 'r').readline())
    # Compute average value in WM and GM on a slice-by-slice basis
    run(f'sct_extract_metric -i {file_1} -f {file_wm} -method wa -o {path_out}signal_wm.csv')
    run(f'sct_extract_metric -i {file_2} -f {file_wm} -method wa -o {path_out}signal_wm.csv -append 1')
    run(f'sct_extract_metric -i {file_1} -f {file_gm} -method wa -o {path_out}signal_gm.csv')
    run(f'sct_extract_metric -i {file_2} -f {file_gm} -method wa -o {path_out}signal_gm.csv -append 1')
    # Compute contrast slicewise and average across slices
    pd_gm = pandas.read_csv(f'{path_out}signal_gm.csv')
    pd_wm = pandas.read_csv(f'{path_out}signal_wm.csv')
    pd_contrast = 100 * abs(pd_gm['WA()'] - pd_wm['WA()']) / pandas.DataFrame([pd_gm['WA()'], pd_wm['WA()']]).min()
    contrast = pd_contrast.mean()
    # Build dict
    dict_out = {
        'SNR_single': snr_single,
        'SNR_diff': float(open(f'{path_out}snr_diff.txt', 'r').readline()),
        'Contrast': contrast,
        'CNR': contrast * snr_single,
        }
    return dict_out


def main(argv=None):
    parser = get_parser()
    args = parser.parse_args(argv)
    path_output = 'simu_results/'
    file_output = os.path.join(path_output, "results_all.csv")

    # Get list of files in folder1
    folder1, folder2 = args.input
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
    pbar = tqdm.tqdm(total=len(fname_csv_list))
    for fname_csv in fname_csv_list:
        # get file name
        metadata = pandas.read_csv(fname_csv, index_col=0).to_dict()['0']
        file_data = metadata["File"]
        # get fname of each nifti file
        fname1 = os.path.join(folder1, file_data)
        fname2 = os.path.join(folder2, file_data)
        # process pair of data
        results = compute_metrics(fname1, fname2, file_wm, file_gm, path_output)
        # TODO: replace code above by code below.
        # https://github.com/sct-pipeline/gm-challenge/issues/70
        # results = compute_cnr.main(['--data1', fname1,
        #                             '--data2', fname2,
        #                             '--mask-noise', file_wm,
        #                             '--mask-wm', file_wm,
        #                             '--mask-gm', file_gm])
        # append to dataframe
        results_all = results_all.append({'WM': metadata['WM'],
                                          'GM': metadata['GM'],
                                          'Noise': metadata['Noise'],
                                          'Smooth': metadata['Smooth'],
                                          'SNR_single': results['SNR_single'],
                                          'SNR_diff': results['SNR_diff'],
                                          'Contrast': results['Contrast'],
                                          'CNR': results['CNR']},ignore_index=True)
        pbar.update(1)
    pbar.close()
    results_all.to_csv(file_output)


if __name__ == "__main__":
    main()
