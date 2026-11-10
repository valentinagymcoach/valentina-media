#!/bin/bash
# Pod setup: Z-Image + Wan 2.2 models, encrypted LoRA, gen3 driver.
# usage: LKEY=<passphrase> bash pod_setup4.sh
C=/workspace/runpod-slim/ComfyUI
cd $C || exit 1
mkdir -p models/diffusion_models/Wan2.2 models/text_encoders models/vae models/loras /workspace/gen3
B=https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files
W=https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files
R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main
dl() { wget -q -c -O "$1" "$2" && echo "OK $1 $(du -h "$1" | cut -f1)" || echo "FAIL $1"; }
( dl models/diffusion_models/z_image_turbo_bf16.safetensors $B/diffusion_models/z_image_turbo_bf16.safetensors
  dl models/text_encoders/qwen_3_4b.safetensors $B/text_encoders/qwen_3_4b.safetensors
  dl models/vae/ae.safetensors $B/vae/ae.safetensors
  echo ZIMAGE_DONE ) > /tmp/zdl.log 2>&1 &
( dl models/diffusion_models/Wan2.2/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors $W/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
  dl models/diffusion_models/Wan2.2/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors $W/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
  dl models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors $W/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
  dl models/vae/wan_2.1_vae.safetensors $W/vae/wan_2.1_vae.safetensors
  echo WAN_DONE ) > /tmp/wdl.log 2>&1 &
( mkdir -p /tmp/lp && for i in 00 01 02 03; do wget -q -O /tmp/lp/p$i $R/bin/vl.enc.part$i; done
  cat /tmp/lp/p00 /tmp/lp/p01 /tmp/lp/p02 /tmp/lp/p03 | openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:LKEY > models/loras/vl.tmp \
    && mv models/loras/vl.tmp models/loras/valentina_vlntna_v1_000001500.safetensors
  sha256sum models/loras/valentina_vlntna_v1_000001500.safetensors
  echo LORA_DONE ) > /tmp/lora.log 2>&1 &
wget -q -O /workspace/gen3/gen3.py $R/scripts/gen3.py
wget -q -O /workspace/gen3/plan.json $R/plans/gym_plan2.json
wait
echo ALL_DONE
cat /tmp/zdl.log /tmp/wdl.log /tmp/lora.log
