#!/usr/bin/env bash
# KI-Stack auf EINEM RunPod-Pod (Template "ComfyUI", CUDA 12.8): Qwen3.8 (Ollama) + Open WebUI + ComfyUI
# (Z-Image + Valentina-LoRA, Wan 2.2 14B) + Maya1-Stimme + Browser-Use-Agent + Werkzeug-Server für Qwen.
# Aufruf im Pod-Terminal:  LKEY=<LoRA-Schlüssel> bash bootstrap.sh
# Ohne Volume: nach jedem Pod-Start erneut ausführen (Downloads sind schnell, ca. 10-15 min).
set -uo pipefail
A=/workspace/ai
R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main
C=/workspace/runpod-slim/ComfyUI
CPY=$C/.venv-cu128/bin/python
LLM=${LLM:-qwen3.8:27b}
mkdir -p $A/{logs,venvs,ollama,open-webui,agent_out,tasks}
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a $A/logs/bootstrap.log; }

log "System-Pakete"
apt-get update -qq && apt-get install -y -qq zstd curl git ffmpeg python3-venv lsof openssl >/dev/null 2>&1

log "Skripte holen"
for f in start.sh stop.sh status.sh tools_server.py qwen_chat.py webui_link_tools.py run_agent.py agent.sh download_models.sh; do wget -q -O $A/$f $R/runpod/$f; done
wget -q -O $A/tasks/beispiel.txt $R/runpod/beispiel.txt
chmod +x $A/*.sh

log "Ollama"
[ -x /usr/local/bin/ollama ] || curl -fsSL https://ollama.com/install.sh | sh >> $A/logs/bootstrap.log 2>&1
export OLLAMA_MODELS=$A/ollama OLLAMA_HOST=127.0.0.1:11434
pgrep -x ollama >/dev/null || (nohup ollama serve > $A/logs/ollama.log 2>&1 &)
for i in $(seq 30); do ollama list >/dev/null 2>&1 && break; sleep 2; done

log "Downloads und Installationen parallel"
( ollama pull "$LLM" ) > $A/logs/ollama_pull.log 2>&1 &
( LKEY="${LKEY:-}" bash $A/download_models.sh ) > $A/logs/models.log 2>&1 &
( [ -x $A/venvs/webui/bin/open-webui ] || { python3 -m venv $A/venvs/webui && $A/venvs/webui/bin/pip install -q open-webui; } ) > $A/logs/pip_webui.log 2>&1 &
( [ -f $A/venvs/agent/ok ] || { python3 -m venv $A/venvs/agent && $A/venvs/agent/bin/pip install -q "browser-use>=1.0,<2" playwright \
    && $A/venvs/agent/bin/playwright install --with-deps chromium && touch $A/venvs/agent/ok; } ) > $A/logs/pip_agent.log 2>&1 &
( $CPY -m pip install -q fastapi "uvicorn[standard]" snac soundfile accelerate av
  $CPY -c "from huggingface_hub import snapshot_download as s; s('maya-research/maya1'); s('hubertsiuzdak/snac_24khz'); print('MAYA_OK')"
  cd $C/custom_nodes && for r in Kosinkadink/ComfyUI-VideoHelperSuite kijai/ComfyUI-KJNodes; do
    d=${r#*/}; [ -d "$d" ] || git clone -q --depth 1 https://github.com/$r.git; [ -f "$d/requirements.txt" ] && $CPY -m pip install -q -r "$d/requirements.txt"; done
) > $A/logs/pip_tools.log 2>&1 &
wait
log "Installation fertig"
bash $A/start.sh
sleep 20
bash $A/status.sh
