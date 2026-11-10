#!/bin/bash
# Setup for a fresh ComfyUI pod: Z-Image models, LoRA assembly from browser-uploaded parts, Maya1 TTS deps.
C=/workspace/runpod-slim/ComfyUI
cd $C || exit 1
PY=$C/.venv-cu128/bin/python
B=https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files
(
  wget -q -c -O models/diffusion_models/z_image_turbo_bf16.safetensors $B/diffusion_models/z_image_turbo_bf16.safetensors
  wget -q -c -O models/text_encoders/qwen_3_4b.safetensors $B/text_encoders/qwen_3_4b.safetensors
  wget -q -c -O models/vae/ae.safetensors $B/vae/ae.safetensors
  echo ZIMAGE_DONE
) > /tmp/zdl.log 2>&1 &
(
  while [ ! -f input/vlora_done.bin ]; do sleep 10; done; sleep 3
  cat $(ls input/vlora_part*.bin | sort) > models/loras/vl.tmp && mv models/loras/vl.tmp models/loras/valentina_vlntna_v1_000001500.safetensors && rm -f input/vlora_part*.bin
  ls -la models/loras; echo LORA_OK
) > /tmp/lora.log 2>&1 &
(
  $PY -m pip install -q snac soundfile accelerate
  $PY -c "from huggingface_hub import snapshot_download as s; s('maya-research/maya1'); s('hubertsiuzdak/snac_24khz'); print('MAYA_READY')"
) > /tmp/maya.log 2>&1 &
wait
echo ALL_DONE >> /tmp/zdl.log
