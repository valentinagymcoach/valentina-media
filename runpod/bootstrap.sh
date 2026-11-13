#!/usr/bin/env bash
# KI-Stack auf EINEM RunPod-Pod (Template "ComfyUI", CUDA 12.8). Docker-in-Docker gibt es auf RunPod nicht,
# deshalb laufen die Dienste als getrennte Prozesse mit eigenen Python-Umgebungen.
# Alles liegt unter /workspace -> bleibt erhalten, wenn der Pod ein Volume hat.
#   Installieren:  bash bootstrap.sh            (idempotent, kann mehrfach laufen)
#   Starten:       bash /workspace/ai/start.sh  (nach jedem Pod-Neustart)
set -uo pipefail
A=/workspace/ai
R=https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main/runpod
C=/workspace/runpod-slim/ComfyUI
CPY=$C/.venv-cu128/bin/python
OLLAMA_MODELS_LIST=${OLLAMA_MODELS_LIST:-"qwen3:14b qwen2.5vl:7b"}
mkdir -p $A/{logs,venvs,ollama,open-webui,tts_out,agent_out,tasks,loras}
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a $A/logs/bootstrap.log; }

log "System-Pakete"
apt-get update -qq && apt-get install -y -qq zstd curl git ffmpeg python3-venv lsof >/dev/null

log "Skripte holen"
for f in start.sh stop.sh status.sh tts_app.py run_agent.py agent.sh download_models.sh; do wget -q -O $A/$f $R/$f; done
chmod +x $A/*.sh
[ -f $A/tasks/beispiel.txt ] || wget -q -O $A/tasks/beispiel.txt $R/beispiel.txt

log "Ollama"
if [ ! -x /usr/local/bin/ollama ]; then curl -fsSL https://ollama.com/install.sh | sh >> $A/logs/bootstrap.log 2>&1; fi
export OLLAMA_MODELS=$A/ollama OLLAMA_HOST=127.0.0.1:11434
pgrep -x ollama >/dev/null || (nohup ollama serve > $A/logs/ollama.log 2>&1 &)
for i in $(seq 30); do ollama list >/dev/null 2>&1 && break; sleep 2; done

log "Python-Umgebungen (parallel)"
( [ -x $A/venvs/webui/bin/open-webui ] || { python3 -m venv $A/venvs/webui && $A/venvs/webui/bin/pip install -q open-webui; } ) > $A/logs/pip_webui.log 2>&1 &
( [ -f $A/venvs/tts/ok ] || { python3 -m venv $A/venvs/tts && $A/venvs/tts/bin/pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cu128 \
    && $A/venvs/tts/bin/pip install -q "git+https://github.com/huggingface/parler-tts.git" fastapi "uvicorn[standard]" soundfile && touch $A/venvs/tts/ok; } ) > $A/logs/pip_tts.log 2>&1 &
( [ -f $A/venvs/agent/ok ] || { python3 -m venv $A/venvs/agent && $A/venvs/agent/bin/pip install -q "browser-use>=1.0,<2" playwright \
    && $A/venvs/agent/bin/playwright install --with-deps chromium && touch $A/venvs/agent/ok; } ) > $A/logs/pip_agent.log 2>&1 &
( cd $C/custom_nodes && for r in Kosinkadink/ComfyUI-VideoHelperSuite city96/ComfyUI-GGUF kijai/ComfyUI-KJNodes Fannovel16/ComfyUI-Frame-Interpolation; do
    d=${r#*/}; [ -d "$d" ] || git clone -q --depth 1 https://github.com/$r.git; [ -f "$d/requirements.txt" ] && $CPY -m pip install -q -r "$d/requirements.txt"; done
  $CPY -m pip install -q gguf ) > $A/logs/nodes.log 2>&1 &
( bash $A/download_models.sh ) > $A/logs/models.log 2>&1 &
( for m in $OLLAMA_MODELS_LIST; do ollama pull "$m"; done ) > $A/logs/ollama_pull.log 2>&1 &
wait
log "Installation fertig, starte Dienste"
bash $A/start.sh
bash $A/status.sh
