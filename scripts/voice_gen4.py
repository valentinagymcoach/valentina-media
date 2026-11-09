# Chatterbox tuned for natural prosody: whole sentences, lower exaggeration, higher cfg
import torch, torchaudio, os
from chatterbox.tts import ChatterboxTTS
OUT = '/workspace/voice/out/v4'; os.makedirs(OUT, exist_ok=True)
REF = '/workspace/voice/refs/clean_mix.wav'
LINES = ["You said tomorrow? Well, it's tomorrow. Four sets, no excuses. Vamos!",
         "Don't look at me like that. One more rep, I'm watching you."]
en = ChatterboxTTS.from_pretrained(device='cuda')
for tag, ex, cfg in [('chatterbox_natuerlich', 0.5, 0.5), ('chatterbox_mittel', 0.65, 0.45)]:
    torch.manual_seed(3)
    segs = []
    for t in LINES:
        segs += [en.generate(t, audio_prompt_path=REF, exaggeration=ex, cfg_weight=cfg, temperature=0.7), torch.zeros(1, int(0.5 * en.sr))]
    torchaudio.save(f'{OUT}/{tag}.wav', torch.cat(segs, 1), en.sr); print('saved', tag, flush=True)
