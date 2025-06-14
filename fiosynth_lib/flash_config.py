# Copyright (c) Facebook, Inc. and its affiliates.
#
# AUTHOR = "Darryl Gardner <darryleg@fb.com>"
#
# flash_config.py- Logs flash configuration information in .csv format
# By default, results will be stored in "flashconfig.csv" file.
#

# pyre-unsafe

import argparse
import csv
import json
import os
import re
import shlex
import subprocess
import sys
from subprocess import PIPE, Popen
from typing import Any, Dict, Optional, Union


def set_attributes():
    #
    # Attribute Table Definition
    #
    parser = argparse.ArgumentParser(
        description="flash_config- Logs flash configuration in .csv file."
    )
    parser.add_argument(
        "-f",
        action="store",
        dest="filename",
        type=str,
        help=("(Optional) Flash configuration filename (default = " "flashconfig.csv"),
        default="flashconfig.csv",
    )
    args = parser.parse_args()
    return args


def smartctlToJson(data):
    # Skip boot device (sda)
    index = 1
    device = "disk"
    smart = {}
    KEY = 0
    VALUE = 2
    while index != len(data[device]):
        syntax = "smartctl -i /dev/%s | grep :" % (data[device][index])
        lb = subprocess.Popen(syntax, stdout=subprocess.PIPE, shell=True)
        smart.setdefault(index, {})
        device_path = "/dev/%s" % data[device][index]
        smart[index].setdefault("Device Path:", device_path)
        for line in lb.stdout:
            bits = line.split()
            a = "{} {}".format(bits[KEY].decode("utf-8"), bits[KEY + 1].decode("utf-8"))
            try:
                b = "{} {}".format(
                    bits[VALUE].decode("utf-8"),
                    bits[VALUE + 1].decode("utf-8"),
                )
            except IndexError:
                b = "%s" % (bits[VALUE].decode("utf-8"))
            smart.setdefault(index, {})
            smart[index].setdefault(a, b)
        index += 1
    return json.dumps(smart)


def drivesToJson():
    lb = subprocess.Popen(["/bin/lsblk", "-rnb"], stdout=subprocess.PIPE)
    drives = {}
    TYPE = 5
    DEVICE = 0
    maxcol = max(TYPE, DEVICE)
    for line in lb.stdout:
        bits = line.split()
        if len(bits) > maxcol:
            drive_type = bits[TYPE].decode("utf-8")
            drive_device = bits[DEVICE].decode("utf-8")
            drives.setdefault(drive_type, [])
            drives[drive_type].append(drive_device)
    return json.dumps(drives)


def cmdline(cmd):
    process = Popen(args=cmd, stdout=PIPE, shell=True)
    return process.communicate()[0]


def new_csv(f):
    try:
        col_names = []
        col_names = [
            "Index",
            "DevicePath",
            "Capacity",
            "ModelNumber",
            "SerialNumber",
            "Firmware",
            "Hostname",
            "KernelVersion",
        ]
        writer = csv.writer(f)
        writer.writerow(col_names)
    except OSError:
        print("cannot write to ", f)
        f.close()
        sys.exit(1)


def print_nvme_line(f, data, hostname, kernel):
    CAPACITY_KEY = 3
    for datum in data:
        device = datum["DevicePath"]
        index = datum.get("Index", None)
        if not index:
            index = int(re.search(r"nvme(\d+)n", device).group(1))
        syntax = "lsblk -rnb %s | grep disk" % device
        capacity = cmdline(syntax).split()[CAPACITY_KEY]
        try:
            writer = csv.writer(f)
            row = (
                index,
                datum["DevicePath"],
                capacity,
                datum["ModelNumber"],
                datum["SerialNumber"],
                datum["Firmware"],
                hostname,
                kernel,
            )
            writer.writerow(row)
        except OSError:
            print("cannot write to ", f)
            f.close()
            sys.exit(1)


def print_flash_line(f, data, hostname, kernel):
    # Use flash_manager for legacy flash card support.
    card_id = "card.1"
    try:
        writer = csv.writer(f)
        writer.writerow(
            (
                data[card_id]["pci_address"],
                data[card_id]["logical_location"],
                data[card_id]["size"],
                data[card_id]["board_name"],
                data[card_id]["sn"],
                data[card_id]["firmware_version"],
                hostname,
                kernel,
            )
        )
    except OSError:
        print("cannot write to ", f)
        sys.exit(1)


