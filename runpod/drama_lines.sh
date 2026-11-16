#!/usr/bin/env bash
# Drama 3 Sprachaufnahmen aus vo_lines.txt (name|text), Vorlage = Stimme E
O=/workspace/runpod-slim/ComfyUI/output/voice_samples; mkdir -p $O
R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main
cd /workspace/fish-speech
REF=$O/c2_valentina_expressive_talk.wav
RT="Listen, discipline beats motivation. Show up today, even if it's just twenty minutes. Deal?"
wget -q -O /workspace/vo_lines.txt $R/runpod/vo_lines.txt
while IFS='|' read -r k txt; do
  [ -z "$k" ] && continue
  for s in 7 21; do
    d=out_${k}_$s; rm -rf $d; mkdir $d
    VIRTUAL_ENV= uv run python fish_speech/models/text2semantic/inference.py --text "$txt" --prompt-text "$RT" --prompt-audio "$REF" \
      --checkpoint-path /workspace/drama3 --codec-path /workspace/drama3/codec.pth --output-dir $d --seed $s > /workspace/vo_$k.log 2>&1
    W=$(ls $d/*.wav 2>/dev/null | head -1)
    if [ -z "$W" ]; then VIRTUAL_ENV= uv run python fish_speech/models/dac/inference.py -i "$(ls $d/*.npy | head -1)" --checkpoint-path /workspace/drama3/codec.pth -o $d/out.wav >> /workspace/vo_$k.log 2>&1; W=$d/out.wav; fi
    [ -f "$W" ] && ffmpeg -v error -y -i "$W" -ar 48000 $O/vo_${k}_s$s.wav && echo "OK $k $s" || echo "FAIL $k $s"
  done
done < /workspace/vo_lines.txt
echo VO_DONE
