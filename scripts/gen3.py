#!/usr/bin/env python3
"""On-pod generator for Valentina (runs next to ComfyUI, talks to 127.0.0.1:8188).
  gen3.py photos            -> all photos of plan.json, contact sheets in output/qa/
  gen3.py videos picks.json -> 10 s exercise clips (2 chained Wan 2.2 segments) from picked photos,
                               mp4 + QA strips in output/gen3_mp4 and output/qa/
  gen3.py pack              -> output/gen3_pack.zip (mp4s + all photos)
Log: output/qa/log.txt (readable via /view?filename=log.txt&subfolder=qa&type=output)
"""
import json, os, sys, time, random, zipfile, urllib.request, urllib.parse

BASE = "http://127.0.0.1:8188"
C = "/workspace/runpod-slim/ComfyUI"
OUT = f"{C}/output"
W = "/workspace/gen3"
QA = f"{OUT}/qa"
MP4 = f"{OUT}/gen3_mp4"
os.makedirs(QA, exist_ok=True); os.makedirs(MP4, exist_ok=True)
LORA = "valentina_vlntna_v1_000001500.safetensors"
WAN_HI = "Wan2.2/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
WAN_LO = "Wan2.2/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
NEG = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，"
       "残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，"
       "三条腿，背景人很多，倒着走, text, watermark, logo, nudity, CGI, cartoon, duplicate barbell, second barbell, extra dumbbell, "
       "extra weights, objects appearing, objects disappearing, equipment merging with body, weights floating, extra limbs, "
       "camera movement, zoom, cut, scene change, bad exercise form, rounded back")
REAL = ("Realistic gym video filmed on a tripod, static camera, the whole body stays in frame, natural lighting, natural human "
        "motion, real physics of the weights. Toned athletic woman with long straight black hair in a high ponytail. ")


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(f"{QA}/log.txt", "a") as f:
        f.write(s + "\n")


def req(path, obj=None, timeout=60):
    data = json.dumps(obj).encode() if obj is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(r, timeout=timeout) as x:
        return json.loads(x.read())


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
        "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": "gen3p/" + prefix}},
    }


def sampler_pair(wf, k, cond, seed, steps=20):
    """two-stage Wan 2.2 sampling: nodes k (high noise) and k+1 (low noise) on WanImageToVideo node `cond`."""
    half = steps // 2
    wf[str(k)] = {"class_type": "KSamplerAdvanced", "inputs": {"model": ["3", 0], "add_noise": "enable", "noise_seed": seed,
                  "steps": steps, "cfg": 3.5, "sampler_name": "euler", "scheduler": "simple", "positive": [cond, 0],
                  "negative": [cond, 1], "latent_image": [cond, 2], "start_at_step": 0, "end_at_step": half,
                  "return_with_leftover_noise": "enable"}}
    wf[str(k + 1)] = {"class_type": "KSamplerAdvanced", "inputs": {"model": ["4", 0], "add_noise": "disable", "noise_seed": seed,
                      "steps": steps, "cfg": 3.5, "sampler_name": "euler", "scheduler": "simple", "positive": [cond, 0],
                      "negative": [cond, 1], "latent_image": [str(k), 0], "start_at_step": half, "end_at_step": 10000,
                      "return_with_leftover_noise": "disable"}}


def wf_chain(image, text, seed, prefix, w=480, h=832):
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
    }
    sampler_pair(wf, 11, "10", seed)
    wf["13"] = {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["8", 0]}}
    wf["20"] = {"class_type": "ImageFromBatch", "inputs": {"image": ["13", 0], "batch_index": 80, "length": 1}}
    wf["22"] = {"class_type": "WanImageToVideo", "inputs": {"positive": ["6", 0], "negative": ["7", 0], "vae": ["8", 0],
                "start_image": ["20", 0], "width": w, "height": h, "length": 81, "batch_size": 1}}
    sampler_pair(wf, 23, "22", seed + 1)
    wf["25"] = {"class_type": "VAEDecode", "inputs": {"samples": ["24", 0], "vae": ["8", 0]}}
    wf["26"] = {"class_type": "ImageFromBatch", "inputs": {"image": ["25", 0], "batch_index": 1, "length": 80}}
    wf["27"] = {"class_type": "ImageBatch", "inputs": {"image1": ["13", 0], "image2": ["26", 0]}}
    wf["28"] = {"class_type": "SaveAnimatedWEBP", "inputs": {"images": ["27", 0], "filename_prefix": "gen3v/" + prefix,
                "fps": 16, "lossless": False, "quality": 92, "method": "default"}}
    return wf


def queue(jobs):
    ids = {}
    for name, wf in jobs:
        r = req("/prompt", {"prompt": wf, "client_id": "gen3"})
        if "prompt_id" not in r:
            log("REJECTED", name, json.dumps(r)[:400]); continue
        ids[r["prompt_id"]] = name
        log("queued", name)
    return ids


