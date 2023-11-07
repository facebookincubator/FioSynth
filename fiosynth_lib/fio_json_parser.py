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
# @nolint

import argparse
import csv
import glob
import json
import os
import sys
from collections import OrderedDict
from distutils.version import StrictVersion
import itertools

TOOL_NAME = "fio-parse-json-flash"
tunnel2host = {}


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
    if not fn:
        return None
    if not os.path.isfile(fn):
        print("%s does not exist" % fn)
        sys.exit(1)
    check_if_mounted(fn)
    f = open(fn)
    if serverMode:
        f.seek(0)
        jsonstr = f.read()
        jsonstr = "{" + jsonstr[jsonstr.rfind('"fio version" : ') :]
        try:
            data = json.loads(jsonstr)
        except ValueError:
            print("serverMode %s; JSON decoding failed on %s, is file corrupt?" % (serverMode, fn))
            f.close()
            sys.exit(1)
    else:
        try:
            data = json.load(f)
        except ValueError:
            print("serverMode %s; JSON decoding failed on %s, now trying to format json before parsing" % (serverMode, fn))
            try:
                f.seek(0)
                jsonstr = f.read()
                jsonstr = "{" + jsonstr[jsonstr.rfind('"fio version" : ') :]

                data = json.loads(jsonstr)

            except:
                print("serverMode %s; JSON decoding failed on %s, is file corrupt?" % (serverMode, fn))
                f.close()
                sys.exit(1)
    f.close()
    return data

def read_extsmart(filename):
    with open(filename, 'r') as f:
        f_data = f.read()
    return f_data


def new_csv(f, notStdPercentile1, notStdPercentile2, add_waf_header, add_lm_header, create_file=True):
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
    if add_waf_header:
        col_names += [
            "Total_FIO_Writes",
            "Host_Writes_BEFORE",
            "Host_Writes_AFTER",
            "NAND_Writes_BEFORE",
            "NAND_Writes_AFTER",
        ]
    if add_lm_header:
        col_names += [
            "Max_Read_Latency_Counter_BEFORE",
            "Max_Write_Latency_Counter_BEFORE",
            "Max_Read_Latency_Measured_BEFORE",
            "Max_Write_Latency_Measured_BEFORE",
            "Max_Read_Latency_Counter_AFTER",
            "Max_Write_Latency_Counter_AFTER",
            "Max_Read_Latency_Measured_AFTER",
            "Max_Write_Latency_Measured_AFTER",
            ]
    if create_file:
        try:
            writer = csv.writer(f)
            writer.writerow(col_names)
        except IOError:
            print("cannot write to ", f)
            f.close()
            sys.exit(1)

    return col_names


def get_csv_line(jobname, json, index, data, version_str, serverMode, scale_by_TB=1):
    clat = "clat"
    con = 1
    # clat -> clat_ns in version 3.0
    verstr = version_str.split("-")[1]
    fio_version = StrictVersion(verstr)
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
        data["read"]["iops"] / scale_by_TB,
        data["read"]["bw"] / scale_by_TB,
        data["write"]["iops"] / scale_by_TB,
        data["write"]["bw"] / scale_by_TB,
        data["trim"]["iops"] / scale_by_TB,
        data["trim"]["bw"] / scale_by_TB,
    ]
    for io in iotype:
        line.append(str(data[io][clat]["mean"] / con))
        line.append(str(data[io][clat]["max"] / con))
        if data[io]["iops"] > 0:
            for p in percent:
                if "percentile" in data[io][clat]:
                    line.append(str(data[io][clat]["percentile"][p] / con))
                else:  #if FIO bugged out and didnt report percentile
                    line.append(0)
        else:
            for _p in percent:
                line.append(0)
    return line


def get_fio_writes(data):
    line = []
    line.append(data['write']['io_bytes'])
    return line


def get_smart_line(data):
    sum = 0
    smart_keys = [
        'data_units_written',
    ]

    if not data:
        return []

    # extract the correct key
    try:
        results = find(smart_keys, data)
        for x in results:
            for key, value in x.items():
                if isinstance(value, int):
                    sum += value
                else:
                    sum += int(value, 0) # autoguess the format
                sum *= 512 * 1000
    except:
        return ["na"]

    return [sum]

def get_extsmart_line(data):
    sum = 0
    extsmart_keys = [
        'Physical media units written',
        'Physical Media Units Written-TLC',
        'Physical Media Units Written-SLC',
        'NAND Writes TLC (Bytes)',
        'NAND Writes SLC (Bytes)',
        'Physical Media Units Written - TLC',
        'Physical Media Units Written - SLC',
        'physical_media_units_bytes_tlc',
        'physical_media_units_bytes_slc',
        'Physical Media Units Written - TLC (Bytes)',
        'Physical Media Units Written - SLC (Bytes)',
    ]

    if not data:
        return []

    # extract the correct key
    try:
        results = find(extsmart_keys, data)
        for x in results:
            for key, value in x.items():
                if isinstance(value, int):
                    sum += value
                else:
                    sum += int(value, 0) # autoguess the format
    except:
        return [0]

    return [sum]

