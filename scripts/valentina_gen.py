#!/usr/bin/env python3
"""
valentina_gen.py – Valentina-Videos und -Fotos auf deinem RunPod-ComfyUI-Server erzeugen.
Läuft auf deinem PC (Linux/Mac/Windows), braucht nur Python 3 – keine Zusatzpakete.

BEISPIELE
  # 20 Videos aus Startbildern (Ordner mit .jpg/.png) – Prompts aus prompts_videos.json
  python3 valentina_gen.py videos --server https://DEINPOD-8188.proxy.runpod.net \
          --images ./startbilder --prompts prompts_videos.json --count 20 --out ./clips

  # 20 Fotos mit dem Valentina-LoRA – Prompts aus prompts_fotos.json
  python3 valentina_gen.py photos --server https://DEINPOD-8188.proxy.runpod.net \
          --prompts prompts_fotos.json --count 20 --out ./fotos

  # Prüfen, welche Modelle auf dem Server fehlen (und die Video-Modelle laden lassen)
  python3 valentina_gen.py check --server https://DEINPOD-8188.proxy.runpod.net --install

OPTIONAL: Server nach getaner Arbeit automatisch stoppen
  export RUNPOD_API_KEY=...   (eigenen Key in RunPod > Settings > API Keys erstellen)
  ... --stop-pod DEINPOD      (die Pod-ID, z.B. tl0mksbj8hgoqm)
"""
import argparse, json, os, random, sys, time, uuid, urllib.request, urllib.parse, urllib.error

NEG_VIDEO = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，"
             "残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，"
             "三条腿，背景人很多，倒着走, text, watermark, logo, nudity, CGI, cartoon")
REALISM = ("Smartphone video, realistic, natural lighting, natural human motion, slight handheld camera shake, "
           "toned athletic woman with long straight black hair. ")
DEFAULT_MOTIONS = [
    "She looks into the camera, raises an eyebrow and smiles confidently.",
    "She walks toward the camera with a confident stride.",
    "She ties her hair into a ponytail and looks at the camera.",
    "She stretches her arms overhead, then turns to the camera and smiles.",
    "She nods slowly at the camera, then crosses her arms.",
]
VIDEO_MODELS = {"diffusion_models": ["Wan2.2/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
                                     "Wan2.2/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"],
                "text_encoders": ["umt5_xxl_fp8_e4m3fn_scaled.safetensors"],
                "vae": ["wan_2.1_vae.safetensors"]}
PHOTO_MODELS = {"diffusion_models": ["z_image_turbo_bf16.safetensors"],
                "text_encoders": ["qwen_3_4b.safetensors"],
                "vae": ["ae.safetensors"],
                "loras": ["valentina_vlntna_v1_000001500.safetensors"]}


# ---------------------------------------------------------------- HTTP helpers
def http(url, data=None, headers=None, method=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def get_json(base, path):
    return json.loads(http(base + path))

def post_json(base, path, obj):
    return json.loads(http(base + path, json.dumps(obj).encode(), {"Content-Type": "application/json"}))

def upload_image(base, path):
    name = "vg_" + os.path.basename(path)
    boundary = uuid.uuid4().hex
    with open(path, "rb") as f:
        content = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n").encode() + content + \
           (f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue"
            f"\r\n--{boundary}--\r\n").encode()
    res = json.loads(http(base + "/upload/image", body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}))
    return res["name"]

def model_list(base, folder):
    try:
        return get_json(base, f"/api/models/{folder}")
    except Exception:
        return []


# ---------------------------------------------------------------- workflows
def wf_video(image, text, seed, prefix, width, height, frames, steps):
    half = steps // 2
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": VIDEO_MODELS["diffusion_models"][0], "weight_dtype": "default"}},
        "2": {"class_type": "UNETLoader", "inputs": {"unet_name": VIDEO_MODELS["diffusion_models"][1], "weight_dtype": "default"}},
        "3": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["1", 0], "shift": 8.0}},
        "4": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["2", 0], "shift": 8.0}},
        "5": {"class_type": "CLIPLoader", "inputs": {"clip_name": VIDEO_MODELS["text_encoders"][0], "type": "wan", "device": "default"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["5", 0], "text": text}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["5", 0], "text": NEG_VIDEO}},
        "8": {"class_type": "VAELoader", "inputs": {"vae_name": VIDEO_MODELS["vae"][0]}},
        "9": {"class_type": "LoadImage", "inputs": {"image": image}},
        "10": {"class_type": "WanImageToVideo", "inputs": {"positive": ["6", 0], "negative": ["7", 0], "vae": ["8", 0],
               "start_image": ["9", 0], "width": width, "height": height, "length": frames, "batch_size": 1}},
        "11": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["3", 0], "add_noise": "enable", "noise_seed": seed,
               "steps": steps, "cfg": 3.5, "sampler_name": "euler", "scheduler": "simple", "positive": ["10", 0],
               "negative": ["10", 1], "latent_image": ["10", 2], "start_at_step": 0, "end_at_step": half,
               "return_with_leftover_noise": "enable"}},
        "12": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["4", 0], "add_noise": "disable", "noise_seed": seed,
               "steps": steps, "cfg": 3.5, "sampler_name": "euler", "scheduler": "simple", "positive": ["10", 0],
               "negative": ["10", 1], "latent_image": ["11", 0], "start_at_step": half, "end_at_step": 10000,
               "return_with_leftover_noise": "disable"}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["8", 0]}},
        "14": {"class_type": "SaveAnimatedWEBP", "inputs": {"images": ["13", 0], "filename_prefix": "vgen/" + prefix,
               "fps": 16, "lossless": False, "quality": 92, "method": "default"}},
    }

