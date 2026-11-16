#!/usr/bin/env bash
# Frischer Pod (>=80 GB VRAM): Fish Audio Drama 3 installieren, Vorlage (Stimme E) holen, Proben erzeugen
O=/workspace/runpod-slim/ComfyUI/output/voice_samples; mkdir -p $O
R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main
apt-get update -qq && apt-get install -y -qq portaudio19-dev libsox-dev ffmpeg >/dev/null 2>&1
pip install -q uv huggingface_hub
wget -q -O /tmp/e.mp3 $R/audio/voice_samples/c2_valentina_expressive_talk.mp3 && ffmpeg -v error -y -i /tmp/e.mp3 -ar 44100 -ac 1 $O/c2_valentina_expressive_talk.wav
cd /workspace && git clone -q --depth 1 https://github.com/fishaudio/fish-speech.git
(cd fish-speech && uv sync --python 3.12 --extra cu128 > /workspace/fish_install.log 2>&1) &
python3 -c "from huggingface_hub import snapshot_download as s; s(\"fishaudio/drama-3\", local_dir=\"/workspace/drama3\")" > /workspace/fish_dl.log 2>&1
wait
wget -q -O /workspace/drama_lines.sh $R/runpod/drama_lines.sh
bash /workspace/drama_lines.sh
