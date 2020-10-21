#!/usr/bin/env python3
# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
import codecs
import glob
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def get_data_files():
    # To install data files here will require root privileges
    base_dir = '/usr/local/fb-FioSynthFlash'
    data_files = [
        (base_dir, ['CODE_OF_CONDUCT.md']),
        (base_dir, ['CONTRIBUTING.md']),
        (base_dir, ['LICENSE']),
        (base_dir, ['PATENTS']),
        (base_dir, ['README.md']),
        (base_dir, ['README-READHAMMER.txt']),
        (base_dir, ['Release_Notes.txt']),
        (os.path.join(base_dir, 'jobfiles'), glob.glob('jobfiles/*')),
        (os.path.join(base_dir, 'wkldsuites'), glob.glob('wkldsuites/*')),
        (os.path.join(base_dir, 'fiosynth_lib'), glob.glob('fiosynth_lib/*'))
    ]
    return data_files


setup(
    name='fiosynth',
    version='3.5.39',
    description='FB fio Synthetic Benchmark Suite',
    long_description=long_description,
    author='Darryl Gardner',
    author_email='darryleg@fb.com',
    packages=find_packages(exclude=['jobfiles', 'wkldsuites', 'tests']),
    data_files=get_data_files(),
    license='BSD+PATENTS',
    scripts=['fiosynth.py'],
    entry_points={
        'console_scripts': [
            'fiosynth=fiosynth_lib.fiosynth:main',
            'FioFlashJsonParser=fiosynth_lib.fio_json_parser:cli_main',
            'GetFlashConfig=fiosynth_lib.flash_config:main',
            'healthTools=fiosynth_lib.health_tools:main'
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    keywords='benchmark fio performance storage',
)
