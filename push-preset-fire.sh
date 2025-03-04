#!/bin/bash
cp presets-fire.json presets.json


python push-presets.py --target-ip 10.201.12.48 presets.json
python reboot.py --target-ip 10.201.12.48