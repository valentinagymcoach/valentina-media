#!/usr/bin/env python3
"""Nachtlauf Valentina (läuft auf dem Pod neben ComfyUI 127.0.0.1:8188).
  night.py photos              -> Startfotos aus night_plan.json, Kontaktbögen output/qa/n_<gruppe>.jpg
  night.py tts                 -> Drama-3-Sprachaufnahmen (vo_lines.txt, Seeds 7/21) + Whisper-Prüfung -> output/qa/tts.json
  night.py videos picks.json   -> Lipsync (InfiniteTalk) und Wan-2.2-Clips der Reihe nach, mp4 in output/night/, QA-Streifen
Status: output/qa/night_status.json, Log: output/qa/night_log.txt
"""
import json, os, re, subprocess, sys, time, glob, shutil, random, urllib.request

BASE = "http://127.0.0.1:8188"
C = "/workspace/runpod-slim/ComfyUI"; OUT = f"{C}/output"; QA = f"{OUT}/qa"; NV = f"{OUT}/night"
A = "/workspace/ai"; R = "https://raw.githubusercontent.com/valentinagymcoach/valentina-media/main"
for d in (QA, NV): os.makedirs(d, exist_ok=True)
LORA = "valentina_vlntna_v1_000001500.safetensors"
WAN_HI = "Wan2.2/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
WAN_LO = "Wan2.2/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
NEG = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，"
       "残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，"
       "三条腿，背景人很多，倒着走, text, watermark, logo, nudity, CGI, cartoon, duplicate barbell, second barbell, extra dumbbell, "
       "extra weights, objects appearing, objects disappearing, equipment merging with body, weights floating, extra limbs, "
       "camera movement, zoom, cut, scene change, bad exercise form, rounded back, wrist rotation, swinging legs")
REAL = {"gym": ("Realistic gym video filmed on a tripod, static camera, the whole body stays in frame, natural lighting, natural human "
                "motion, real physics of the weights. Toned athletic woman with long straight black hair. "),
        "life": ("Realistic smartphone video, cinematic, natural lighting, natural human motion, real physics. "
                 "Fit young woman with long straight black hair. ")}


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    open(f"{QA}/night_log.txt", "a").write(s + "\n")


def req(path, obj=None, timeout=60):
    data = json.dumps(obj).encode() if obj is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(r, timeout=timeout) as x:
        return json.loads(x.read())


def run(wf, name, limit=3600, poll=5):
    r = req("/prompt", {"prompt": wf, "client_id": "night"})
    if "prompt_id" not in r:
        log("REJECTED", name, json.dumps(r)[:600]); return []
    pid, t0 = r["prompt_id"], time.time()
    while time.time() - t0 < limit:
        time.sleep(poll)
        try:
            h = req(f"/history/{pid}").get(pid)
        except Exception as e:  # noqa: BLE001
            log("history", e); continue
        if not h: continue
        if h.get("status", {}).get("status_str") == "error":
            log("ERROR", name, json.dumps(h["status"].get("messages", []))[-800:]); return []
        return [os.path.join(OUT, f.get("subfolder", ""), f["filename"])
                for n in h.get("outputs", {}).values() for k in ("images", "videos", "gifs") for f in n.get(k, [])]
    log("TIMEOUT", name); return []


def wf_photo(text, seed, prefix, w, h):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": LORA, "strength_model": 1.0}},
        "3": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["2", 0], "shift": 3.0}},
        "4": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": text}},
        "6": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["5", 0]}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["3", 0], "seed": seed, "steps": 8, "cfg": 1.0,
              "sampler_name": "res_multistep", "scheduler": "simple", "positive": ["5", 0], "negative": ["6", 0],
              "latent_image": ["7", 0], "denoise": 1.0}},
        "9": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["9", 0]}},
        "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": "night/p/" + prefix}},
    }


def wf_wan(image, text, seed, prefix, w=480, h=832, steps=20):
    half = steps // 2
    wf = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": WAN_HI, "weight_dtype": "default"}},
        "2": {"class_type": "UNETLoader", "inputs": {"unet_name": WAN_LO, "weight_dtype": "default"}},
        "3": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["1", 0], "shift": 8.0}},
        "4": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["2", 0], "shift": 8.0}},
        "5": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["5", 0], "text": text}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["5", 0], "text": NEG}},
        "8": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
        "9": {"class_type": "LoadImage", "inputs": {"image": image}},
        "10": {"class_type": "WanImageToVideo", "inputs": {"positive": ["6", 0], "negative": ["7", 0], "vae": ["8", 0],
               "start_image": ["9", 0], "width": w, "height": h, "length": 81, "batch_size": 1}},
        "11": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["3", 0], "add_noise": "enable", "noise_seed": seed,
               "steps": steps, "cfg": 3.5, "sampler_name": "euler", "scheduler": "simple", "positive": ["10", 0],
               "negative": ["10", 1], "latent_image": ["10", 2], "start_at_step": 0, "end_at_step": half,
               "return_with_leftover_noise": "enable"}},
        "12": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["4", 0], "add_noise": "disable", "noise_seed": seed,
               "steps": steps, "cfg": 3.5, "sampler_name": "euler", "scheduler": "simple", "positive": ["10", 0],
               "negative": ["10", 1], "latent_image": ["11", 0], "start_at_step": half, "end_at_step": 10000,
               "return_with_leftover_noise": "disable"}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["8", 0]}},
        "14": {"class_type": "CreateVideo", "inputs": {"images": ["13", 0], "fps": 16}},
        "15": {"class_type": "SaveVideo", "inputs": {"video": ["14", 0], "filename_prefix": "night/raw/" + prefix, "format": "mp4", "codec": "h264"}},
    }
    return wf


