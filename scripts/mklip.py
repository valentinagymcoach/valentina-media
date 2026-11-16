"""Lipsync-Reel: InfiniteTalk-Clip (480x832, mit Ton) -> 1080x1920/30 fps mit getimten Kurz-Untertiteln,
Wasserzeichen «AI-generated» und leisem Musikbett.  python3 mklip.py spec.json
spec: {"vid":..., "out":..., "music":..., "y":1380, "lines":[["gesprochener Satz","KURZTEXT"], ...]}"""
import json, re, subprocess, sys

FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
S = json.load(open(sys.argv[1]))
vid, out = S["vid"], S["out"]
adur = float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=duration", "-of", "csv=p=0", vid]))
vdur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", vid]))
dur = adur
# Sprechabschnitte über Stille-Erkennung
log = subprocess.run(["ffmpeg", "-nostdin", "-i", vid, "-af", "silencedetect=noise=-32dB:d=0.22", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
sil = list(zip(st, en + [dur] * (len(st) - len(en))))
speech, cur = [], 0.0
for a, b in sil:
    if a > cur + 0.05: speech.append([cur, a])
    cur = b
if cur < dur - 0.05: speech.append([cur, dur])
tot = sum(b - a for a, b in speech)
def at(x):  # Sprechzeit x -> Videozeit
    for a, b in speech:
        if x <= b - a: return a + x
        x -= b - a
    return dur
w = [len(re.sub(r"[^A-Za-z]", "", s)) + 6 for s, _ in S["lines"]]
cues, acc = [], 0.0
for (s, cap), wi in zip(S["lines"], w):
    t0 = at(acc * tot / sum(w)); acc += wi; t1 = at(acc * tot / sum(w))
    cues.append((max(0, t0 - 0.08), t1 + 0.12, cap))
for i in range(len(cues) - 1):  # lückenlos bis zum nächsten Satz, ohne Überlappung
    cues[i] = (cues[i][0], cues[i + 1][0], cues[i][2])
esc = lambda t: t.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace(",", "\\,").replace("%", "\\%")
y = S.get("y", 1380)
vf = ["scale=-2:1920:flags=lanczos", "crop=1080:1920", "unsharp=5:5:0.5:5:5:0.0", "fps=30", "eq=saturation=1.05:contrast=1.03"]
for t0, t1, cap in cues:
    for j, ln in enumerate(cap.split("\n")):
        vf.append(f"drawtext=fontfile={FONT}:text='{esc(ln)}':fontsize={S.get('fs', 72)}:fontcolor=white:borderw=6:"
                  f"bordercolor=black@0.85:x=(w-text_w)/2:y={y + j * 92}:enable='between(t,{t0:.2f},{t1:.2f})'")
vf.append(f"drawtext=fontfile={FONT}:text='AI-generated':fontsize=30:fontcolor=white@0.75:borderw=2:bordercolor=black@0.6:x=w-text_w-36:y=h-90")
fc = (f"[0:v]{','.join(vf)}[v];[0:a]loudnorm=I=-15:TP=-1.5,aresample=48000[vo];"
      f"[1:a]volume={S.get('mvol', 0.12)},afade=t=in:d=0.8,afade=t=out:st={dur - 0.6:.2f}:d=1.2,aresample=48000[m];"
      f"[vo]apad[vop];[vop][m]amix=inputs=2:duration=longest:normalize=0[a]")
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", vid, "-stream_loop", "-1", "-i", S["music"], "-filter_complex", fc,
                "-map", "[v]", "-map", "[a]", "-t", f"{min(vdur, dur + S.get('tail', 0.6)):.2f}", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
print(out, round(dur, 2), "s,", len(cues), "captions:", [(round(a, 2), round(b, 2), c) for a, b, c in cues])
