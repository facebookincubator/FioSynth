#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
#
# AUTHOR = 'Darryl Gardner <darryleg@fb.com>'
# fio_json_parser.py - script to parse fio workload results
# produced by fio in JSON format.  By default the following values are written
# to a .csv file: Read_IOPS, Read_BW, Write_IOPS, Write_BW, Mean_Read_Latency,
# P50_Read_Latency, P70_Read_Latency, P99_Read_Latency, P99.9_Read_Latency,
# P99.99_Read_Latency, Mean_Write_Latency, P50_Write_Latency,
# P70_Write_Latency, P99_Write_Latency, P99.9_Write_latency,
# P99.99_Write_Latency
#
# input arguments (at least 1 argument is required):
#  -j
#       single fio JSON file to be parsed (default = )
#  -k
#       single fio JSON file path (default = .)'
#  -n
#       file path for multiple fio JSON files (default = )
#  -l
#       csv file path (default = .)
#  -f
#       csv file name (default = fio_fb_results.csv)
#  -c
#       path to directory of csv's from server/client mode that you want to
#       combine
#
# example parse a single json file in the the results directory:
#  FioFlashJsonParser.py -k results -j 4K_random_read.json results.csv
#
# example parse all json files in 'results' directory:
#  FioFlashJsonParser.py -n results -f results.csv
#
# example create combined csv from csvs in a directory:
#  FioFlashJsonParser.py -c /some_path/csv_directory
#
import argparse
import csv
import glob
import json
import os
import sys
from collections import OrderedDict
from distutils.version import StrictVersion

TOOL_NAME = "fio-parse-json-flash"


def set_attributes():
    #
    # Attribute Table Definition
    #

    parser = argparse.ArgumentParser(description="fio JSON File Parser for Flash")
    parser.add_argument(
        "-j",
        action="store",
        dest="json_file",
        type=str,
        help="single fio JSON file to be parsed (default = )",
        default="",
    )
    parser.add_argument(
        "-k",
        action="store",
        dest="json_path",
        type=str,
        help="single fio JSON file path (default = .)",
        default=".",
    )
    parser.add_argument(
        "-n",
        action="store",
        dest="all_json",
        type=str,
        help="file path for multiple fio JSON files (default = )",
        default="",
    )
    parser.add_argument(
        "-l",
        action="store",
        dest="csv_path",
        type=str,
        help="csv file path (default = .)",
        default=".",
    )
    parser.add_argument(
        "-f",
        action="store",
        dest="csv_file",
        type=str,
        help="csv file name (default = fio_fb_results.csv)",
        default="fio_fb_results.csv",
    )
    parser.add_argument(
        "-s",
        action="store",
        dest="serverMode",
        type=str,
        help="denotes server mode: y for server mode, n for local mode",
        default="n",
    )
    parser.add_argument(
        "-c",
        action="store",
        dest="combine_csv_path",
        type=str,
        help=(
            "path to directory holding multiple csvs from different that "
            "will be combined"
        ),
        default="",
    )
    args = parser.parse_args()
    return args


def check_if_mounted(fn):
    mounted = False
    with open(fn) as f:
        for line in f.readlines():
            if "appears mounted, and 'allow_mounted_write' isn't set." in line:
                print(line)
                mounted = True
                break
    if mounted:
        print("To run, please unmount the device and try again")
        sys.exit(1)


def read_json(fn, serverMode=False):
    data = ""
    if not os.path.isfile(fn):
        print("%s does not exist" % fn)
        sys.exit(1)
    check_if_mounted(fn)
    f = open(fn)
    if serverMode:
        jsonstr = f.read()
        jsonstr = "{" + jsonstr[jsonstr.rfind('"fio version" : ') :]
        try:
            data = json.loads(jsonstr)
        except ValueError:
            print("JSON decoding failed on %s, is file corrupt?" % fn)
            f.close()
            sys.exit(1)
    else:
        try:
            data = json.load(f)
        except ValueError:
            print("JSON decoding failed on %s. Is file corrupt?" % fn)
            f.close()
            sys.exit(1)
    f.close()
    return data


