#!/usr/bin/env bash
# Nachtlauf Phase 1: Startfotos + Sprachaufnahmen. Harte Kostengrenze: Pod stoppt nach CAP Sekunden.
A=/workspace/ai; R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main
C=/workspace/runpod-slim/ComfyUI; CPY=$C/.venv-cu128/bin/python
mkdir -p $A/logs
for f in night.py it_run.py night_plan.json; do wget -q -O $A/$f $R/runpod/$f; done
(setsid nohup bash -c "sleep ${CAP:-15600}; runpodctl stop pod $RUNPOD_POD_ID" > /dev/null 2>&1 < /dev/null &)
date +%s > $A/night_start
for i in $(seq 120); do curl -sf 127.0.0.1:8188/system_stats > /dev/null && break; sleep 5; done
$CPY $A/night.py photos > $A/logs/night_photos.log 2>&1
curl -s -X POST 127.0.0.1:8188/free -H 'Content-Type: application/json' -d '{"unload_models":true,"free_memory":true}'
sleep 5
$CPY $A/night.py tts > $A/logs/night_tts.log 2>&1
echo READY > $A/night1.ok
