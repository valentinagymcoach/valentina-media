#!/usr/bin/env bash
# Stimm-Vorschläge auf frischem Pod (ComfyUI-Template). Ergebnis: ComfyUI/output/voice_samples/*.mp3
set -x
O=/workspace/runpod-slim/ComfyUI/output/voice_samples; mkdir -p $O /workspace/vs
R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main
apt-get update -qq && apt-get install -y -qq ffmpeg python3-venv >/dev/null 2>&1
wget -q -O /workspace/vs/voice_samples.py $R/runpod/voice_samples.py
wget -q -O $O/m0_maya_current.wav $R/audio/voice2/vo2_r6_2.wav
cp $O/m0_maya_current.wav /workspace/vs/ref.wav
python3 -m venv /workspace/vs/q && /workspace/vs/q/bin/pip install -q -U qwen-tts soundfile
python3 -m venv /workspace/vs/c && /workspace/vs/c/bin/pip install -q chatterbox-tts soundfile &
/workspace/vs/q/bin/python /workspace/vs/voice_samples.py qwen $O /workspace/vs/ref.wav
wait
/workspace/vs/c/bin/python /workspace/vs/voice_samples.py chatterbox $O /workspace/vs/ref.wav
cd $O && for f in *.wav; do ffmpeg -v error -y -i "$f" -af loudnorm=I=-16:TP=-1.5 -b:a 160k "${f%.wav}.mp3"; done
ls $O; echo VOICE_DONE
