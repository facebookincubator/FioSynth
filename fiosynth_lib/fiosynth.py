#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# AUTHOR = 'Darryl Gardner <darryleg@fb.com>'
# @nolint

# pyre-unsafe

import argparse
import datetime
import json
import os
import os.path
import shutil
import socket
import subprocess
import sys
import time
from distutils.version import LooseVersion
from random import randint
from subprocess import PIPE, Popen

from . import fio_json_parser, flash_config, health_tools


class Parser:
    def __init__(self, jname, cname, only_targets=False, job_targets={}, scale_by_TB=1, smart_before_jname="", smart_after_jname="", extsmart_before_jname="", extsmart_after_jname="", lm_before_file="", lm_after_file="", lm_mapping=None):
        self.json_file = jname
        self.json_path = "."
        self.only_targets = only_targets
        self.job_targets = job_targets
        self.scale_by_TB = scale_by_TB
        self.smart_before_file = smart_before_jname
        self.smart_after_file = smart_after_jname
        self.extsmart_before_file = extsmart_before_jname
        self.extsmart_after_file = extsmart_after_jname
        self.lm_before_file = lm_before_file
        self.lm_after_file = lm_after_file
        self.lm_mapping = lm_mapping
        self.all_json = ""
        self.csv_path = "."
        self.csv_file = cname
        self.serverMode = "n"
        self.combine_csv_path = ""


def parseLocalResults(args):
    fio_json_parser.main(args)

def set_attributes():
    #
    # Attribute Table Definition
    #
    parser = argparse.ArgumentParser(
        description="FB fio Synthetic Benchmark Suite for storage ver 3.6.0"
    )
    parser.add_argument(
        "-d",
        action="store",
        dest="device",
        type=str,
        help=(
            "(Required) device path for single device target, ALL for all"
            "data devices, or ALLRAID for all mdraid devices"
        ),
        required=True,
        default="",
    )
    parser.add_argument(
        "-c",
        action="store",
        dest="factor",
        type=float,
        help="(Optional) specify capacity in TB (default = <device capacity>)",
        default=-1.0,
    )
    parser.add_argument(
        "-w",
        action="store",
        dest="wklds",
        type=str,
        help="(Required) filename for workload suite (default = )",
        required=True,
        default="",
    )
    parser.add_argument(
        "-f",
        action="store",
        dest="fname",
        type=str,
        help="(Required) Results filename (default = )",
        required=True,
        default=".",
    )
    parser.add_argument(
        "-r",
        action="store",
        dest="dryrun",
        type=str,
        help="(Optional) Set to y to do dry run (default = n)",
        default="n",
    )
    parser.add_argument(
        "-t",
        action="store",
        dest="health",
        type=str,
        help="(Optional) Enter Health Monitoring Tool Syntax (default = )",
        default="",
    )
    parser.add_argument(
        "-p",
        action="store",
        dest="prep",
        type=str,
        help="(Optional) Set to n to skip drive prep, o to prep on first cycle "
        "only (default = y)",
        default="y",
    )
    parser.add_argument(
        "-n",
        action="store",
        dest="cycles",
        type=int,
        help="(Optional) Specific the number of run cycles (default = 3 )",
        default=-1,
    )
    parser.add_argument(
        "-g",
        action="store",
        dest="getflash",
        type=str,
        help="(Optional) Set to y to enable flash configuration logging "
        "(default = n)",
        default="n",
    )
    parser.add_argument(
        "-s",
        action="append",
        dest="servers",
        type=str,
        help="(Optional) Add a server to the list for client/server mode",
        default=[],
    )
    parser.add_argument(
        "-l",
        action="store",
        dest="server_file",
        type=str,
        help="(Optional) Path to a text file with a server name on each line",
        default="",
    )
    parser.add_argument(
        "-j",
        action="store",
        dest="job_scale",
        type=int,
        help="(Optional) Scale by jobs (default = 1 job per drive)",
        default=1,
    )
    parser.add_argument(
        "-x",
        action="store_true",
        dest="exitall",
        help="(Optional) Pass --exitall to fio",
    )
    parser.add_argument(
        "-z",
        action="store_true",
        dest="deterministic",
        help="(Optional) Static file and directory names",
    )
    parser.add_argument(
        "-m",
        action="store",
        dest="misc",
        type=str,
        help="(Optional) Set a misc variable in a workload suite" "(default = )",
        default="",
    )
    parser.add_argument(
        "-e",
        action="store",
        dest="expert",
        type=str,
        help="(Optional) Pass this string directly to fio command line invocation and attach just before jobfile argument"
        "(default = )",
        default="",
    )
    parser.add_argument(
        "-u",
        action="store",
        dest="user",
        type=str,
        help="(Optional) The user to login as on the server when running fiosynth in client/server mode (default = root)",
        default="root",
    )
    parser.add_argument(
        "-y",
        action="store",
        dest="tunneling",
        type=str,
        help="(Optional) Set to y to perform server/client mode fio via SSH tunnels. (default = n)",
        default="n",
    )
    parser.add_argument(
        "--waf",
        action="store_true",
        dest="calc_waf",
        help="(Optional) Set to use calculate WAF (Write Amplification Factor) based on OCP SMART / Health Inforamtion Extended (Log Identifier C0h) data. OCP compliant devices only. (default = disabled)",
    )
    parser.add_argument(
        "--lm",
        action="store_true",
        dest="check_lm",
        help="(Optional) Set to use OCP Latency Monitor to check max read and max write latencies if targets avaiable. OCP 2.0 compliant devices only. (default = disabled)",
    )
    parser.add_argument(
        "--targets",
        action="store_true",
        dest="show_targets",
        help="(Optional) Set to add performance targets in the output CSV file. Targets are taken from workload file. (default = disabled)",
    )
    parser.add_argument(
        "--scale-by-TB",
        action="store_true",
        dest="scale_by_TB",
        help="(Optional) Set to scale BW and IOPs by device capacity in the output CSV file. Workload must have store_by_TB set to true. (default = disabled)",
    )

    parser.add_argument("-v", action="version", version=parser.description)
    args = parser.parse_args()
    return args


