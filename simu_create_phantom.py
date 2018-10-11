#!/usr/bin/env python
#
# Generates synthetic phantoms from the WM and GM atlas.
#
# USAGE:
# The script should be launched using SCT's python:
#   PATH_GMCHALLENGE="PATH TO THIS REPOSITORY"
#   ${SCT_DIR}/python/bin/python ${PATH_GMCHALLENGE}simu_create_phantom.py folder_out
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
# TDOD: param for selecting z

import os, sys
import argparse
import numpy as np
import nibabel as nib
import scipy.ndimage as ndimage
# append path to useful SCT scripts
path_sct = os.getenv('SCT_DIR')
sys.path.append(os.path.join(path_sct, 'scripts'))
import sct_utils as sct
from spinalcordtoolbox.image import Image
from spinalcordtoolbox.metadata import read_label_file
import pandas as pd

def get_parameters():
    parser = argparse.ArgumentParser(description='Generate a synthetic spinal cord phantom with various values of gray '
                                                 'matter and Gaussian noise amplitude.')
    parser.add_argument('folder_out', help='Name of the output folder')
    args = parser.parse_args()
    return args


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
    indiv_labels_ids, indiv_labels_names, indiv_labels_files, combined_labels_ids, combined_labels_names, combined_labels_id_groups, ml_clusters = read_label_file(
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
        data_tracts[:, :, :, i] = Image(os.path.join(folder_atlas, indiv_labels_files[i])).data[:, :, zslice-(num_slice/2):zslice+(num_slice/2)]
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


def main():
    sct.init_sct()  # start logger
    # default params
    wm_value = 100
    gm_values = [120, 140, 160, 180]
    std_noises = [1, 5, 10]
    smoothing = [0, 0.5, 1]  # standard deviation values for Gaussian kernel
    zslice = 850  # 850: corresponds to mid-C4 level (enlargement)
    num_slice = 10  # number of slices in z direction
    range_tract = 0  # we do not want heterogeneity within WM and within GM. All tracts should have the same value.

    # create output folder
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)

    # Extract the tracts from the atlas folder
    folder_atlas = os.path.join(path_sct, "data/PAM50/atlas/")
    data_tracts = get_tracts(folder_atlas, zslice=zslice, num_slice=num_slice)
    nx, ny, nz, nb_tracts = data_tracts.shape

    # TODO: get WM and GM indexes from info_label.txt
    ind_wm = range(0, 30)
    ind_gm = range(30, 36)

    print("\nGenerate phantom...")
    # loop across gm_value and std_values and generate phantom
    for gm_value in gm_values:
        for std_noise in std_noises:
            for smooth in smoothing:
                data_tracts_modif = data_tracts.copy()
                # Add values to each tract
                data_tracts_modif[:, :, :, ind_wm] *= wm_value
                data_tracts_modif[:, :, :, ind_gm] *= gm_value
                # sum across labels
                data_phantom = np.sum(data_tracts_modif, axis=3)
                # Add blurring
                if smooth:
                    data_phantom = ndimage.gaussian_filter(data_phantom, sigma=(smooth), order=0)
                # add noise
                if std_noise:
                    data_phantom += np.random.normal(loc=0, scale=std_noise, size=(nx, ny, nz))
                # build file name
                file_out = "phantom_WM" + str(wm_value) + "_GM" + str(gm_value) + "_Noise" + str(std_noise) + "_Smooth" + str(smooth)
                # save as nifti file
                save_nifti(data_phantom, os.path.join(folder_out, file_out + ".nii.gz"))
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
    sct.log.info("Done!")


if __name__ == "__main__":
    args = get_parameters()
    folder_out = args.folder_out
    main()