def new_csv(f, notStdPercentile1, notStdPercentile2):
    if notStdPercentile1 or notStdPercentile2:
        col_names = [
            "Jobname",
            "Read_IOPS",
            "Read_BW",
            "Write_IOPS",
            "Write_BW",
            "Trim_IOPS",
            "Trim_BW",
            "Mean_Read_Latency",
            "Max_Read_Latency",
            "P25_Read_Latency",
            "P50_Read_Latency",
            "P70_Read_Latency",
            "P75_Read_Latency",
            "P90_Read_Latency",
            "P99_Read_Latency",
            "P99.9_Read_Latency",
            "P99.99_Read_Latency",
            "P99.999_Read_Latency",
            "P99.9999_Read_Latency",
            "Mean_Write_Latency",
            "Max_Write_Latency",
            "P25_Write_Latency",
            "P50_Write_Latency",
            "P70_Write_Latency",
            "P75_Write_Latency",
            "P90_Write_Latency",
            "P99_Write_Latency",
            "P99.9_Write_Latency",
            "P99.99_Write_Latency",
            "P99.999_Write_Latency",
            "P99.9999_Write_Latency",
            "Mean_Trim_Latency",
            "Max_Trim_Latency",
            "P25_Trim_Latency",
            "P50_Trim_Latency",
            "P70_Trim_Latency",
            "P75_Trim_Latency",
            "P90_Trim_Latency",
            "P99_Trim_Latency",
            "P99.9_Trim_Latency",
            "P99.99_Trim_Latency",
            "P99.999_Trim_Latency",
            "P99.9999_Trim_Latency",
        ]
    else:
        col_names = [
            "Jobname",
            "Read_IOPS",
            "Read_BW",
            "Write_IOPS",
            "Write_BW",
            "Trim_IOPS",
            "Trim_BW",
            "Mean_Read_Latency",
            "Max_Read_Latency",
            "P50_Read_Latency",
            "P70_Read_Latency",
            "P90_Read_Latency",
            "P99_Read_Latency",
            "P99.9_Read_Latency",
            "P99.99_Read_Latency",
            "P99.9999_Read_Latency",
            "Mean_Write_Latency",
            "Max_Write_Latency",
            "P50_Write_Latency",
            "P70_Write_Latency",
            "P90_Write_Latency",
            "P99_Write_Latency",
            "P99.9_Write_Latency",
            "P99.99_Write_Latency",
            "P99.9999_Write_Latency",
            "Mean_Trim_Latency",
            "Max_Trim_Latency",
            "P50_Trim_Latency",
            "P70_Trim_Latency",
            "P90_Trim_Latency",
            "P99_Trim_Latency",
            "P99.9_Trim_Latency",
            "P99.99_Trim_Latency",
            "P99.9999_Trim_Latency",
        ]
    try:
        writer = csv.writer(f)
        writer.writerow(col_names)
    except IOError:
        print("cannot write to ", f)
        f.close()
        sys.exit(1)


def get_csv_line(jobname, json, index, data, version_str, serverMode):
    clat = "clat"
    con = 1
    # clat -> clat_ns in version 3.0
    version_str = version_str[version_str.rfind("-") + 1 :]
    fio_version = StrictVersion(version_str)
    v3_version = StrictVersion("3.0")
    if fio_version >= v3_version:
        clat = "clat_ns"
        # convert nanoseconds to microseconds
        con = 1000
    if serverMode:
        # Support for older and newer fio json formats
        options1 = "percentile_list" in json["job options"]
        options2 = "percentile_list" in json["global options"]
    else:
        options1 = "percentile_list" in json["jobs"][0]["job options"]
        options2 = "percentile_list" in json["global options"]
    iotype = ["read", "write", "trim"]
    if options1 or options2:
        percent = [
            "25.000000",
            "50.000000",
            "70.000000",
            "75.000000",
            "90.000000",
            "99.000000",
            "99.900000",
            "99.990000",
            "99.999000",
            "99.999900",
        ]
    else:
        percent = [
            "50.000000",
            "70.000000",
            "90.000000",
            "99.000000",
            "99.900000",
            "99.990000",
            "99.999900",
        ]
    line = [
        jobname,
        data["read"]["iops"],
        data["read"]["bw"],
        data["write"]["iops"],
        data["write"]["bw"],
        data["trim"]["iops"],
        data["trim"]["bw"],
    ]
    for io in iotype:
        line.append(str(data[io][clat]["mean"] / con))
        line.append(str(data[io][clat]["max"] / con))
        if data[io]["iops"] > 0:
            for p in percent:
                if "percentile" in data[io][clat]:
                    line.append(str(data[io][clat]["percentile"][p] / con))
        else:
            for _p in percent:
                line.append(0)
    return line


def print_csv_line(f, jobname, json, ver="", serverMode=False):
    index = 0
    lines = 1
    if not serverMode:
        lines = len(json["jobs"])
        ver = json["fio version"]
    while index != lines:
        data = json
        if not serverMode:
            data = json["jobs"][index]
        try:
            line = get_csv_line(jobname, json, index, data, ver, serverMode)
            wrtr = csv.writer(f)
            wrtr.writerow(line)
        except IOError:
            print("cannot write to ", f)
            f.close()
            sys.exit(1)
        index += 1


def parseServerResults(json_path, csv_dir):
    if not os.path.isdir(csv_dir):
        os.mkdir(csv_dir)
    write_server_csv_files(csv_dir, json_path)