def wf_photo(text, seed, prefix, width, height, lora, strength):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": PHOTO_MODELS["diffusion_models"][0], "weight_dtype": "default"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": lora, "strength_model": strength}},
        "3": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["2", 0], "shift": 3.0}},
        "4": {"class_type": "CLIPLoader", "inputs": {"clip_name": PHOTO_MODELS["text_encoders"][0], "type": "lumina2", "device": "default"}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": text}},
        "6": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["5", 0]}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["3", 0], "seed": seed, "steps": 8, "cfg": 1.0,
              "sampler_name": "res_multistep", "scheduler": "simple", "positive": ["5", 0], "negative": ["6", 0],
              "latent_image": ["7", 0], "denoise": 1.0}},
        "9": {"class_type": "VAELoader", "inputs": {"vae_name": PHOTO_MODELS["vae"][0]}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["9", 0]}},
        "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": "pgen/" + prefix}},
    }


# ---------------------------------------------------------------- run + download
def run_jobs(base, jobs, out, poll=15):
    """jobs: list of (name, workflow). Queues all, then downloads each result as soon as it is ready."""
    os.makedirs(out, exist_ok=True)
    client = uuid.uuid4().hex
    pending = {}
    for name, wf in jobs:
        res = post_json(base, "/prompt", {"prompt": wf, "client_id": client})
        if "prompt_id" not in res:
            print(f"  ✗ {name}: Server lehnt ab: {json.dumps(res)[:300]}")
            continue
        pending[res["prompt_id"]] = name
        print(f"  → {name} in Warteschlange")
    t0, done = time.time(), 0
    while pending:
        time.sleep(poll)
        for pid, name in list(pending.items()):
            try:
                h = get_json(base, f"/history/{pid}").get(pid)
            except Exception as e:
                print(f"  (Server nicht erreichbar: {e} – versuche weiter)")
                break
            if not h:
                continue
            status = h.get("status", {}).get("status_str")
            files = [f for node in h.get("outputs", {}).values() for k in ("images", "gifs") for f in node.get(k, [])]
            if status == "error" or not files:
                print(f"  ✗ {name}: Fehler auf dem Server")
                pending.pop(pid); continue
            for f in files:
                q = urllib.parse.urlencode({"filename": f["filename"], "subfolder": f.get("subfolder", ""), "type": f.get("type", "output")})
                ext = os.path.splitext(f["filename"])[1]
                dst = os.path.join(out, name + ext)
                with open(dst, "wb") as fh:
                    fh.write(http(base + "/view?" + q, timeout=600))
            done += 1
            pending.pop(pid)
            mins = (time.time() - t0) / 60
            print(f"  ✓ {name} gespeichert ({done}/{done + len(pending)}, {mins:.0f} min)")
    print(f"Fertig: {done} Dateien in {os.path.abspath(out)}")

def convert_webp_to_mp4(out):
    """Optional: animierte WEBP in MP4 umwandeln, wenn Pillow + ffmpeg da sind."""
    try:
        from PIL import Image
        import shutil, subprocess, tempfile
        if not shutil.which("ffmpeg"):
            return
    except ImportError:
        return
    for fn in sorted(os.listdir(out)):
        if not fn.endswith(".webp"):
            continue
        src, dst = os.path.join(out, fn), os.path.join(out, fn[:-5] + ".mp4")
        if os.path.exists(dst):
            continue
        try:
            with tempfile.TemporaryDirectory() as tmp:
                im = Image.open(src); i = 0
                try:
                    while True:
                        im.convert("RGB").save(f"{tmp}/{i:04d}.png"); i += 1; im.seek(im.tell() + 1)
                except EOFError:
                    pass
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "16", "-i", f"{tmp}/%04d.png",
                                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", dst], check=False)
            print(f"  mp4: {os.path.basename(dst)}")
        except Exception as e:
            print(f"  (mp4-Umwandlung für {fn} übersprungen: {e})")

def stop_pod(pod_id):
    key = os.environ.get("RUNPOD_API_KEY")
    if not key:
        print("RUNPOD_API_KEY nicht gesetzt – Server bitte selbst in RunPod stoppen."); return
    try:
        http(f"https://rest.runpod.io/v1/pods/{pod_id}/stop", b"", {"Authorization": f"Bearer {key}"}, method="POST")
        print(f"Server {pod_id} wird gestoppt.")
    except urllib.error.HTTPError as e:
        print(f"Stoppen fehlgeschlagen ({e.code}) – bitte selbst in RunPod stoppen.")