def print_smart_line(f, data, hostname, kernel):
    KEY = "1"
    index = 1
    while index - 1 <= len(data[KEY]):
        sidx = str(index)
        if data[sidx]["Rotation Rate:"] == "Solid State":
            try:
                writer = csv.writer(f)
                writer.writerow(
                    (
                        index,
                        data[sidx]["Device Path:"],
                        data[sidx]["User Capacity:"],
                        data[sidx]["Device Model:"],
                        data[sidx]["Serial Number:"],
                        data[sidx]["Firmware Version:"],
                        hostname,
                        kernel,
                    )
                )
            except OSError:
                print("cannot write to ", f)
                sys.exit(1)
        index += 1


def convert_nvme_output(
    new_output: Dict[str, Any],
) -> list[Optional[Dict[str, Union[str, int]]]]:
    """
    Convert the new nvme list -o json output to old format

    Args:
        new_output: nvme list -o json output in new format

    Return:
        old_format_list: old format
    """
    controllers = new_output.get("Controllers", [])
    old_format_list = []

    for controller in controllers:
        if "Namespaces" in controller and controller["Namespaces"]:
            for namespace_info in controller["Namespaces"]:
                # Create the old output format
                old_format = {
                    "NameSpace": namespace_info.get("NSID"),
                    "DevicePath": f"/dev/{namespace_info.get('NameSpace')}",
                    "Firmware": controller.get("Firmware"),
                    "Index": int(controller.get("Controller").replace("nvme", "")),
                    "ModelNumber": controller.get("ModelNumber"),
                    "SerialNumber": controller.get("SerialNumber"),
                    "UsedBytes": namespace_info.get("UsedBytes"),
                    "MaximumLBA": namespace_info.get("MaximumLBA"),
                    "PhysicalSize": namespace_info.get("PhysicalSize"),
                    "SectorSize": namespace_info.get("SectorSize"),
                }
                old_format_list.append(old_format)

    return old_format_list


def print_csv_line(f, data, tool):
    hostname = cmdline("uname -n").decode("utf-8").rstrip()
    kernel = cmdline("uname -r").decode("utf-8").rstrip()
    # nvme tool will work for all NVMe flash devices
    if tool == "nvme":
        nvme_data = data["Devices"]
        entry_list = []
        for dr in nvme_data:
            if "DevicePath" not in dr:
                for output in dr.get("Subsystems", []):
                    entry_list.extend(convert_nvme_output(output))

        nvme_data = entry_list or nvme_data
        print_nvme_line(f, nvme_data, hostname, kernel)
    elif tool == "flash_manager":
        print_flash_line(f, data, hostname, kernel)
    elif tool == "smartctl":
        print_smart_line(f, data, hostname, kernel)
    else:
        sys.stderr.write(f"Error: tool '{tool}' not found.\n")
        sys.exit(1)


def command_exist(cmd):
    if cmd.split()[0] not in ["nvme", "flash_manager", "smartctl"]:
        return False
    args = shlex.split(cmd)
    try:
        subprocess.call(
            args, stdout=open(os.devnull, "wb"), stderr=open(os.devnull, "wb")
        )
    except OSError:
        print("%s command not installed" % cmd)
        return False
    test = cmdline(cmd)
    if test.decode("UTF-8") == "":
        return False
    else:
        return True


class GetFlashConfig:
    def get_json(self):
        if command_exist("nvme list"):
            syntax = "nvme list -o json"
            tool = "nvme"
            args = shlex.split(syntax)
            config = subprocess.check_output(args)
        elif command_exist("flash_manager status"):
            syntax = "flash_manager status --json"
            tool = "flash_manager"
            args = shlex.split(syntax)
            config = subprocess.check_output(args)
        elif command_exist("smartctl -i /dev/sdb"):
            tool = "smartctl"
            devices = drivesToJson()
            data = json.loads(devices)
            config = smartctlToJson(data)
        else:
            print("Flash configuration tool not found.")
            sys.exit(1)
        config_as_json = json.loads(config)
        return config_as_json, tool

    def json_to_csv(self, path, config, csv_file, tool):
        out_file = os.path.join(path, csv_file)
        with open(out_file, "w") as csv_out:
            new_csv(csv_out)
            print_csv_line(csv_out, config, tool)
        print('Flash configuration filename is "%s"' % csv_file)


def main():
    args = set_attributes()
    config = GetFlashConfig()
    config_as_json, tool = config.get_json()
    config.json_to_csv(".", config_as_json, args.filename, tool)


if __name__ == "__main__":
    main()
