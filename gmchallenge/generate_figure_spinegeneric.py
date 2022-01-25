#!/usr/bin/env python
#
# Generate figures for the spine-generic results

import pandas as pd
import numpy as np
import argparse
import os
import matplotlib.pyplot as plt
import ptitprince as pt
import seaborn as sns
from matplotlib.patches import PathPatch


def get_parser():
    parser = argparse.ArgumentParser(description='Generate figure for spine generic dataset')
    parser.add_argument("-ir", "--path-input-results",
                        help="Path to results.csv",
                        required=True)
    parser.add_argument("-ip", "--path-input-participants",
                        help="Path to participants.tsv",
                        required=True)
    parser.add_argument("-o", "--path-output",
                        help="Path to save images",
                        required=True)
    return parser


def adjust_box_widths(g, fac):
    """
    Adjust the widths of a seaborn-generated boxplot.
    Source: From https://github.com/mwaskom/seaborn/issues/1076#issuecomment-634541579
    """
    # iterating through Axes instances
    for ax in g.axes:

        # iterating through axes artists:
        for c in ax.get_children():

            # searching for PathPatches
            if isinstance(c, PathPatch):
                # getting current width of box:
                p = c.get_path()
                verts = p.vertices
                verts_sub = verts[:-1]
                xmin = np.min(verts_sub[:, 0])
                xmax = np.max(verts_sub[:, 0])
                xmid = 0.5*(xmin+xmax)
                xhalf = 0.5*(xmax - xmin)

                # setting new width of box
                xmin_new = xmid-fac*xhalf
                xmax_new = xmid+fac*xhalf
                verts_sub[verts_sub[:, 0] == xmin, 0] = xmin_new
                verts_sub[verts_sub[:, 0] == xmax, 0] = xmax_new

                # setting new width of median line
                for l in ax.lines:
                    if not len(l.get_xdata()) == 0:
                        if np.all(np.equal(l.get_xdata()[0:2], [xmin, xmax])):
                            l.set_xdata([xmin_new, xmax_new])


def generate_figure(data_in, column, path_output):
    dx = np.ones(len(data_in[column]))
    dy = column
    hue = "Manufacturer"
    pal = ["#1E90FF", "#32CD32", "#FF0000"]
    f, ax = plt.subplots(figsize=(4, 6))
    if column == 'CNR_single/t':
        coeff = 100
    else:
        coeff = 1
    ax = pt.half_violinplot(x=dx, y=dy, data=data_in*coeff, hue=hue, palette=pal, bw=.4, cut=0.,
                            scale="area", width=.8, inner=None, orient="v", dodge=False, alpha=.4, offset=0.5)
    ax = sns.boxplot(x=dx, y=dy, data=data_in*coeff, hue=hue, color="black", palette=pal,
                     showcaps=True, boxprops={'facecolor': 'none', "zorder": 10},
                     showfliers=True, whiskerprops={'linewidth': 2, "zorder": 10},
                     saturation=1, orient="v", dodge=True)
    ax = sns.stripplot(x=dx, y=dy, data=data_in*coeff, hue=hue, palette=pal, edgecolor="white",
                       size=3, jitter=1, zorder=0, orient="v", dodge=True)
    plt.xlim([-1, 0.5])
    handles, labels = ax.get_legend_handles_labels()
    _ = plt.legend(handles[0:len(labels) // 3], labels[0:len(labels) // 3],
                   bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.,
                   title=str(hue))
    f.gca().invert_xaxis()
    adjust_box_widths(f, 0.6)
    ax.grid(axis='y')
    # special hack
    if column == 'CNR_single/t':
        plt.xlabel('CNR_single/√t')
        fname_out = os.path.join(path_output, 'figure_CNR_single_t')
    else:
        plt.xlabel(column)
        fname_out = os.path.join(path_output, 'figure_' + column)
    # remove ylabel
    plt.ylabel('')
    # hide xtick
    plt.tick_params(
        axis='x',
        which='both',
        bottom=False,
        top=False,
        labelbottom=False)
    plt.savefig(fname_out, bbox_inches='tight', dpi=300)


def main(argv=None):
    # user params
    parser = get_parser()
    args = parser.parse_args(argv)
    path_input_results = args.path_input_results
    path_input_participants = args.path_input_participants
    path_output = args.path_output

    if not os.path.isdir(path_output):
        os.makedirs(path_output)

    content_results_csv = pd.read_csv(path_input_results, sep=",")
    content_participants_tsv = pd.read_csv(path_input_participants, encoding="ISO-8859-1", sep="\t")

    list_subjects_results = content_results_csv['Subject'].tolist()

    # loop across subjects list from results
    for subj in list_subjects_results:
        rowIndex = content_participants_tsv[content_participants_tsv['participant_id'] == subj].index
        rowIndexResults = content_results_csv[content_results_csv['Subject'] == subj].index
        content_results_csv.loc[rowIndexResults, 'Manufacturer'] = content_participants_tsv.loc[rowIndex]['manufacturer'].values[0]

    generate_figure(content_results_csv, 'SNR_single', path_output)
    # generate_figure(content_results_csv, 'Contrast', path_output)
    generate_figure(content_results_csv, 'CNR_single/t', path_output)


if __name__ == "__main__":
    main()
