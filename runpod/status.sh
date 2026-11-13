#!/usr/bin/env bash
A=/workspace/ai
chk() { curl -sf -m 5 "$2" >/dev/null && echo "  OK     $1" || echo "  FEHLT  $1  (Log: $3)"; }
echo "Dienste:"
chk "ComfyUI      :8188" http://127.0.0.1:8188/system_stats "Pod-Logs"
chk "Ollama       :11434" http://127.0.0.1:11434/api/tags $A/logs/ollama.log
chk "Werkzeuge    :8030" http://127.0.0.1:8030/health $A/logs/tools.log
chk "Open WebUI   :3000" http://127.0.0.1:3000/health $A/logs/webui.log
[ -f $A/venvs/agent/ok ] && echo "  OK     Browser-Agent" || echo "  FEHLT  Browser-Agent ($A/logs/pip_agent.log)"
echo "Modelle:"; OLLAMA_HOST=127.0.0.1:11434 ollama list 2>/dev/null | sed 's/^/  /'
ls /workspace/runpod-slim/ComfyUI/models/loras/ 2>/dev/null | sed 's/^/  LoRA: /'
echo "GPU:"; nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader | sed 's/^/  /'
[ -n "${RUNPOD_POD_ID:-}" ] && echo "Oberfläche: https://${RUNPOD_POD_ID}-3000.proxy.runpod.net"