def checkVersion(tool):
    cmd = None
    if tool == "fio":
        minVersion = "2.20"
        cmd = "fio -v | sed s/fio-//"
    if cmd is not None:
        min_version = LooseVersion(minVersion)
        v3_version = LooseVersion("3.0")
        version = cmdline(cmd).rstrip()
        fio_version = LooseVersion(version.decode("utf-8"))
        # Using utf-8 encoding to insure that version is reported as a string
        if fio_version < min_version:
            print("{} older than version {}".format(tool, minVersion))
            sys.exit(1)
        if fio_version >= v3_version:
            return 3
        else:
            return 2
    else:
        print("Unknown tool %s, can't check version." % tool)
        sys.exit(1)


def cmdline(cmd):
    process = Popen(args=cmd, stdout=PIPE, shell=True)
    return process.communicate()[0]


def checkMounted(device, dut):
    cmd = "grep -c %s /proc/mounts" % device
    if not dut.inLocalMode():
        dutSsh = getSshProc(dut)
        out, err = dutSsh.communicate(cmd)
        mount = out.strip()
    else:
        mount = cmdline(cmd)
    if int(mount) > 0:
        return True
    else:
        return False


def getAllDataDrives(data, command, profile, dut):
    # getAllDataDrives creates a list of devices separated by a ':'.
    # An example of the string that is created in this function is
    # '/dev/sdb:/dev/sdc:/dev/sdd:/dev/sde:/dev/sdf:'.
    # If devices_in_global option is 'N' each device will be listed
    # on a separate line.
    if command == "ALL":
        device = "disk"
        # Skip boot device (sda)
    else:
        device = getRaidLevel(data)
    dev_path = ""
    dev_list = set()
    for dev in data[device]:
        if checkFileExist(dev, dut) is True:
            if checkMounted(dev, dut) is False:
                if profile["devices_in_global"] == "N":
                    dev_path += "[%s]\n" % dev
                    dev_path += "filename=%s\n" % dev
                    dut.device += "%s:" % dev
                else:
                    if dev not in dev_list:
                        dev_list.add(dev)
                        dev_path += "%s:" % dev
    return dev_path


def createTempJobTemplate(dut, jobname):
    # (Used to be called createTempJobFile, renamed for clarity)
    # Creates a temporary job template
    dst_file = "tmp.fio"
    shutil.copyfile(jobname, dst_file)
    with open(dst_file, "a") as tmp_file:
        try:
            tmp_file.write(dut.dev_list)
        except OSError:
            print("cannot write to %s" % tmp_file)
            sys.exit(1)
    return dst_file


def getTotalDataCapacity(data):
    VAL = 1
    data_cap = int(data["disk"][VAL])
    return data_cap


# For checking devices, but can also be used for checking files
def checkFileExist(path, dut):
    if dut.inLocalMode():
        try:
            os.stat(path)
        except OSError:
            print("%s does not exist " % path)
            return False
        return True
    else:
        proc = getSshProc(dut)
        cmdStr = "stat %s 2> /dev/null | wc -l" % path
        out, err = proc.communicate(cmdStr)
        result = out.strip()
        if int(result) > 0:
            return True
        else:
            print("{} does not exist on server {} ".format(path, dut.serverName))
            return False