def wait(ids, on_done=None, poll=10):
    files = {}
    while ids:
        time.sleep(poll)
        for pid, name in list(ids.items()):
            try:
                h = req(f"/history/{pid}").get(pid)
            except Exception as e:
                log("history error", e); break
            if not h:
                continue
            st = h.get("status", {}).get("status_str")
            fl = [f for n in h.get("outputs", {}).values() for k in ("images", "gifs") for f in n.get(k, [])]
            ids.pop(pid)
            if st == "error" or not fl:
                msgs = [m for m in h.get("status", {}).get("messages", []) if m[0] == "execution_error"]
                log("ERROR", name, json.dumps(msgs)[:600]); continue
            f = fl[0]
            files[name] = os.path.join(OUT, f.get("subfolder", ""), f["filename"])
            log("done", name, files[name], f"({len(ids)} left)")
            if on_done:
                try:
                    on_done(name, files[name])
                except Exception as e:
                    log("post-process error", name, e)
    return files


def sheet(items, dst, cols=7, tw=216):
    from PIL import Image, ImageDraw
    ims = []
    for name, path in items:
        im = Image.open(path).convert("RGB")
        th = int(im.height * tw / im.width)
        im = im.resize((tw, th))
        ImageDraw.Draw(im).rectangle([0, 0, tw, 18], fill=(0, 0, 0))
        ImageDraw.Draw(im).text((4, 3), name[:34], fill=(255, 255, 0))
        ims.append(im)
    if not ims:
        return
    th = max(i.height for i in ims); rows = -(-len(ims) // cols)
    S = Image.new("RGB", (cols * tw, rows * th), (40, 40, 40))
    for i, im in enumerate(ims):
        S.paste(im, ((i % cols) * tw, (i // cols) * th))
    S.save(dst, quality=88)
    log("sheet", dst)


def webp_frames(path):
    from PIL import Image
    im = Image.open(path); fr = []
    try:
        while True:
            n = max(1, round(im.info.get("duration", 62.5) / 62.5))  # merged duplicate frames carry longer durations
            f = im.convert("RGB").copy(); fr.extend([f] * n); im.seek(im.tell() + 1)
    except EOFError:
        pass
    return fr


def post_video(name, path):
    import av
    fr = webp_frames(path)
    dst = f"{MP4}/{name}.mp4"
    c = av.open(dst, "w")
    s = c.add_stream("libx264", rate=16)
    s.width, s.height, s.pix_fmt = fr[0].width, fr[0].height, "yuv420p"
    s.options = {"crf": "15", "preset": "slow"}
    for im in fr:
        for p in s.encode(av.VideoFrame.from_image(im)):
            c.mux(p)
    for p in s.encode():
        c.mux(p)
    c.close()
    log("mp4", dst, len(fr), "frames")
    # QA strips: every 4th frame, two sheets (0-80 / 80-160), labeled with time
    for part, rng in (("a", range(0, 81, 4)), ("b", range(80, len(fr), 4))):
        items = [(f"t={i / 16:.2f}s", _tmp_save(fr[i], i)) for i in rng if i < len(fr)]
        sheet(items, f"{QA}/{name}_{part}.jpg", cols=7, tw=216)


def _tmp_save(im, i):
    p = f"/tmp/qa_{i:04d}.png"; im.save(p); return p


def cmd_photos():
    plan = json.load(open(f"{W}/plan.json"))
    jobs = []
    for i, p in enumerate(plan["photos"]):
        seed = 1000 + i * 7919
        jobs.append((p["name"], wf_photo(p["text"], seed, p["name"], p["w"], p["h"])))
    files = wait(queue(jobs), poll=5)
    json.dump(files, open(f"{W}/photos.json", "w"), indent=1)
    ex = [(n, f) for n, f in files.items() if n.startswith("p_")]
    fe = [(n, f) for n, f in files.items() if n.startswith("f_")]
    sheet(ex, f"{QA}/sheet_ex.jpg", cols=7, tw=216)
    sheet(fe[:12], f"{QA}/sheet_feed1.jpg", cols=6, tw=252)
    sheet(fe[12:], f"{QA}/sheet_feed2.jpg", cols=6, tw=252)
    log("PHOTOS_DONE", len(files))


def cmd_videos(picks_path):
    plan = json.load(open(f"{W}/plan.json"))
    photos = json.load(open(f"{W}/photos.json"))
    picks = json.load(open(picks_path))
    jobs = []
    for ex, pname in picks.items():
        name = pname if isinstance(pname, str) else pname[0]
        rel = os.path.relpath(photos[name], OUT)
        seed = random.randint(1, 2**31)
        text = REAL + plan["videos"][ex]
        jobs.append((f"v3_{ex}_{seed % 1000:03d}", wf_chain(f"{rel} [output]", text, seed, f"v3_{ex}")))
    wait(queue(jobs), on_done=post_video, poll=20)
    log("VIDEOS_DONE")


def cmd_pack():
    photos = json.load(open(f"{W}/photos.json")) if os.path.exists(f"{W}/photos.json") else {}
    dst = f"{OUT}/gen3_pack.zip"
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_STORED) as z:
        for fn in sorted(os.listdir(MP4)):
            z.write(f"{MP4}/{fn}", f"clips/{fn}")
        for n, f in photos.items():
            z.write(f, f"photos/{n}.png")
    log("PACK_DONE", dst, os.path.getsize(dst) // 1e6, "MB")


if __name__ == "__main__":
    {"photos": lambda: cmd_photos(), "videos": lambda: cmd_videos(sys.argv[2]), "pack": lambda: cmd_pack()}[sys.argv[1]]()
