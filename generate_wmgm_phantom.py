#!/usr/bin/env python
#
# Generates a synthetic phantom from the WM and GM atlas.
# Saves the phantom to a NIfTI image
#
# USAGE:
# The script should be launched using SCT's python:
#   cd $SCT_DIR
#   source python/bin/activate
#   python generate_wmgm_phantom.py
#
# Ranges of GM and noise STD can be changed inside the code. They are hard-coded so that a specific version of the code
# can be tagged, and will always produce the same results (whereas if we allow users to enter params, the output will
# depends on the input params).
#
# OUTPUT:
# The script generates a collection of files under local folder data_phantom/
#
# Authors: Stephanie Alley, Julien Cohen-Adad
# License: https://github.com/neuropoly/gm_challenge/blob/master/LICENSE

# TODO: remove input params and set them as list inside code
# TODO: download PAM50 by default, and have option to set path to atlas
# TDOD: param for selecting z

import os, sys
import argparse
# import glob
# import sct_utils as sct
import numpy as np
# import random
import nibabel as nib
# append path to useful SCT scripts
path_sct = os.getenv('SCT_DIR')
sys.path.append(os.path.join(path_sct, 'scripts'))
import sct_utils as sct
from msct_image import Image
from spinalcordtoolbox.metadata import read_label_file, parse_id_group


def get_parameters():
    parser = argparse.ArgumentParser(description='Generate a synthetic spinal cord phantom with various values of gray '
                                                 'matter and Gaussian noise amplitude.')
    args = parser.parse_args()
    return args

def get_tracts(folder_atlas, zslice=500):
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
    data_tracts = np.zeros([nx, ny, nb_tracts])
    #Load each partial volume of each tract
    for i in range(nb_tracts):
        sct.no_new_line_log('Load each atlas label: {}/{}'.format(i + 1, nb_tracts))
        # TODO: display counter
        data_tracts[:, :, i] = Image(os.path.join(folder_atlas, indiv_labels_files[i])).data[:, :, zslice]
    return data_tracts

#
# def phantom_generation(tracts, std_noise_perc, range_tract_perc, value_wm, value_gm, folder_out):
#     """
#     :param tracts: np array
#     :param std_noise: std of noise to generate pseudo-random Gaussian noise
#     :param range_tract: range of value to generate pseudo-random uniformly distributed tract value
#     :param value_wm: true value of the wm tract
#     :param folder_out: output folder
#     :return: synthetic_vol, synthetic_voln, values_synthetic_data, tracts_sum
#     """
#
#     # Transform std noise and range tract to a percentage of the true value
#     range_tract = float(range_tract_perc) / 100 * value_wm
#     std_noise = float(std_noise_perc) / 100 * value_wm
#
#     # Generate synthetic Volume
#     numtracts = len(tracts)
#     nx, ny, nz = tracts[0][0].shape
#
#    # open txt file that includes true values per tract
#     fid_file = open(fname_phantom, 'w+')
#     print >> fid_file, 'std_noise='+str(std_noise_perc)+'%, range_tract='+str(range_tract_perc)+'%, value_wm='+str(value_wm)+', value_gm='+str(value_gm)
#
#     # create volume of tracts with randomly-assigned values
#     tracts_weighted = np.zeros([numtracts, nx, ny, nz])
#     synthetic_vol = np.zeros([nx, ny, nz])
#     synthetic_voln = np.zeros([nx, ny, nz])
#     values_synthetic_data = np.zeros([numtracts])
#     for i in range(0, numtracts):
#         if i == numtracts-1:
#             values_synthetic_data[i] = value_gm
#         else:
#             values_synthetic_data[i] = (value_wm - range_tract + random.uniform(0, 2*range_tract))
#         print >> fid_file, 'label=' + str(i) + ', value=' + str(values_synthetic_data[i])
#         tracts_weighted[i, :, :, :] = values_synthetic_data[i] * tracts[i, 0]
#         # add tract to volume
#         synthetic_vol = synthetic_vol + tracts_weighted[i, :, :, :]
#
#     # sum all tracts
#     tracts_sum = np.zeros([nx, ny, nz])
#     for i in range(0, numtracts):
#         tracts_sum = tracts_sum + tracts[i, 0]
#
#     # close txt file
#     fid_file.close()
#
#     # add gaussian noise
#     if not std_noise == 0:
#         synthetic_voln = synthetic_vol + np.random.normal(loc=0, scale=std_noise, size=(nx, ny, nz))
#     else:
#         synthetic_voln = synthetic_vol
#
#     return[synthetic_vol, synthetic_voln, values_synthetic_data, tracts_sum]

