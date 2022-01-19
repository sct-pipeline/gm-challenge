#!/usr/bin/env python
# Compute SNR, contrast, CNR and CNR/unit time. Write output  Output values in stdout.
# Author: Julien Cohen-Adad

# TODO: use logging

import argparse
import json
import os.path
import nibabel
import numpy as np


def get_parser():
    parser = argparse.ArgumentParser(description='Compute SNR, contrast, CNR using two different methods. These '
                                                 'metrics are computed slice-by-slice and then averaged across slices. '
                                                 'If a JSON sidecar is present and includes the field '
                                                 'AcquisitionDuration, this script will also compute CNR per unit '
                                                 'time.')
    parser.add_argument('--data1', help='First volume')
    parser.add_argument('--data2', help='Second volume (required for the "diff" method)', required=False)
    parser.add_argument('--mask-noise', help='Mask where to compute noise.')
    parser.add_argument('--mask-wm', help='Mask of the white matter.')
    parser.add_argument('--mask-gm', help='Mask of the gray matter.')
    parser.add_argument('--json', help='JSON sidecar to fetch acquisition duration.')
    parser.add_argument('--subject', help='Subject ID', default='sub')
    parser.add_argument('--output', help='CSV output file.')
    return parser


def compute_cnr_time(data, mask_wm, mask_gm, noise_slice, fname_json):
    """
    Compute contrast, CNR and CNR per unit time
    Args:
        data: 3d array to compute CNR from
        mask_wm: mask of white matter
        mask_gm: mask of gray matter
        noise_slice: noise standard deviation per slice
        fname_json: file name of JSON file that contains the AcquisitionDuration information. If 'None', does not
                    compute cnr_time and output 'None' instead

    Returns:
        contrast: in percent
        cnr
        cnr_time
    """
    nx, ny, nz = data.shape
    mean_wm_slice = \
        [np.average(data[..., iz], weights=mask_wm[..., iz]) for iz in range(nz) if np.any(mask_wm[..., iz])]
    mean_gm_slice = \
        [np.average(data[..., iz], weights=mask_gm[..., iz]) for iz in range(nz) if np.any(mask_gm[..., iz])]
    contrast_slice = [abs(mean_wm_slice[iz] - mean_gm_slice[iz]) / mean_wm_slice[iz] for iz in range(nz)]
    contrast = 100 * sum(contrast_slice) / len(contrast_slice)
    cnr_slice = [abs(mean_wm_slice[iz] - mean_gm_slice[iz]) / noise_slice[iz] for iz in range(nz)]
    cnr = sum(cnr_slice) / len(cnr_slice)
    # If no JSON file is provided, only return 'cnr'
    if fname_json is None:
        cnr_time = None
    else:
        # Try fetching acquisition duration. If the field is not present in the JSON file, 'ReferenceError' is raised
        try:
            acq_duration = fetch_acquisition_duration(fname_json)
            cnr_time = cnr / np.sqrt(acq_duration)
        except ReferenceError:
            print("Field 'AcquisitionDuration' was not found in the JSON sidecar. Cannot compute CNR per unit time and will"
                  "leave an empty string instead.")
            cnr_time = ''
    return contrast, cnr, cnr_time


def fetch_acquisition_duration(fname_json):
    """
    Fetch the value of AcquisitionDuration in the JSON file of the same basename as fname_nifti
    Return: float: Acquisition duration in seconds
    """
    # Open JSON file
    with open(fname_json) as f:
        dict_json = json.load(f)
        if 'AcquisitionDuration' in dict_json:
            return float(dict_json['AcquisitionDuration'])
        else:
            raise ReferenceError


def weighted_std(values, weights):
    """
    Return the weighted average and standard deviation.
    values, weights -- Numpy ndarrays with the same shape.
    Source: https://stackoverflow.com/questions/2413522/weighted-standard-deviation-in-numpy
    """
    average = np.average(values, weights=weights)
    # Fast and numerically precise:
    variance = np.average((values - average) ** 2, weights=weights)
    return np.sqrt(variance)


