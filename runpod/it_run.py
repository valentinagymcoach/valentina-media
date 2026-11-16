"""InfiniteTalk-Lipsync über die ComfyUI-API (Wan 2.1 I2V 480p + InfiniteTalk-Patch + lightx2v, 6 Schritte).
python3 it_run.py info                                  -> zeigt Eingänge des Knotens
python3 it_run.py run BILD.png AUDIO.wav "Prompt" PREFIX [seed]
BILD/AUDIO: Dateinamen im ComfyUI-input-Ordner (werden bei Bedarf aus output kopiert)."""
import json, math, os, shutil, subprocess, sys, time, urllib.request
C = "http://127.0.0.1:8188"; CD = "/workspace/runpod-slim/ComfyUI"
def req(p, d=None):
    r = urllib.request.Request(C + p, data=None if d is None else json.dumps(d).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=120).read())
if sys.argv[1] == "info":
    print(json.dumps(req("/object_info/WanInfiniteTalkToVideo")["WanInfiniteTalkToVideo"]["input"], indent=1)[:3000]); sys.exit()
img, aud, prompt, prefix = sys.argv[2:6]; seed = int(sys.argv[6]) if len(sys.argv) > 6 else 7
for f in (img, aud):
    if not os.path.exists(f"{CD}/input/{os.path.basename(f)}"):
        src = f if os.path.exists(f) else next((os.path.join(r, os.path.basename(f)) for r, _, fs in os.walk(f"{CD}/output") if os.path.basename(f) in fs), None)
        shutil.copy(src, f"{CD}/input/{os.path.basename(f)}")
img, aud = os.path.basename(img), os.path.basename(aud)
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{CD}/input/{aud}"]))
need = math.ceil(dur * 25) + 4; L, MF = 81, 9
segs = 1 + max(0, math.ceil((need - L) / (L - MF)))
print("audio", dur, "s ->", segs, "segments", flush=True)
g = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "Wan2_1-I2V-14B-480p_fp8_e4m3fn_scaled_KJ.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors", "strength_model": 1.0}},
 "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
 "4": {"class_type": "VAELoader", "inputs": {"vae_name": "Wan2_1_VAE_bf16.safetensors"}},
 "5": {"class_type": "ModelPatchLoader", "inputs": {"name": "wan2.1_infiniteTalk_single_fp16.safetensors"}},
 "6": {"class_type": "AudioEncoderLoader", "inputs": {"audio_encoder_name": "wav2vec2-chinese-base_fp16.safetensors"}},
 "7": {"class_type": "LoadAudio", "inputs": {"audio": aud}},
 "8": {"class_type": "AudioEncoderEncode", "inputs": {"audio_encoder": ["6", 0], "audio": ["7", 0]}},
 "9": {"class_type": "LoadImage", "inputs": {"image": img}},
 "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": prompt}},
 "11": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["10", 0]}},
 "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
}
acc = None
for i in range(segs):
    b = 100 + i * 10
    t = {"mode": os.environ.get("IT_MODE_JSON") and json.loads(os.environ["IT_MODE_JSON"]) or "single_speaker",
         "model": ["2", 0], "model_patch": ["5", 0], "positive": ["10", 0], "negative": ["11", 0], "vae": ["4", 0],
         "width": 480, "height": 832, "length": L, "start_image": ["9", 0], "audio_encoder_output_1": ["8", 0],
         "motion_frame_count": MF, "audio_scale": 1.0}
    if acc: t["previous_frames"] = acc
    g[str(b)] = {"class_type": "WanInfiniteTalkToVideo", "inputs": t}
    g[str(b+1)] = {"class_type": "BasicScheduler", "inputs": {"model": [str(b), 0], "scheduler": "normal", "steps": 6, "denoise": 1.0}}
    g[str(b+2)] = {"class_type": "CFGGuider", "inputs": {"model": [str(b), 0], "positive": [str(b), 1], "negative": [str(b), 2], "cfg": 1.0}}
    g[str(b+3)] = {"class_type": "RandomNoise", "inputs": {"noise_seed": seed + i}}
    g[str(b+4)] = {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": [str(b+3), 0], "guider": [str(b+2), 0], "sampler": ["12", 0], "sigmas": [str(b+1), 0], "latent_image": [str(b), 3]}}
    g[str(b+5)] = {"class_type": "VAEDecode", "inputs": {"samples": [str(b+4), 0], "vae": ["4", 0]}}
    if acc is None:
        acc = [str(b+5), 0]
    else:
        g[str(b+6)] = {"class_type": "ImageFromBatch", "inputs": {"image": [str(b+5), 0], "batch_index": MF, "length": L - MF}}
        g[str(b+7)] = {"class_type": "ImageBatch", "inputs": {"image1": acc, "image2": [str(b+6), 0]}}
        acc = [str(b+7), 0]
g["90"] = {"class_type": "CreateVideo", "inputs": {"images": acc, "fps": 25, "audio": ["7", 0]}}
g["91"] = {"class_type": "SaveVideo", "inputs": {"video": ["90", 0], "filename_prefix": "lipsync/" + prefix, "format": "mp4", "codec": "h264"}}
r = req("/prompt", {"prompt": g})
pid = r.get("prompt_id"); print("queued", pid, r.get("node_errors") or "", flush=True)
if not pid: print(json.dumps(r)[:3000]); sys.exit(1)
t0 = time.time()
while True:
    time.sleep(15)
    h = req(f"/history/{pid}")
    if pid in h:
        st = h[pid].get("status", {})
        if st.get("status_str") == "error": print("ERROR", json.dumps(st)[:3000]); sys.exit(1)
        for o in h[pid]["outputs"].values():
            for k in ("images", "videos", "gifs"):
                for x in o.get(k, []): print("OUT", x.get("subfolder"), x.get("filename"), round(time.time() - t0), "s")
        break
