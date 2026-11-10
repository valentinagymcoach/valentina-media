#!/bin/bash
C=/workspace/runpod-slim/ComfyUI
cd $C || exit 1
PY=$C/.venv-cu128/bin/python
B=https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files
( wget -q -c -O models/diffusion_models/z_image_turbo_bf16.safetensors $B/diffusion_models/z_image_turbo_bf16.safetensors
  wget -q -c -O models/text_encoders/qwen_3_4b.safetensors $B/text_encoders/qwen_3_4b.safetensors
  wget -q -c -O models/vae/ae.safetensors $B/vae/ae.safetensors
  echo ZIMAGE_DONE ) > /tmp/zdl.log 2>&1 &
( while [ ! -f input/vlora_done.bin ]; do sleep 10; done; sleep 3
  cat $(ls input/vlora_part*.bin | sort) > models/loras/vl.tmp && mv models/loras/vl.tmp models/loras/valentina_vlntna_v1_000001500.safetensors && rm -f input/vlora_part*.bin
  ls -la models/loras; echo LORA_OK ) > /tmp/lora.log 2>&1 &
( mkdir -p /workspace/voice2 && cd /workspace/voice2 && \
  for n in $(seq 4 12); do for i in 1 2 3 4 5; do f=vo2_r${n}_${i}.wav; wget -q -O $f https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main/audio/voice2/$f || rm -f $f; done; done
  $PY -m pip install -q faster-whisper && wget -q -O /tmp/asr.py https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main/scripts/asr_check.py && \
  $PY /tmp/asr.py /workspace/voice2 /workspace/voice2/asr.json ) > /tmp/asr.log 2>&1 &
wait; echo ALL_DONE >> /tmp/zdl.log
