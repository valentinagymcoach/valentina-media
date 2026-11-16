# Whisper-Prüfung der Sprachaufnahmen (CPU, ohne PyAV): python asr2.py
import glob, json, os, subprocess, numpy as np
from faster_whisper import WhisperModel
vd = "/workspace/runpod-slim/ComfyUI/output/voice_samples"
m = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=8)
out = {}
for f in sorted(glob.glob(f"{vd}/vo_*_s*.wav")):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(a, beam_size=5, language="en")
    t = " ".join(s.text.strip() for s in segs)
    out[os.path.basename(f)] = {"dur": round(len(a) / 16000, 2), "text": t}
    print(os.path.basename(f), out[os.path.basename(f)]["dur"], "|", t, flush=True)
json.dump(out, open("/workspace/runpod-slim/ComfyUI/output/qa/asr2.json", "w"), indent=1)
