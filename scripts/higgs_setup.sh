#!/bin/bash
# Higgs Audio v2 (open source, Apache-2.0) in its own venv; voice described in text, no real person.
set -x
cd /workspace && [ -d higgs-audio ] || git clone -q https://github.com/boson-ai/higgs-audio.git
python -m venv /workspace/hvenv && . /workspace/hvenv/bin/activate
pip install -q --upgrade pip
pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cu124
cd /workspace/higgs-audio && pip install -q -r requirements.txt && pip install -q -e . && echo HIGGS_INSTALLED
cat >> examples/voice_prompts/profile.yaml <<'Y'
  valentina: "feminine, young adult woman in her twenties, latina with a light natural Spanish accent, warm and slightly husky low voice, confident, calm and teasing, speaks clearly at a relaxed pace like a personal fitness coach"
Y
mkdir -p /workspace/voice/out/v4
T1="You said tomorrow? Well, it's tomorrow. Four sets, no excuses. Vamos! Don't look at me like that. One more rep, I'm watching you."
for s in 1 2; do
python examples/generation.py --transcript "$T1" --ref_audio profile:valentina --scene_prompt examples/scene_prompts/quiet_indoor.txt \
  --temperature 0.4 --seed $s --out_path /workspace/voice/out/v4/higgs_valentina_$s.wav
done
echo HIGGS_DONE
