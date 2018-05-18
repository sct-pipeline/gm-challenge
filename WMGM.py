#!/usr/bin/env python

import sys, os, shutil, subprocess, time
import numpy as np
import pandas as pd


class Param:
    def __init__(self):
        parameters = sys.argv[:]

        self.dir_data = os.path.dirname(parameters[2])
        self.num = parameters[1]

        self.file_1 = parameters[2]
        self.file_2 = parameters[3]

        self.filename_1 = os.path.basename(parameters[2])
        self.filename_2 = os.path.basename(parameters[3])

        self.volume_1 = self.filename_1.split(os.extsep)[0]
        self.volume_2 = self.filename_2.split(os.extsep)[0]
        self.ext = '.'.join(self.filename_1.split(os.extsep)[1:])

def err(output):
    status = output.communicate()

    if output.returncode != 0:
        print(status[0])

def main():
    program = "WMGM"
    dir_data = param.dir_data
    num = param.num
    file_1 = param.file_1
    file_2 = param.file_2
    volume_1 = param.volume_1
    volume_2 = param.volume_2
    ext = param.ext
    output_dir = os.path.join(dir_data + '/' + num + '_' + program)

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    shutil.copy2(file_1, output_dir)
    shutil.copy2(file_2, output_dir)

    os.chdir(output_dir)

    # Register image 2 to image 1
    register = subprocess.Popen(
        ["sct_register_multimodal", "-i", file_2, "-d", file_1, "-param", "step=1,type=im,algo=rigid", "-x", "nn", "-o",
         os.path.join(volume_2 + '_reg' + '.' + ext)], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    register.wait()
    err(register)

    # Segment spinal cord
    if not os.path.exists(os.path.join(output_dir,volume_1 + '_seg_manual' + '.' + ext)):
        seg_sc_v1 = subprocess.Popen(["sct_deepseg_sc", "-i", os.path.join(volume_1 + '.' + ext), "-c", "t2s"], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        seg_sc_v1.wait()
        err(seg_sc_v1)

    # Segment gray matter
    if not os.path.exists(os.path.join(output_dir,volume_1 + '_gmseg_manual' + '.' + ext)):
        seg_gm_v1 = subprocess.Popen(["sct_deepseg_gm", "-i", os.path.join(volume_1 + '.' + ext)], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        seg_gm_v1.wait()
        err(seg_gm_v1)

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
    param = Param()
    main()
