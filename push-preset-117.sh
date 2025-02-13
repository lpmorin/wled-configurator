#!/bin/bash
cp presets-117.json presets.json

python push-presets.py --target-ip 10.201.12.51 presets.json
python reboot.py --target-ip 10.201.12.51