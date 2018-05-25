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
    args = parser.parse_args()
    return args


# class Param:
#     def __init__(self):
#         parameters = sys.argv[:]
#
#         self.dir_data = os.path.dirname(parameters[2])
#         self.num = parameters[1]
#
#         self.file_1 = parameters[2]
#         self.file_2 = parameters[3]
#
#         self.filename_1 = os.path.basename(parameters[2])
#         self.filename_2 = os.path.basename(parameters[3])
#
#         self.volume_1 = self.filename_1.split(os.extsep)[0]
#         self.volume_2 = self.filename_2.split(os.extsep)[0]
#         self.ext = '.'.join(self.filename_1.split(os.extsep)[1:])

def err(output):
    status = output.communicate()

    if output.returncode != 0:
        print(status[0])


def main():
    # program = "WMGM"
    # dir_data = param.dir_data
    # num = param.num
    # file_1 = param.file_1
    # file_2 = param.file_2
    # volume_1 = param.volume_1
    # volume_2 = param.volume_2
    # ext = param.ext
    # output_dir = os.path.join(dir_data + '/' + num + '_' + program)
    output_dir = './output_wmgm'

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # copy to output directory and convert to nii.gz
    convert(file_data[0], os.path.join(output_dir, "data1.nii.gz"))
    convert(file_data[1], os.path.join(output_dir, "data2.nii.gz"))
    os.chdir(output_dir)

    # Segment spinal cord
    if file_seg is None:
        sct.run("sct_deepseg_sc -i data1.nii.gz -c t2s")
    else:
        convert(file_seg, os.path.join(output_dir, "data1_seg.nii.gz"))

    # Segment gray matter
    if file_gmseg is None:
        sct.run("sct_deepseg_sc -i data1.nii.gz")
    else:
        convert(file_gmseg, os.path.join(output_dir, "data1_gmseg.nii.gz"))

    # Create mask around the cord for more accurate registration
    # TODO

    # Register image 2 to image 1
    sct.run("sct_register_multimodal -i data2.nii.gz -d data1.nii.gz -param step=1,type=im,algo=slicereg,metric=CC "
            "-m mask_data1.nii.gz -x spline")


    # Move cord and gray matter segmentations into a separate folder to be returned to the user
    segmentations = os.path.join(output_dir + '/segmentations')
    if not os.path.exists(segmentations):
        os.makedirs('segmentations')

    shutil.copy2(os.path.join(volume_1 + '_seg' + '.' + ext), segmentations)
    shutil.copy2(os.path.join(volume_1 + '_gmseg' + '.' + ext), segmentations)

    if os.path.exists(os.path.join(output_dir,volume_1 + '_seg_manual' + '.' + ext)):
        shutil.copy2(os.path.join(volume_1 + '_seg_manual' + '.' + ext), segmentations)
        shutil.copy2(os.path.join(volume_1 + '_gmseg_manual' + '.' + ext), segmentations)

    # Generate white matter segmentation
    if not os.path.exists(os.path.join(volume_1 + '_wmseg_manual' + '.' + ext)):
        seg_wm_v1 = subprocess.Popen(["sct_maths", "-i", os.path.join(volume_1 + '_seg' + '.' + ext), "-sub",
                             os.path.join(volume_1 + '_gmseg' + '.' + ext), "-o",
                             os.path.join(volume_1 + '_wmseg' + '.' + ext)], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        seg_wm_v1.wait()
        err(seg_wm_v1)

    # Analysis: compute metrics
    # Initialize data frame for reporting results
    results = pd.DataFrame(np.nan, index=['SNR', 'Contrast', 'Sharpness'], columns=['Metric Value'])

    #------- SNR -------
    concat = subprocess.Popen(
        ["sct_image", "-i", os.path.join(volume_1 + '.' + ext + ',' + volume_2 + '_reg' + '.' + ext), "-concat", "t",
         "-o", "t2s_concat.nii.gz"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    concat.wait()
    err(concat)

    if not os.path.exists(os.path.join(output_dir,volume_1 + '_seg_manual' + '.' + ext)):
        snr = subprocess.Popen(
        ["sct_compute_snr", "-i", "t2s_concat.nii.gz", "-m", os.path.join(volume_1 + '_seg' + '.' + ext), "-vol",
         "0,1"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        snr.wait()
    else:
        snr = subprocess.Popen(
        ["sct_compute_snr", "-i", "t2s_concat.nii.gz", "-m", os.path.join(volume_1 + '_seg_manual' + '.' + ext), "-vol",
         "0,1"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        snr.wait()

    if snr.returncode != 0:
        print(snr.communicate()[0])

    snr_output = snr.communicate()[0]
    snr_results = snr_output.split("SNR_diff =")

    results.loc['SNR'] = snr_results[1].strip()

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
    main()
