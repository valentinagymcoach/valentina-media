#!/usr/bin/env bash
# Nachtlauf Phase 2: Videos gemäss night_picks.json, danach 20 min Puffer zum Abholen, dann Pod-Stopp.
A=/workspace/ai; R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main
CPY=/workspace/runpod-slim/ComfyUI/.venv-cu128/bin/python
wget -q -O $A/night.py $R/runpod/night.py; wget -q -O $A/picks.json $R/runpod/night_picks.json
$CPY $A/night.py videos $A/picks.json > $A/logs/night_videos.log 2>&1
sleep ${GRACE:-1200}; runpodctl stop pod $RUNPOD_POD_ID
