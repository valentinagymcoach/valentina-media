#!/usr/bin/env bash
# Startet Ollama, Werkzeug-Server, Open WebUI (ComfyUI startet das RunPod-Template selbst auf Port 8188).
A=/workspace/ai
C=/workspace/runpod-slim/ComfyUI
LLM=${LLM:-qwen3.8:27b}
export OLLAMA_MODELS=$A/ollama OLLAMA_HOST=127.0.0.1:11434 OLLAMA_KEEP_ALIVE=10m OLLAMA_MAX_LOADED_MODELS=1 \
       OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 OLLAMA_CONTEXT_LENGTH=32768
up() { lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }
up 11434 || nohup ollama serve > $A/logs/ollama.log 2>&1 &
sleep 3
# Werkzeug-Server für Qwen (nur intern)
up 8030 || (cd $A && nohup $C/.venv-cu128/bin/python -m uvicorn tools_server:app --host 127.0.0.1 --port 8030 > $A/logs/tools.log 2>&1 &)
# Open WebUI (über RunPod-Proxy Port 3000; Login Pflicht, das erste Konto wird Admin)
TSC='[{"type":"openapi","url":"http://127.0.0.1:8030","path":"openapi.json","auth_type":"none","key":"","config":{"enable":true},"info":{"id":"valentina","name":"Valentina-Werkzeuge","description":"Fotos, Videos, Stimme, Browser"}}]'
up 3000 || DATA_DIR=$A/open-webui WEBUI_AUTH=True ENABLE_SIGNUP=True DEFAULT_USER_ROLE=pending \
  OLLAMA_BASE_URL=http://127.0.0.1:11434 DEFAULT_MODELS=$LLM ENABLE_OPENAI_API=False \
  TOOL_SERVER_CONNECTIONS="$TSC" \
  ENABLE_IMAGE_GENERATION=True IMAGE_GENERATION_ENGINE=comfyui COMFYUI_BASE_URL=http://127.0.0.1:8188 \
  nohup $A/venvs/webui/bin/open-webui serve --host 0.0.0.0 --port 3000 > $A/logs/webui.log 2>&1 &
echo "gestartet; Status: bash $A/status.sh"
