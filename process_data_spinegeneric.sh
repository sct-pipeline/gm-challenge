#!/bin/bash
#
# This file is a copy of process_data.sh, but adapted to the spine-generic data.
#
# Author: Julien Cohen-Adad

# The following global variables are retrieved from the caller sct_run_batch
# but could be overwritten by uncommenting the lines below:
# PATH_DATA_PROCESSED="~/data_processed"
# PATH_RESULTS="~/results"
# PATH_LOG="~/log"
# PATH_QC="~/qc"

# Uncomment for full verbose
#set -x

# Immediately exit if error
set -e -o pipefail

# Exit if user presses CTRL+C (Linux) or CMD+C (OSX)
trap "echo Caught Keyboard Interrupt within script. Exiting now.; exit" INT

# Retrieve input params
SUBJECT=$1

# get starting time:
start=`date +%s`


# FUNCTIONS
# ==============================================================================

# Check if manual segmentation already exists. If it does, copy it locally. If
# it does not, perform seg.
segment_if_does_not_exist(){
  local file="$1"
  local contrast="$2"
  # Update global variable with segmentation file name
  FILESEG="${file}_seg"
  FILESEGMANUAL="${PATH_DATA}/derivatives/labels/${SUBJECT}/anat/${FILESEG}-manual${ext}"
  echo "Looking for manual segmentation: $FILESEGMANUAL"
  if [[ -e $FILESEGMANUAL ]]; then
    echo "Found! Using manual segmentation."
    rsync -avzh $FILESEGMANUAL ${FILESEG}${ext}
    sct_qc -i ${file}${ext} -s ${FILESEG}${ext} -p sct_deepseg_sc -qc ${PATH_QC} -qc-subject ${SUBJECT}
  else
    echo "Not found. Proceeding with automatic segmentation."
    # Segment spinal cord
    sct_deepseg_sc -i ${file}${ext} -c $contrast -qc ${PATH_QC} -qc-subject ${SUBJECT}
  fi
}

# Check if manual segmentation already exists. If it does, copy it locally. If
# it does not, perform seg.
segment_gm_if_does_not_exist(){
  local file="$1"
  local contrast="$2"
  # Update global variable with segmentation file name
  FILESEG="${file}_gmseg"
  FILESEGMANUAL="${PATH_DATA}/derivatives/labels/${SUBJECT}/anat/${FILESEG}-manual${ext}"
  echo "Looking for manual segmentation: $FILESEGMANUAL"
  if [[ -e $FILESEGMANUAL ]]; then
    echo "Found! Using manual segmentation."
    rsync -avzh $FILESEGMANUAL ${FILESEG}${ext}
    sct_qc -i ${file}${ext} -s ${FILESEG}${ext} -p sct_deepseg_gm -qc ${PATH_QC} -qc-subject ${SUBJECT}
  else
    echo "Not found. Proceeding with automatic segmentation."
    # Segment spinal cord
    sct_deepseg_gm -i ${file}${ext} -qc ${PATH_QC} -qc-subject ${SUBJECT}
  fi
  # Converts GM segmentation to UINT8. See: https://github.com/spinalcordtoolbox/spinalcordtoolbox/issues/3488
  sct_image -i ${FILESEG}${ext} -type uint8 -o ${FILESEG}${ext}
}


# SCRIPT STARTS HERE
# ==============================================================================
# Display useful info for the log, such as SCT version, RAM and CPU cores available
sct_check_dependencies -short

# Go to folder where data will be copied and processed
cd $PATH_DATA_PROCESSED
# Copy source images
rsync -avzh $PATH_DATA/$SUBJECT .
# Go to folder
cd ${SUBJECT}/anat
file_1="${SUBJECT}_T2star"
ext=".nii.gz"
# Segment spinal cord
segment_if_does_not_exist $file_1 "t2s"
file_1_seg=$FILESEG
# Segment gray matter
segment_gm_if_does_not_exist $file_1
file_1_gmseg=$FILESEG
# Crop data (for faster processing)
sct_create_mask -i ${file_1}${ext} -p centerline,${file_1_seg}${ext} -size 35mm
file_mask=mask_${file_1}
sct_crop_image -i ${file_1}${ext} -m ${file_mask}${ext} -o ${file_1}_crop${ext}
file_1=${file_1}_crop
sct_crop_image -i ${file_1_seg}${ext} -m ${file_mask}${ext} -o ${file_1_seg}_crop${ext}
file_1_seg=${file_1_seg}_crop
sct_crop_image -i ${file_1_gmseg}${ext} -m ${file_mask}${ext} -o ${file_1_gmseg}_crop${ext}
file_1_gmseg=${file_1_gmseg}_crop
# Generate white matter segmentation
sct_maths -i ${file_1_seg}${ext} -sub ${file_1_gmseg}${ext} -o ${file_1}_wmseg${ext}
# Erode white matter mask to minimize partial volume effect
# Note: we cannot erode the gray matter because it is too thin (most of the time, only one voxel)
sct_maths -i ${file_1}_wmseg${ext} -erode 1 -o ${file_1}_wmseg_erode${ext}
# Compute SNR
sct_compute_snr -i ${file_1}${ext} -method single -m ${file_1}_wmseg_erode.nii.gz -m-noise ${file_1}_wmseg_erode.nii.gz -rayleigh 0 -o snr_single.txt
# Compute average value in WM and GM on a slice-by-slice basis
sct_extract_metric -i ${file_1}${ext} -f ${file_1}_wmseg${ext} -method bin -o signal_wm.csv
sct_extract_metric -i ${file_1}${ext} -f ${file_1_gmseg}${ext} -method bin -o signal_gm.csv
# Compute contrast slicewise and average across slices. Output in file: contrast.txt
python -c "import pandas; pd_gm = pandas.read_csv('signal_gm.csv'); pd_wm = pandas.read_csv('signal_wm.csv'); pd = abs(pd_gm['BIN()'] - pd_wm['BIN()']) / pandas.DataFrame([pd_gm['BIN()'], pd_wm['BIN()']]).min(); print(f'{pd.mean()}')" > contrast.txt
# Aggregate results in single CSV file
file_results="${PATH_RESULTS}/results.csv"
if [[ ! -e $file_results ]]; then
  # add a header in case the file does not exist yet
  echo "Subject,SNR_single,Contrast" >> $file_results
fi
echo "${SUBJECT},`cat snr_single.txt`,`cat contrast.txt`" >> ${PATH_RESULTS}/results.csv

# Verify presence of output files and write log file if error
# ------------------------------------------------------------------------------
FILES_TO_CHECK=(
	"signal_wm.csv"
	"signal_gm.csv"
  "snr_single.txt"
  "contrast.txt"
)
for file in ${FILES_TO_CHECK[@]}; do
  if [[ ! -e $file ]]; then
    echo "${file} does not exist" >> $PATH_LOG/_error_check_output_files.log
  fi
done

# Display useful info for the log
end=`date +%s`
runtime=$((end-start))
echo
echo "~~~"
echo "SCT version: `sct_version`"
echo "Ran on:      `uname -nsr`"
echo "Duration:    $(($runtime / 3600))hrs $((($runtime / 60) % 60))min $(($runtime % 60))sec"
echo "snr_single:    `cat snr_single.txt`"
echo "contrast:    `cat contrast.txt`"
echo "~~~"
