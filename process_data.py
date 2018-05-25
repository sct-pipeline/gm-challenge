#!/usr/bin/env python
#
# Compute metrics to assess the quality of spinal cord images.
#
# USAGE:
# The script should be launched using SCT's python:
#   PATH_GMCHALLENGE="PATH TO THIS REPOSITORY"
#   ${SCT_DIR}/python/bin/python ${PATH_GMCHALLENGE}process_data.py
#
#
# OUTPUT:
# The script generates a collection of files under specified folder.
#
# Authors: Stephanie Alley, Julien Cohen-Adad
# License: https://github.com/neuropoly/gm_challenge/blob/master/LICENSE

# TODO: get verbose working (current issue is sys.stdout.isatty()) is False, hence sct.run() is using sct.log with no terminal output
# TODO: make flag to bypass registration (not needed for phantom)

import sys, os, shutil, subprocess, time, argparse
import numpy as np
import pandas as pd
# append path to useful SCT scripts
path_sct = os.getenv('SCT_DIR')
sys.path.append(os.path.join(path_sct, 'scripts'))
import sct_utils as sct
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
    parser.add_argument("-v", "--verbose",
                        help="Verbose {0,1}. Default=1",
                        type=int,
                        default=1,
                        required=False)
    args = parser.parse_args()
    return args


def err(output):
    status = output.communicate()

    if output.returncode != 0:
        print(status[0])