def sheet(items, dst, cols=6, tw=200):
    from PIL import Image, ImageDraw
    ims = []
    for name, path in items:
        im = Image.open(path).convert("RGB"); im = im.resize((tw, int(im.height * tw / im.width)))
        d = ImageDraw.Draw(im); d.rectangle([0, 0, tw, 16], fill=(0, 0, 0)); d.text((3, 2), name[:32], fill=(255, 255, 0))
        ims.append(im)
    if not ims: return
    th = max(i.height for i in ims); rows = -(-len(ims) // cols)
    S = Image.new("RGB", (cols * tw, rows * th), (40, 40, 40))
    for i, im in enumerate(ims): S.paste(im, ((i % cols) * tw, (i // cols) * th))
    S.save(dst, quality=90)


def status(**kw):
    p = f"{QA}/night_status.json"
    s = json.load(open(p)) if os.path.exists(p) else {}
    s.update(kw); s["updated"] = time.strftime("%H:%M:%S")
    json.dump(s, open(p, "w"), indent=1)


def cmd_photos():
    if not os.path.exists(f"{A}/night_plan.json"):
        urllib.request.urlretrieve(f"{R}/runpod/night_plan.json", f"{A}/night_plan.json")
    plan = json.load(open(f"{A}/night_plan.json"))
    files = {}
    for g in plan["photos"]:
        items = []
        for i in range(g["n"]):
            nm = f"{g['name']}_{i}"
            fl = run(wf_photo(g["text"], 4242 + i * 7919 + len(g["name"]) * 131, nm, g["w"], g["h"]), nm, 300, 1)
            if fl:
                files[nm] = fl[0]; items.append((nm, fl[0]))
        sheet(items, f"{QA}/n_{g['name']}.jpg", cols=len(items) if len(items) <= 6 else 6)
        log("sheet", g["name"], len(items))
    json.dump(files, open(f"{A}/night_photos.json", "w"), indent=1)
    status(photos="done", n_photos=len(files))
    log("PHOTOS_DONE", len(files))


def cmd_tts():
    vd = f"{OUT}/voice_samples"; os.makedirs(vd, exist_ok=True)
    urllib.request.urlretrieve(f"{R}/runpod/vo_lines.txt", "/workspace/vo_lines.txt")
    ref = f"{vd}/c2_valentina_expressive_talk.wav"
    if not os.path.exists(ref):
        urllib.request.urlretrieve(f"{R}/audio/voice_samples/c2_valentina_expressive_talk.mp3", "/tmp/e.mp3")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", "/tmp/e.mp3", "-ar", "44100", "-ac", "1", ref])
    rt = "Listen, discipline beats motivation. Show up today, even if it's just twenty minutes. Deal?"
    env = dict(os.environ); env.pop("VIRTUAL_ENV", None)
    lines = [l.strip().split("|", 1) for l in open("/workspace/vo_lines.txt") if "|" in l]
    only = set(filter(None, os.environ.get("TTS_ONLY", "").split(",")))
    seeds = [int(x) for x in os.environ.get("TTS_SEEDS", "7,21").split(",")]
    for k, txt in lines:
        if only and k not in only: continue
        for s in seeds:
            if os.path.exists(f"{vd}/vo_{k}_s{s}.wav"): continue
            d = f"/workspace/fish-speech/out_{k}_{s}"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
            subprocess.run(["uv", "run", "python", "fish_speech/models/text2semantic/inference.py", "--text", txt,
                            "--prompt-text", rt, "--prompt-audio", ref, "--checkpoint-path", "/workspace/drama3",
                            "--codec-path", "/workspace/drama3/codec.pth", "--output-dir", d, "--seed", str(s)],
                           cwd="/workspace/fish-speech", env=env, stdout=open(f"/workspace/vo_{k}.log", "a"),
                           stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
            w = sorted(glob.glob(f"{d}/*.wav"))
            if not w and glob.glob(f"{d}/*.npy"):
                subprocess.run(["uv", "run", "python", "fish_speech/models/dac/inference.py", "-i", sorted(glob.glob(f"{d}/*.npy"))[0],
                                "--checkpoint-path", "/workspace/drama3/codec.pth", "-o", f"{d}/out.wav"],
                               cwd="/workspace/fish-speech", env=env, stdout=open(f"/workspace/vo_{k}.log", "a"),
                               stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
                w = [f"{d}/out.wav"]
            if w and os.path.exists(w[0]):
                subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", w[0], "-ar", "48000", f"{vd}/vo_{k}_s{s}.wav"])
                log("tts ok", k, s)
            else:
                log("tts FAIL", k, s)
    # Whisper-Prüfung (CPU)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "faster-whisper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    from faster_whisper import WhisperModel
    m = WhisperModel("small.en", device="cpu", compute_type="int8")
    norm = lambda t: re.sub(r"[^a-z ]", " ", re.sub(r"\[[^\]]*\]", " ", t.lower())).split()
    res = {}
    for k, txt in lines:
        want = norm(txt); res[k] = {}
        for s in (7, 21):
            f = f"{vd}/vo_{k}_s{s}.wav"
            if not os.path.exists(f): continue
            segs, info = m.transcribe(f, beam_size=5, language="en")
            heard = " ".join(x.text.strip() for x in segs)
            got = norm(heard)
            hit = sum(1 for wd in want if wd in got) / max(1, len(want))
            extra = max(0, len(got) - len(want)) / max(1, len(want))
            dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
            res[k][s] = {"heard": heard, "score": round(hit - extra, 3), "dur": round(dur, 2)}
            log("asr", k, s, res[k][s]["score"], dur, heard[:120])
        if res[k]:
            res[k]["best"] = max((x for x in res[k] if x != "best"), key=lambda s: res[k][s]["score"])
    json.dump(res, open(f"{QA}/tts.json", "w"), indent=1)
    status(tts="done")
    log("TTS_DONE")


def qa_strip(mp4, name):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", mp4, "-vf", "fps=2,scale=150:-1,tile=11x3",
                    "-frames:v", "1", f"{QA}/v_{name}.jpg"])


def cmd_videos(picks_path):
    picks = json.load(open(picks_path))
    photos = json.load(open(f"{A}/night_photos.json"))
    tts = json.load(open(f"{QA}/tts.json")) if os.path.exists(f"{QA}/tts.json") else {}
    done = []
    status(videos="running", total=len(picks["jobs"]), done=done)
    for j in picks["jobs"]:
        name, t0 = j["name"], time.time()
        if os.path.exists(f"{NV}/{name}.mp4"):
            done.append(name); continue
        src = photos[j["photo"]]
        status(current=name, started=time.strftime("%H:%M:%S"))
        if j["type"] == "lip":
            k = j["audio"]; s = j.get("take") or tts.get(k, {}).get("best", 7)
            aud = f"vo_{k}_s{s}.wav"
            img = f"{j['photo']}.png"; shutil.copy(src, f"{C}/input/{img}")
            if j.get("crop"):  # [x, y, w] -> Ausschnitt im Seitenverhältnis 480:832 (näher ans Gesicht)
                from PIL import Image
                x, y, w = j["crop"]; im = Image.open(src).convert("RGB")
                img = f"{j['photo']}_c.png"
                im.crop((x, y, x + w, y + round(w * 832 / 480))).resize((480, 832), Image.LANCZOS).save(f"{C}/input/{img}")
            p = subprocess.run([sys.executable, f"{A}/it_run.py", "run", img, aud, j["prompt"], name, str(j.get("seed", 7))],
                               capture_output=True, text=True)
            outs = [l.split()[1:3] for l in p.stdout.splitlines() if l.startswith("OUT")]
            fl = [os.path.join(OUT, a, b) for a, b in outs]
            if not fl: log("lip ERROR", name, p.stdout[-600:], p.stderr[-600:])
        else:
            rel = os.path.relpath(src, OUT)
            fl = run(wf_wan(f"{rel} [output]", REAL[j.get("kind", "gym")] + j["motion"], j.get("seed") or random.randint(1, 2**31), name), name)
        if fl:
            shutil.copy(fl[0], f"{NV}/{name}.mp4"); qa_strip(f"{NV}/{name}.mp4", name)
            done.append(name); log("DONE", name, round(time.time() - t0), "s")
        status(done=done)
    status(videos="done", current=None)
    log("VIDEOS_DONE", len(done))


if __name__ == "__main__":
    {"photos": cmd_photos, "tts": cmd_tts, "videos": lambda: cmd_videos(sys.argv[2])}[sys.argv[1]]()