def getNumJobs(data, command, dut):
    # getNumJobs checks the number of devices in the system and
    # subtracts by 1 to avoid counting the boot device if using
    # ALL option. If using ALLRAID option, it will could the
    # number of unique mdraid devices. Number of jobs is used
    # to scale fio jobfiles for multiple devices.
    if command == "ALL":
        jobs = len(data["disk"]) - 1
    else:
        dev_list = set()
        raid = getRaidLevel(data)
        for dev in data[raid]:
            if checkFileExist(dev, dut) is True:
                dev_list.add(dev)
        jobs = len(dev_list)
    return jobs


def getSshProc(dut):
    sshProc = subprocess.Popen(
        ["ssh", dut.sshUser + "@" + dut.serverName, "/bin/bash"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )
    return sshProc


def getMultiplier(capacity):
    factor = float(capacity) / 1e12
    return max(round(factor, 1), 0.1)


def getJobVars(dut, profile, scale_factor):
    vars_static = [
        "SIZE",
        "TIME",
        "RAMPTIME",
        "RATE1",
        "RATE2",
        "BLKSIZE",
        "DEPTH1",
        "DEPTH2",
        "MISC",
        "MD",
        "DIRECT",
        "RANDRW",
        "RWMIXREAD",
        "IOENGINE",
        "RAMP",
        "NUMJOBS",
    ]
    vars_scaleup = ["RRATE", "DEPTH", "OFFSET2"]
    vars_scaledown = ["W1THINK", "W2THINK", "W3THINK", "W4THINK", "W5THINK"]
    job_vars = {}
    for var in vars_static:
        if var in profile:
            job_vars[var] = profile[var]
    for var in vars_scaleup:
        if var in profile:
            if var == "OFFSET2":
                job_vars["OFFSET2"] = int(
                    profile["OFFSET2"] * getMultiplier(dut.capacity)
                )
            else:
                job_vars[var] = int(profile[var] * scale_factor)
            if job_vars[var] < 1:
                job_vars[var] = 1
    for var in vars_scaledown:
        if var in profile:
            job_vars[var] = int(int(profile[var]) / scale_factor)
            if job_vars[var] < 1:
                job_vars[var] = 1
    job_vars["DEV"] = dut.device
    job_vars["JOBS"] = dut.numjobs
    if "JOBS" in profile:
        job_vars["JOBS"] *= profile["JOBS"]
    job_vars["OFFSET1"] = dut.offset
    job_vars["INCREMENT"] = dut.increment
    return job_vars


def run_fio(p, VAL, dut_list, args, run, rtype):

    resultsFileName = "%s/%s_run%d.json" % (FioDUT.fname, p[rtype][VAL]["alias"], run)
    exitall_flag = " "
    if args.exitall:
        exitall_flag = " --exitall "
    fioCmd = "fio --output-format=json{}--output={} ".format(
        exitall_flag,
        resultsFileName,
    )
    fioCmd += " " + args.expert.lstrip().rstrip() + " "
    currDir = os.getcwd()
    tmpJobDir = ""
    if not dut_list[0].inLocalMode():
        tmpJobDir = os.path.join(currDir, "tmpJobFiles")
        cmdline("rm -rf %s" % (tmpJobDir))
        cmdline("mkdir %s" % (tmpJobDir))
    for dut in dut_list:
        template = os.path.join(FioDUT.jobfiles, p[rtype][VAL]["template"])
        f = dut.factor
        jobVars = getJobVars(dut, p[rtype][VAL]["values"], f)
        if args.misc != "":
            jobVars["MISC"] = args.misc
        if p["devices_in_global"] == "N":
            template = createTempJobTemplate(dut, template)
        if dut.inLocalMode():
            for k, v in jobVars.items():
                fioCmd = k + "=" + str(v) + " " + fioCmd
            fioCmd = fioCmd + template
        else:
            f = open(template)
            tmpJbStr = f.read()
            f.close()
            for var in jobVars.keys():
                tmpJbStr = tmpJbStr.replace("${%s}" % str(var), str(jobVars[var]))
            tmpJbFileName = dut.serverName + "tmpJbFile"
            tmpJbFilePath = os.path.join(tmpJobDir, tmpJbFileName)
            cmdline("touch %s" % tmpJbFilePath)
            try:
                tmpFile = open(tmpJbFilePath, "w")
                tmpFile.write(tmpJbStr)
            finally:
                tmpFile.close()
            if dut.tunnel:
                fioCmd = fioCmd + (
                    " --client=ip6:localhost,%d %s" % (dut.sshTunnelPort, tmpJbFilePath)
                )
            else:
                fioCmd = fioCmd + (
                    " --client=ip6:{} {}".format(dut.serverName, tmpJbFilePath)
                )
    if args.dryrun == "n":
        cmdline(fioCmd)
    else:
        print(fioCmd)
    return resultsFileName


def isPortAvailable(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        return False
    finally:
        sock.close()
    return True


class FioDUT:
    # FioDUT (Device Under Test) represents a single machine that runs fio jobs
    jobfiles = "/usr/local/fb-FioSynthFlash/jobfiles"
    wkldsuites = "/usr/local/fb-FioSynthFlash/wkldsuites"
    fname = ""
    prep = "prep"
    csvfname = ""
    nextTunnelPort = 8765

    def __init__(self, sName="", user=""):
        self.factor = 0.0
        self.numjobs = 1
        self.offset = 0
        self.increment = 30
        self.dev_list = ""  # String, not a list!
        self.device = ""  # This replaces args.device
        self.capacity = 0
        self.serverName = sName  # If blank string, then local mode
        self.sshUser = user
        self.sshTunnelPort = 0
        self.tunnel = None

    def __del__(self):
        if isinstance(self.tunnel, Popen):
            self.tunnel.terminate()

    def inLocalMode(self):
        return self.serverName == ""

    @classmethod
    def getTunnelPort(cls):
        port = -1
        while cls.nextTunnelPort < 65535:
            try:
                if not isPortAvailable(cls.nextTunnelPort):
                    continue
                else:
                    port = cls.nextTunnelPort
                    break
            finally:
                cls.nextTunnelPort += 1
        return port


def drivesToJson(dut):
    drives = {}
    TYPE = 5
    DEVICE = 0
    maxcol = max(TYPE, DEVICE)
    output = None
    if dut.inLocalMode():
        proc = subprocess.Popen(["/bin/lsblk", "-rnbp"], stdout=subprocess.PIPE)
        output = proc.stdout.read()
        output = output.decode("utf-8")
    else:
        sshProc = getSshProc(dut)
        output, err = sshProc.communicate("/bin/lsblk -rnbp\n")
    for line in output.splitlines():
        bits = line.split()
        if len(bits) > maxcol:
            # drive_type = bits[TYPE].decode("utf-8")
            drive_type = bits[TYPE]
            # drive_device = bits[DEVICE].decode("utf-8")
            drive_device = bits[DEVICE]
            drives.setdefault(drive_type, [])
            drives[drive_type].append(drive_device)
    return json.dumps(drives)


def createOffsetFile(dut, dst_file):
    if dut.inLocalMode():
        try:
            tmp_file = open(dst_file, "w")
            tmp_file.write(str(dut.offset))
        except OSError:
            print("cannot write to %s" % tmp_file)
            sys.exit(1)
        finally:
            tmp_file.close()
        return
    else:
        dutSsh = getSshProc(dut)
        dutSsh.communicate('echo "{}" > {}'.format(str(dut.offset), dst_file))
        return


def readOffsetFile(dut, dst_file):
    if checkFileExist(dst_file, dut):
        tmp_file = open(dst_file)
        try:
            dut.offset = int(tmp_file.readline().strip())
        except OSError:
            print("cannot read from %s" % tmp_file)
            sys.exit(1)
        tmp_file.close()
    else:
        if dut.inLocalMode():
            print("offset file (%s) does not exist" % dst_file)
        else:
            print(
                "offset file (%s) does not exist on server %s"
                % (dst_file, dut.server_name)
            )
        print("Device has not been preconditioned yet")
        sys.exit(1)


def getRaidLevel(data):
    raid = None
    raidLevels = ["raid0", "raid1", "raid5", "raid6"]
    for x in data:
        for y in raidLevels:
            if x.startswith(y):
                raid = x
                break
    if raid:
        return raid
    else:
        print("No mdraid arrays found")
        sys.exit(1)


def setDutCapacity(dut, cmd, profile):
    if not cmd:
        if not dut.inLocalMode():
            host = " on %s" % dut.serverName
        else:
            host = ""
        sys.exit("No devices available or device is mounted%s." % host)
    if profile["devices_in_global"] != "N":
        dut.device = dut.dev_list
    if not dut.inLocalMode():
        dutSsh = getSshProc(dut)
        out, err = dutSsh.communicate(cmd)
        dut.capacity = out.strip()
    else:
        # set capacity to the smallest device under test
        cmd_filtered = cmd.replace("ng", "nvme")
        capacity = cmdline(cmd_filtered)
        if (int(capacity) < int(dut.capacity)) or (int(dut.capacity) == 0):
            dut.capacity = capacity


def loadDevList(dut_list, args, profile):
    prefix = "lsblk -bno SIZE "
    suffix = " | head -n 1"
    command = args.device
    if (command == "ALL") or (command == "ALLRAID"):
        for dut in dut_list:
            cmd = None
            devices = drivesToJson(dut)
            data = json.loads(devices)
            dut.dev_list = getAllDataDrives(data, command, profile, dut)
            devs = None
            if command == "ALL":
                devs = data["disk"]
            else:
                devs = data[getRaidLevel(data)]
            for dev in devs:
                if checkFileExist(dev, dut) and not checkMounted(dev, dut):
                    cmd = prefix + dev + suffix
                    setDutCapacity(dut, cmd, profile)
            dut.numjobs = getNumJobs(data, command, dut)
    else:
        devs = command.split(":")
        ndevs = len(devs)
        for dut in dut_list:
            for dev in devs:
                cmd = None
                if checkFileExist(dev, dut) and not checkMounted(dev, dut):
                    cmd = prefix + dev + suffix
                    if profile["devices_in_global"] == "N":
                        dut.dev_list += "[%s]\n" % dev
                        dut.dev_list += "filename=%s\n" % dev
                setDutCapacity(dut, cmd, profile)
            dut.device = command
            dut.numjobs = ndevs


def startAoeServer(dut):
    sshProc = getSshProc(dut)
    ipAddr, err = sshProc.communicate("killall fio -q; hostname -i")

    fioSvrCmd = (
        "nohup fio --server=ip6:%s " % (ipAddr.rstrip())
        + "> /tmp/fio.log 2> /tmp/fio.err &\n"
    )
    sshProc = getSshProc(dut)
    sshProc.stdin.write(fioSvrCmd)
    sshProc.stdin.close()
    sshProc.stdout.close()


def startSshTunnel(dut):
    dut.sshTunnelPort = FioDUT.getTunnelPort()
    if dut.sshTunnelPort <= 0:
        print(
            "Unable to find an available port for ssh tunneling for host %s."
            % dut.serverName
        )
        sys.exit(1)

    cmd = [
        "ssh",
        "{}@{}".format(dut.sshUser, dut.serverName),
        "-N",
        "-L",
        "%d:%s:8765" % (dut.sshTunnelPort, dut.serverName),
    ]
    dut.tunnel = Popen(cmd, stdout=subprocess.DEVNULL)


def clearDriveData(dut_list, dryrun="n"):
    cmd = ""
    if dut_list[0].inLocalMode():
        cmd = "fio --name=trim --filename=%s --rw=trim --bs=1G" % (dut_list[0].device)
    else:
        cmd = "fio --name=trim --rw=trim --bs=1G "
        for dut in dut_list:
            if dut.tunnel:
                cmd = cmd + "--client=ip6:localhost,%d --filename=%s" % (
                    dut.sshTunnelPort,
                    dut.device,
                )
            else:
                cmd = cmd + "--client=ip6:{} --filename={}".format(
                    dut.serverName,
                    dut.device,
                )
    if dryrun == "n":
        cmdline(cmd)


def getServers(servers, server_file, user):
    dut_list = []  # list of machines running tests
    if len(servers) == 0 and server_file == "":
        dut_list.append(FioDUT())
    else:
        if len(servers) > 0:
            for server in servers:
                dut_list.append(FioDUT(sName=server, user=user))
        if not server_file == "":
            try:
                sf = open(server_file)
                for server in sf.read().split():
                    server = server.strip()
                    dut_list.append(FioDUT(sName=server, user=user))
            except OSError:
                print("Can't open server file")
            finally:
                sf.close()
    return dut_list


def prepServers(dut_list, args, profile):
    # The increment variable is used to set the "offset_increment" fio option
    # for the readhammer workload. Setting this option allows the workload to
    # read from 32 equally
    # spaced regions on the flash device in parallel.
    # The offset_increment is calculated by converting the flash device
    # capacity from bytes to MiB then dividing by 32, representing  1/32
    # of the total flash device capacity.  Offet is in MiB.
    for dut in dut_list:
        if not dut.inLocalMode():
            startAoeServer(dut)
        if args.tunneling == "y":
            startSshTunnel(dut)
            fio_json_parser.tunnel2host[dut.sshTunnelPort] = dut.serverName
        if dut.capacity:
            dut.increment = int(float(dut.capacity) / 2**20 / 32)
            dut.offset = randint(0, dut.increment)
            dut.numjobs *= args.job_scale

        if args.factor <= 0.0:
            if profile["scale_by_capacity"] != "N":
                dut.factor = getMultiplier(dut.capacity)
            else:
                dut.factor = 1.0
        else:
            dut.factor = args.factor


def runHealthMon(fname, health="", flash=None):
    if health != "":
        runHealthTool = health_tools.HealthTools()
        runHealthTool.logger(health)
    if flash == "y":
        filename = os.path.join(fname, "flashconfig.csv")
        runGetFlashConfig = flash_config.GetFlashConfig()
        config_as_json, tool = runGetFlashConfig.get_json()
        runGetFlashConfig.json_to_csv(".", config_as_json, filename, tool)


def getSmart(device, output_filename):
    smart_cmds = [
        'nvme smart-log {} -o json | tee {}'.format(device, output_filename),
    ]
    smart_dict = {}

    for cmd in smart_cmds:
        try:
            cmd_output = cmdline(cmd)
            try:
                smart_dict = json.loads(cmd_output)
            except:
                for line in cmd_output.split('\n'):
                    key = line.split(':')[0].strip()
                    value = line.split(':')[-1].strip()
                    smart_dict[key] = value
                with open(output_filename, 'w') as f:
                    json.dump(smart_dict, f)
        except:
            pass
        else:
            break


def getVID(device):
    cmd = 'nvme id-ctrl %s -o json' % (device)
    cmd_output = cmdline(cmd)
    idctrl_dict = json.loads(cmd_output)
    return idctrl_dict["vid"]


def getOCP(device):
    OCP_map = {
        "OCP Datacenter NVMe SSD Specification Version 2.0": {
            "Log Page Version": 0x3,
            "Log Page GUID": 0xAFD514C97C6F4F9CA4f2BFEA2810AFC5,
            "calc_waf": True,
            "check_lm": True,
        },
        "OCP NVMe Cloud SSD Specification Version 1.0": {
            "Log Page Version": 0x2,
            "Log Page GUID": 0xAFD514C97C6F4F9CA4f2BFEA2810AFC5,
            "calc_waf": True,
            "check_lm": False,
        },
        "OCP Hyperscale NVMe Boot SSD Specification Version 1.0": {
            "Log Page Version": 0x1,
            "Log Page GUID": 0xC46DD7920F1E4266A178D8AC78884365,
            "calc_waf": True,
            "check_lm": False,
        },
        "No OCP Compliance": {
            "Log Page Version": 0x0,
            "Log Page GUID": 0x0,
            "calc_waf": False,
            "check_lm": False,
        },
    }

    cmd = 'nvme get-log %s --log-id=0xC0 --log-len=512 -b' % (device)
    cmd_output = cmdline(cmd)  # bytes type

    if not cmd_output:
        return OCP_map["No OCP Compliance"]

    version = cmd_output[494:496]
    guid = cmd_output[496:512]

    for spec, content in OCP_map.items():
        if version == content["Log Page Version"].to_bytes(2, 'little'):
            if guid == content["Log Page GUID"].to_bytes(16, 'little'):
                print("{} supports {}. Setting calc_waf:{} and check_lm:{}".format(device, spec, content["calc_waf"], content["check_lm"]))
                return content

    return OCP_map["No OCP Compliance"]


def getExtSmart(device, output_filename):
    vid = getVID(device)
    vid_extsmart_dict = {
        # VID : EXT SMART CMD
        '': 'nvme ocp smart-add-log {} -o json | tee {}'.format(device, output_filename),
    }
    extsmart_dict = {}
    cmd_list = []
    cmd_list += [vid_extsmart_dict['']]
    cmd_list += [vid_extsmart_dict[hex(vid)] for key in vid_extsmart_dict.keys() if key==hex(vid)]

    for cmd in cmd_list:
        try:
            cmd_output = cmdline(cmd)
            try:
                extsmart_dict = json.loads(cmd_output)
            except:
                for line in cmd_output.split('\n'):
                    key = line.split(':')[0].strip()
                    value = line.split(':')[-1].strip()
                    extsmart_dict[key] = value
                with open(output_filename, 'w') as f:
                    json.dump(extsmart_dict, f)
        except:
            pass
        else:
            break

def setupLM(drive, job_targets, enable_lm):
    lm_mapping = {
        "Bucket 0":
            {
                "target": [],
                "threshold": 0x0,  # minimum value allowed by LM
            },
        "Bucket 1":
            {
                "target": [],
                "threshold": 0x1,  # minimum value allowed by LM
            },
        "Bucket 2":
            {
                "target": [],
                "threshold": 0x2,  # minimum value allowed by LM
            },
        "Bucket 3":
            {
                "target": [],
                "threshold": 0x3,  # minimum value allowed by LM
            },
    }

    if job_targets:
        enable = enable_lm
        for io_type in ["Read", "Write"]:
            threshold = job_targets["latency"][io_type.lower()]["MAX"] / 1000 / 5 - 1  # convert us to ms zero based
            for bucket, value in list(lm_mapping.items())[:-1]:
                if value["threshold"] == threshold:
                    value["target"] += [io_type]
                    break
            else:
                lm_mapping["Bucket 3"]["target"] += [io_type]
                lm_mapping["Bucket 3"]["threshold"] = threshold
                continue
    else:
        print("No max latency target found. Disabling LM setup.")
        enable = 0

    setLM(
        drive=drive,
        threshold_a = lm_mapping["Bucket 0"]["threshold"],
        threshold_b = lm_mapping["Bucket 1"]["threshold"],
        threshold_c = lm_mapping["Bucket 2"]["threshold"],
        threshold_d = lm_mapping["Bucket 3"]["threshold"],
        enable_lm = enable,
    )

    return lm_mapping


def setLM(drive, threshold_a, threshold_b, threshold_c, threshold_d, enable_lm):
    # LM Rules:
    # Log data no more than 10 minutes old
    # Bucket Thresholds must be A<B<C<D

    cmd_options = [
    "nvme ocp set-latency-monitor-feature",
    "%s" % (drive),
    "--active_bucket_timer_threshold=%d" % (2016),  # 5 min increments; default is 07E0h or 2016 which is 1 week
    "--active_threshold_a=%d" % (threshold_a),  # 5 ms increments; default is 05h which is 30 ms
    "--active_threshold_b=%d" % (threshold_b),  # 5 ms increments; default is 13h which is 100 ms
    "--active_threshold_c=%d" % (threshold_c),  # 5 ms increments; default is 1Eh which is 155 ms
    "--active_threshold_d=%d" % (threshold_d),  # 5 ms increments; default is 2Eh which is 235 ms
    "--active_latency_config=%s" % ("0x0fff"),  # default is 0FFFh
    "--active_latency_minimum_window=%d" % (0),  # set to 0 to disable
    "--debug_log_trigger_enable=%d" % (0),  # set to 0 to disable
    "--discard_debug_log=%d" % (1),  # set to 1 to discard log and reset LM with this cmd's settings
    "--latency_monitor_feature_enable=%d" % (enable_lm), #set to 1 to enable
    ]
    cmd_output = cmdline(" ".join(cmd_options))
    return cmd_output


def getLM(drive, output_filename):
    cmd = "nvme ocp latency-monitor-log {} -o json | tee {}".format(drive, output_filename)
    cmd_output = cmdline(cmd)
    return json.loads(cmd_output)  # TODO save as file

def getLMbinary(drive, output_filename):
    cmd = "nvme get-log {} -i 0xC3 -l 512 -b | tee {}".format(drive, output_filename)
    cmdline(cmd)
    return

def runTest(dut_list, profile, args, csvFolderPath, rtype, index, rcycle, only_targets=False):
    job_targets = None
    smart_before_filename = ""
    smart_after_filename = ""
    extsmart_before_filename = ""
    extsmart_after_filename = ""
    lm_before_filename = ""
    lm_after_filename = ""
    fio_jfile = ""
    ocp_support = getOCP(dut_list[0].device)
    args.calc_waf = args.calc_waf and ocp_support["calc_waf"]
    args.check_lm = args.check_lm and ocp_support["check_lm"]
    lm_mapping = args.check_lm

    if args.scale_by_TB:
        scale_by_TB = dut_list[0].factor
    else:
        scale_by_TB = 1

    if "targets" in profile[rtype][index]:
        job_targets = profile[rtype][index]["targets"]
    elif args.check_lm:
        job_targets = {}

    if all([args.calc_waf, not only_targets]):
        smart_before_filename = "%s/%s_run%d_smart_before.log" % (FioDUT.fname, profile[rtype][index]["alias"], rcycle)
        smart_after_filename = "%s/%s_run%d_smart_after.log" % (FioDUT.fname, profile[rtype][index]["alias"], rcycle)
        extsmart_before_filename = "%s/%s_run%d_extsmart_before.log" % (FioDUT.fname, profile[rtype][index]["alias"], rcycle)
        extsmart_after_filename = "%s/%s_run%d_extsmart_after.log" % (FioDUT.fname, profile[rtype][index]["alias"], rcycle)

        getSmart(dut_list[0].device, smart_before_filename)
        getExtSmart(dut_list[0].device, extsmart_before_filename)

    if all([args.check_lm, job_targets, not only_targets]):
        lm_before_filename = "%s/%s_run%d_lm_before.log" % (FioDUT.fname, profile[rtype][index]["alias"], rcycle)
        lm_after_filename = "%s/%s_run%d_lm_after.log" % (FioDUT.fname, profile[rtype][index]["alias"], rcycle)
        lmbinary_before_filename = "%s/%s_run%d_lmbinary_before.log" % (FioDUT.fname, profile[rtype][index]["alias"], rcycle)
        lmbinary_after_filename = "%s/%s_run%d_lmbinary_after.log" % (FioDUT.fname, profile[rtype][index]["alias"], rcycle)

        lm_mapping = setupLM(dut_list[0].device, job_targets, enable_lm=1)
        getLM(dut_list[0].device, lm_before_filename)
        getLMbinary(dut_list[0].device, lmbinary_before_filename)

    if all([args.dryrun == "n", not only_targets]):
        fio_jfile = run_fio(profile, index, dut_list, args, rcycle, rtype)
    elif only_targets:
        fio_jfile = profile[rtype][index]["alias"]

    if all([args.calc_waf, not only_targets]):
        getSmart(dut_list[0].device, smart_after_filename)
        getExtSmart(dut_list[0].device, extsmart_after_filename)

    if all([args.check_lm, job_targets, not only_targets]):
        getLM(dut_list[0].device, lm_after_filename)
        getLMbinary(dut_list[0].device, lmbinary_after_filename)
        setupLM(dut_list[0].device, job_targets, enable_lm=0)

    if args.dryrun == "n":
        if dut_list[0].inLocalMode():  # Health tools only works locally
            runHealthMon(dut_list[0].fname, args.health, args.getflash)
            results = Parser(
                jname = fio_jfile,
                cname = "{}/{}.csv".format(FioDUT.fname, FioDUT.fname),
                only_targets = only_targets,
                job_targets = job_targets,
                scale_by_TB = scale_by_TB,
                smart_before_jname = smart_before_filename,
                smart_after_jname = smart_after_filename,
                extsmart_before_jname = extsmart_before_filename,
                extsmart_after_jname = extsmart_after_filename,
                lm_before_file = lm_before_filename,
                lm_after_file = lm_after_filename,
                lm_mapping = lm_mapping)
            parseLocalResults(results)
        else:
            fio_json_parser.parseServerResults(fio_jfile, csvFolderPath)
    else:
        print("parse file: %s" % fio_jfile)


def runCycles(dut_list, profile, args, rc, pc, lp, csvFolderPath):
    for rcycle in range(1, rc + 1):
        if "pre" in profile and pc > 0 and lp > 0:
            lp -= 1
            for _pcycle in range(1, pc + 1):
                for index in range(len(profile["pre"])):
                    clearDriveData(dut_list, args.dryrun)
                    runTest(
                        dut_list, profile, args, csvFolderPath, "pre", index, rcycle, False
                    )

        for index in range(len(profile["def"])):
            runTest(dut_list, profile, args, csvFolderPath, "def", index, rcycle, False)
        if rcycle == rc and args.show_targets:
            print("Adding workload targets to the CSV file")
            for index in range(len(profile["def"])):
                runTest(dut_list, profile, args, csvFolderPath, "def", index, rcycle, True)

def runSuite(args):
    dut_list = getServers(args.servers, args.server_file, args.user)

    # Use absolute path for workload suite files
    wklds = os.path.join(FioDUT.wkldsuites, args.wklds)
    profile = fio_json_parser.read_json(wklds)
    # dst_file = '/usr/local/fb-FioSynthFlash/offset.txt'
    dst_file = "/tmp/offset.txt"
    loadDevList(dut_list, args, profile)

    prepServers(dut_list, args, profile)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    if args.deterministic:
        FioDUT.fname = args.fname
    else:
        FioDUT.fname = "-".join([args.fname, timestamp])
    FioDUT.csvfname = "-".join([FioDUT.fname, "compiled_results"])
    csvFolderPath = os.path.join(os.getcwd(), FioDUT.csvfname)
    print("Results are in directory: %s" % FioDUT.fname)
    if not os.path.isdir(FioDUT.fname):
        os.mkdir(FioDUT.fname)
    if args.cycles == -1:
        rc = profile["run_cycles"]
    else:
        rc = args.cycles
    if "precondition_first_cycle_only" not in profile:
        profile["precondition_first_cycle_only"] = None
    if profile["precondition_first_cycle_only"] == "Y":
        lp = 1
    else:
        lp = 1000
    if args.prep == "n":
        pc = 0
        if dut_list[0].inLocalMode():
            for dut in dut_list:
                dut.offset = readOffsetFile(dut, dst_file)
    elif args.prep == "o":
        lp = 1  # The number of loops that will be prepared
        pc = profile["precondition_cycles"]
        for dut in dut_list:
            createOffsetFile(dut, dst_file)
    else:
        pc = profile["precondition_cycles"]
        for dut in dut_list:
            createOffsetFile(dut, dst_file)
    runCycles(dut_list, profile, args, rc, pc, lp, csvFolderPath)

    if dut_list[0].inLocalMode():
        runHealthMon(dut_list[0].fname, args.health, args.getflash)

    if args.dryrun == "n":
        if not dut_list[0].inLocalMode():
            fio_json_parser.combineCsv(csvFolderPath, FioDUT.fname, dut_list)
            print("Your results are in: %s" % csvFolderPath)


def main():
    args = set_attributes()
    # checkVersion('fio')
    runSuite(args)


if __name__ == "__main__":
    main()
