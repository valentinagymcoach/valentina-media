import torch, torchaudio, html, os
from chatterbox.tts import ChatterboxTTS
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
OUT = '/workspace/voice/out'
LINES = ["You said tomorrow? It's tomorrow. Four sets. No excuses. Vamos!",
         "Don't look at me like that. One more rep. I'm watching you."]
def save(name, wavs, sr):
    gap = torch.zeros(1, int(0.5 * sr))
    w = torch.cat([x for wv in wavs for x in (wv, gap)], dim=1)
    torchaudio.save(f'{OUT}/{name}.wav', w, sr); print('saved', name, flush=True)
torch.manual_seed(7)
mtl = ChatterboxMultilingualTTS.from_pretrained(device='cuda')
# synthetic Spanish reference voice (no real person)
ref = mtl.generate("Hola, soy Valentina. Hoy entrenamos duro, sin excusas. ¿Estás lista? ¡Vamos!",
                   language_id='es', exaggeration=0.7, cfg_weight=0.4)
torchaudio.save(f'{OUT}/ref_es.wav', ref, mtl.sr)
save('A_spanisch_englisch', [mtl.generate(t, language_id='es', exaggeration=0.7, cfg_weight=0.35) for t in LINES], mtl.sr)
save('C_spanisch_ref', [mtl.generate(t, language_id='es', audio_prompt_path=f'{OUT}/ref_es.wav', exaggeration=0.8, cfg_weight=0.3) for t in LINES], mtl.sr)
del mtl; torch.cuda.empty_cache()
en = ChatterboxTTS.from_pretrained(device='cuda')
save('B_englisch_latina', [en.generate(t, audio_prompt_path=f'{OUT}/ref_es.wav', exaggeration=0.75, cfg_weight=0.3) for t in LINES], en.sr)
save('D_englisch_latina_intensiv', [en.generate(t, audio_prompt_path=f'{OUT}/ref_es.wav', exaggeration=1.0, cfg_weight=0.25) for t in LINES], en.sr)
files = sorted(f for f in os.listdir(OUT) if f.endswith('.wav'))
with open(f'{OUT}/index.html', 'w') as f:
    f.write('<html><meta name=viewport content="width=device-width"><body style="font-family:sans-serif"><h3>Valentina – Stimmen</h3>')
    for fn in files:
        f.write(f'<p><b>{html.escape(fn[:-4])}</b><br><audio controls src="{fn}"></audio></p>')
    f.write('</body></html>')
print('DONE', files)
