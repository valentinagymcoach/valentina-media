"""Multi-Szenen-Reel aus Formkurve-Clips + Voiceover. python3 -I mkreel.py spec.json"""
import json, subprocess, sys, os
spec = json.load(open(sys.argv[1]))
FK = "/home/claude/valentina-media/formkurve/"
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
tmp = spec["tmp"]; os.makedirs(tmp, exist_ok=True)
vo = spec["vo"]
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", vo]))
total = dur + 0.9
fr = [s["f"] for s in spec["scenes"]]; tot = sum(fr)
parts = []
def esc(t): return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace(",", "\\,")
for i, s in enumerate(spec["scenes"]):
    d = total * s["f"] / tot
    z = s.get("zoom", 1.0); fx, fy = s.get("focus", (0.5, 0.5)); sp = s.get("speed", 1.0)
    W, H = int(1108 * z), int(1920 * z)
    vf = [f"setpts={1/sp:.3f}*PTS", "fps=30", f"scale={W}:{H}:flags=lanczos",
          f"crop=1080:1920:'min(max(0,{W}*{fx}-540),{W}-1080)':'min(max(0,{H}*{fy}-960),{H}-1920)'",
          f"fade=t=in:st=0:d=0.12"]
    lines = s["text"].split("\n")
    for j, ln in enumerate(lines):
        y = 300 + j * 96
        vf.append(f"drawtext=fontfile={FONT}:text='{esc(ln)}':fontsize={s.get('fs', 74)}:fontcolor=white:borderw=5:bordercolor=black@0.85:x=(w-text_w)/2:y={y}:alpha='min(1,t/0.2)'")
    vf.append(f"drawtext=fontfile={FONT}:text='AI-generated':fontsize=30:fontcolor=white@0.75:borderw=2:bordercolor=black@0.6:x=w-text_w-36:y=h-90")
    out = f"{tmp}/s{i}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", FK + s["clip"] + ".mp4", "-t", f"{d:.3f}",
                    "-vf", ",".join(vf), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], check=True)
    parts.append(out)
open(f"{tmp}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy", f"{tmp}/v.mp4"], check=True)
music = spec.get("music")
inputs = ["-i", f"{tmp}/v.mp4", "-i", vo]
fc = "[1:a]adelay=350|350,loudnorm=I=-15:TP=-1.5,apad[vo]"
if music:
    inputs += ["-i", music]
    fc += f";[2:a]volume=0.16,afade=t=out:st={total-1:.2f}:d=1[m];[vo][m]amix=inputs=2:duration=first:normalize=0[a]"
else:
    fc += ";[vo]anull[a]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-t", f"{total:.3f}",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", spec["out"]], check=True)
print("ok", spec["out"], round(total, 2))
