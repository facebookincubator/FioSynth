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

# pyre-unsafe

import argparse
import re
import shlex
import subprocess


def set_attributes():
    #
    # Attribute Table Definition
    #

    parser = argparse.ArgumentParser(
        description='Logs Flash Health Tool Output to "health.log" file'
    )
    parser.add_argument(
        "-s",
        action="store",
        dest="syntax",
        type=str,
        help="(Required) Enter Health Monitoring Tool Syntax (default = )",
        required=True,
        default="",
    )
    args = parser.parse_args()
    return args


class HealthTools:
    def logger(self, syntax):
        allowed_commands = [
            r"^smartctl\s+.*\s+/dev/[a-zA-Z0-9]+$",
            r"^nvme\s+.*\s+/dev/[a-zA-Z0-9]+$",
        ]

        try:
            args = shlex.split(syntax)
        except ValueError:
            raise ValueError(f"Invalid syntax format: {syntax}")

        command_str = " ".join(args)
        if not any(re.match(pattern, command_str) for pattern in allowed_commands):
            raise ValueError(f"Invalid or unauthorized command: {syntax}")

        FILENAME = "health.log"
        with open(FILENAME, "a") as file_:
            subprocess.Popen(["date"], stdout=file_)
            subprocess.Popen(args, stdout=file_)


def main():
    args = set_attributes()
    health = HealthTools()
    health.logger(args.syntax)


if __name__ == "__main__":
    main()
