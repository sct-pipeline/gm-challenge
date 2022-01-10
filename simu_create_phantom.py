#!/usr/bin/env python
#
# Generates synthetic phantoms from the WM and GM atlas.
#
# USAGE:
# The script should be launched using SCT's python:
#   python simu_create_phantom.py [-o output_folder]
#
# Ranges of GM and noise STD can be changed inside the code. They are hard-coded so that a specific version of the code
# can be tagged, and will always produce the same results (whereas if we allow users to enter params, the output will
# depends on the input params).
#
# OUTPUT:
# The script generates a collection of files under specified folder.
#
# Authors: Stephanie Alley, Julien Cohen-Adad


import os, sys
import argparse
import numpy as np
import nibabel as nib
import scipy.ndimage as ndimage
import pandas as pd
import tqdm


def get_parser():
    parser = argparse.ArgumentParser(
        description="Generate a synthetic spinal cord phantom with various values of gray matter and Gaussian "
                    "noise amplitude.")
    parser.add_argument(
        '-o',
        help='Name of the output folder',
        default='phantom')
    return parser


def crop_data(data):
    """Crop around the spinal cord"""
    return data[53:89, 58:82, 845:855]


def main(argv=None):
    # default params
    wm_value = 100
    gm_values = [120, 140, 160, 180]
    std_noises = [1, 5, 10]
    smoothing = [0, 0.5, 1]  # standard deviation values for Gaussian kernel
    thr_mask = 0.9  # Set threshold for masks

    # user params
    parser = get_parser()
    args = parser.parse_args(argv)
    folder_out = args.o

    # create output folder
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)

    # Open white and gray matter masks from SCT
    path_sct = os.getenv('SCT_DIR')
    folder_template = os.path.join(path_sct, 'data', 'PAM50', 'template')
    nii_atlas_wm = nib.load(os.path.join(folder_template, 'PAM50_wm.nii.gz'))
    nii_atlas_gm = nib.load(os.path.join(folder_template, 'PAM50_gm.nii.gz'))

    print("\nGenerate phantom...")
    pbar = tqdm.tqdm(total=len(gm_values)*len(std_noises)*len(smoothing))
    # loop across gm_value and std_values and generate phantom
    for gm_value in gm_values:
        for std_noise in std_noises:
            for smooth in smoothing:
                nii_atlas_wm.uncache()
                data_wm = nii_atlas_wm.get_fdata()
                nii_atlas_gm.uncache()
                data_gm = nii_atlas_gm.get_fdata()
                # Add values to each tract
                data_wm *= wm_value
                data_gm *= gm_value
                # sum across labels
                data_phantom = data_wm + data_gm
                # Add blurring
                if smooth:
                    data_phantom = ndimage.gaussian_filter(data_phantom, sigma=(smooth), order=0)
                # add noise
                if std_noise:
                    data_phantom += np.random.normal(loc=0, scale=std_noise, size=data_phantom.shape)
                # build file name
                file_out = "phantom_WM" + str(wm_value) + "_GM" + str(gm_value) + "_Noise" + str(std_noise) + \
                           "_Smooth" + str(smooth)
                # save as NIfTI file
                nii_phantom = nib.Nifti1Image(crop_data(data_phantom), nii_atlas_wm.affine)
                nib.save(nii_phantom, os.path.join(folder_out, file_out + ".nii.gz"))
                # save metadata
                metadata = pd.Series({'WM': wm_value,
                                      'GM': gm_value,
                                      'Noise': std_noise,
                                      'Smooth': smooth,
                                      'File': file_out + ".nii.gz"})
                metadata.to_csv(os.path.join(folder_out, file_out + ".csv"))
                pbar.update(1)
    pbar.close()

    # generate mask of gray matter
    nii_atlas_gm.uncache()
    data_gm = nii_atlas_gm.get_fdata()
    data_gm[np.where(data_gm < thr_mask)] = 0
    nii_phantom = nib.Nifti1Image(crop_data(data_gm), nii_atlas_wm.affine)
    nib.save(nii_phantom, os.path.join(folder_out, "mask_gm.nii.gz"))

    # generate mask of white matter
    nii_atlas_wm.uncache()
    data_wm = nii_atlas_wm.get_fdata()
    data_wm[np.where(data_wm < thr_mask)] = 0
    nii_phantom = nib.Nifti1Image(crop_data(data_wm), nii_atlas_wm.affine)
    nib.save(nii_phantom, os.path.join(folder_out, "mask_wm.nii.gz"))

    # display
    print("Done!")


if __name__ == "__main__":
    main()
