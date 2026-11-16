#!/usr/bin/env bash
# Komplettes Studio auf EINEM A100-80GB-Pod: Z-Image+LoRA, Wan 2.2 14B, InfiniteTalk (Lipsync), Fish Audio Drama 3, Werkzeug-Server.
# Aufruf: LKEY=... bash go_studio.sh
set -x
R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main
C=/workspace/runpod-slim/ComfyUI; M=$C/models; CPY=$C/.venv-cu128/bin/python
A=/workspace/ai; mkdir -p $A/logs $A/app $M/{model_patches,audio_encoders,diffusion_models,loras,vae,text_encoders}
O=$C/output/voice_samples; mkdir -p $O
apt-get update -qq && apt-get install -y -qq portaudio19-dev libsox-dev ffmpeg >/dev/null 2>&1
pip install -q uv huggingface_hub
for f in tools_server.py download_models.sh drama_lines.sh it_run.py; do wget -q -O $A/$f $R/runpod/$f; done
wget -q -O /tmp/e.mp3 $R/audio/voice_samples/c2_valentina_expressive_talk.mp3 && ffmpeg -nostdin -v error -y -i /tmp/e.mp3 -ar 44100 -ac 1 $O/c2_valentina_expressive_talk.wav
# 1) Fish Audio Drama 3 (Stimme G)
( cd /workspace && git clone -q --depth 1 https://github.com/fishaudio/fish-speech.git && cd fish-speech && uv sync --python 3.12 --extra cu128 > $A/logs/fish_install.log 2>&1
  python3 -c "from huggingface_hub import snapshot_download as s; s('fishaudio/drama-3', local_dir='/workspace/drama3')" > $A/logs/fish_dl.log 2>&1
  echo FISH_READY > $A/fish.ok ) &
# 2) Bild/Video-Modelle
( LKEY="$LKEY" bash $A/download_models.sh > $A/logs/models.log 2>&1
  W=https://huggingface.co
  wget -q -c -O $M/diffusion_models/Wan2_1-I2V-14B-480p_fp8_e4m3fn_scaled_KJ.safetensors $W/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_1-I2V-14B-480p_fp8_e4m3fn_scaled_KJ.safetensors &
  wget -q -c -O $M/model_patches/wan2.1_infiniteTalk_single_fp16.safetensors $W/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/model_patches/wan2.1_infiniteTalk_single_fp16.safetensors &
  wget -q -c -O $M/audio_encoders/wav2vec2-chinese-base_fp16.safetensors $W/Kijai/wav2vec2_safetensors/resolve/main/wav2vec2-chinese-base_fp16.safetensors &
  wget -q -c -O $M/vae/Wan2_1_VAE_bf16.safetensors $W/Kijai/WanVideo_comfy/resolve/main/Wan2_1_VAE_bf16.safetensors &
  wget -q -c -O $M/loras/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors $W/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors &
  wait; echo MODELS_READY > $A/models.ok ) &
# 3) Werkzeug-Server
( $CPY -m pip install -q fastapi "uvicorn[standard]" && cd $A && RUNPOD_POD_ID=$RUNPOD_POD_ID nohup $CPY -m uvicorn tools_server:app --host 127.0.0.1 --port 8030 > $A/logs/tools.log 2>&1 & ) 
wait
# 4) Sprachaufnahmen (vor Bild/Video, damit der Grafikspeicher frei ist)
cd /workspace/fish-speech && SEEDS="7 21" bash $A/drama_lines.sh > $A/logs/vo.log 2>&1
echo STUDIO_READY > $A/studio.ok
