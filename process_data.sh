#!/bin/bash
#
# Process data.
#
# Usage:
#  process_data_spinegeneric.sh <SUBJECT> <PATH_TO_SCRIPT>
#
# Where <PATH_TO_SCRIPT> is the path to the folder that contains the script compute_contrast.py
#
# Example when called via sct_run_batch:
#  sct_run_batch -path-data /Users/julien/code/spine-generic/data-multi-subject \
#                -path-output gmchallenge_spinegeneric_20211110_162254 \
#                -script /Users/julien/code/gm-challenge/process_data_spinegeneric.sh \
#                -script-args "/Users/julien/code/gm-challenge"
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
PATH_TO_SCRIPT=$2

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
# Accommodate file naming between GM challenge data and spine-generic data
ext=".nii.gz"
if [[ -e "${SUBJECT}_run-1_T2starw${ext}" ]]; then
  dataset="gm-challenge"
  file_1="${SUBJECT}_run-1_T2starw"
  file_2="${SUBJECT}_run-2_T2starw"
else
  dataset="spine-generic"
  file_1="${SUBJECT}_T2star"
fi
file_json="${file_1}.json"
# Compute root-mean square across 4th dimension (if it exists), corresponding to all echoes in Philips scans. Note: we
# only need to do this for the first file, because this only concerns the spine-generic dataset (which does not have a
# second scan).
sct_maths -i ${file_1}${ext} -rms t -o ${file_1}_rms${ext}
file_1="${file_1}_rms"
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
file_1_wmseg=${file_1}_wmseg
# Erode white matter mask to minimize partial volume effect
# Note: we cannot erode the gray matter because it is too thin (most of the time, only one voxel)
sct_maths -i ${file_1}_wmseg${ext} -erode 1 -o ${file_1}_wmseg_erode${ext}
# Register data2 on data1 (only for gm-challenge dataset)
if [[ $dataset == "gm-challenge" ]]; then
  # Note: We use NearestNeighbour for final interpolation to not alter noise distribution
  sct_register_multimodal -i ${file_2}${ext} -d ${file_1}${ext} -dseg ${file_1_seg}${ext} -param step=1,type=im,algo=rigid,metric=MeanSquares,smooth=1,slicewise=1,iter=50 -x nn -qc ${PATH_QC} -qc-subject ${SUBJECT}
  file_2=${file_2}_reg
else
  # define a variable just so the syntax below will not crash. The empty variable will be dealt with by compute_cnr.py.
  file_2=""
fi
# Compute SNR and CNR
python ${PATH_TO_SCRIPT}/compute_cnr.py \
  --data1 ${file_1}${ext} \
  --data2 ${file_2}${ext} \
  --mask-noise ${file_1_wmseg}_erode.nii.gz \
  --mask-wm ${file_1_wmseg}${ext} \
  --mask-gm ${file_1_gmseg}${ext} \
  --json ${file_json} \
  --subject ${SUBJECT} \
  --output "${PATH_RESULTS}/results.csv"

# Verify presence of output files and write log file if error
# ------------------------------------------------------------------------------
# Nothing to check :-)
FILES_TO_CHECK=(
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
