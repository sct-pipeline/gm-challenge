#!/usr/bin/env python
#
# Make figures to compare SNR methods: SNR_diff versus SNR_single.
# This script will loop across all subjects, retrieve the results/results.csv and generate a plot.
#
# USAGE:
# The script should be launched using SCT's python:
#   ${SCT_DIR}/python/bin/python simu_make_figures_compare_SNR.py -i PATH_TO_DATA
#
# OUTPUT:
# Fig
#
# Authors: Nicolas Pinon

import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt


def get_parameters():
    parser = argparse.ArgumentParser(description='Generate a figure which compares the two SNR methods : SNR_single VS'
                                                 'SNR_diff . Run after simu_process_data.py')
    parser.add_argument("-i", "--input",
                        help="List here the path to the data, which should include ",
                        required=True)
    args = parser.parse_args()
    return args


def main():

    os.chdir(data_path)  # making the path provided by the user the cwd
    SNR_diff,SNR_single  = [],[]

    for folder in os.listdir('.'):  # going trough all folders
        try:
            os.chdir(data_path + '/' + folder + '/' + 'results')
            # in each subjects folder's there should be a folder named 'results' and inside a csv file named 'results.csv'
            results = pd.read_csv('results.csv')
            SNR_diff.append(results.iat[0,1])
            SNR_single.append(results.iat[2, 1])
        except: # if there is something else than a subject's folder or if there is no csv results in the folder
            pass


    _, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(SNR_diff, SNR_single, c=".3", color='blue')
    ax.plot(ax.get_xlim(), ax.get_ylim(), color='blue', ls="--", c=".3") # adding a y=x line to show correlation
    plt.xlabel('SNR_diff', color='blue', fontsize=15)
    plt.ylabel('SNR_single', color='blue', fontsize=15)
    plt.title('Correlation between SNR_single and SNR_diff')

    os.chdir(data_path)
    plt.savefig('SNR_diff_VS_SNR_single.png')
    plt.show()



if __name__ == "__main__":
    args = get_parameters()
    data_path = args.input
    main()