def write_server_csv_files(csv_dir, json_path):
    """Writes fio server mode json results into CSV files.

    One CSV file is written per hostname.
    """
    data = read_json(json_path, serverMode=True)
    version_str = data["fio version"]
    jobname = os.path.splitext(os.path.basename(json_path))[0]
    hostname_data_dict = get_hostname_to_data_dict(data)
    for hostname in hostname_data_dict:
        host_csv_path = os.path.join(csv_dir, "%s.csv" % hostname)
        is_new_file = not os.path.isfile(host_csv_path)
        with open(host_csv_path, "a") as csv_out:
            jb_data = hostname_data_dict[hostname]
            jb = jb_data[0]
            if is_new_file:
                new_csv(csv_out, ("percentile_list" in jb["job options"]))
            print_csv_line(csv_out, jobname, jb, version_str, serverMode=True)
            for jb in jb_data[1:]:
                print_csv_line(csv_out, jobname, jb, serverMode=True)


def get_hostname_to_data_dict(fio_data):
    """Create dictionary mapping hostname to its fio data.

    Returns:
        Dict[str, List[dict]] - hostname to its fio data
    """
    hostname_data_dict = {}
    for jb in fio_data["client_stats"]:
        if jb["jobname"] == "All clients":
            continue
        hostname = jb["hostname"]
        if hostname not in hostname_data_dict:
            hostname_data_dict[hostname] = [jb]
        else:
            hostname_data_dict[hostname].append(jb)
    return hostname_data_dict


def get_combined_stats(stats):
    combined_stats = OrderedDict()
    for job in stats.keys():
        combined_stats[job] = OrderedDict()
        for stat in stats[job].keys():
            currStat = map(float, stats[job][stat])
            if "_IOPS" in stat or "_BW" in stat:
                combined_stats[job][stat + "_TOTAL"] = sum(currStat)
                combined_stats[job][stat + "_MIN"] = min(currStat)
            combined_stats[job][stat + "_AVG"] = sum(currStat) / len(currStat)
            combined_stats[job][stat + "_MAX"] = max(currStat)
    return combined_stats


def combineCsv(csvFolder, fname, dut_list):
    csvName = "Combined_Results-%s.csv" % fname
    csvPath = os.path.join(csvFolder, csvName)
    stats = OrderedDict()  # Using OrderedDict to preserve job and stat ordering

    try:
        os.remove(csvPath)  # Remove it if it already exists
    except OSError:
        pass
    csvList = glob.glob(os.path.join(csvFolder, "*.csv"))
    reader = csv.reader(open(csvList[0]))
    col_names = next(reader)

    for row in reader:
        stats[row[0]] = OrderedDict()
        for c in col_names[1:]:  # remove "jobname" column
            stats[row[0]][c] = []

    for c in csvList:
        with open(c) as fd:
            creader = csv.reader(fd)
            next(creader)
            for row in creader:
                for i in range(1, len(row)):
                    stats[row[0]][col_names[i]].append(row[i])
    combined_stats = get_combined_stats(stats)
    with open(csvPath, "a") as csv_out:
        writer = csv.writer(csv_out)
        server_list = ";".join([dut.serverName for dut in dut_list])
        writer.writerow([fname] + [server_list])
        stats_headers = combined_stats[combined_stats.keys()[0]].keys()
        writer.writerow(["Jobname"] + stats_headers)

        for job in combined_stats.keys():
            row = [job]
            for stat in combined_stats[job].keys():
                row.append(combined_stats[job][stat])
            writer.writerow(row)


def get_json_files(dir_path):
    """Returns list of files under `dir_path` with a `.json` extension."""
    json_files = []
    for f in sorted(os.listdir(dir_path)):
        if f.endswith(".json"):
            json_files.append(os.path.join(dir_path, f))
    return json_files


def write_csv_file(csv_filepath, fio_json_files):
    """Converts and writes each fio json file into a single CSV file."""
    is_new_file = not os.path.isfile(csv_filepath)
    with open(csv_filepath, "a") as csv_out:
        first_file = fio_json_files[0]
        fio_jobname = os.path.splitext(os.path.basename(first_file))[0]
        fio_data = read_json(first_file)
        if is_new_file:
            new_csv(
                csv_out,
                ("percentile_list" in fio_data["jobs"][0]["job options"]),
                "percentile_list" in fio_data["global options"],
            )
        print_csv_line(csv_out, fio_jobname, fio_data)
        for f in fio_json_files[1:]:  # Continue from second element, if any
            fio_jobname = os.path.splitext(os.path.basename(f))[0]
            fio_data = read_json(f)
            print_csv_line(csv_out, fio_jobname, fio_data)


def main(args):
    if args.combine_csv_path != "":
        combineCsv(args.combine_csv_path)
        return

    if args.all_json:
        json_files = get_json_files(args.all_json)
    else:
        json_files = [args.json_file]

    if json_files:
        csv_filepath = os.path.join(args.csv_path, args.csv_file)
        write_csv_file(csv_filepath, json_files)


def cli_main():
    args = set_attributes()
    main(args)


if __name__ == "__main__":
    cli_main()
