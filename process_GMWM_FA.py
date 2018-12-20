#!/usr/bin/env python
#
# Make figures to compare SNR methods: SNR_diff versus SNR_single.
# This script will loop across all subjects, retrieve the results/results.csv and generate a plot.
#
# USAGE:
# The script should be launched using SCT's python:
#   ${SCT_DIR}/python/bin/python path/to/this/script/process_GMWM_FA.py -i PATH_TO_DATA

#   /!\ Any files that wants to be excluded should not be part of the dataset /!\
#   /!\ Dicom files should first be converted to nii, using dcm2niix /!\
#
# OUTPUT:
# Fig
#
# Authors: Nicolas Pinon

import sys, os, shutil, argparse, pickle, io, argparse
import numpy as np
import pandas as pd
# append path to useful SCT scripts
path_sct = os.getenv('SCT_DIR')
sys.path.append(os.path.join(path_sct, 'scripts'))
import sct_utils as sct
from spinalcordtoolbox.image import Image
import fnmatch
import matplotlib.pyplot as plt

path_sct = os.getenv('SCT_DIR')
sys.path.append(os.path.join(path_sct, 'scripts'))
import sct_utils as sct
from process_data import main as process_data

def get_parameters():
    parser = argparse.ArgumentParser(description='Generate a figure which compares the two SNR methods : SNR_single VS'
                                                 'SNR_diff . Run after simu_process_data.py')
    parser.add_argument("-i", "--input",
                        help="List here the path to the data, which should include all the patients directory",
                        required=True)
    parser.add_argument("-ref", "--ref",
                        help="Image used as a reference",
                        required=True)
    args = parser.parse_args()
    return args


def main():

    FA_list = []
    ratio_list = []

    # os.chdir(data_path)  # making the path provided by the user the cwd
    # for root, dirs, files in os.walk(data_path):
    #     for dir in dirs:
    #         if dir == '03-GRE-ME':
    #             for file in os.listdir(os.path.join(data_path, dir)):
    #                 if fnmatch.fnmatch(file, '*.nii'):
    #                     ref = os.path.join(root, dir, file)  # retrieve reference file to register to
    #                     sct.printv("Segmenting reference")
    #                     sct.run("sct_deepseg_sc -i " + ref + " -c t2s -ofolder " + os.path.join(data_path, dir), verbose=0)
    #                     sct.run("sct_deepseg_gm -i " + ref, verbose=0)
    #                     ref_seg_sc = sct.add_suffix(ref, "_seg")
    #                     ref_seg_gm = sct.add_suffix(ref, "_gmseg")
    #                     print("ref is " + ref)
    #
    #     for dir in dirs:
    #         for file in os.listdir(os.path.join(data_path, dir)):
    #             if fnmatch.fnmatch(file, '*FA*.nii'):
    #                 image = os.path.join(root, dir, file)
    #                 print("a file found zith FA is " + image)
    #                 results = process_data([ref, image], file_seg=ref_seg_sc, file_gmseg=ref_seg_gm, num=None, register=True,
    #                              output_dir=os.path.join(root, dir), create_txt_output=False, verbose=1)

    found = False
    file_list = []
    dir_list = []
    FA_list = []
    ratio_list = []

    os.chdir(data_path)
    for root, dirs, files in os.walk(data_path):
        for file in files:
            if fnmatch.fnmatch(file, fname_ref):
                ref = os.path.join(root, file)  # retrieve reference file to register to
                sct.printv("Segmenting reference")
                sct.run("sct_deepseg_sc -i " + ref + " -c t2s -ofolder " + root, verbose=0)  # TODO make output folder derivatives
                sct.run("sct_deepseg_gm -i " + ref, verbose=0)
                ref_seg_sc = sct.add_suffix(ref, "_seg")
                ref_seg_gm = sct.add_suffix(ref, "_gmseg")
                print("ref is " + ref)
                found = True
            elif fnmatch.fnmatch(file, "*T2star.nii.gz"):
                dir_list.append(root)
                file_list.append(file)

    if not found:
        sct.printv("reference file not found in the data path")
        raise

    for i in range(0,len(file_list)):
        results = process_data([ref, dir_list[i] + "/" + file_list[i]], file_seg=ref_seg_sc, file_gmseg=ref_seg_gm, num=None, register=True,
                              output_dir=data_path + "/derivatives", create_txt_output=False, verbose=1)
        ratio_list.append(results.iat[2, 0])
        idx_FA = file_list[i].find("FA")
        FA = int(file_list[i][idx_FA + 2] + file_list[i][idx_FA + 3])
        FA_list.append(FA)

        # for dir in dirs:
        #     for file in os.listdir(os.path.join(data_path, dir)):
        #         if fnmatch.fnmatch(file, '*FA*.nii'):
        #             os.chdir(os.path.join(root, dir))
        #             idx_FA = file.find("FA")
        #             FA = int(file[idx_FA+2] + file[idx_FA+3])
        #             FA_list.append(FA)
        #             wm_tab = pd.read_excel('mean_mask1.xls')
        #             gm_tab = pd.read_excel('mean_mask2.xls')
        #             wm_mean = wm_tab.iat[0, 8]
        #             gm_mean = gm_tab.iat[0, 8]
        #             ratio_list.append(gm_mean/wm_mean)


    plt.figure()
    plt.plot(FA_list, ratio_list, "bo")
    plt.xlabel("FA in degrees")
    plt.ylabel("GM/WM ratio")
    plt.title("GM/WM ratio vs Flip Angle")
    plt.savefig("GMWMratio_VS_FA.png")
    1+1





if __name__ == "__main__":
    args = get_parameters()
    data_path = args.input
    fname_ref = args.ref
    main()
