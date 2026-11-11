#!/bin/bash
# Pod setup round 3: Z-Image + LoRA -> photos (plan3); Wan 2.2; Maya1 voices. usage: LKEY=<pass> bash pod_setup5.sh
C=/workspace/runpod-slim/ComfyUI
cd $C || exit 1
PY=$C/.venv-cu128/bin/python
mkdir -p models/diffusion_models/Wan2.2 models/text_encoders models/vae models/loras /workspace/gen3 output/qa
B=https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files
W=https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files
R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main
dl() { wget -q -c -O "$1" "$2" && echo "OK $1 $(du -h "$1" | cut -f1)" || echo "FAIL $1"; }
wget -q -O /workspace/gen3/gen3.py $R/scripts/gen3.py
wget -q -O /workspace/gen3/plan.json $R/plans/gym_plan3.json
wget -q -O /workspace/gen3/maya3.py $R/scripts/maya_month3.py
( mkdir -p /tmp/lp && for i in 00 01 02 03; do wget -q -O /tmp/lp/p$i $R/bin/vl.enc.part$i; done
  cat /tmp/lp/p00 /tmp/lp/p01 /tmp/lp/p02 /tmp/lp/p03 | openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:LKEY > models/loras/vl.tmp \
    && mv models/loras/vl.tmp models/loras/valentina_vlntna_v1_000001500.safetensors
  sha256sum models/loras/valentina_vlntna_v1_000001500.safetensors; echo LORA_DONE ) > /tmp/lora.log 2>&1 &
LP=$!
( dl models/diffusion_models/z_image_turbo_bf16.safetensors $B/diffusion_models/z_image_turbo_bf16.safetensors
  dl models/text_encoders/qwen_3_4b.safetensors $B/text_encoders/qwen_3_4b.safetensors
  dl models/vae/ae.safetensors $B/vae/ae.safetensors
  echo ZIMAGE_DONE
  while kill -0 $LP 2>/dev/null; do sleep 2; done
  $PY -m pip install -q av
  cd /workspace/gen3 && $PY gen3.py photos ) > /tmp/zdl.log 2>&1 &
( dl models/diffusion_models/Wan2.2/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors $W/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
  dl models/diffusion_models/Wan2.2/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors $W/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
  dl models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors $W/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  dl models/vae/wan_2.1_vae.safetensors $W/vae/wan_2.1_vae.safetensors
  echo WAN_DONE ) > /tmp/wdl.log 2>&1 &
( $PY -m pip install -q snac soundfile accelerate
  $PY -c "from huggingface_hub import snapshot_download as s; s('maya-research/maya1'); s('hubertsiuzdak/snac_24khz'); print('MAYA_READY')"
  $PY /workspace/gen3/maya3.py ) > /tmp/maya.log 2>&1 &
wait
echo ALL_DONE
