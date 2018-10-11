#!/usr/bin/env python
#
# Make figures to assess metrics sensitivity to image quality. Run after simu_process_data.py
#
# USAGE:
# The script should be launched using SCT's python:
#   ${SCT_DIR}/python/bin/python simu_make_figures.py -i results_all.csv
#
# OUTPUT:
# Figs
#
# Authors: Julien Cohen-Adad

import os, sys, csv
import argparse
import numpy as np
import nibabel as nib
import scipy.ndimage as ndimage
# append path to useful SCT scripts
path_sct = os.getenv('SCT_DIR')
sys.path.append(os.path.join(path_sct, 'scripts'))
import sct_utils as sct
from msct_image import Image
from spinalcordtoolbox.metadata import read_label_file, parse_id_group
import pandas as pd
import matplotlib.pyplot as plt

def get_parameters():
    parser = argparse.ArgumentParser(description='Make figures to assess metrics sensitivity to image quality. Run '
                                                 'after process_folder.py')
    parser.add_argument("-i", "--input",
                        help="CSV file generated by process_folder.py.",
                        required=True)
    args = parser.parse_args()
    return args


def main():
    sct.init_sct()  # start logger
    # default params
    smooth = 0
    # Read CSV
    results_all = pd.read_csv(file_csv)

    # build index
    list_gm = sorted(list(set(results_all['GM'].tolist())))
    list_noise = sorted(list(set(results_all['Noise'].tolist())))
    wm = sorted(list(set(results_all['WM'].tolist())))[0]

    for metric in ['Contrast', 'SNR', 'Sharpness']:
        # build array
        data = np.zeros([len(list_gm), len(list_noise)])
        for i_gm in range(len(list_gm)):
            for i_noise in range(len(list_noise)):
                data[i_gm, i_noise] = results_all.query("Noise == " + str(list_noise[i_noise]) +
                                                        " & Smooth == " + str(smooth) +
                                                        " & GM == " + str(list_gm[i_gm]))[metric]
        # plot fig
        N = len(list_gm)
        fig, ax = plt.subplots()
        ind = np.arange(N)  # the x locations for the groups
        width = 0.20  # the width of the bars
        fontsize = 20
        fontsize_axes = 16
        p2 = ax.bar(ind - width, data[:, 2], width, color='b')
        p1 = ax.bar(ind, data[:, 1], width, color='y')
        p3 = ax.bar(ind + width, data[:, 0], width, color='r')
        ax.set_title(metric, fontsize=fontsize)
        ax.set_xlabel("Simulated Contrast (in %)", fontsize=fontsize)
        ax.set_xticks(ind + width / 2)
        xticklabels = (abs(list_gm - wm) / [float(min(i, wm)) for i in list_gm] * 100).astype(int)
        ax.set_xticklabels(xticklabels, fontsize=fontsize_axes)
        # ax.legend((p1[0], p2[0], p3[0]), (["Noise STD = " + str(i) for i in list_noise]))
        ax.set_ylabel("Measured " + metric, fontsize=fontsize)
        # ax.set_ylim(0, 80)
        yticklabels = ax.get_yticks().astype(int)
        ax.set_yticklabels(yticklabels, fontsize=fontsize_axes)
        plt.grid(axis='y')
        ax.autoscale_view()
        # plt.show()
        plt.savefig("results_" + metric + "_smooth" + str(smooth) + ".png")

        # save csv for importing as table
        with open("results_" + metric + "_smooth" + str(smooth) + ".csv", "wb") as f:
            writer = csv.writer(f)
            for row in data.transpose():
                row = ["%.2f" % f for f in row]  # we need to do this otherwise float conversion gives e.g. 23.00000001
                writer.writerow(row)


if __name__ == "__main__":
    args = get_parameters()
    file_csv = args.input
    main()