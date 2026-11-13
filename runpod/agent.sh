#!/usr/bin/env bash
# Browser-Use-Agent im Pod: /workspace/ai/agent.sh "Aufgabe"   oder   /workspace/ai/agent.sh --file tasks/beispiel.txt
A=/workspace/ai
cd $A
export ANONYMIZED_TELEMETRY=false LLM_MODEL=${LLM_MODEL:-qwen3.8:27b} \
       ALLOWED_DOMAINS=${ALLOWED_DOMAINS:-127.0.0.1,localhost}
exec $A/venvs/agent/bin/python $A/run_agent.py "$@"
