#!/usr/bin/env python
#
# Compute metrics to assess the quality of spinal cord images.
#
# USAGE:
# The script should be launched using SCT's python:
#   PATH_GMCHALLENGE="PATH TO THIS REPOSITORY"
#   ${SCT_DIR}/python/bin/python ${PATH_GMCHALLENGE}process_data.py
#
# OUTPUT:
#   results.csv: quantitative results in CSV format
#   results.txt: results in txt form to be sent to participant
#
# Authors: Stephanie Alley, Julien Cohen-Adad
# License: https://github.com/neuropoly/gm_challenge/blob/master/LICENSE

# TODO: enable to input suffix for results filename (otherwise, overwriting in process_folder
# TODO: get verbose working (current issue is sys.stdout.isatty()) is False, hence sct.run() is using sct.log with no terminal output

import sys, os, shutil, argparse, pickle, io
import numpy as np
import pandas as pd
# append path to useful SCT scripts
path_sct = os.getenv('SCT_DIR')
sys.path.append(os.path.join(path_sct, 'scripts'))
import sct_utils as sct
from msct_image import Image
from sct_convert import convert


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
                        help="Spinal cord segmentation for the first dataset.",
                        required=False)
    parser.add_argument("-g", "--gmseg",
                        help="Gray matter segmentation for the first dataset.",
                        required=False)
    parser.add_argument("-r", "--register",
                        help="Perform registration between scan #1 and scan #2. Default=1.",
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


def compute_snr_diff(file_data1, file_data2, file_mask):
    """
    Compute SNR based on two input data and a mask
    :param file_data1: image 1
    :param file_data1: image 2
    :param file_mask: mask where to compute SNR
    :return: float: SNR rounded at 2 decimals
    """
    print("Compute SNR_diff...")
    sct.run("sct_image -i " + file_data1 + "," + file_data2 + " -concat t -o data_concat.nii.gz")
    status, output = sct.run("sct_compute_snr -i data_concat.nii.gz -vol 0,1 -m " + file_mask)
    # parse SNR info
    snr_diff = np.float(output[output.index("SNR_diff =") + 11:])
    return round(snr_diff, 2) # round at 2 decimals

def compute_snr_single(file_data, file_mask):
    """
    Compute SNR based on a single image and a mask
    :param file_data: image
    :param file_mask: mask for ROI_body
    :return: float: SNR rounded at 2 decimals
    """
    print("Compute SNR_single...")
    # Convert image to array
    data = Image(file_data).data
    # Convert mask to array
    wm_mask = Image(file_mask).data
    roi= np.where(wm_mask == 1)
    roi_data = data[roi]
    snr_single = np.mean(roi_data) / np.std(roi_data)
    return round(snr_single, 2)

def compute_contrast(file_data, file_mask1, file_mask2):
    """
    Compute contrast in image between two regions
    :param file_data: image
    :param file_mask1: mask for region 1
    :param file_mask2: mask for region 2
    :return: float: contrast in percent (rounded at 2 decimals)
    """
    print("Compute contrast...")
    # Get mean value within mask
    sct.run("sct_extract_metric -i " + file_data + " -f " + file_mask1 + " -method bin -o mean_mask1.pickle")
    sct.run("sct_extract_metric -i " + file_data + " -f " + file_mask2 + " -method bin -o mean_mask2.pickle")
    # Retrieve values from saved pickle
    mean_mask1 = pickle.load(io.open("mean_mask1.pickle"))["Metric value"][0]
    mean_mask2 = pickle.load(io.open("mean_mask2.pickle"))["Metric value"][0]
    # Compute contrast in percentage
    contrast = abs(mean_mask1 - mean_mask2) / min(mean_mask1, mean_mask2) * 100
    return round(contrast, 2)  # round at 2 decimals


def compute_sharpness(file_data, file_mask_gm):
    """
    Compute sharpness at GM/WM interface. The mask of GM is dilated, and then subtracted from the GM mask, in order to
    produce a mask at the GM/WM interfact. This mask is then used to extract the Laplacian value of the image. The
    sharper the transition, the higher the Laplacian. Note that the Laplacian will also be affected by the underlying
    WM/GM contrast, hence the WM and GM values need to be normalized before computing the Laplacian.
    :param file_data:
    :param file_mask_gm:
    :return: float: sharpness
    """
    print("Compute sharpness...")
    # Dilate GM mask
    sct.run("sct_maths -i data1_gmseg.nii.gz -dilate 1 -o data1_gmseg_dil.nii.gz")
    # Subtract to get mask at WM/GM interface
    sct.run("sct_maths -i data1_gmseg_dil.nii.gz -sub data1_gmseg.nii.gz -o mask_interface.nii.gz")
    # Compute Laplacian on image
    sct.run("sct_maths -i data1.nii.gz -laplacian 0.5,0.5,0 -o data1_lapl.nii.gz")
    # Normalize WM/GM before computing Laplacian
    # TODO
    # Extract Laplacian at WM/GM interface
    sct.run("sct_extract_metric -i data1_lapl.nii.gz -f mask_interface.nii.gz -o laplacian.pickle")
    # return
    return pickle.load(io.open("laplacian.pickle"))["Metric value"][0]


def main(file_data, file_seg, file_gmseg, register=1, num=None, output_dir=None, verbose=1):
    """
    Compute metrics to assess the quality of spinal cord images.
    :param file_data:
    :param file_seg:
    :param file_gmseg:
    :param register:
    :param num:
    :param output_dir:
    :param verbose:
    :return: results: pandas dataframe with results
    """

    # Params
    if not output_dir:
        output_dir = "./output_wmgm"
    file_output = "results"  # no prefix
    fdata2 = "data2.nii.gz"

    # Parse arguments
    # if not args:
    #     args = sys.argv[1:]
    # file_data = args.input
    # file_seg = args.seg
    # file_gmseg = args.gmseg
    # register = args.register
    # num = args.num
    # verbose = args.verbose

    # Make output dir
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # copy to output directory and convert to nii.gz
    print("Copy data...")
    convert(file_data[0], os.path.join(output_dir, "data1.nii.gz"))
    convert(file_data[1], os.path.join(output_dir, fdata2))
    if file_seg is not None:
        convert(file_seg, os.path.join(output_dir, "data1_seg.nii.gz"))
    if file_gmseg is not None:
        convert(file_gmseg, os.path.join(output_dir, "data1_gmseg.nii.gz"))

    curdir = os.getcwd()
    os.chdir(output_dir)

    # Segment spinal cord
    if file_seg is None:
        print("Segment spinal cord...")
        sct.run("sct_deepseg_sc -i data1.nii.gz -c t2s", verbose=verbose)

    # Segment gray matter
    if file_gmseg is None:
        print("Segment gray matter...")
        sct.run("sct_deepseg_gm -i data1.nii.gz", verbose=verbose)

    # Generate white matter segmentation
    print("Generate white matter segmentation...")
    sct.run("sct_maths -i data1_seg.nii.gz -sub data1_gmseg.nii.gz -o data1_wmseg.nii.gz", verbose=verbose)

    if register:
        print("Register data2 to data1...")
        # Create mask around the cord for more accurate registration
        sct.run("sct_create_mask -i data1.nii.gz -p centerline,data1_seg.nii.gz -size 35mm", verbose=verbose)
        # Register image 2 to image 1
        sct.run("sct_register_multimodal -i " + fdata2 + " -d data1.nii.gz -param step=1,type=im,algo=slicereg,metric=CC "
                "-m mask_data1.nii.gz -x nn", verbose=verbose)
        # Add suffix to file name
        sct.add_suffix(fdata2, "_reg")

    # Analysis: compute metrics
    # Initialize data frame for reporting results
    results = pd.DataFrame(np.nan, index=['SNR_diff', 'SNR_single', 'Contrast'], columns=['Metric Value'])

    # Compute metrics
    results.loc['SNR_diff'] = compute_snr_diff("data1.nii.gz", fdata2, "data1_wmseg.nii.gz")
    results.loc['SNR_single'] = compute_snr_single("data1.nii.gz", "data1_wmseg.nii.gz")
    results.loc['Contrast'] = compute_contrast("data1.nii.gz", "data1_wmseg.nii.gz", "data1_gmseg.nii.gz")
    # results.loc['Sharpness'] = compute_sharpness("data1.nii.gz", "data1_gmseg.nii.gz")

    # Display results
    results.columns = ['']

    # Save DataFrame as CSV
    results.to_csv(file_output + ".csv")
    print("--> created file: " + file_output + ".csv")

    # Build text file for user
    results_to_return = open(file_output + ".txt", 'w')
    results_to_return.write('The following metric values were calculated:\n')
    results_to_return.write(results.__repr__())
    results_to_return.write('\n\nA text file containing this information, as well as the image segmentations, are '
                            'available for download through the link below. Please note that these are the intermediate '
                            'results (automatically processed). We acknowledge that manual adjustment of the cord and '
                            'gray matter segmentations might be necessary. They will be performed in the next few days, '
                            'and the final results will be sent back to you.\n')
    results_to_return.close()
    print("--> created file: " + file_output + ".txt")

    # Package results inside folder
    # TODO
    #Package results for daemon
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
    main(args.input, args.seg, args.gmseg, register=args.register, num=args.num, output_dir=args.output_dir, verbose=args.verbose)
