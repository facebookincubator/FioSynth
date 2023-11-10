# fiosynth
FB fio Synthetic Benchmark Suite for Flash ver 3.6.0

## Examples

Run workload suite on a single device:
```
fiosynth -d /dev/sdc -w LE_Flash -f LE_Flash_sdc
```

Run workload suite on all data devices:
```
fiosynth -d ALL -w LE_Flash -f LE_Flash_noRAID
```

Run workload suite on all mdraid devices:
```
fiosynth -d ALLRAID -w LE_Flash -f LE_Flash_MDRAID
```

Run workload suite on all data devices while collecting smartctl logs
```
fiosynth -d ALL -w LE_Flash -f LE_Flash_noRAID -t "./smartAll.sh"
```

Run a dry run of workload suite for all mdraid devices:
```
fiosynth -d ALLRAID -w LE_Flash -f LE_Flash_MDRAID -r y
```

Run a workload suite across multiple servers:
```
fiosynth -d ALL -w LE_Flash -f LE_Flash_server -s <server1> -s <server2>
```

Run a workload suite from a server list:
```
fiosynth -d ALL -w LE_Flash -f LE_Flash_server -l '/path/servers.txt'
```

## Requirements
fiosynth should work
* Linux (CentOS, RedHat, Ubuntu)

## Installing fiosynth
To install fiosynth simply `git clone` this repo and have the latest
versions of pip with setuptools installed

### Installing into Python environment
```
$ git clone https://github.com/facebookincubator/FioSynth
$ sudo apt install python3 python3-pip fio
$ cd FioSynth
$ sudo python3 setup.py install
$ fiosynth -h
```

### Executing fiosynth without installing
Simply execute the `fiosynth.py` entry script.
```
$ cd FioSynth
$ python3 fiosynth.py -h
```
Note: You may require `sudo` if installing to System's Python environment

Note: We recommend using a `virtualenv` to avoid polluting the Systems dependencies.

## How fiosynth works
Requires the use of workload suite files (in JSON format).  Workload
suite files can be edited to adjust the number of precondition cycles,
number of runs, number of workloads and individual workload parameters.
Use the dry run option to verify that benchmark suite executes as expected.
All workloads are normalized on a per TB bases. If capacity is not
specified, capacity will be based on capacity of the first specified device.
If specified, a vendor specific health monitor tool will be executed before
and after each benchmark suite executes and logged in "health.log" file.
Log can be used to calculate write amplification factor.
Raw results are stored in individual JSON files but are also parsed into
single a csv file for easy visualization in Excel.
Prefix for result filename must be specified.  This will define the name
of the result files directory and csv filename.

```
Input arguments (3 of arguments are required):

 -d
      (Required) device path for single device target, ALL for all
      all data devices, or ALLRAID for all mdraid devices
 -w
      (Required) filename for workload suite (default = )
 -f
      (Required) Results filename (default = )
 -c
      (Optional) specify capacity in TB (default = <device capacity>)
 -r
      (Optional) Set to y to do dry run (default = n)
 -t
      (Optional) Enter Health Monitoring Tool Syntax (default = )
 -p
      (Optional) Set to n to skip drive prep (default = y)
 -n
      (Optional) Specific the number of run cycles (default = 3 )
 -g
      (Optional) Set to y to enable flash configuration logging (default = n)
 -s
      (Optional) Add a server for workload to run on when in server mode.
      For multiple servers add multiple times. (default = )
 -l
      (Optional) Add a text file listing a server on each line (default = )
```

### Workload suites
```
PeakWklds
      Executes workloads to measure the peak small block random and large
      block sequential performance of a single or multiple flash devices.

LE_Flash
      Executes rate limited workloads with similar I/O characteristics to
      applications that run on Type VIII (Low Flash) production hardware
      on a single or multiple flash devices. Workloads use a combination
      of read iops bins (low, medium, high) and write DWPD (Drive Writes
      Per Day) bins that correlate to various Type VIII flash application
      I/O profiles.  Workload alias names are a combination of read I/O
      block size, read iops bins and write DWPD bins.

HE_Flash
      Executes rate limited workloads with similar I/O characteristics to
      applications that run on Type VI and III (High Endurance Flash)
      production hardware on a single or multiple flash devices.
      Workloads use a combination of read iops bins (low, medium, high)
      and write DWPD (Drive Writes Per Day) bins that correlate to various
      Type VI flash application I/O  profiles.  Workload alias names are
      a combination of read I/O block size, read iops bins and write DWPD
      bins.

TrimRate
      Executes a workload that evaluates the raw trim performance of a
      flash device.

LE_Flash_Short
      Short version of LE_Flash.  Executes a limited set of rate limited
      workloads to provide a high level view of performance in a few hours.

HE_Flash_Short
      Short version of HE_Flash.  Executes a limited set of rate limited
      workloads to provide a high level view of performance in a few hours.

readhammer
      Executes a workload that evaluates a flash device ability to
      continually read from a small LBA range on a single or multiple
      flash devices.
      See README-READHAMMER.txt for more information.

prep
      Executes two full capacity writes on a single or multiple flash
      devices to get the flash close to steady state.
```

### Creating/Modifying Workload Suites

Workload suites are json formatted files with a list of run rules for fio.
Follow the formatting used in other workload suites.  Generally, if all
parameters in the workload suite workload file is note defined, it will
not run.

The following parameters need to be defined globally:
```
run_cycles
      Number of times the entire workload suite will run.

precondition_cycles
      Number of times the flash will be preconditioned before each
      run cycle.  A full TRIM of the flash device will complete before
      the flash is preconditioned.  Each precondition consist of 2 full
      sequential writes of the flash device.

devices_in_global
      Specifies if the devices should be defined in the global field or
      within jobs.  Most fio job files should define devices_in_global
      parameter to Y and can scale to multiple drives using the numjob fio
      parameter.  Some jobfiles will not run properly with the devices
      defined in the global section.  These jobfiles need to create
      new job section for each device and the device_in_global parameter
      should be set to N.
      For more on fio job file format, see section 4 of
      https://github.com/axboe/fio/blob/master/HOWTO
```

The following parameters are workload specific:
```
template
      Fio jobfile name that should be used.

alias
      Name of the workload.  Use a name that describes the workload that
      is being executed.

TIME
      Sets the "runtime" parameter in the fio job file (where applicable).

BLKSIZE
      Sets the "blocksize" and "blockalign" parameter in the fio job file
      (where applicable).

DEPTH
      Sets the "iodepth" parameter in the fio job file (where applicable).

RRATE
      Sets the "rate_iops" parameter in the fio job file (where applicable).

SIZE
      Sets the "size" parameter in the fio job file (where applicable).

W1THINK, W2THINK, W3THINK & W4THINK
      Sets the "thinktime" parameter in the fio job file (where applicable).
      W1THINK and W2THINK are the think time in between each write. The smaller
      the number, the higher the write rate. 6pDWPD writes at a rate of about
      72 MB/s per TB. W3THINK and W4THINK are typically used as the think
      time in between each trim command.
```

### Client/Server Mode

To run in client/server mode, ensure that the following requirements are met:

* Both your client and all of your servers must have the same version of fio

* Any devices you want to test on the clients must be unmounted from the
  filesystem

* You may want to prepend "nohup" to the command when you call this tool, that
  way if your ssh session ends, the test will continue to run on your
  devserver.


## Join the fiosynth community
See the CONTRIBUTING file for how to help out.

## License

MIT License

Copyright (c) Facebook, Inc. and its affiliates.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