#
# #=======================================================================================================================
# # Save 3D numpy array to a nifti
# #=======================================================================================================================
# def save_3D_nparray_nifti(np_matrix_3d, output_image):
#     """
#     Save 3d numpy matrix to niftii image
#     :param np_matrix_3d: 3d numpy array
#     :param output_image:  name of the created nifti file. e.g.; 3d_matrix.nii.gz
#     :return: none
#     """
#     img = nib.Nifti1Image(np_matrix_3d, np.eye(4))
#     affine = img.get_affine()
#     np_matrix_3d_nii = nib.Nifti1Image(np_matrix_3d,affine)
#     nib.save(np_matrix_3d_nii, os.path.join(folder_out,output_image))
#     return None
#

def main():
    # default params
    wm_value = 50
    gm_values = [50, 60, 70, 80, 90, 100]
    std_noises = [0, 10, 20, 40]
    zslice = 850  # 850: corresponds to mid-C4 level (enlargement)
    folder_out = 'data_phantom'  # output folder
    range_tract = 0  # we do not want heterogeneity within WM and within GM. All tracts should have the same value.
    # parameters
    # args = get_parameters()
    # value_wm = args.value_wm
    # value_gm = args.value_gm
    # std_noise = args.std_noise
    # folder_out = os.path.join(os.getcwd(), "phantom_WM" + str(value_wm) + "_GM" + str(value_gm) + "_STD" + str(std_noise) + ".nii.gz")

    # Generated phantom with and without noise
    # phantom = 'phantom.nii.gz'
    # phantom_noise = 'phantom_noise_' + image + '.nii.gz'
    # tracts_sum_img = 'tracts_sum.nii.gz'

    # Extract the tracts from the atlas folder
    folder_atlas = os.path.join(path_sct, "data/PAM50/atlas/")
    data_tracts = get_tracts(folder_atlas, zslice=zslice)
    nx, ny, nb_tracts = data_tracts.shape

    # TODO: get WM and GM indexes from info_label.txt
    ind_wm = range(0, 30)
    ind_gm = range(30, 36)

    # loop across gm_value and std_values and generate phantom
    for gm_value in gm_values:
        for std_noise in std_noises:
            # Add values to each tract
            data_tracts[:, :, ind_wm] *= wm_value
            data_tracts[:, :, ind_gm] *= gm_value
            # sum across labels
            data_phantom = np.sum(data_tracts, axis=2)
            # add noise
            if not std_noise:
                data_phantom += np.random.normal(loc=0, scale=std_noise, size=(nx, ny))
            # save as nifti file
            affine = np.diag([1, 1, 1, 1])
            im_phantom = nib.Nifti1Image(data_phantom, affine)
            fname_out = os.path.join(os.getcwd(), folder_out, "phantom_WM" + str(wm_value) + "_GM" + str(gm_value) + "_STD" + str(std_noise) + ".nii.gz")
            nib.save(im_phantom, fname_out)


    #
    #
    # # Generate the phantom
    # [synthetic_vol, synthetic_voln, values_synthetic_data, tracts_sum] = phantom_generation(tracts, std_noise, range_tract, value_wm, value_gm, folder_out)
    #
    # # Save the phantom without added noise to niftii image
    # save_3D_nparray_nifti(synthetic_vol, phantom)
    #
    # # Save the phantom with added noise to niftii image
    # save_3D_nparray_nifti(synthetic_voln, phantom_noise)
    #
    # # Save the sum of the tracts to nifti image
    # save_3D_nparray_nifti(tracts_sum, tracts_sum_img)
    #
    # # adjust geometry between saved images and tracts
    # fname_tract = glob.glob(os.path.join(folder_atlas, "*.nii.gz"))
    # # sct.run('fslcpgeom ' + fname_tract[0] + ' ' + os.path.join(folder_out,phantom))
    # # sct.run('fslcpgeom ' + fname_tract[0] + ' ' + os.path.join(folder_out,phantom_noise))
    # # sct.run('fslcpgeom ' + fname_tract[0] + ' ' + os.path.join(folder_out,tracts_sum_img))

if __name__ == "__main__":
    # if not os.path.exists(folder_out):
    #     os.makedirs(folder_out)
    # fname_phantom = os.path.join(folder_out, 'phantom_values.txt')
    sct.init_sct()  # start logger
    main()
