import torch, torchaudio, html, os, glob
from chatterbox.tts import ChatterboxTTS
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
OUT = '/workspace/voice/out'; REF = '/workspace/voice/refs'
for f in glob.glob(f'{OUT}/*.wav'): os.remove(f)
LINES = ["You said tomorrow? It's tomorrow. Four sets. No excuses. Vamos!",
         "Don't look at me like that. One more rep. I'm watching you."]
def save(name, wavs, sr):
    gap = torch.zeros(1, int(0.45 * sr))
    w = torch.cat([x for wv in wavs for x in (wv, gap)], dim=1)
    torchaudio.save(f'{OUT}/{name}.wav', w, sr); print('saved', name, flush=True)
refs = {'dora': f'{REF}/ref_female_dora.wav', 'mix': f'{REF}/ref_female_mix.wav'}
torch.manual_seed(11)
mtl = ChatterboxMultilingualTTS.from_pretrained(device='cuda')
for rn, rp in refs.items():
    # natural Spanish re-voicing of the reference (female), used as cleaner clone source
    es = mtl.generate("Hola, soy Valentina. Hoy entrenamos duro, sin excusas. Respira y dame una repetición más. ¡Vamos!",
                      language_id='es', audio_prompt_path=rp, exaggeration=0.6, cfg_weight=0.4)
    torchaudio.save(f'{REF}/clean_{rn}.wav', es, mtl.sr)
    save(f'{rn}_1_akzent_stark', [mtl.generate(t, language_id='es', audio_prompt_path=f'{REF}/clean_{rn}.wav', exaggeration=0.7, cfg_weight=0.3) for t in LINES], mtl.sr)
del mtl; torch.cuda.empty_cache()
en = ChatterboxTTS.from_pretrained(device='cuda')
for rn in refs:
    rp = f'{REF}/clean_{rn}.wav'
    save(f'{rn}_2_fluessig', [en.generate(t, audio_prompt_path=rp, exaggeration=0.6, cfg_weight=0.35) for t in LINES], en.sr)
    save(f'{rn}_3_fordernd', [en.generate(t, audio_prompt_path=rp, exaggeration=0.95, cfg_weight=0.25) for t in LINES], en.sr)
files = sorted(f for f in os.listdir(OUT) if f.endswith('.wav'))
with open(f'{OUT}/index.html', 'w') as f:
    f.write('<html><meta name=viewport content="width=device-width"><body style="font-family:sans-serif"><h3>Valentina – Stimmen v2 (weiblich)</h3>')
    for fn in files: f.write(f'<p><b>{html.escape(fn[:-4])}</b><br><audio controls src="{fn}"></audio></p>')
    f.write('</body></html>')
print('DONE', files)
