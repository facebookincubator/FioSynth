Currently the read hammer test will run for 14 days ( 336 hours) after the SSDs
are prepared.  Increase the number of run cycles in the "readhammer" workload
profile file to run the test for longer.

Use the following steps to run the readhammer test.
1. Precondition a single device:
  fb-FioSynthFlash -d /dev/sdc -w prep -f precondition
  or
   Precondition all devices:
  fb-FioSynthFlash -d ALL -w prep -f precondition
2. Run readhammer test on a single device:
  fb-FioSynthFlash -d /dev/sdc -w readhammer -f readhammer
  or
   Run readhammer test on all devices:
  fb-FioSynthFlash -d ALL -w readhammer -f readhammer
3. All results are stored in a .csv file in the specified results directory.

Note:  If you are running the read hammer test on more than one device, it
  is recommended to increase the maximum number of active aio contexts.
   echo "262144" > /proc/sys/fs/aio-max-nr

License
Copyright (c) Facebook, Inc. and its affiliates.
