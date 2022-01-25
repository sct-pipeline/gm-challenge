import pandas as pd
import numpy as np
import argparse
import os
import matplotlib.pyplot as plt
import ptitprince as pt
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
                    if not l.get_xdata().size == 0:
                        if np.all(np.equal(l.get_xdata(), [xmin, xmax])):
                            l.set_xdata([xmin_new, xmax_new])


def generate_figure(data_in, column, path_output):
    # Hue Input for Subgroups
    dx = np.ones(len(data_in[column]))
    dy = column
    dhue = "Manufacturer"
    ort = "v"
    #  dodge blue, limegreen, red
    colors = [  "#1E90FF", "#32CD32","#FF0000"  ]
    pal = colors
    sigma = .2
    f, ax = plt.subplots(figsize=(4, 6))

    ax = pt.RainCloud(x=dx, y=dy, hue=dhue, data=data_in, palette=pal, bw=sigma,
                      width_viol=.5, ax=ax, orient=ort, alpha=.4, dodge=True, width_box=.35,
                      box_showmeans=True,
                      box_meanprops={"marker":"^", "markerfacecolor":"black", "markeredgecolor":"black", "markersize":"10"},
                      box_notch=True)
    f.gca().invert_xaxis()
    #adjust boxplot width
    adjust_box_widths(f, 0.4)
    plt.xlabel(column)
    # remove ylabel
    plt.ylabel('')
    # hide xtick
    plt.tick_params(
        axis='x',
        which='both',
        bottom=False,
        top=False,
        labelbottom=False)
    # plt.legend(title="Line", loc='upper left', handles=handles[::-1])
    plt.savefig(os.path.join(path_output, 'figure_' + column), bbox_inches='tight', dpi=300)


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
