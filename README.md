![](https://github.com/neuropoly/gm_challenge/blob/master/doc/logo_challenge.png)

# Spinal Cord Gray Matter Imaging Challenge
Spinal cord gray matter imaging challenge for the [5th Spinal Cord Workshop (June 22<sup>nd</sup> 2018, Paris)](http://www.spinalcordmri.org/2018/06/22/workshop.html).
The objective for this challenge is to propose a protocol that will generate the best image quality. For more details,
please see: https://goo.gl/2owcL7.

## Dependencies

- Python 3.8+
- [SCT v5.4](https://github.com/spinalcordtoolbox/spinalcordtoolbox/releases/tag/5.4).

## Getting started

- Download the dataset of the challenge:
  ~~~
  git clone https://github.com/sct-pipeline/gm-challenge-data.git
  ~~~
- Download this repository and go in it:
  ~~~
  git clone https://github.com/sct-pipeline/gm-challenge.git
  cd gm-challenge
  ~~~
- Create virtual environment and install dependencies:
  ~~~
  virtualenv venv
  pip install -r requirements.txt
  ~~~
- Run (you need to have SCT installed):
  ```
  sct_run_batch -script process_data.sh -jobs -1 -path-data <PATH_DATA> -path-output <PATH_OUT>
  ```
  with
    - PATH_DATA: The path to the downloaded dataset
    - PATH_OUTPUT: The path where results will be output.

At the end of the processing, you can review:
- **<PATH_OUT>/log/**: Log files of the processing for each subject.
- **<PATH_OUT>/qc/index.html**: Quality Control report
- **<PATH_OUT>/results/results.csv**: CSV file containing the results. Example:

  |Subject|SNR_diff          |SNR_single        |Contrast          |
  |-------|------------------|------------------|------------------|
  |9604   |17.955421557112000|15.036597989806800|0.1532358378597440|
  |9605   |24.851538876483400|18.7942962516352  |0.1238874277356780|
  |9584   |18.45677255732030 |14.395098187990800|0.124765433521577 |
  |9418   |20.29502533086980 |16.989013170063300|0.1093208813636860|

## Description of the analysis

Two NIfTI files are required: an initial scan and a re-scan without repositioning. The analysis script `process_data.sh`
includes the following steps:

- Check if a mask for the spinal cord and/or gray matter (GM) already exists. If not, segment them automatically.
- Register the second scan to the first one. Use nearest-neighbour interpolation to preserve noise properties.
- Compute white matter (WM) mask by subtracting the spinal cord and the GM masks.
- Erode the WM mask to mitigate partial volume, yielding the WMe mask.
- Compute `SNR_diff` using the two-image subtraction method (Dietrich et al. J Magn Reson Imaging, 2007) in the WMe mask.
- Compute `SNR_single` using the first scan, by dividing the mean in the WMe mask and the STD in the WMe masks. 
- Compute `Contrast` by dividing the mean signal in the GM by that in the WM, on a slice-by-slice basis and then 
  average across slices.

## Analysis on the spine-generic dataset

A similar analysis can also be run on the spine-generic dataset. However, given that only one scan was available, 
SNR_diff could not be calculated and as a result the processing script is slightly different. Moreover, the location
of the repository needs to be input into the shell script. The command looks like this:
~~~
sct_run_batch -script <PATH_REPOSITORY>/process_data_spinegeneric.sh -path-data <PATH_DATA> -path-out <PATH_OUTPUT> -script-args <PATH_REPOSITORY>
~~~

After running this script, figures can be generated as follows:
~~~
python generate_figure_spinegeneric.py -ip <PATH_DATA>/participants.tsv -ir cd <PATH_OUT>/results/results.csv -o fig
~~~

## Simulations

* [simu_create_phantom.py](./simu_create_phantom.py): Generate synthetic phantom
of WM and GM that can be used to validate the proposed evaluation metrics. The phantoms are generated with random noise,
 so running the script multiple times will not produce the same output.
This script is meant to be run twice in order to assess the metrics with the following functions. Example:
  ```bash
  python simu_create_phantom.py -o simu_phantom1
  python simu_create_phantom.py -o simu_phantom2
  ```
* [simu_process_data.py](./simu_process_data.py): Process data by batch within
folders. This script will look for csv files, which are generated by
simu_create_phantom.py, and which contain file names of the nifti phantom data.
This script is particularly useful for processing the large amount of files
generated by the phantom construction.
* [simu_make_figures.py](./simu_make_figures.py): Make figures to assess
metrics sensitivity to image quality. Run after simu_process_data.py
  
## Configuration of Niftyweb server

- make sure the script niftyweb/WMGM is declared in `PATH`
- add an entry to the crontab that points to the Daemon. Example (to edit, use `crontab -e`):
~~~
python niftyweb/setup/daemon_SOFTWEB_2files.py WMGM
~~~

## Contributors
Stephanie Alley, Ferran Prados, Julien Cohen-Adad

## License
See: [LICENSE](./LICENSE)
