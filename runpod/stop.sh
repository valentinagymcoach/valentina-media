#!/usr/bin/env bash
pkill -f "open-webui serve"; pkill -f "uvicorn tts_app"; pkill -x ollama; echo "Ollama, Open WebUI, TTS gestoppt (ComfyUI läuft weiter)"
