# Copyright (c) Facebook, Inc. and its affiliates.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import shutil
import tempfile
import unittest

from fiosynth_lib import fio_json_parser

FIO_SAMPLES_DIR = 'sample_fio_results'
FIO_SAMPLE_CSV = 'sample-2017-11-21_16-40.csv'


class TestFioJsonParser(unittest.TestCase):
    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        samples_dirpath = os.path.join(current_dir, FIO_SAMPLES_DIR)
        self.fio_json_files = fio_json_parser.get_json_files(samples_dirpath)
        self.tmp_dir = tempfile.mkdtemp()  # Create temporary directory for csv
        self.expected_csv_output = ''
        expected_csv_path = os.path.join(samples_dirpath, FIO_SAMPLE_CSV)
        with open(expected_csv_path, 'r') as csv_output:
            self.expected_csv_output = csv_output.read().splitlines()

    def tearDown(self):
        # Clean up temporary directory
        if self.tmp_dir:
            shutil.rmtree(self.tmp_dir)

    def _assert_csv_format(self, csv_filepath):
        with open(csv_filepath, 'r') as csv_out:
            actual_csv_lines = csv_out.read().splitlines()
            for a, e in zip(actual_csv_lines, self.expected_csv_output):
                self.assertEqual(a, e)

    def test_write_csv_file_many_json_files(self):
        csv_filepath = os.path.join(self.tmp_dir, 'multiple_test.csv')
        fio_json_parser.write_csv_file(csv_filepath, self.fio_json_files)
        self._assert_csv_format(csv_filepath)

    def test_write_csv_file_append_exisiting(self):
        csv_filepath = os.path.join(self.tmp_dir, 'append_test.csv')
        for json_file in self.fio_json_files:
            fio_json_parser.write_csv_file(csv_filepath, [json_file])
            self._assert_csv_format(csv_filepath)


if __name__ == '__main__':
    unittest.main()
