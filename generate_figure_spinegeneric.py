import pandas as pd
import numpy as np
import argparse
import seaborn as sns
import os
import matplotlib.pyplot as plt
import ptitprince as pt

sns.set(style="whitegrid", font_scale=1)


def get_parameters():
    parser = argparse.ArgumentParser(description='Generate figure for spine generic dataset')
    parser.add_argument("-ir", "--path-input-results",
                        help="Path to results.csv",
                        required=True)
    parser.add_argument("-ip", "--path-input-participants",
                        help="Path to participants.tsv",
                        required=True)
    parser.add_argument("-o", "--path-output",
                        help="Path to save images",
                        required=True,
                        )
    arguments = parser.parse_args()
    return arguments


def generate_figure(data_in, column, path_output):
    # Hue Input for Subgroups
    dx = np.ones(len(data_in[column]))
    dy = column
    dhue = "Manufacturer"
    ort = "v"
    pal = "Set2"
    sigma = .2
    f, ax = plt.subplots(figsize=(10, 5))

    ax = pt.RainCloud(x=dx, y=dy, hue=dhue, data=data_in, palette=pal, bw=sigma,
                      width_viol=.5, ax=ax, orient=ort, alpha=.65, dodge=True)
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
    plt.savefig(os.path.join(path_output, 'figure_' + column), bbox_inches='tight')


def main(path_input_results, path_input_participants, path_output):
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
    generate_figure(content_results_csv, 'Contrast', path_output)


if __name__ == "__main__":
    args = get_parameters()
    main(args.path_input_results, args.path_input_participants, args.path_output)
