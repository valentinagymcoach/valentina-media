"""Valentina-Werkzeuge für Qwen (OpenAPI-Tool-Server für Open WebUI).
Läuft im Pod auf 127.0.0.1:8030. Open WebUI ruft die Endpunkte serverseitig auf.
Bilder/Videos/Audio werden über die ComfyUI-Adresse des Pods ausgeliefert (/view), damit sie im Chat erscheinen.
"""
import json, os, random, subprocess, threading, time, uuid, urllib.parse, urllib.request
from typing import Literal, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

COMFY = "http://127.0.0.1:8188"
C = "/workspace/runpod-slim/ComfyUI"
OUT = f"{C}/output"
POD = os.environ.get("RUNPOD_POD_ID", "")
PUBLIC = f"https://{POD}-8188.proxy.runpod.net" if POD else COMFY
LORA = os.environ.get("VALENTINA_LORA", "valentina_vlntna_v1_000001500.safetensors")
WAN_HI = "Wan2.2/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
WAN_LO = "Wan2.2/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
PERSONA = ("vlntna, photo of a fit young latina woman with long straight black hair, toned athletic body, ")
STYLE = ", realistic smartphone photo, natural lighting, sharp focus, high detail"
NEG_V = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，"
         "多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，杂乱的背景，三条腿，背景人很多，倒着走, "
         "text, watermark, nudity, duplicate objects, objects appearing or disappearing, extra limbs, camera shake")
VOICE_DESC = {
    "coach": "Female voice, 25 years old, Spanish accent in English, demanding and intense drill-sergeant style fitness coach but still playful, medium pitch, warm breathy timbre, fast punchy pacing, high energy.",
    "calm": "Female voice, 25 years old, Spanish accent in English, calm and warm, soft timbre, relaxed pacing.",
    "german": "Female voice, 25 years old, speaking German with a light Spanish accent, energetic fitness coach, clear and warm.",
}
JOBS: dict = {}

app = FastAPI(title="Valentina Tools",
              description="Werkzeuge für Bilder, Videos, Sprachaufnahmen und Browser-Aufgaben rund um die KI-Fitness-Persona Valentina. "
                          "Alle Inhalte sind KI-generiert und für Instagram gedacht: sportlich, selbstbewusst, Instagram-tauglich.",
              version="1.0")


# ---------------------------------------------------------------- ComfyUI helpers
def _req(path, obj=None, timeout=60):
    data = json.dumps(obj).encode() if obj is not None else None
    r = urllib.request.Request(COMFY + path, data=data, headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(r, timeout=timeout) as x:
        return json.loads(x.read())


def _queue(wf):
    r = _req("/prompt", {"prompt": wf, "client_id": "tools"})
    if "prompt_id" not in r:
        raise HTTPException(500, f"ComfyUI lehnt ab: {json.dumps(r)[:300]}")
    return r["prompt_id"]


def _wait(pid, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = _req(f"/history/{pid}").get(pid)
        if h:
            if h.get("status", {}).get("status_str") == "error":
                raise RuntimeError("ComfyUI-Fehler: " + json.dumps(h["status"].get("messages", []))[-400:])
            return [f for n in h.get("outputs", {}).values() for k in ("images", "gifs") for f in n.get(k, [])]
        time.sleep(3)
    raise TimeoutError("Zeitüberschreitung")


def _url(f):
    q = urllib.parse.urlencode({"filename": f["filename"], "subfolder": f.get("subfolder", ""), "type": f.get("type", "output")})
    return f"{PUBLIC}/view?{q}"


def wf_photo(text, seed, w, h, lora_strength):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": LORA, "strength_model": lora_strength}},
        "3": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["2", 0], "shift": 3.0}},
        "4": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": text}},
        "6": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["5", 0]}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["3", 0], "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "res_multistep",
              "scheduler": "simple", "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["7", 0], "denoise": 1.0}},
        "9": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["9", 0]}},
        "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": "tools/img"}},
    }


def _pair(wf, k, cond, seed, steps=20):
    half = steps // 2
    base = {"steps": steps, "cfg": 3.5, "sampler_name": "euler", "scheduler": "simple", "positive": [cond, 0], "negative": [cond, 1]}
    wf[str(k)] = {"class_type": "KSamplerAdvanced", "inputs": {**base, "model": ["3", 0], "add_noise": "enable", "noise_seed": seed,
                  "latent_image": [cond, 2], "start_at_step": 0, "end_at_step": half, "return_with_leftover_noise": "enable"}}
    wf[str(k + 1)] = {"class_type": "KSamplerAdvanced", "inputs": {**base, "model": ["4", 0], "add_noise": "disable", "noise_seed": seed,
                      "latent_image": [str(k), 0], "start_at_step": half, "end_at_step": 10000, "return_with_leftover_noise": "disable"}}


