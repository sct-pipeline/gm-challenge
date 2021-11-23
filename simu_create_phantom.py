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

# TODO: generated cord mask is too large!
# TODO: remove input params and set them as list inside code
# TODO: download PAM50 by default, and have option to set path to atlas
# TODO: param for selecting z

import os, sys
import argparse
import numpy as np
import nibabel as nib
import scipy.ndimage as ndimage
import pandas as pd


def get_parser():
    parser = argparse.ArgumentParser(
        description="Generate a synthetic spinal cord phantom with various values of gray matter and Gaussian "
                    "noise amplitude.")
    parser.add_argument(
        '-o',
        help='Name of the output folder',
        default='phantom')
    return parser


def get_tracts(folder_atlas, zslice=500, num_slice=10):
    """
    Loads tracts in an atlas folder and converts them from .nii.gz format to numpy ndarray
    :param tracts_folder:
    :param zslice: slice to select for generating the phantom
    :return: ndarray nx,ny,nb_tracts
    """
    # parameters
    file_info_label = 'info_label.txt'
    # read info labels
    indiv_labels_ids, indiv_labels_names, indiv_labels_files, combined_labels_ids, combined_labels_names, \
    combined_labels_id_groups, ml_clusters = read_label_file(
        folder_atlas, file_info_label)

    # fname_tracts = glob.glob(folder_atlas + '/*' + '.nii.gz')
    nb_tracts = np.size(indiv_labels_files)
    # load first file to get dimensions
    im = Image(os.path.join(folder_atlas, indiv_labels_files[0]))
    nx, ny, nz, nt, px, py, pz, pt = im.dim
    # initialize data tracts
    data_tracts = np.zeros([nx, ny, num_slice, nb_tracts])
    #Load each partial volume of each tract
    for i in range(nb_tracts):
        sct.no_new_line_log('Load each atlas label: {}/{}'.format(i + 1, nb_tracts))
        # TODO: display counter
        # TODO: remove usage of Image
        data_tracts[:, :, :, i] = \
            Image(os.path.join(folder_atlas, indiv_labels_files[i])).data[:, :, zslice-(num_slice/2):zslice+(num_slice/2)]
    return data_tracts


def save_nifti(data, fname):
    """
    Create a standard header with nibabel and save matrix as NIFTI
    :param data:
    :param fname:
    :return:
    """
    affine = np.diag([1, 1, 1, 1])
    im_phantom = nib.Nifti1Image(data, affine)
    nib.save(im_phantom, fname)


def main(argv=None):
    # default params
    wm_value = 100
    gm_values = [120, 140, 160, 180]
    std_noises = [1, 5, 10]
    smoothing = [0, 0.5, 1]  # standard deviation values for Gaussian kernel
    zslice = 850  # 850: corresponds to mid-C4 level (enlargement)
    num_slice = 10  # number of slices in z direction

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
    # loop across gm_value and std_values and generate phantom
    for gm_value in gm_values:
        for std_noise in std_noises:
            for smooth in smoothing:
                data_wm = nii_atlas_wm.get_fdata()
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
                # Only select few slices
                data_phantom_small = data_phantom[:, :, zslice - int(num_slice / 2):int(zslice + num_slice / 2)]
                # build file name
                file_out = "phantom_WM" + str(wm_value) + "_GM" + str(gm_value) + "_Noise" + str(std_noise) + \
                           "_Smooth" + str(smooth)
                # save as NIfTI file
                nii_phantom = nib.Nifti1Image(data_phantom_small, nii_atlas_wm.affine)
                nib.save(nii_phantom, os.path.join(folder_out, file_out + ".nii.gz"))
                # save metadata
                metadata = pd.Series({'WM': wm_value,
                                      'GM': gm_value,
                                      'Noise': std_noise,
                                      'Smooth': smooth,
                                      'File': file_out + ".nii.gz"})
                metadata.to_csv(os.path.join(folder_out, file_out + ".csv"))


    # generate mask of spinal cord
    data_cord = np.sum(data_tracts[:, :, :, ind_wm+ind_gm], axis=3)
    data_cord[np.where(data_cord >= 0.5)] = 1
    data_cord[np.where(data_cord < 0.5)] = 0
    save_nifti(data_cord, os.path.join(folder_out, "mask_cord.nii.gz"))
    # generate mask of gray matter
    data_gm = np.sum(data_tracts[:, :, :, ind_gm], axis=3)
    data_gm[np.where(data_gm >= 0.5)] = 1
    data_gm[np.where(data_gm < 0.5)] = 0
    save_nifti(data_gm, os.path.join(folder_out, "mask_gm.nii.gz"))
    # display
    print("Done!")


if __name__ == "__main__":
    main(sys.argv[1:])
