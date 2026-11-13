#!/usr/bin/env bash
# Startet Ollama, Open WebUI und TTS (ComfyUI startet das RunPod-Template selbst auf Port 8188).
A=/workspace/ai
export OLLAMA_MODELS=$A/ollama OLLAMA_HOST=127.0.0.1:11434 OLLAMA_KEEP_ALIVE=2m OLLAMA_MAX_LOADED_MODELS=1 \
       OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0
up() { lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }
up 11434 || nohup ollama serve > $A/logs/ollama.log 2>&1 &
sleep 3
# Open WebUI auf Port 3000 (über RunPod-Proxy erreichbar, Login Pflicht; das erste Konto wird Admin)
up 3000 || DATA_DIR=$A/open-webui WEBUI_AUTH=True ENABLE_SIGNUP=True \
  OLLAMA_BASE_URL=http://127.0.0.1:11434 \
  ENABLE_IMAGE_GENERATION=True IMAGE_GENERATION_ENGINE=comfyui COMFYUI_BASE_URL=http://127.0.0.1:8188 \
  AUDIO_TTS_ENGINE=openai AUDIO_TTS_OPENAI_API_BASE_URL=http://127.0.0.1:8020/v1 AUDIO_TTS_OPENAI_API_KEY=local \
  nohup $A/venvs/webui/bin/open-webui serve --host 0.0.0.0 --port 3000 > $A/logs/webui.log 2>&1 &
# TTS nur intern (127.0.0.1), Open WebUI und Skripte sprechen es lokal an
up 8020 || (cd $A && TTS_DEVICE=${TTS_DEVICE:-cuda} nohup $A/venvs/tts/bin/uvicorn tts_app:app --host 127.0.0.1 --port 8020 > $A/logs/tts.log 2>&1 &)
echo "gestartet; Status: bash $A/status.sh"
