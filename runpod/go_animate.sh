#!/usr/bin/env bash
# Frischer Pod (>=80 GB VRAM): Wan 2.2 Animate einrichten. Bewegungsvorlagen (motion/*.mp4) + Startfotos (formkurve/*.jpg) holen.
# Aufruf: bash go_animate.sh   → Protokoll /workspace/setup.log, am Ende SETUP_DONE
cd /workspace
R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main
( apt-get update -qq && apt-get install -y -qq ffmpeg git-lfs ) >/dev/null 2>&1
[ -d Wan2.2 ] || git clone -q --depth 1 https://github.com/Wan-Video/Wan2.2.git
cd Wan2.2
pip install -q -r requirements.txt 2>&1 | tail -2
[ -f requirements_animate.txt ] && pip install -q -r requirements_animate.txt 2>&1 | tail -2
pip install -q "huggingface_hub[cli]" hf_transfer 2>&1 | tail -1
export HF_HUB_ENABLE_HF_TRANSFER=1
python3 -c "from huggingface_hub import snapshot_download as s; s('Wan-AI/Wan2.2-Animate-14B', local_dir='/workspace/Wan2.2/Wan2.2-Animate-14B')" 2>&1 | tail -2
mkdir -p /workspace/in /workspace/out /workspace/www
declare -A P=( [deadlift]=deadlift [ohp]=barbell_overhead_press [cablerow]=seated_cable_row [pushdown]=triceps_pushdown [lunge]=dumbbell_lunge [inclinedb]=incline_dumbbell_press )
for id in deadlift legpress ohp hipthrust cablerow pushdown legcurl lunge inclinedb chestpress; do
  wget -q -O /workspace/in/$id.mp4 $R/motion/$id.mp4
  [ -n "${P[$id]}" ] && wget -q -O /workspace/in/$id.jpg $R/formkurve/${P[$id]}.jpg
done
wget -q -O /workspace/in/face.jpg $R/src/s01.jpg
ls -la /workspace/in | tail -20; du -sh /workspace/Wan2.2/Wan2.2-Animate-14B; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
(cd /workspace/www && nohup python3 -m http.server 8000 >/dev/null 2>&1 &)
echo SETUP_DONE
