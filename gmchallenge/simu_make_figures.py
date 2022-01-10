#!/usr/bin/env python
#
# Make figures to assess metrics sensitivity to image quality. Run after simu_process_data.py
#
# USAGE:
#   python simu_make_figures.py -i simu_results/results_all.csv
#
# OUTPUT:
# Figs
#
# Authors: Julien Cohen-Adad


import os
import csv
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def get_parser():
    parser = argparse.ArgumentParser(description='Make figures to assess metrics sensitivity to image quality. Run '
                                                 'after simu_process_data.py')
    parser.add_argument("-i", "--input",
                        help="CSV file generated by simu_process_data.py.",
                        required=True)
    parser.add_argument("-s", "--smooth",
                        help="Smoothing factor. Default=0.",
                        type=float,
                        default=0,
                        required=False)
    return parser


def main(argv=None):
    path_output = 'simu_results/'
    # Get input args
    parser = get_parser()
    args = parser.parse_args(argv)
    file_csv = args.input
    smooth = args.smooth

    results_all = pd.read_csv(file_csv)

    # build index
    list_gm = sorted(list(set(results_all['GM'].tolist())))
    list_noise = sorted(list(set(results_all['Noise'].tolist())))
    wm = sorted(list(set(results_all['WM'].tolist())))[0]

    for metric in ['Contrast', 'SNR_diff', 'SNR_single']:
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
        fontsize = 16
        fontsize_axes = 14
        linewidth = 1  # linewidth of bar contour
        p2 = ax.bar(ind - width, data[:, 2], width, color='b', linewidth=linewidth, edgecolor='k')
        p1 = ax.bar(ind, data[:, 1], width, color='y', linewidth=linewidth, edgecolor='k', align='center')
        p3 = ax.bar(ind + width, data[:, 0], width, color='r', linewidth=linewidth, edgecolor='k')
        ax.set_title(metric, fontsize=fontsize)
        ax.set_xlabel("Simulated Contrast (in %)", fontsize=fontsize)
        ax.set_xticks(ind)
        xticklabels = [int(100 * abs(i_gm-wm) / min(i_gm, wm)) for i_gm in list_gm]
        ax.set_xticklabels(xticklabels, fontsize=fontsize_axes)
        # ax.legend((p1[0], p2[0], p3[0]), (["Noise STD = " + str(i) for i in list_noise]))
        ax.set_ylabel("Measured " + metric, fontsize=fontsize)
        # ax.set_ylim(0, 80)
        yticklabels = ax.get_yticks().astype(int)
        ax.yaxis.set_major_locator(mticker.FixedLocator(yticklabels))
        ax.set_yticklabels(yticklabels, fontsize=fontsize_axes)
        plt.grid(axis='y', linestyle="dashed")
        ax.autoscale_view()
        # plt.show()
        plt.savefig(os.path.join(path_output, "results_" + metric + "_smooth" + str(smooth) + ".png"), dpi=300)

        # save csv for importing as table
        with open(os.path.join(path_output, "results_" + metric + "_smooth" + str(smooth) + ".csv"), "w") as f:
            writer = csv.writer(f)
            for row in data.transpose():
                row = [f"%.2f" % f for f in row]  # we need to do this otherwise float conversion gives e.g. 23.00000001
                writer.writerow(row)


if __name__ == "__main__":
    main()