#!/usr/bin/env bash
# Browser-Use-Agent im Pod: /workspace/ai/agent.sh "Aufgabe"   oder   /workspace/ai/agent.sh --file tasks/beispiel.txt
A=/workspace/ai
cd $A
export ANONYMIZED_TELEMETRY=false LLM_MODEL=${LLM_MODEL:-qwen3.8:27b} \
       ALLOWED_DOMAINS=${ALLOWED_DOMAINS:-} \
       BLOCKED_DOMAINS=${BLOCKED_DOMAINS:-instagram.com,*.instagram.com,facebook.com,*.facebook.com,threads.net,*.threads.net}
exec $A/venvs/agent/bin/python $A/run_agent.py "$@"
