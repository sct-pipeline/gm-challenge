![](https://github.com/neuropoly/gm_challenge/blob/master/doc/logo_challenge.png)

# Spinal Cord Gray Matter Imaging Challenge
Spinal cord gray matter imaging challenge for the [5th Spinal Cord Workshop (June 22<sup>nd</sup> 2018, Paris)](http://www.spinalcordmri.org/2018/06/22/workshop.html).
The objective for this challenge is to propose a protocol that will generate the best image quality. For more details,
please see: https://goo.gl/2owcL7.

## Dependencies

- Python 3.9 with [pandas](https://pandas.pydata.org/) library
- [SCT v5.3.0](https://github.com/spinalcordtoolbox/spinalcordtoolbox/releases/tag/5.3.0).

## Getting started

- Download the dataset of the challenge:
  ~~~
  git clone https://github.com/sct-pipeline/gm-challenge-data
  ~~~
- Download this repository and go in it:
  ~~~
  git clone https://github.com/sct-pipeline/gm-challenge.git
  cd gm-challenge
  ~~~
- Run (you need to have SCT installed):
  ```
  sct_run_batch -script process_data.sh -j -1 -path-data <PATH_DATA> -path-output <PATH_OUT>
  ```
  with
    - PATH_DATA: The path to the downloaded dataset
    - PATH_OUTPUT: The path where results will be output.

At the end of the processing, you can review:
- **<PATH_OUT>/log/**: Log files of the processing for each subject.
- **<PATH_OUT>/qc/index.html**: Quality Control report
- **<PATH_OUT>/results/results.csv**: CSV file containing the results. Example:

  |Subject|SNR_diff          |SNR_mult          |Contrast          |
  |-------|------------------|------------------|------------------|
  |9604   |16.418544978421163|11.191525890141964|1.153235837859744 |
  |9605   |23.651120016640174|29.48051021596357 |1.1238874277356785|
  |9584   |17.143453301063012|21.092693041826486|1.1247654335215769|
  |9418   |19.558182966645223|19.61176661536486 |1.1093208813636863|

## Description of the analysis

Two NIfTI files are required: an initial scan and a re-scan without repositioning. The analysis script `process_data.sh`
includes the following steps:

- Check if a mask for the spinal cord and/or gray matter already exists. If not, segment them automatically.
- Register the second scan to the first one. Use nearest-neighbour interpolation to preserve noise properties.
- Compute white matter mask by subtracting the spinal cord and the gray matter masks. 
- Compute `SNR_diff` using the two-image subtraction method (Dietrich et al. J Magn Reson Imaging, 2007).
- Compute `SNR_mult` using the first scan (Griffanti et al., Biomed Sign Proc and Control, 2012).
- Compute `Contrast` by dividing the mean signal in the GM by that in the WM, on a slice-by-slice basis and then 
  average across slices.

## Simulations

* [simu_create_phantom.py](./simu_create_phantom.py): Generate synthetic phantom
of WM and GM that can be used to validate the proposed evaluation metrics. The phantoms are generated with random noise,
 so running the script multiple times will not produce the same output.
This script is meant to be run twice in order to assess the metrics with the following functions.
* [simu_process_data.py](./simu_process_data.py): Process data by batch within
folders. This script will look for csv files, which are generated by
simu_create_phantom.py, and which contain file names of the nifti phantom data.
This script is particularly useful for processing the large amount of files
generated by the phantom construction.
* [simu_make_figures.py](./simu_make_figures.py): Make figures to assess
metrics sensitivity to image quality. Run after simu_process_data.py
  
## Configuration of Niftyweb server
- make sure the script WMGM is declared in `PATH`
- add an entry to the crontab that points to the Daemon. Example (to edit, use `crontab -e`):
~~~
python /home/niftyweb_sct/gm_challenge/NiftyWeb_setup/daemon_SOFTWEB_2files.py WMGM
~~~

## Contributors
Stephanie Alley, Ferran Prados, Julien Cohen-Adad

## License
See: [LICENSE](./LICENSE)
