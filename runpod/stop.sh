#!/usr/bin/env bash
pkill -f "open-webui serve"; pkill -f "uvicorn tools_server"; pkill -x ollama; echo "gestoppt (ComfyUI läuft weiter)"
