#!/bin/bash
# Copyright (c) Facebook, Inc. and its affiliates.

for i in $(sg_map -i -x | grep ATA | awk "{print $7}")
do
  smartctl -x "$i"
done
