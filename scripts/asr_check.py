# Transcribe voiceovers to verify the spoken words (QA). Runs on the GPU pod.
import glob, os, sys, json
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cuda", compute_type="float16")
out = {}
for f in sorted(glob.glob(sys.argv[1] + "/*.wav")):
    segs, _ = m.transcribe(f, beam_size=5, language="en")
    out[os.path.basename(f)] = " ".join(s.text.strip() for s in segs)
    print(os.path.basename(f), "|", out[os.path.basename(f)], flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1)
