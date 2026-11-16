#!/usr/bin/env bash
# Fish Audio Drama 3: Valentina-Stimme (Vorlage = Chatterbox-Variante E) mit Regieanweisungen
cd /workspace/fish-speech
O=/workspace/runpod-slim/ComfyUI/output/voice_samples
REF=$O/c2_valentina_expressive_talk.wav
RT="Listen, discipline beats motivation. Show up today, even if it's just twenty minutes. Deal?"
declare -A T
T[d1_drama_hype]="[excited, energetic, a little loud] Vamos! One more set. [teasing, playful] No excuses... I'm watching you."
T[d1_drama_talk]="Listen... [warm, sincere] discipline beats motivation. Show up today, even if it's just twenty minutes. [playful smile] Deal?"
T[d1_drama_calm]="[calm, soft, slow] Okay, slow down. Breathe in... [exhale] and out. Good. Form before weight, always."
for k in d1_drama_hype d1_drama_talk d1_drama_calm; do
  rm -rf out_$k; mkdir out_$k
  uv run python fish_speech/models/text2semantic/inference.py --text "${T[$k]}" --prompt-text "$RT" --prompt-audio "$REF" \
     --checkpoint-path /workspace/drama3 --codec-path /workspace/drama3/codec.pth --output-dir out_$k --seed 7 > /workspace/drama_$k.log 2>&1
  W=$(ls out_$k/*.wav 2>/dev/null | head -1)
  if [ -z "$W" ] && ls out_$k/*.npy >/dev/null 2>&1; then
    uv run python fish_speech/models/dac/inference.py -i "$(ls out_$k/*.npy | head -1)" --checkpoint-path /workspace/drama3/codec.pth -o out_$k/out.wav >> /workspace/drama_$k.log 2>&1
    W=out_$k/out.wav
  fi
  [ -n "$W" ] && [ -f "$W" ] && ffmpeg -v error -y -i "$W" -af loudnorm=I=-16:TP=-1.5 -b:a 160k $O/$k.mp3 && echo "OK $k" || { echo "FAIL $k"; tail -5 /workspace/drama_$k.log; ls out_$k; }
done
echo DRAMA_DONE
