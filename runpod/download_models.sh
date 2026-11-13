#!/usr/bin/env bash
# ComfyUI-Modelle: Z-Image Turbo (Bild) + Wan 2.2 TI2V 5B (Video). Bereits vorhandene Dateien werden übersprungen.
M=/workspace/runpod-slim/ComfyUI/models
mkdir -p $M/{diffusion_models,text_encoders,vae,loras}
dl() { [ -s "$1" ] && return; wget -q -c -O "$1.part" "$2" && mv "$1.part" "$1" && echo "OK $1"; }
ZI=https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files
WAN=https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files
dl $M/diffusion_models/z_image_turbo_bf16.safetensors $ZI/diffusion_models/z_image_turbo_bf16.safetensors
dl $M/text_encoders/qwen_3_4b.safetensors $ZI/text_encoders/qwen_3_4b.safetensors
dl $M/vae/ae.safetensors $ZI/vae/ae.safetensors
dl $M/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors $WAN/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors
dl $M/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors $WAN/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
dl $M/vae/wan2.2_vae.safetensors $WAN/vae/wan2.2_vae.safetensors
echo MODELS_DONE