def main():
    output_dir = './output_wmgm'  # TODO: be able to set with argument
    fdata2 = "data2.nii.gz"

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # copy to output directory and convert to nii.gz
    convert(file_data[0], os.path.join(output_dir, "data1.nii.gz"))
    convert(file_data[1], os.path.join(output_dir, fdata2))
    if file_seg is not None:
        convert(file_seg, os.path.join(output_dir, "data1_seg.nii.gz"))
    if file_gmseg is not None:
        convert(file_gmseg, os.path.join(output_dir, "data1_gmseg.nii.gz"))

    os.chdir(output_dir)

    # Segment spinal cord
    if file_seg is None:
        sct.run("sct_deepseg_sc -i data1.nii.gz -c t2s", verbose=verbose)

    # Segment gray matter
    if file_gmseg is None:
        sct.run("sct_deepseg_gm -i data1.nii.gz", verbose=verbose)

    # Generate white matter segmentation
    sct.run("sct_maths -i data1_seg.nii.gz -sub data1_gmseg.nii.gz -o data1_wmseg.nii.gz", verbose=verbose)

    if register:
        # Create mask around the cord for more accurate registration
        sct.run("sct_create_mask -i data1.nii.gz -p centerline,data1_seg.nii.gz -size 35mm", verbose=verbose)
        # Register image 2 to image 1
        sct.run("sct_register_multimodal -i " + fdata2 + " -d data1.nii.gz -param step=1,type=im,algo=slicereg,metric=CC "
                "-m mask_data1.nii.gz -x spline", verbose=verbose)
        # Add suffix to file name
        sct.add_suffix(fdata2, "_reg")

    # Analysis: compute metrics
    # Initialize data frame for reporting results
    results = pd.DataFrame(np.nan, index=['SNR', 'Contrast', 'Sharpness'], columns=['Metric Value'])

    # Compute SNR
    sct.run("sct_image -i data1.nii.gz," + fdata2 + " -concat t -o data_concat.nii.gz")
    status, output = sct.run("sct_compute_snr -i data_concat.nii.gz -vol 0,1 -m data1_seg.nii.gz")
    # parse SNR info
    snr = np.float(output[output.index("SNR_diff =") + 11:])
    results.loc['SNR'] = snr

    #------- Contrast -------
    if not os.path.exists(os.path.join(output_dir,volume_1 + '_gmseg_manual' + '.' + ext)):
        mean_wm = subprocess.Popen(["sct_extract_metric", "-i", os.path.join(volume_1 + '.' + ext), "-f",
                             os.path.join(volume_1 + '_wmseg' + '.' + ext), "-method", "max", "-o", "mean_wm.txt"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        mean_wm.wait()
        err(mean_wm)

        mean_gm = subprocess.Popen(["sct_extract_metric", "-i", os.path.join(volume_1 + '.' + ext), "-f",
                             os.path.join(volume_1 + '_gmseg' + '.' + ext), "-method", "max", "-o", "mean_gm.txt"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        mean_gm.wait()
        err(mean_gm)
    else:
        mean_wm = subprocess.Popen(["sct_extract_metric", "-i", os.path.join(volume_1 + '.' + ext), "-f",
                             os.path.join(volume_1 + '_wmseg_manual' + '.' + ext), "-method", "max", "-o", "mean_wm.txt"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        mean_wm.wait()
        err(mean_wm)

        mean_gm = subprocess.Popen(["sct_extract_metric", "-i", os.path.join(volume_1 + '.' + ext), "-f",
                             os.path.join(volume_1 + '_gmseg_manual' + '.' + ext), "-method", "max", "-o", "mean_gm.txt"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        mean_gm.wait()
        err(mean_gm)

    with open("mean_wm.txt") as file:
        output_wm = file.readlines()

    mean_wm_results = output_wm[-1].split(",")

    with open("mean_gm.txt") as file:
        output_gm = file.readlines()

    mean_gm_results = output_gm[-1].split(",")

    contrast = abs(float(mean_wm_results[3]) - float(mean_gm_results[3])) / min([float(mean_wm_results[3]), float(mean_gm_results[3])])

    results.loc['Contrast'] = contrast

    #------- Sharpness -------
    laplacian = subprocess.Popen(["sct_maths", "-i", os.path.join(volume_1 + '.' + ext), "-laplacian", "3", "-o",
                             os.path.join(volume_1 + '_lap' + '.' + ext)], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    laplacian.wait()
    err(laplacian)

    if not os.path.exists(os.path.join(output_dir,volume_1 + '_seg_manual' + '.' + ext)):
        mean_lap = subprocess.Popen(["sct_extract_metric", "-i", os.path.join(volume_1 + '_lap' + '.' + ext), "-f",
                             os.path.join(volume_1 + '_seg' + '.' + ext), "-method", "max", "-o", "sharpness.txt"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        mean_lap.wait()
        err(mean_lap)
    else:
        mean_lap = subprocess.Popen(["sct_extract_metric", "-i", os.path.join(volume_1 + '_lap' + '.' + ext), "-f",
                             os.path.join(volume_1 + '_seg_manual' + '.' + ext), "-method", "max", "-o", "sharpness.txt"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        mean_lap.wait()
        err(mean_lap)

    with open("sharpness.txt") as file:
        output_sharp = file.readlines()

    sharpness = output_sharp[-1].split(",")

    results.loc['Sharpness'] = sharpness[3]

    if os.path.isfile(os.path.join(num + '_' + program + '_results' + '.txt')):
        os.remove(os.path.join(num + '_' + program + '_results' + '.txt'))

    results.columns = ['']

    results_to_return = open(os.path.join(num + '_' + program + '_results' + '.txt'), 'w')
    results_to_return.write('The following metric values were calculated:\n')
    results_to_return.write(results.__repr__())
    results_to_return.write('\n\nA text file containing this information, as well as the image segmentations, is available for download through the link below. Please note that these are the intermediate results (automatically processed). We acknowledge that manual adjustment of the cord and gray matter segmentations might be necessary. They will be performed in the next few days, and the final results will be sent back to you.\n')
    results_to_return.close()

    # Copy text file containing results to segmentations folder
    shutil.copy2(os.path.join(num + '_' + program + '_results' + '.txt'), os.path.join(output_dir + '/segmentations'))

    # Create ZIP file of segmentation results
    shutil.make_archive(os.path.join(num + '_' + program + '_results'), 'zip', os.path.join(output_dir + '/segmentations'))

    # Move results files to data directory 
    if os.path.isfile(os.path.join(dir_data + '/' + num + '_' + program + '_results' + '.txt')):
        os.remove(os.path.join(dir_data + '/' + num + '_' + program + '_results' + '.txt'))
    shutil.move(os.path.join(output_dir + '/segmentations/' + num + '_' + program + '_results' + '.txt'), os.path.join(dir_data  + '/' + num + '_' + program + '.txt'))

    if os.path.isfile(os.path.join(dir_data + '/' + num + '_' + program + '_results' + '.zip')):
        os.remove(os.path.join(dir_data + '/' + num + '_' + program + '_results' + '.zip'))
    shutil.move(os.path.join(num + '_' + program + '_results' + '.zip'), os.path.join(dir_data  + '/' + num + '_' + program + '.zip'))


if __name__ == "__main__":
    args = get_parameters()
    file_data = args.input
    file_seg = args.seg
    file_gmseg = args.gmseg
    register = args.register
    verbose = args.verbose
    main()
