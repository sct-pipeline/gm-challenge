#!/usr/bin/env python
#
# Compute metrics to assess the quality of spinal cord images.
#
# This script is "old" and was replaced by process_data.sh. However, the portion specific to niftiweb was kept
# uncommented and requires some digging before being used.
#
# USAGE:
# The script should be launched using SCT's python:
#   PATH_GMCHALLENGE="PATH TO THIS REPOSITORY"
#   ${SCT_DIR}/python/bin/python ${PATH_GMCHALLENGE}/process_data.py
#
# OUTPUT:
#   results.csv: quantitative results in CSV format
#   results.txt: results in txt form to be sent to participant
#
# Authors: Stephanie Alley, Julien Cohen-Adad
# License: https://github.com/neuropoly/gm_challenge/blob/master/LICENSE

# TODO: enable to input suffix for results filename (otherwise, overwriting in process_folder
# TODO: get verbose working (current issue is sys.stdout.isatty()) is False, hence sct.run() is using sct.log with no terminal output


import sys, os, shutil, argparse, pickle, io, argparse
import numpy as np
import pandas as pd
# append path to useful SCT scripts
path_sct = os.getenv('SCT_DIR')
sys.path.append(os.path.join(path_sct, 'scripts'))
import sct_utils as sct
from spinalcordtoolbox.image import Image


def get_parameters():
    parser = argparse.ArgumentParser(description='Compute metrics to assess the quality of spinal cord images. This '
                                                 'script requires two input files of scan-rescan acquisitions, which '
                                                 'will be used to compute the SNR. Other metrics (contrast, sharpness) '
                                                 'will be computed from the first file.')
    parser.add_argument("-i", "--input",
                        help="List here the two nifti files to compute the metrics on, separated by space.",
                        nargs='+',
                        required=True)
    parser.add_argument("-s", "--seg",
                        help="Spinal cord segmentation for the first dataset. If not provided, segmentation will be "
                             "performed.",
                        required=False)
    parser.add_argument("-g", "--gmseg",
                        help="Gray matter segmentation for the first dataset. If not provided, segmentation will be "
                             "performed.",
                        required=False)
    parser.add_argument("-r", "--register",
                        help="{0, 1}. Perform registration between scan #1 and scan #2. Default=1.",
                        type=int,
                        default=1,
                        required=False)
    parser.add_argument("-n", "--num",
                        help="NiftyWeb ID",
                        required=False)
    parser.add_argument("-o", "--output_dir",
                        help="Output directory",
                        required=False)
    parser.add_argument("-v", "--verbose",
                        help="Verbose {0,1}. Default=1",
                        type=int,
                        default=1,
                        required=False)
    args = parser.parse_args()
    return args