def wf_video(image, text, seed, segments):
    wf = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": WAN_HI, "weight_dtype": "default"}},
        "2": {"class_type": "UNETLoader", "inputs": {"unet_name": WAN_LO, "weight_dtype": "default"}},
        "3": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["1", 0], "shift": 8.0}},
        "4": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["2", 0], "shift": 8.0}},
        "5": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["5", 0], "text": text}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["5", 0], "text": NEG_V}},
        "8": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
        "9": {"class_type": "LoadImage", "inputs": {"image": image}},
        "10": {"class_type": "WanImageToVideo", "inputs": {"positive": ["6", 0], "negative": ["7", 0], "vae": ["8", 0], "start_image": ["9", 0],
               "width": 480, "height": 832, "length": 81, "batch_size": 1}},
    }
    _pair(wf, 11, "10", seed)
    wf["13"] = {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["8", 0]}}
    last = ["13", 0]
    if segments == 2:
        wf["20"] = {"class_type": "ImageFromBatch", "inputs": {"image": ["13", 0], "batch_index": 80, "length": 1}}
        wf["22"] = {"class_type": "WanImageToVideo", "inputs": {"positive": ["6", 0], "negative": ["7", 0], "vae": ["8", 0], "start_image": ["20", 0],
                    "width": 480, "height": 832, "length": 81, "batch_size": 1}}
        _pair(wf, 23, "22", seed + 1)
        wf["25"] = {"class_type": "VAEDecode", "inputs": {"samples": ["24", 0], "vae": ["8", 0]}}
        wf["26"] = {"class_type": "ImageFromBatch", "inputs": {"image": ["25", 0], "batch_index": 1, "length": 80}}
        wf["27"] = {"class_type": "ImageBatch", "inputs": {"image1": ["13", 0], "image2": ["26", 0]}}
        last = ["27", 0]
    wf["30"] = {"class_type": "CreateVideo", "inputs": {"images": last, "fps": 16}}
    wf["31"] = {"class_type": "SaveVideo", "inputs": {"video": ["30", 0], "filename_prefix": "tools/video", "format": "mp4", "codec": "h264"}}
    return wf


# ---------------------------------------------------------------- Maya1 TTS (lazy)
_tts = {}
_tts_lock = threading.Lock()


def _load_tts():
    if _tts:
        return _tts
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from snac import SNAC
    _tts["torch"] = torch
    _tts["tok"] = AutoTokenizer.from_pretrained("maya-research/maya1")
    _tts["model"] = AutoModelForCausalLM.from_pretrained("maya-research/maya1", torch_dtype=torch.bfloat16, device_map="cuda").eval()
    _tts["snac"] = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval().to("cuda")
    return _tts


def _synth(desc, text, seed):
    t = _load_tts(); torch = t["torch"]
    SOH, EOH, BOS, EOT, SOS, EOS, SMIN, SMAX = 128259, 128260, 128000, 128009, 128257, 128258, 128266, 156937
    torch.manual_seed(seed)
    ids = [SOH, BOS] + t["tok"].encode(f'<description="{desc}"> {text}', add_special_tokens=False) + [EOT, EOH, 128261, SOS]
    x = torch.tensor([ids], device="cuda")
    with torch.no_grad():
        g = t["model"].generate(x, attention_mask=torch.ones_like(x), max_new_tokens=2500, min_new_tokens=28, temperature=0.4,
                                top_p=0.9, repetition_penalty=1.1, do_sample=True, eos_token_id=EOS)
    v = [c for c in g[0, len(ids):].tolist() if SMIN <= c <= SMAX]
    n = len(v) // 7; v = v[:n * 7]
    l1, l2, l3 = [], [], []
    for i in range(n):
        s = [(c - SMIN) % 4096 for c in v[i * 7:(i + 1) * 7]]
        l1.append(s[0]); l2 += [s[1], s[4]]; l3 += [s[2], s[3], s[5], s[6]]
    codes = [torch.tensor(l, device="cuda").unsqueeze(0) for l in (l1, l2, l3)]
    with torch.no_grad():
        return t["snac"].decoder(t["snac"].quantizer.from_codes(codes))[0, 0].float().cpu().numpy()[2048:]


# ---------------------------------------------------------------- API
class PhotoReq(BaseModel):
    scene: str = Field(..., description="Was auf dem Foto zu sehen ist, auf Englisch: Ort, Pose, Kleidung, Licht, Kamerawinkel. "
                                        "Valentina wird automatisch eingesetzt, nicht beschreiben, wie sie aussieht.")
    count: int = Field(2, ge=1, le=6, description="Anzahl Varianten")
    format: Literal["portrait", "feed", "square", "story"] = Field("feed", description="portrait 736x1280, feed 896x1120 (4:5), square 1024x1024, story 768x1344")
    lora_strength: float = Field(1.0, ge=0.5, le=1.2, description="Wie stark Valentinas Gesicht erzwungen wird")


class VideoReq(BaseModel):
    image_url: str = Field(..., description="URL eines zuvor erzeugten Bildes (aus create_photos)")
    motion: str = Field(..., description="Bewegung auf Englisch, z. B. 'She performs slow goblet squats with perfect form. Static camera.'")
    seconds: Literal[5, 10] = Field(5, description="5 s (ca. 12 min Rechenzeit) oder 10 s (ca. 25 min)")


