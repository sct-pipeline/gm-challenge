# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gm-challenge',
    version='0.5',
    description='Analysis code for the Spinal Cord Gray Matter Imaging Challenge.',
    long_description=long_description,
    url='https://github.com/sct-pipeline/gm-challenge',
    author='NeuroPoly Lab, Polytechnique Montreal',
    author_email='neuropolylab@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Education',
        'Topic :: Scientific/Engineering :: Image Processing',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='Magnetic Resonance Imaging MRI spinal cord analysis template',
    packages=find_packages(exclude=['.git', 'fig', 'doc', 'niftyweb', 'notebooks', 'qualitative_assessment', 'venv']),
    include_package_data=True,
    python_requires="==3.8.*",
    entry_points=dict(
        console_scripts=[
            'compute_cnr=gmchallenge.compute_cnr:main',
            'simu_create_phantom=gmchallenge.simu_create_phantom:main',
            'simu_process_data=gmchallenge.simu_process_data:main',
            'simu_make_figures=gmchallenge.simu_make_figures:main',
            'generate_figure_spinegeneric=gmchallenge.generate_figure_spinegeneric:main'],
    ),
)