def main(argv=None):
    # No correction for Rician noise because the noise mask is in a region of high SNR regime (not in the background)
    rayleigh_correction = False
    # get arguments
    parser = get_parser()
    args = parser.parse_args(argv)
    data1 = nibabel.load(args.data1).get_fdata()
    nx, ny, nz = data1.shape
    mask = nibabel.load(args.mask_noise).get_fdata()
    mask_wm = nibabel.load(args.mask_wm).get_fdata()
    mask_gm = nibabel.load(args.mask_gm).get_fdata()

    # Compute mean in ROI for each z-slice, if the slice in the mask is not null
    mean_in_roi = \
        [np.average(data1[..., iz], weights=mask[..., iz]) for iz in range(nz) if np.any(mask[..., iz])]
    noise_single_slice = \
        [weighted_std(data1[..., iz], weights=mask[..., iz]) for iz in range(nz) if np.any(mask[..., iz])]
    snr_single_slice = [m / s for m, s in zip(mean_in_roi, noise_single_slice)]
    if rayleigh_correction:
        # Correcting for Rayleigh noise (see eq. A12 in Dietrich et al.)
        snr_single_slice = [snr_single_slice[iz] * np.sqrt((4 - np.pi) / 2) for iz in range(len(snr_single_slice))]
    snr_single = sum(snr_single_slice) / len(snr_single_slice)
    contrast, cnr_single, cnr_single_time = compute_cnr_time(data1, mask_wm, mask_gm, noise_single_slice, args.json)

    # Try opening data2. If it fails, inform the user and do not compute *_diff metrics
    try:
        data2 = nibabel.load(args.data2).get_fdata()
        # Compute mean across the two volumes
        data_mean = (data1 + data2) / 2
        # Compute mean in ROI for each z-slice, if the slice in the mask is not null
        mean_in_roi = [np.average(data_mean[..., iz], weights=mask[..., iz])
                       for iz in range(nz) if np.any(mask[..., iz])]
        data_sub = data2 - data1
        # Compute STD in the ROI for each z-slice. The "np.sqrt(2)" results from the variance of the subtraction of two
        # distributions: var(A-B) = var(A) + var(B).
        # More context in: https://github.com/spinalcordtoolbox/spinalcordtoolbox/issues/3481
        noise_diff_slice = [weighted_std(data_sub[..., iz] / np.sqrt(2), weights=mask[..., iz])
                            for iz in range(nz) if np.any(mask[..., iz])]
        # Compute SNR
        snr_roi_slicewise = [m / s for m, s in zip(mean_in_roi, noise_diff_slice)]
        snr_diff = sum(snr_roi_slicewise) / len(snr_roi_slicewise)
        # Compute CNR
        # Note: we compute (and overwrite) the contrast on the 'diff' case because here we are using the mean data 
        # across two volumes, which improves the precision of the contrast estimation.
        contrast, cnr_diff, cnr_diff_time = compute_cnr_time(data_mean, mask_wm, mask_gm, noise_diff_slice, args.json)
    except FileNotFoundError:
        print("'--data2' does not exist. Will not compute *_diff metrics.")
        # need to assign empty strings variables
        snr_diff, cnr_diff, cnr_diff_time = '', '', ''

    # If user asked for output in a CSV file, aggregate results and write file
    if args.output is not None:
        fname_out = args.output
        if not os.path.isfile(fname_out):
            # Add a header in case the file does not exist yet
            with open(fname_out, 'w') as f:
                f.write(f"Subject,SNR_single,SNR_diff,Contrast,CNR_single,CNR_diff,CNR_single/t,CNR_diff/t\n")
        with open(fname_out, 'a') as f:
            f.write(f"{args.subject},{snr_single},{snr_diff},{contrast},{cnr_single},{cnr_diff},{cnr_single_time},"
                    f"{cnr_diff_time}\n")
    # Otherwise, return to caller function
    else:
        # Aggregate results into a clean dictionary
        results = {
            'SNR_single': snr_single,
            'SNR_diff': snr_diff,
            'Contrast': contrast,
            'CNR_single': cnr_single,
            'CNR_diff': cnr_diff,
            'CNR_single_time': cnr_single_time,
            'CNR_diff_time': cnr_diff_time
            }
        return results


if __name__ == "__main__":
    main()
