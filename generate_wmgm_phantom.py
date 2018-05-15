#!/usr/bin/env python
#
# Generates a synthetic phantom from the WM and GM atlas.
# Saves the phantom to a NIfTI image
#
# The script should be launched using SCT's python:
#
#    cd $SCT_DIR
#    source python/bin/activate
#    python generate_wmgm_phantom.py <value_wm> <value_gm> <std_noise> <image>
#
# Example of usage:
#    python generate_wmgm_phantom.py 50 40 10 created_phantom.nii.gz
#
# Authors: Stephanie Alley, Julien Cohen-Adad
# License: https://github.com/neuropoly/gm_challenge/blob/master/LICENSE


import os
import argparse
import glob
import sct_utils as sct
import numpy as np
import random
import nibabel as nib

def get_parameters():
    parser = argparse.ArgumentParser(description='Generate a phantom for measuring metric sensitivity')
    parser.add_argument('value_wm', type=int)
    parser.add_argument('value_gm', type=int)
    parser.add_argument('std_noise', type=int)
    parser.add_argument('image')
    args = parser.parse_args()

    return args

#=======================================================================================================================
# Get tracts 
#=======================================================================================================================
def get_tracts(tracts_folder):
    # Loads tracts in an atlas folder and converts them from .nii.gz format to numpy ndarray 
    # Save path of each tracts
    # Only the tract must be in tracts_format in the folder
    fname_tract = glob.glob(tracts_folder + '/*' + '.nii.gz')
    
    #Initialise tracts variable as object because there are 4 dimensions
    tracts = np.empty([len(fname_tract), 1], dtype=object)
    
    #Load each partial volume of each tract
    for label in range(0, len(fname_tract)):
       tracts[label, 0] = nib.load(fname_tract[label]).get_data()
    
    #Reshape tracts if it is the 2D image instead of 3D
    for label in range(0, len(fname_tract)):
       if (tracts[label,0]).ndim == 2:
           tracts[label,0] = tracts[label,0].reshape(int(np.size(tracts[label,0],0)), int(np.size(tracts[label,0],1)),1)
    return tracts

#=======================================================================================================================
# phantom generation
#=======================================================================================================================

def phantom_generation(tracts, std_noise_perc, range_tract_perc, value_wm, value_gm, folder_out):
    """
    :param tracts: np array
    :param std_noise: std of noise to generate pseudo-random Gaussian noise
    :param range_tract: range of value to generate pseudo-random uniformly distributed tract value
    :param value_wm: true value of the wm tract
    :param folder_out: output folder
    :return: synthetic_vol, synthetic_voln, values_synthetic_data, tracts_sum
    """

    # Transform std noise and range tract to a percentage of the true value
    range_tract = float(range_tract_perc) / 100 * value_wm
    std_noise = float(std_noise_perc) / 100 * value_wm

    # Generate synthetic Volume  
    numtracts = len(tracts)
    nx, ny, nz = tracts[0][0].shape

   # open txt file that includes true values per tract
    fid_file = open(fname_phantom, 'w+')
    print >> fid_file, 'std_noise='+str(std_noise_perc)+'%, range_tract='+str(range_tract_perc)+'%, value_wm='+str(value_wm)+', value_gm='+str(value_gm)

    # create volume of tracts with randomly-assigned values
    tracts_weighted = np.zeros([numtracts, nx, ny, nz])
    synthetic_vol = np.zeros([nx, ny, nz])
    synthetic_voln = np.zeros([nx, ny, nz])
    values_synthetic_data = np.zeros([numtracts])
    for i in range(0, numtracts):
        if i == numtracts-1:
            values_synthetic_data[i] = value_gm
        else:
            values_synthetic_data[i] = (value_wm - range_tract + random.uniform(0, 2*range_tract))
        print >> fid_file, 'label=' + str(i) + ', value=' + str(values_synthetic_data[i])
        tracts_weighted[i, :, :, :] = values_synthetic_data[i] * tracts[i, 0]
        # add tract to volume
        synthetic_vol = synthetic_vol + tracts_weighted[i, :, :, :]

    # sum all tracts
    tracts_sum = np.zeros([nx, ny, nz])
    for i in range(0, numtracts):
        tracts_sum = tracts_sum + tracts[i, 0]

    # close txt file
    fid_file.close()

    # add gaussian noise
    if not std_noise == 0:
        synthetic_voln = synthetic_vol + np.random.normal(loc=0, scale=std_noise, size=(nx, ny, nz))
    else:
        synthetic_voln = synthetic_vol

    return[synthetic_vol, synthetic_voln, values_synthetic_data, tracts_sum]


#=======================================================================================================================
# Save 3D numpy array to a nifti
#=======================================================================================================================
def save_3D_nparray_nifti(np_matrix_3d, output_image):
    """
    Save 3d numpy matrix to niftii image
    :param np_matrix_3d: 3d numpy array
    :param output_image:  name of the created nifti file. e.g.; 3d_matrix.nii.gz
    :return: none
    """
    img = nib.Nifti1Image(np_matrix_3d, np.eye(4))
    affine = img.get_affine()
    np_matrix_3d_nii = nib.Nifti1Image(np_matrix_3d,affine)
    nib.save(np_matrix_3d_nii, os.path.join(folder_out,output_image))
    return None

def main():
    # Generated phantom with and without noise
    phantom = 'phantom.nii.gz'
    phantom_noise = 'phantom_noise_' + image + '.nii.gz'
    tracts_sum_img = 'tracts_sum.nii.gz'

    # Extract the tracts from the atlas folder
    tracts = get_tracts(folder_atlas)

    # Generate the phantom
    [synthetic_vol, synthetic_voln, values_synthetic_data, tracts_sum] = phantom_generation(tracts, std_noise, range_tract, value_wm, value_gm, folder_out)
    
    # Save the phantom without added noise to niftii image
    save_3D_nparray_nifti(synthetic_vol, phantom)
    
    # Save the phantom with added noise to niftii image
    save_3D_nparray_nifti(synthetic_voln, phantom_noise)
    
    # Save the sum of the tracts to nifti image
    save_3D_nparray_nifti(tracts_sum, tracts_sum_img)
    
    # adjust geometry between saved images and tracts
    fname_tract = glob.glob(os.path.join(folder_atlas, "*.nii.gz"))
    sct.run('fslcpgeom ' + fname_tract[0] + ' ' + os.path.join(folder_out,phantom))
    sct.run('fslcpgeom ' + fname_tract[0] + ' ' + os.path.join(folder_out,phantom_noise))
    sct.run('fslcpgeom ' + fname_tract[0] + ' ' + os.path.join(folder_out,tracts_sum_img))

if __name__ == "__main__":
    args = get_parameters()
    
    # Phantom parameters
    value_wm = args.value_wm
    value_gm = args.value_gm
    std_noise = args.std_noise
    image = args.image
    range_tract = 5
    folder_out = os.path.join(os.getcwd(),"phantom_" + str(value_wm) + "_" + str(value_gm) + "_" + str(std_noise) + "_image" + image)
    folder_atlas = "data/final_results"

    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    fname_phantom = os.path.join(folder_out, 'phantom_values.txt')
    main()