# ---------------------------------------------------------------- commands
def cmd_check(a):
    need = {**VIDEO_MODELS} if a.what in ("videos", "all") else {}
    if a.what in ("photos", "all"):
        for k, v in PHOTO_MODELS.items():
            need.setdefault(k, []).extend(v)
    missing = [(folder, m) for folder, ms in need.items() for m in ms if m not in model_list(a.server, folder)]
    if not missing:
        print("✓ Alle Modelle vorhanden."); return
    for folder, m in missing:
        print(f"✗ fehlt: {folder}/{m}")
    if a.install:
        print("Lasse fehlende Modelle über den ComfyUI-Manager laden (nur Modelle aus der offiziellen Liste) …")
        lst = get_json(a.server, "/externalmodel/getlist?mode=cache").get("models", [])
        for folder, m in missing:
            hit = next((x for x in lst if x.get("filename") == os.path.basename(m)), None)
            if not hit:
                print(f"  – {m}: nicht in der Manager-Liste, bitte manuell hochladen (z.B. LoRA per JupyterLab nach ComfyUI/models/loras)")
                continue
            post_json(a.server, "/manager/queue/install_model", hit); print(f"  ↓ {m}")
        http(a.server + "/manager/queue/start", b"", method="POST")
        print("Download läuft auf dem Server. In ein paar Minuten nochmals 'check' ausführen.")

def cmd_videos(a):
    imgs = sorted(os.path.join(a.images, f) for f in os.listdir(a.images) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
    if not imgs:
        sys.exit("Keine Startbilder im Ordner " + a.images)
    prompts = json.load(open(a.prompts)) if a.prompts else []
    jobs = []
    print(f"Lade Startbilder hoch und plane {a.count} Videos …")
    for i in range(a.count):
        if prompts:
            p = prompts[i % len(prompts)]
            img = os.path.join(a.images, p["image"]) if p.get("image") else imgs[i % len(imgs)]
            text = p["prompt"]
        else:
            img, text = imgs[i % len(imgs)], DEFAULT_MOTIONS[i % len(DEFAULT_MOTIONS)]
        name = f"clip_{i + 1:02d}_" + os.path.splitext(os.path.basename(img))[0]
        server_img = upload_image(a.server, img)
        jobs.append((name, wf_video(server_img, REALISM + text, random.randrange(10**12), name, a.width, a.height, a.frames, a.steps)))
    print(f"Pro Video ca. 12 Minuten auf einer A40 – {a.count} Videos ≈ {a.count * 12 / 60:.1f} Stunden.")
    run_jobs(a.server, jobs, a.out)
    convert_webp_to_mp4(a.out)
    if a.stop_pod:
        stop_pod(a.stop_pod)

def cmd_photos(a):
    prompts = json.load(open(a.prompts))
    jobs = []
    for i in range(a.count):
        text = prompts[i % len(prompts)]
        if "vlntna" not in text:
            text = "vlntna, " + text
        name = f"foto_{i + 1:02d}"
        jobs.append((name, wf_photo(text, random.randrange(10**12), name, a.width, a.height, a.lora, a.strength)))
    print(f"Plane {a.count} Fotos (je ca. 10–20 Sekunden) …")
    run_jobs(a.server, jobs, a.out, poll=5)
    if a.stop_pod:
        stop_pod(a.stop_pod)

def main():
    ap = argparse.ArgumentParser(description="Valentina-Videos/Fotos auf ComfyUI erzeugen")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("check", "videos", "photos"):
        s = sub.add_parser(n)
        s.add_argument("--server", required=True, help="z.B. https://DEINPOD-8188.proxy.runpod.net")
        s.add_argument("--stop-pod", help="Pod-ID: Server danach stoppen (braucht RUNPOD_API_KEY)")
    c = sub.choices["check"]; c.add_argument("--what", default="all", choices=["videos", "photos", "all"]); c.add_argument("--install", action="store_true")
    v = sub.choices["videos"]
    v.add_argument("--images", required=True); v.add_argument("--prompts"); v.add_argument("--count", type=int, default=20)
    v.add_argument("--out", default="./clips"); v.add_argument("--width", type=int, default=480); v.add_argument("--height", type=int, default=832)
    v.add_argument("--frames", type=int, default=81); v.add_argument("--steps", type=int, default=20)
    p = sub.choices["photos"]
    p.add_argument("--prompts", required=True); p.add_argument("--count", type=int, default=20); p.add_argument("--out", default="./fotos")
    p.add_argument("--width", type=int, default=896); p.add_argument("--height", type=int, default=1120)
    p.add_argument("--lora", default=PHOTO_MODELS["loras"][0]); p.add_argument("--strength", type=float, default=1.0)
    a = ap.parse_args()
    a.server = a.server.rstrip("/")
    {"check": cmd_check, "videos": cmd_videos, "photos": cmd_photos}[a.cmd](a)

if __name__ == "__main__":
    main()
