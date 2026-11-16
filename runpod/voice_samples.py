"""Stimm-Vorschläge für Valentina. Aufruf: <venv>/python voice_samples.py qwen|chatterbox OUTDIR REF_WAV"""
import sys, os, torch, soundfile as sf
mode, out, ref = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
T = {
 "hype": "Vamos! One more set. No excuses... I'm watching you.",
 "talk": "Listen, discipline beats motivation. Show up today, even if it's just twenty minutes. Deal?",
 "calm": "Okay, slow down. Breathe in... and out. Good. Form before weight, always.",
}
if mode == "qwen":
    from qwen_tts import Qwen3TTSModel
    D = {
     "q1_warm_colombian": "Warm, natural young Latina woman in her mid-twenties speaking English with a light Colombian Spanish accent. Confident, energetic fitness coach, playful and a little teasing, smiling while she talks, natural breaths, conversational pace, medium-low pitch, slightly husky.",
     "q2_bright_mexican": "Young Latina woman, twenty-six, speaking English with a noticeable Mexican Spanish accent. Bright, upbeat and friendly gym coach hyping someone up, lively fast delivery, clear articulation, genuine laughter in her voice.",
     "q3_calm_soft": "Calm, soft-spoken young Latina woman speaking English with a gentle Spanish accent. Relaxed and warm like talking to a close friend, smooth mid-range voice, unhurried pace, natural pauses.",
    }
    m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cuda:0", dtype=torch.bfloat16)
    for name, desc in D.items():
        for k, txt in T.items():
            torch.manual_seed(7)
            wavs, sr = m.generate_voice_design(text=txt, language="English", instruct=desc)
            sf.write(f"{out}/{name}_{k}.wav", wavs[0], sr); print("ok", name, k, flush=True)
else:
    from chatterbox.tts import ChatterboxTTS
    m = ChatterboxTTS.from_pretrained(device="cuda")
    refs = {"c1_valentina_natural": (ref, 0.5, 0.4), "c2_valentina_expressive": (ref, 0.8, 0.3)}
    q1 = f"{out}/q1_warm_colombian_talk.wav"
    if os.path.exists(q1):
        refs["c3_colombian_clone"] = (q1, 0.6, 0.35)
    for name, (r, ex, cfg) in refs.items():
        for k, txt in T.items():
            torch.manual_seed(7)
            w = m.generate(txt, audio_prompt_path=r, exaggeration=ex, cfg_weight=cfg)
            sf.write(f"{out}/{name}_{k}.wav", w.squeeze(0).cpu().numpy(), m.sr); print("ok", name, k, flush=True)