def get_lm_line(data, lm_mapping):
    line = []
    lm_log = {
        "Active Bucket Counter": {
            "Read": "na",
            "Write": "na",
        },
        "Active Measured Latency": {
            "Read": "na",
            "Write": "na",
        },
    }

    if isinstance(data, dict):
        map = lm_mapping
    elif all([data is None, lm_mapping]):
        map = {}
    elif all([data is None, not lm_mapping]):
        return []

    for metric, _ in lm_log.items():
        for io_type, value in _.items():
            for bucket, settings in map.items():
                if io_type in settings["target"]:
                    lm_log[metric][io_type] = data["%s: %s" % (metric, bucket)][io_type]

    for metric, _ in lm_log.items():
        for io_type, value in _.items():
            line += [value]

    return line

def find(search, data):
    matches = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in search:
                if isinstance(value, dict):
                    if 'lo' in value:  # workaround for OCP plugin output schema
                        matches.append({key: value['lo']})
                else:
                    matches.append({key: value})
            else:
                dive = find(search, value)
                if dive:
                    matches.extend(dive)
    elif isinstance(data, list):
        for idx, x in enumerate(data):
            sweep_result = find(search, x)
            if sweep_result:
                matches.extend(sweep_result)
    else:
        return None
    return matches

def recursive_items(dictionary):
    for key, value in dictionary.items():
        if type(value) is dict:
            yield from recursive_items(value)
        else:
            yield key

def get_target_line(col_names, job_targets):
    target_list = []
    target_dict = {}
    col_names_filtered = col_names

    for name in col_names:
        target_dict[name] = "na"

    if isinstance(job_targets, dict):
        for metric, subdict1 in job_targets.items():
            for iotype, subdict2 in subdict1.items():
                for valuetype, value in subdict2.items():
                    target_list += [[metric, iotype, valuetype, value]]

    for col in [x.split("_") for x in col_names_filtered]:
        col_filtered = col
        col_filtered = list(itertools.chain.from_iterable(["throughput", "MIN"] if x == "BW" else [x] for x in col_filtered))
        col_filtered = list(itertools.chain.from_iterable(["iops", "MIN"] if x == "IOPS" else [x] for x in col_filtered))
        col_filtered = list(itertools.chain.from_iterable(["latency"] if x == "Latency" else [x] for x in col_filtered))
        col_filtered = list(itertools.chain.from_iterable(["read"] if x == "Read" else [x] for x in col_filtered))
        col_filtered = list(itertools.chain.from_iterable(["write"] if x == "Write" else [x] for x in col_filtered))
        col_filtered = list(itertools.chain.from_iterable(["trim"] if x == "Trim" else [x] for x in col_filtered))
        col_filtered = list(itertools.chain.from_iterable(["MAX"] if x == "Max" else [x] for x in col_filtered))

        for target in target_list:
            target_param = target[0:3]
            if all(item in target_param for item in col_filtered):
                target_dict["_".join(col)] = target[-1]

    return list(target_dict.values())


def print_csv_line(f, jobname, fio_data, col_names, only_targets, job_targets, scale_by_TB, smart_before_data, smart_after_data, extsmart_before_data, extsmart_after_data, lm_before_data, lm_after_data, lm_mapping, ver="", serverMode=False, ):
    index = 0
    lines = 1
    line_parts = []
    scale_by_TB_factor = 1

    if job_targets:
        if "throughput" in job_targets.keys():
            if "scale_by_TB" in job_targets["throughput"].keys():
                if job_targets["throughput"]["scale_by_TB"]["value"]:
                    scale_by_TB_factor = scale_by_TB

    if only_targets:
        lines = 1
    elif not serverMode:
        lines = len(fio_data["jobs"])
        ver = fio_data["fio version"]

    while index != lines:
        data = fio_data
        if only_targets:
            try:
                line_parts = []
                line_parts += [jobname + "_targets"]
                line_parts += get_target_line([x for x in col_names if x != "Jobname"], job_targets)

                rdr = list(csv.reader(f))
                f.seek(0)
                for row, line in enumerate(rdr):
                    for col in line:
                        if any([x in col for x in ["Jobname", "targets"]]):
                            idx = row

                rdr.insert(idx+1, line_parts)
                wrtr = csv.writer(f)
                wrtr.writerows(rdr)
            except IOError:
                print("cannot write to ", f)
                f.close()
                sys.exit(1)
            break

        if not serverMode:
            data = fio_data["jobs"][index]

        try:
            line_parts = []
            line_parts += get_csv_line(jobname, fio_data, index, data, ver, serverMode, scale_by_TB_factor)
            if smart_before_data:
                line_parts += get_fio_writes(data)
            line_parts += get_smart_line(smart_before_data)
            line_parts += get_smart_line(smart_after_data)
            line_parts += get_extsmart_line(extsmart_before_data)
            line_parts += get_extsmart_line(extsmart_after_data)
            line_parts += get_lm_line(lm_before_data, lm_mapping)
            line_parts += get_lm_line(lm_after_data, lm_mapping)
            wrtr = csv.writer(f)
            wrtr.writerow(line_parts)
        except IOError:
            print("cannot write to ", f)
            f.close()
            sys.exit(1)
        index += 1

