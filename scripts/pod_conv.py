import av, glob, os, zipfile
from PIL import Image, ImageSequence
src = "/workspace/runpod-slim/ComfyUI/output/gym"
dst = "/workspace/runpod-slim/ComfyUI/output/gym_mp4"
os.makedirs(dst, exist_ok=True)
for f in sorted(glob.glob(src + "/*.webp")):
    out = os.path.join(dst, os.path.basename(f)[:-5] + ".mp4")
    if os.path.exists(out):
        continue
    im = Image.open(f)
    c = av.open(out + ".tmp.mp4", "w")
    s = c.add_stream("libx264", rate=16)
    s.width, s.height = im.size
    s.pix_fmt = "yuv420p"
    s.options = {"crf": "15", "preset": "slow"}
    n = 0
    for fr in ImageSequence.Iterator(im):
        for p in s.encode(av.VideoFrame.from_image(fr.convert("RGB"))):
            c.mux(p)
        n += 1
    for p in s.encode():
        c.mux(p)
    c.close()
    os.replace(out + ".tmp.mp4", out)
    print(os.path.basename(out), n, "frames", os.path.getsize(out) // 1024, "KB")
z = "/workspace/runpod-slim/ComfyUI/output/valentina_gym_clips.zip"
with zipfile.ZipFile(z + ".tmp", "w", zipfile.ZIP_STORED) as zf:
    for f in sorted(glob.glob(dst + "/*.mp4")):
        zf.write(f, "valentina_gym_clips/" + os.path.basename(f))
os.replace(z + ".tmp", z)
print("ZIP", os.path.getsize(z) // 1024 // 1024, "MB")
