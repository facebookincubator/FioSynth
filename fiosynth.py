#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# AUTHOR = 'Darryl Gardner <darryleg@fb.com>'
#
# fiosynth.py - FB Fio Synthetic Benchmark Suite for Flash ver 3.5.43
#
# Requires the use of workload suite files (in JSON format).  Workload
# suite files can be edited to adjust the number of precondition cycles,
# number of runs, number of workloads and individual workload parameters.
# Use the dry run option to verify that benchmark suite executes as expected.
# All workloads are normalized on a per TB bases. If capacity is not
# specified, capacity will be based on capacity of the first specified device.
# If specified, a vendor specific health monitor tool will be executed before
# and after each benchmark suite executes and logged in 'health.log' file.
# Log can be used to calculate write amplification factor.
# Raw results are stored in individual JSON files but are also parsed into
# single a csv file for easy visualization in Excel.
# Prefix for result filename must be specified.  This will define the name
# of the result files directory and csv filename.
#
# Input arguments (3 of arguments are required):
#  -d
#       (Required) device path for single device target, ALL for all
#       data devices, or ALLRAID for all mdraid devices
#  -w
#       (Required) filename for workload suite (default = )
#  -f
#       (Required) Results filename (default = )
#  -c
#       (Optional) specify capacity in TB (default = <device capacity>)
#  -r
#       (Optional) Set to y to do dry run (default = n)
#  -t
#       (Optional) Enter Health Monitoring Tool Syntax (default = )
#  -p
#       (Optional) Set to n to skip drive prep (default = y)
#  -n
#       (Optional) Specific the number of run cycles (default = 3 )
#  -g
#       (Optional) Set to y to enable flash configuration logging (default = n)
#  -s
#       (Optional) Set to a server name if you want to run in server mode,
#       for multiple servers add multiple times
#  -l
#       (Optional) Set to name of text file with server name on each line
#
# Example run workload suite on a single device:
#  fb-FioSynthFlash -d /dev/sdc -w LE_Flash -f LE_Flash_sdc
#
# Example run workload suite on all data devices:
#  fb-FioSynthFlash -d ALL -w LE_Flash -f LE_Flash_noRAID
#
# Example run workload suite on all mdraid devices:
#  fb-FioSynthFlash -d ALLRAID -w LE_Flash -f LE_Flash_MDRAID
#
# Example run workload suite across multiple servers:
#
# fb-FioSynthFlash -d ALL -w LE_Flash -f LE_Flash_server_noRAID -s <server>
#   -s <otherserver>
#

# pyre-unsafe
from fiosynth_lib import fiosynth


def main() -> None:
    fiosynth.main()


if __name__ == "__main__":
    main()  # pragma: no cover
