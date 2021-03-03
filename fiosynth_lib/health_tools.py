# Copyright (c) Facebook, Inc. and its affiliates.
#
# AUTHOR = "Darryl Gardner <darryleg@fb.com>"
#
# health_tools.py- Logs Flash Health Tool Output to "health.log" file.
#
# A vendor specific health monitor tool will be executed and logged in
# "health.log" file. Log can be used to calculate write amplification factor.
#
# Input arguments:
#  -s
#       (Required) Enter Health Monitoring Tool Syntax
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import subprocess


def set_attributes():
    #
    # Attribute Table Definition
    #

    parser = argparse.ArgumentParser(
        description='Logs Flash Health Tool Output to "health.log" file'
    )
    parser.add_argument(
        '-s',
        action='store',
        dest='syntax',
        type=str,
        help='(Required) Enter Health Monitoring Tool Syntax (default = )',
        required=True,
        default=''
    )
    args = parser.parse_args()
    return args


class HealthTools():
    def logger(self, syntax):
        FILENAME = 'health.log'
        file_ = open(FILENAME, 'a')
        subprocess.Popen("date", stdout=file_)
        subprocess.Popen(syntax, stdout=file_, shell=True)
        file_.close()


def main():
    args = set_attributes()
    health = HealthTools()
    health.logger(args.syntax)


if __name__ == '__main__':
    main()
