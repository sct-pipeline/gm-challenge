<?php
$program='WMGM';
$link_short='SCGM';
$image='wmgm.png';
$keywords="spinal cord,challenge,wm,gm";
$link_long='SPINAL CORD GRAY MATTER IMAGING CHALLENGE';
$title="SPINAL CORD GRAY MATTER IMAGING CHALLENGE";
$initial_text="The goal of the challenge is to propose a protocol to get the best image quality. The evaluation methods include signal-to-noise ratio, white matter/gray matter contrast, contrast-to-noise ratio, sharpness, and level of artifacts.<br><br>";
$presentation=$initial_text;
$initial_text.="For more details, please see: <a target='gg' href='https://goo.gl/2owcL7'>https://goo.gl/2owcL7</a>.<br><br>";
/*$initial_text.="<b>GUIDELINES</b>:<br><br>";
$initial_text.="<table style='border: 1px solid black; width:60%;'>";
$initial_text.="<tr>";
$initial_text.="<th style='width:100px;font-size:small'>Item</th>";
$initial_text.="<th style='width:100px;font-size:small'>Value</th>";
$initial_text.="<th style='width:100px;font-size:small'>Comment</th></tr>";
$initial_text.="<tr>";
$initial_text.="<td style='padding:10;font-size:small' nowrap>Field strength</td>";
$initial_text.="<td style='padding:10;font-size:small' nowrap>3T or 7T</td>";
$initial_text.="<td style='padding:10;font-size:small'></td></tr>";
$initial_text.="<tr><td style='padding:10;font-size:small'>Coils</td>";
$initial_text.="<td style='padding:10;font-size:small'>product or custom</td>";
$initial_text.="<td style='padding:10;font-size:small'></td></tr>";
$initial_text.="<tr><td style='padding:10;font-size:small'>Sequence</td>";
$initial_text.="<td style='padding:10;font-size:small'>product or custom</td>";
$initial_text.="<td style='padding:10;font-size:small'>If product, please indicate if license is required. If custom, please indicate availability (e.g., WIP, C2P).</td></tr>";
$initial_text.="<tr><td style='padding:10;font-size:small' nowrap>Acquisition time</td>";
$initial_text.="<td style='padding:10;font-size:small'>10 minutes max</td>";
$initial_text.="<td style='padding:10;font-size:small'>Try to make it as fast as possible (TA will be a criteria).</td></tr>";
$initial_text.="<tr><td style='padding:10;font-size:small' nowrap>Slice thickness</td>";
$initial_text.="<td style='padding:10;font-size:small'>3mm or less</td>";
$initial_text.="<td style='padding:10;font-size:small'>Balance between thick slices (cons: intravoxel rephrasing in T2*w) and thin slices (cons: lower SNR).</td></tr>";
$initial_text.="<tr><td style='padding:10;font-size:small'>FOV</td>";
$initial_text.="<td style='padding:10;font-size:small'>Centered at C2-C3 disc, 50 mm coverage in superior-inferior direction</td>";
$initial_text.="<td style='padding:10;font-size:small'></td></tr>";
$initial_text.="<tr><td style='padding:10;font-size:small'>Interpolation</td>";
$initial_text.="<td style='padding:10;font-size:small'>No interpolation</td>";
$initial_text.="<td style='padding:10;font-size:small'>Most scanners have an automatic k-space zero-padding that you need to uncheck.</td></tr>";
$initial_text.="<tr><td style='padding:10;font-size:small'>Filter</td>";
$initial_text.="<td style='padding:10;font-size:small'>No filtering</td>";
$initial_text.="<td style='padding:10;font-size:small'>This includes raw filter, elliptical, bias correction, distortion correction, etc.</td></tr>";
$initial_text.="<tr><td style='padding:10;font-size:small' nowrap>Type of data</td>";
$initial_text.="<td style='padding:10;font-size:small'>Calculated map (e.g., T2 map) or raw data (e.g., T2w) accepted</td>";
$initial_text.="<td style='padding:10;font-size:small'></td></tr></table><br>";
*/
$initial_text.="<b>IMPORTANT DATES</b>:<br>";
$initial_text.="<b>15th May 2018</b> - Submit data for analysis<br>";
$initial_text.="<b>1st June 2018</b> - End of analysis and pooling of results<br>";

$text_button_files='Upload files and obtain the results';
$parameter_list=array();

$num_uploaders=3;
$files_description=array(
	"Initial scan",
	"Re-scan without repositioning",
	"PDF printout of the protocol"
	);
$file_types_1=array(
	array(
		'description' => 'NIFTI GZ files',
		'extension' => 'nii.gz'
		),
	array(
		'description' => 'NIFTI files',
		'extension' => 'nii'
	),
	array(
		'description' => 'PDF',
		'extension' => 'pdf'
		)
	);
$file_types_2=array(
	array(
		'description' => 'PDF',
		'extension' => 'pdf'
		)
	);
$file_type=array($file_types_1,$file_types_1,$file_types_1);


$parameter_list=array(
    array(
            'name' => 'field',
            'description' => 'Field strength',
            'value' => array(
                '3T' => '3T',
                '7T' => '7T'
            )
        ),
    array(
            'name' => 'coil',
            'description' => 'Coil type',
            'value' => array(
                'PRODUCT' => 'Product',
                'CUSTOM' => 'Custom'
            )
        ),
    array(
            'name' => 'sequence',
            'description' => 'Sequence',
            'value' => array(
                'PRODUCT' => 'Product',
                'CUSTOM' => 'Custom'
            )
        ),
  /*  array(
            'name' => 'ta',
            'description' => 'Acquisition time (in seconds)',
            'value' => array('0' => 'e.g.: 360 s'),
            'validation' => '/^[1-9]\d*$/',
            'error_msg' => 'Please, an integer.'
          ),*/
    array(
            'name' => 'data',
            'description' => 'Type of data',
            'value' => array('0' => 'e.g.: multi-echo T2*w, PSIR, ...'),
            'validation' => '',
            'error_msg' => ''
          )
    );

$results_extension=".txt";

$references='<b>Organizers</b><br><br>';
$references.='Stephanie Alley and Julien Cohen-Adad (NeuroPoly Lab, Polytechnique Montreal, University of Montreal)<br>';
$references.='Ferran Prados (University College London)<br>';

?>
