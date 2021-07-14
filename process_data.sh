#!/bin/bash
#
# Process data.
#
# Usage:
#   ./process_data.sh <SUBJECT>
#
# Manual segmentations or labels should be located under:
# <SUBJECT>/
#
# Authors: Julien Cohen-Adad

# The following global variables are retrieved from the caller sct_run_batch
# but could be overwritten by uncommenting the lines below:
# PATH_DATA_PROCESSED="~/data_processed"
# PATH_RESULTS="~/results"
# PATH_LOG="~/log"
# PATH_QC="~/qc"

# Uncomment for full verbose
set -x

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
  # Find contrast
  if [[ $contrast == "dwi" ]]; then
    folder_contrast="dwi"
  else
    folder_contrast="anat"
  fi
  # Update global variable with segmentation file name
  FILESEG="${file}_seg"
  FILESEGMANUAL="${PATH_DATA}/derivatives/labels/${SUBJECT}/${folder_contrast}/${FILESEG}-manual${ext}"
  echo
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
cd ${SUBJECT}
file_1="data1"
file_2="data2"
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
# Register data2 on data1
# Note: We use NearestNeighboor for final interpolation to not alter noise distribution
sct_register_multimodal -i ${file_2}${ext} -d ${file_1}${ext} -dseg ${file_1_seg}${ext} -param step=1,type=im,algo=rigid,metric=MeanSquares,smooth=1,slicewise=1,iter=50 -x nn -qc ${PATH_QC} -qc-subject ${SUBJECT}
file_2=${file_2}_reg
# Compute SNR using both methods
sct_image -i ${file_1}${ext} ${file_2}${ext} -concat t -o data_concat.nii.gz
sct_compute_snr -i data_concat.nii.gz -method diff -m data1_crop_wmseg_erode.nii.gz > snr_diff.txt 
sct_compute_snr -i data_concat.nii.gz -method mult -m data1_crop_wmseg_erode.nii.gz > snr_mult.txt
# Compute average value in WM and GM to subsequently compute contrast
sct_extract_metric -i ${file_1}${ext} -f ${file_1}_wmseg${ext} -method bin -o signal_wm.csv
sct_extract_metric -i ${file_2}${ext} -f ${file_1}_wmseg${ext} -method bin -o signal_wm.csv -append 1
sct_extract_metric -i ${file_1}${ext} -f ${file_1_gmseg}${ext} -method bin -o signal_gm.csv
sct_extract_metric -i ${file_2}${ext} -f ${file_1_gmseg}${ext} -method bin -o signal_gm.csv -append 1

# Verify presence of output files and write log file if error
# ------------------------------------------------------------------------------
FILES_TO_CHECK=(
  "data1_seg_manual${ext}"
	"data1_gmseg_manual${ext}"
	"data1_crop_wmseg_erode${ext}"
	"signal_wm.csv"
	"signal_gm.csv"
  "snr_diff.txt"
  "snr_mult.txt"
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
echo "~~~"
