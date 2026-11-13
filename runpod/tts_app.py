"""Parler-TTS als kleiner HTTP-Dienst.
POST /tts               {"text": "...", "description": "..."}           -> audio/wav
POST /v1/audio/speech   OpenAI-kompatibel (für Open WebUI): {"input": "...", "voice": "..."}
Die Stimme wird über eine Textbeschreibung gesteuert, nicht durch Klonen einer echten Person.
"""
import io, os, threading
import soundfile as sf
import torch
from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

MODEL = os.environ.get("TTS_MODEL", "parler-tts/parler-tts-mini-v1")
DEVICE = os.environ.get("TTS_DEVICE", "cuda") if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32
DEFAULT_DESC = ("A female speaker with a warm, clear voice speaks at a moderately fast pace with energy. "
                "The recording is very clear with no background noise.")
VOICES = {  # Kurzbeschreibungen für den "voice"-Parameter
    "coach": "A female speaker with an energetic, confident and slightly playful voice speaks fast. Very clear audio.",
    "calm": "A female speaker with a calm, soft voice speaks slowly. Very clear audio.",
    "male": "A male speaker with a deep, friendly voice speaks at a normal pace. Very clear audio.",
}

model = ParlerTTSForConditionalGeneration.from_pretrained(MODEL, torch_dtype=DTYPE).to(DEVICE)
tok = AutoTokenizer.from_pretrained(MODEL)
lock = threading.Lock()
app = FastAPI(title="Parler-TTS")


def synth(text: str, desc: str) -> bytes:
    with lock, torch.inference_mode():
        d = tok(desc, return_tensors="pt").to(DEVICE)
        p = tok(text, return_tensors="pt").to(DEVICE)
        audio = model.generate(input_ids=d.input_ids, attention_mask=d.attention_mask,
                               prompt_input_ids=p.input_ids, prompt_attention_mask=p.attention_mask)
    buf = io.BytesIO()
    sf.write(buf, audio.float().cpu().numpy().squeeze(), model.config.sampling_rate, format="WAV")
    return buf.getvalue()


class TTSReq(BaseModel):
    text: str
    description: str | None = None


class OpenAIReq(BaseModel):
    input: str
    voice: str | None = None
    model: str | None = None


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL, "device": DEVICE}


@app.post("/tts")
def tts(r: TTSReq):
    return Response(synth(r.text, r.description or DEFAULT_DESC), media_type="audio/wav")


@app.post("/v1/audio/speech")
def openai_speech(r: OpenAIReq):
    return Response(synth(r.input, VOICES.get(r.voice or "", DEFAULT_DESC)), media_type="audio/wav")
