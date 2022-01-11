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
    return parser


def run(cmd):
    """Wrapper to run Unix commands"""
    call(cmd.split(' '), stdout=open(os.devnull, "w"))


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
                                            'SNR_single',
                                            'SNR_diff',
                                            'Contrast',
                                            'CNR_single',
                                            'CNR_diff'})

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
        results = compute_cnr.main(['--data1', fname1,
                                    '--data2', fname2,
                                    '--mask-noise', file_wm,
                                    '--mask-wm', file_wm,
                                    '--mask-gm', file_gm])
        # append to dataframe
        results_all = results_all.append({'WM': metadata['WM'],
                                          'GM': metadata['GM'],
                                          'Noise': metadata['Noise'],
                                          'Smooth': metadata['Smooth'],
                                          'SNR_single': results['SNR_single'],
                                          'SNR_diff': results['SNR_diff'],
                                          'Contrast': results['Contrast'],
                                          'CNR_single': results['CNR_single'],
                                          'CNR_diff': results['CNR_diff']},
                                         ignore_index=True)
        pbar.update(1)
    pbar.close()
    results_all.to_csv(file_output)


if __name__ == "__main__":
    main()
