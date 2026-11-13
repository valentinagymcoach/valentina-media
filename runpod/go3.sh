#!/usr/bin/env bash
# Pod-Neustart ohne Volume: Stack aufbauen, dann Startfotos erzeugen, VRAM-Wächter, Auto-Stopp.
cd /workspace && wget -q -O bootstrap.sh https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main/runpod/bootstrap.sh
LLM=qwen3.8:27b bash bootstrap.sh > /workspace/boot.log 2>&1
wget -q -O /workspace/ai/app_batch3.sh https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main/runpod/app_batch3.sh
for i in $(seq 60); do curl -sf 127.0.0.1:8030/health >/dev/null && curl -sf 127.0.0.1:8188/system_stats >/dev/null && break; sleep 5; done
cat > /workspace/ai/vram_guard.sh <<'G'
while true; do
  if curl -s 127.0.0.1:8188/queue | grep -q WanImageToVideo; then
    for m in $(curl -s 127.0.0.1:11434/api/ps | python3 -c 'import json,sys;[print(x["name"]) for x in json.load(sys.stdin).get("models",[])]'); do
      curl -s 127.0.0.1:11434/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" >/dev/null; done
  fi; sleep 20; done
G
(setsid nohup bash /workspace/ai/vram_guard.sh >/dev/null 2>&1 &)
bash /workspace/ai/app_batch3.sh > /workspace/ai/logs/app_batch3.log 2>&1