#
# def compute_snr_diff(file_data1, file_data2, file_mask):
#     """
#     Compute SNR based on two input data and a mask
#     :param file_data1: image 1
#     :param file_data2: image 2
#     :param file_mask: mask where to compute SNR
#     :return: float: SNR_diff rounded at 2 decimals
#     """
#     print("Compute SNR_diff...")
#     sct.run("sct_image -i " + file_data1 + "," + file_data2 + " -concat t -o data_concat.nii.gz")
#     status, output = sct.run("sct_compute_snr -i data_concat.nii.gz -vol 0,1 -m " + file_mask)
#     # parse SNR info
#     # TODO: run sct_compute_snr as Python module
#     try:
#         outstring = output[output.index("SNR_diff =") + 11:]
#         snr_diff = np.float(outstring[: outstring.index("\n")])
#     except Exception as e:
#         print(e)
#     return round(snr_diff, 2)  # round at 2 decimals
#
#
# def compute_snr_single(file_data, file_mask):
#     """
#     Compute SNR based on a single image and a mask
#     :param file_data: image
#     :param file_mask: mask for ROI_body
#     :return: float: SNR_single rounded at 2 decimals
#     """
#     print("Compute SNR_single...")
#     # Convert image to array
#     data = Image(file_data).data
#     # Convert mask to array
#     wm_mask = Image(file_mask).data
#     # Use mask to select data in ROI_body
#     roi_data = np.where(wm_mask == 1, data, 0)
#     # Compute SNR slice-wise
#     # snr_slices = np.zeros((roi_data.shape[2]))
#     snr_slices = []
#     for i in range(roi_data.shape[2]):
#         ind_nonzero = np.where(roi_data[:, :, i] > 0)
#         # check if there is non-null voxel on this slice
#         if len(ind_nonzero[0]):
#             mean_slice = np.mean(roi_data[:, :, i][ind_nonzero])
#             std_slice = np.std(roi_data[:, :, i][ind_nonzero])
#             snr_slice = mean_slice / std_slice
#             # snr_slices[i] = snr_slice
#             snr_slices.append(snr_slice)
#     snr_single = np.mean(snr_slices)
#     return round(snr_single, 2)
#
#
# def compute_contrast(file_data, file_mask1, file_mask2):
#     """
#     Compute contrast in image between two regions
#     :param file_data: image
#     :param file_mask1: mask for region 1
#     :param file_mask2: mask for region 2
#     :return: float: contrast in percent (rounded at 2 decimals)
#     """
#     print("Compute contrast...")
#     # Get mean value within mask
#     sct.run("sct_extract_metric -i " + file_data + " -f " + file_mask1 + " -method bin -o mean_mask1.pickle")
#     sct.run("sct_extract_metric -i " + file_data + " -f " + file_mask2 + " -method bin -o mean_mask2.pickle")
#     # Retrieve values from saved pickle
#     mean_mask1 = pickle.load(io.open("mean_mask1.pickle"))["Metric value"][0]
#     mean_mask2 = pickle.load(io.open("mean_mask2.pickle"))["Metric value"][0]
#     # Compute contrast in percentage
#     contrast = abs(mean_mask1 - mean_mask2) / min(mean_mask1, mean_mask2) * 100
#     return round(contrast, 2)  # round at 2 decimals
#
#
# def compute_sharpness(file_data, file_mask_gm):
#     """
#     Compute sharpness at GM/WM interface. The mask of GM is dilated, and then subtracted from the GM mask, in order to
#     produce a mask at the GM/WM interfact. This mask is then used to extract the Laplacian value of the image. The
#     sharper the transition, the higher the Laplacian. Note that the Laplacian will also be affected by the underlying
#     WM/GM contrast, hence the WM and GM values need to be normalized before computing the Laplacian.
#     :param file_data:
#     :param file_mask_gm:
#     :return: float: sharpness
#     """
#     print("Compute sharpness...")
#     # Dilate GM mask
#     sct.run("sct_maths -i data1_gmseg.nii.gz -dilate 1 -o data1_gmseg_dil.nii.gz")
#     # Subtract to get mask at WM/GM interface
#     sct.run("sct_maths -i data1_gmseg_dil.nii.gz -sub data1_gmseg.nii.gz -o mask_interface.nii.gz")
#     # Compute Laplacian on image
#     sct.run("sct_maths -i data1.nii.gz -laplacian 0.5,0.5,0 -o data1_lapl.nii.gz")
#     # Normalize WM/GM before computing Laplacian
#     # TODO
#     # Extract Laplacian at WM/GM interface
#     sct.run("sct_extract_metric -i data1_lapl.nii.gz -f mask_interface.nii.gz -o laplacian.pickle")
#     # return
#     return pickle.load(io.open("laplacian.pickle"))["Metric value"][0]


