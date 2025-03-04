#!/bin/bash
cp presets-collect-green.json presets.json

python push-presets.py \
--target-ip 10.201.12.70,10.201.12.71,10.201.12.72,10.201.12.73,10.201.12.74,10.201.12.75,10.201.12.76,10.201.12.77\
 presets.json
python reboot.py \
--target-ip 10.201.12.70,10.201.12.71,10.201.12.72,10.201.12.73,10.201.12.74,10.201.12.75,10.201.12.76,10.201.12.77