def print_csv_line_generic(filename, content):
    with open(filename, "a") as f:
        try:
            wrtr = csv.writer(f)
            wrtr.writerow(content)
        except IOError:
            print("cannot write to ", filename)
            f.close()
            sys.exit(1)

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
            jb["global options"] = data["global options"]
            if is_new_file:
                new_csv(
                    csv_out,
                    ("percentile_list" in jb["job options"]),
                    ("percentile_list" in data["global options"]),
                )
            print_csv_line(csv_out, jobname, jb, version_str, serverMode=True)
            for jb in jb_data[1:]:
                jb["global options"] = data["global options"]
                print_csv_line(csv_out, jobname, jb, version_str, serverMode=True)


def get_hostname_to_data_dict(fio_data):
    """Create dictionary mapping hostname to its fio data.

    Returns:
        Dict[str, List[dict]] - hostname to its fio data
    """
    hostname_data_dict = {}
    for jb in fio_data["client_stats"]:
        if jb["jobname"] == "All clients":
            continue
        if len(tunnel2host) == 0:
            hostname = jb["hostname"]
        else:
            hostname = tunnel2host[jb["port"]]

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
            currStat = [float(val) for val in stats[job][stat]]
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
        stats_headers = combined_stats[list(combined_stats.keys())[0]].keys()
        writer.writerow(["Jobname"] + list(stats_headers))

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


def write_csv_file(csv_filepath, fio_json_files, only_targets, job_targets, scale_by_TB, smart_before_json, smart_after_json, extsmart_before_json, extsmart_after_json, lm_before_json, lm_after_json, lm_mapping):
    """Converts and writes each fio json file into a single CSV file."""
    is_new_file = not os.path.isfile(csv_filepath)
    first_file = fio_json_files[0]
    fio_jobname = os.path.splitext(os.path.basename(first_file))[0] #gen_write_run1

    if only_targets:
        with open(csv_filepath, "r+") as csv_out:
            col_names = list(csv.reader(csv_out))[0]
            csv_out.seek(0)
            print_csv_line(csv_out, fio_jobname, None, col_names, only_targets, job_targets, 1, None, None, None, None, None, None, None)
            for f in fio_json_files[1:]:  # Continue from second element, if any
                fio_jobname = os.path.splitext(os.path.basename(f))[0]
                print_csv_line(csv_out, fio_jobname, None, col_names, only_targets, job_targets, 1, None, None, None, None, None, None, None)
    else:
        with open(csv_filepath, "a+") as csv_out:
            fio_data = read_json(first_file)
            smart_before_data = read_json(smart_before_json)
            smart_after_data = read_json(smart_after_json)
            extsmart_before_data = read_json(extsmart_before_json)
            extsmart_after_data = read_json(extsmart_after_json)
            lm_before_data = read_json(lm_before_json)
            lm_after_data = read_json(lm_after_json)

            col_names = new_csv(
                csv_out,
                ("percentile_list" in fio_data["jobs"][0]["job options"]),
                "percentile_list" in fio_data["global options"],
                bool(smart_before_json),
                bool(lm_mapping),
                is_new_file,
            )

            print_csv_line(csv_out, fio_jobname, fio_data, col_names, only_targets, job_targets, scale_by_TB, smart_before_data, smart_after_data, extsmart_before_data, extsmart_after_data, lm_before_data, lm_after_data, lm_mapping)
            for f in fio_json_files[1:]:  # Continue from second element, if any
                fio_jobname = os.path.splitext(os.path.basename(f))[0]
                fio_data = read_json(f)
                print_csv_line(csv_out, fio_jobname, fio_data, col_names, only_targets, job_targets, scale_by_TB, smart_before_data, smart_after_data, extsmart_before_data, extsmart_after_data, lm_before_data, lm_after_data, lm_mapping)


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
        write_csv_file(csv_filepath, json_files, args.only_targets, args.job_targets, args.scale_by_TB, args.smart_before_file, args.smart_after_file, args.extsmart_before_file, args.extsmart_after_file, args.lm_before_file, args.lm_after_file, args.lm_mapping)


def cli_main():
    args = set_attributes()
    main(args)


if __name__ == "__main__":
    cli_main()