def main(file_input, file_seg, file_gmseg, num=None, register=True, output_dir=None, create_txt_output=False, verbose=1):
    """
    Compute metrics to assess the quality of spinal cord images.
    :param file_data:
    :param file_seg:
    :param file_gmseg:
    :param num:
    :param register: Bool: Register data2 to data1. Could be skipped if data are already registered (e.g. simulations)
    :param output_dir:
    :param create_txt_output: Bool: Create output txt file for Niftyweb server
    :param verbose:
    :return: results: pandas dataframe with results
    """
    # 
    # # Params
    # if not output_dir:
    #     output_dir = "./results"
    # file_output = "results"  # no prefix
    # fdata = ['data1.nii.gz', 'data2.nii.gz']
    # fseg = 'data1_seg.nii.gz'
    # fgmseg = 'data1_gmseg.nii.gz'

    # Parse arguments
    # if not args:
    #     args = sys.argv[1:]
    # file_data = args.input
    # file_seg = args.seg
    # file_gmseg = args.gmseg
    # register = args.register
    # num = args.num
    # verbose = args.verbose
    # 
    # # Make output dir
    # if not os.path.isdir(output_dir):
    #     os.makedirs(output_dir)
    # 
    # # copy to output directory and convert to nii.gz
    # print("Copy data...")
    # sct.copy(file_input[0], os.path.join(output_dir, fdata[0]))
    # if os.path.isfile(file_input[1]):
    #     sct.copy(file_input[1], os.path.join(output_dir, fdata[1]))
    #     run_diff_method = True
    # else:
    #     run_diff_method = False
    # if file_seg is not None:
    #     sct.copy(file_seg, os.path.join(output_dir, fseg))
    # if file_gmseg is not None:
    #     sct.copy(file_gmseg, os.path.join(output_dir, fgmseg))
    # 
    # # move to results directory
    # curdir = os.getcwd()
    # os.chdir(output_dir)
    # 
    # # Segment spinal cord
    # if file_seg is None:
    #     print("Segment spinal cord...")
    #     sct.run("sct_deepseg_sc -i " + fdata[0] + " -c t2s", verbose=verbose)
    # 
    # # Segment gray matter
    # if file_gmseg is None:
    #     print("Segment gray matter...")
    #     sct.run("sct_deepseg_gm -i " + fdata[0], verbose=verbose)

    # # Crop data (for faster processing)
    # print("Crop data (for faster processing)...")
    # sct.run("sct_create_mask -i " + fdata[0] + " -p centerline," + fseg + " -size 35mm", verbose=verbose)
    # fmask = "mask_" + fdata[0]
    # sct.run("sct_crop_image -i " + fdata[0] + " -m " + fmask + " -o " + sct.add_suffix(fdata[0], 'c'))
    # fdata[0] = sct.add_suffix(fdata[0], 'c')
    # sct.run("sct_crop_image -i " + fseg + " -m " + fmask + " -o " + sct.add_suffix(fseg, 'c'))
    # fseg = sct.add_suffix(fseg, 'c')
    # sct.run("sct_crop_image -i " + fgmseg + " -m " + fmask + " -o " + sct.add_suffix(fgmseg, 'c'))
    # fgmseg = sct.add_suffix(fgmseg, 'c')
    # 
    # # Generate white matter segmentation
    # print("Generate white matter segmentation...")
    # sct.run("sct_maths -i " + fseg + " -sub " + fgmseg + " -o " + fdata[0] + "_wmseg.nii.gz", verbose=verbose)
    # 
    # # Erode white matter mask to minimize partial volume effect
    # # Note: we cannot erode the gray matter because it is too thin (most of the time, only one voxel)
    # print("Erode white matter mask...")
    # sct.run("sct_maths -i " + fdata[0] + "_wmseg.nii.gz -erode 1 -o " + fdata[0] + "_wmseg_erode.nii.gz", verbose=verbose)

    # if run_diff_method and register:
    #     print("Register data2 to data1...")
    #     # Register image 2 to image 1
    #     sct.run("sct_register_multimodal -i " + fdata[1] + " -d " + fdata[0] + " -param step=2,type=im,algo=rigid,metric=MeanSquares,smooth=1,iter=50,slicewise=1 -x nn", verbose=verbose)
    #     # Add suffix to file name
    #     fdata[1] = sct.add_suffix(fdata[1], "_reg")

    # Analysis: compute metrics
    # Initialize data frame for reporting results
    results = pd.DataFrame(0, index=['SNR_diff', 'SNR_single', 'Contrast'], columns=['Metric Value'])

    # Compute metrics
    results.loc['Contrast'] = compute_contrast(fdata[0], fdata[0] + "_wmseg.nii.gz", fgmseg)
    results.loc['SNR_single'] = compute_snr_single(fdata[0], fdata[0] + "_wmseg_erode.nii.gz")
    if run_diff_method:
        results.loc['SNR_diff'] = compute_snr_diff(fdata[0], fdata[1], fdata[0] + "_wmseg_erode.nii.gz")
    # results.loc['Sharpness'] = compute_sharpness("data1.nii.gz", "data1_gmseg.nii.gz")

    # Save DataFrame as CSV
    results.columns = ['']
    results.to_csv(file_output + ".csv")
    print("--> created file: " + file_output + ".csv")

    if create_txt_output:
        # Build text file for user
        results_to_return = open(file_output + ".txt", 'w')
        results_to_return.write('The following metrics were calculated:\n')
        results_to_return.write(results.__repr__())
        results_to_return.write('\n\nA text file containing this information, as well as the image segmentations, are '
                                'available for download through the link below. Please note that these are the intermediate '
                                'results (automatically processed). We acknowledge that manual adjustment of the cord and '
                                'gray matter segmentations might be necessary. Please check carefully, adjust the '
                                'segmentations if necessary, and contact us for recalculating the metrics with the '
                                'corrected segmentations.\n')
        results_to_return.close()
        print("--> created file: " + file_output + ".txt")

    # Package results for daemon
    if num:
        # Create folder for segmentations
        segmentations = 'segmentations'
        if not os.path.exists(segmentations):
            os.makedirs(segmentations)

        # Copy data1_seg.nii.gz and data1_gmseg.nii.gz to segmentations folder
        shutil.copy2("data1_seg.nii.gz", segmentations)
        shutil.copy2("data1_gmseg.nii.gz", segmentations)

        # Rename text file for interaction with daemon
        os.rename(file_output + '.txt', num + '_WMGM.txt')

        # Copy text file containing results to segmentations folder
        shutil.copy2(num + '_WMGM.txt', segmentations)

        # Create ZIP file of segmentation results
        shutil.make_archive(os.path.join(num + '_WMGM'), 'zip', segmentations)

        # Move results files to data directory
        if os.path.isfile(os.path.join(curdir, num + '_WMGM.txt')):
            os.remove(os.path.join(curdir, num + '_WMGM.txt'))
        shutil.move(os.path.join(num + '_WMGM.txt'), os.path.join(curdir, num + '_WMGM.txt'))

        if os.path.isfile(os.path.join(curdir, num + '_WMGM.zip')):
            os.remove(os.path.join(curdir, num + '_WMGM.zip'))
        shutil.move(os.path.join(num + '_WMGM.zip'), os.path.join(curdir, num + '_WMGM.zip'))

    # back to current folder
    os.chdir(curdir)

    return results


if __name__ == "__main__":
    args = get_parameters()
    main(args.input, args.seg, args.gmseg, num=args.num, register=args.register, output_dir=args.output_dir,
         verbose=args.verbose)
