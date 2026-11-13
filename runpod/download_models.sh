#!/usr/bin/env bash
# Z-Image Turbo + Valentina-LoRA (verschlüsselt im Repo, Schlüssel per LKEY) + Wan 2.2 I2V 14B fp8
M=/workspace/runpod-slim/ComfyUI/models
R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main
mkdir -p $M/{diffusion_models/Wan2.2,text_encoders,vae,loras}
dl() { [ -s "$1" ] && return; wget -q -c -O "$1.part" "$2" && mv "$1.part" "$1" && echo "OK $1"; }
ZI=https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files
WAN=https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files
dl $M/diffusion_models/z_image_turbo_bf16.safetensors $ZI/diffusion_models/z_image_turbo_bf16.safetensors &
dl $M/text_encoders/qwen_3_4b.safetensors $ZI/text_encoders/qwen_3_4b.safetensors &
dl $M/vae/ae.safetensors $ZI/vae/ae.safetensors &
dl $M/diffusion_models/Wan2.2/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors $WAN/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors &
dl $M/diffusion_models/Wan2.2/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors $WAN/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors &
dl $M/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors $WAN/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors &
dl $M/vae/wan_2.1_vae.safetensors $WAN/vae/wan_2.1_vae.safetensors &
L=$M/loras/valentina_vlntna_v1_000001500.safetensors
if [ ! -s $L ] && [ -n "${LKEY:-}" ]; then
  for i in 00 01 02 03; do wget -q -O /tmp/vl$i $R/bin/vl.enc.part$i; done
  cat /tmp/vl00 /tmp/vl01 /tmp/vl02 /tmp/vl03 | openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:LKEY > $L.tmp && mv $L.tmp $L && echo "OK LoRA"
  rm -f /tmp/vl0*
fi
wait
echo MODELS_DONE