class SpeakReq(BaseModel):
    text: str = Field(..., description="Text, der gesprochen werden soll (kurz, max. 2-3 Sätze pro Aufruf)")
    voice: Literal["coach", "calm", "german"] = Field("coach", description="coach = Valentinas Standardstimme (Englisch)")
    seed: int = Field(2, description="2 = Valentinas gewohnte Stimme")


class BrowseReq(BaseModel):
    task: str = Field(..., description="Aufgabe für den Browser-Agenten in Klartext")
    max_steps: int = Field(20, ge=3, le=40)


@app.post("/create_photos", summary="Fotos von Valentina erzeugen",
          description="Erzeugt Fotos von Valentina mit ihrem LoRA (Z-Image Turbo). Dauert ca. 10 s pro Bild. "
                      "Gibt Bild-URLs zurück. Zeige sie dem Nutzer als Markdown-Bilder ![](url).")
def create_photos(r: PhotoReq):
    w, h = {"portrait": (736, 1280), "feed": (896, 1120), "square": (1024, 1024), "story": (768, 1344)}[r.format]
    pids = [_queue(wf_photo(PERSONA + r.scene + STYLE, random.randint(1, 2**31), w, h, r.lora_strength)) for _ in range(r.count)]
    urls = []
    for p in pids:
        urls += [_url(f) for f in _wait(p, 300)]
    return {"images": urls, "hint": "Mit create_video ein Bild als Startbild animieren."}


def _video_job(jid, r: VideoReq):
    try:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(r.image_url).query)
        image = f"{q.get('subfolder', [''])[0]}/{q['filename'][0]}".lstrip("/") + " [output]"
        pid = _queue(wf_video(image, "Realistic video, static camera on a tripod, natural motion, real physics. " + r.motion,
                              random.randint(1, 2**31), 2 if r.seconds == 10 else 1))
        JOBS[jid].update(status="läuft", prompt_id=pid)
        files = _wait(pid, 3600)
        JOBS[jid].update(status="fertig", video=[_url(f) for f in files])
    except Exception as e:  # noqa: BLE001
        JOBS[jid].update(status="fehler", error=str(e)[:400])


@app.post("/create_video", summary="Video aus einem Bild erzeugen (Hintergrundauftrag)",
          description="Animiert ein Bild mit Wan 2.2 (14B). Läuft im Hintergrund: gibt sofort eine job_id zurück. "
                      "Status später mit get_job abfragen. 5 s dauern ca. 12 Minuten, 10 s ca. 25 Minuten.")
def create_video(r: VideoReq):
    jid = uuid.uuid4().hex[:8]
    JOBS[jid] = {"status": "wartet", "type": "video", "created": time.strftime("%H:%M:%S")}
    threading.Thread(target=_video_job, args=(jid, r), daemon=True).start()
    return {"job_id": jid, "status": "gestartet", "hint": "In einigen Minuten get_job aufrufen."}


@app.get("/get_job/{job_id}", summary="Status eines Video-Auftrags", description="Gibt Status und, wenn fertig, die Video-URL zurück.")
def get_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "unbekannte job_id")
    return JOBS[job_id]


@app.get("/list_jobs", summary="Alle Aufträge auflisten")
def list_jobs():
    return JOBS


@app.post("/speak", summary="Sprachaufnahme erzeugen",
          description="Spricht Text mit Valentinas Stimme (Maya1, Stimme aus Beschreibung, keine echte Person). Gibt eine WAV-URL zurück.")
def speak(r: SpeakReq):
    import soundfile as sf
    with _tts_lock:
        audio = _synth(VOICE_DESC[r.voice], r.text, r.seed)
    os.makedirs(f"{OUT}/voice", exist_ok=True)
    name = f"vo_{uuid.uuid4().hex[:8]}.wav"
    sf.write(f"{OUT}/voice/{name}", audio, 24000)
    return {"audio": _url({"filename": name, "subfolder": "voice", "type": "output"}), "seconds": round(len(audio) / 24000, 1)}


@app.post("/browse", summary="Browser-Agent ausführen",
          description="Lässt einen Browser-Agenten eine Aufgabe auf Weboberflächen erledigen (standardmässig nur die eigenen Dienste im Pod). "
                      "Gibt das Ergebnis als Text zurück. Keine Passwörter in Aufgaben schreiben.")
def browse(r: BrowseReq):
    p = subprocess.run(["/workspace/ai/agent.sh", r.task, "--max-steps", str(r.max_steps)], capture_output=True, text=True, timeout=1500)
    out = (p.stdout or "")[-3000:]
    return {"ok": p.returncode == 0, "result": out.split("=== Ergebnis ===")[-1].strip()[:2000] or (p.stderr or "")[-1000:]}


@app.get("/health")
def health():
    return {"ok": True, "pod": POD, "public": PUBLIC}
