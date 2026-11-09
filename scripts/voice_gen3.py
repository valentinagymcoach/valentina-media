# Valentina final voice: mix_3_fordernd (en model, ref clean_mix.wav, exaggeration 0.95, cfg 0.25)
import torch, torchaudio, os, zipfile, html
from chatterbox.tts import ChatterboxTTS
OUT = '/workspace/voice/out/final'; os.makedirs(OUT, exist_ok=True)
REF = '/workspace/voice/refs/clean_mix.wav'
VO = {
 'vo_w1_tag1': ["Stop scrolling.", "Start lifting.", "New coach in town... and I don't do excuses."],
 'vo_w1_tag3': ["One more set.", "Yes, you.", "I'm watching."],
 'vo_w1_tag5': ["Your excuse just left the chat.", "Coffee first... then reps.", "Deal?"],
 'vo_pov_legday': ["Oh... you're skipping leg day?", "Cute.", "Four sets. Now. Vamos!"],
 'vo_discipline': ["Motivation fades.", "Discipline doesn't.", "Get up. Every. Single. Day."],
 'vo_dayinmylife': ["Six thirty. Coffee first.", "Then we run.", "Then we lift.", "And then... we earn the sunset."],
 'vo_dont_accept': ["Things I don't accept as your coach.", "I'm too tired.", "I'll start Monday.", "Five more minutes.", "Follow me if you're done with excuses."],
}
torch.manual_seed(21)
en = ChatterboxTTS.from_pretrained(device='cuda')
for name, parts in VO.items():
    segs = []
    for p in parts:
        w = en.generate(p, audio_prompt_path=REF, exaggeration=0.95, cfg_weight=0.25)
        segs += [w, torch.zeros(1, int(0.35 * en.sr))]
    torchaudio.save(f'{OUT}/{name}.wav', torch.cat(segs, dim=1), en.sr); print('saved', name, flush=True)
import shutil; shutil.copy(REF, f'{OUT}/valentina_voice_reference.wav')
with zipfile.ZipFile('/workspace/voice/out/valentina_voice.zip', 'w') as z:
    for f in sorted(os.listdir(OUT)): z.write(f'{OUT}/{f}', f'valentina_voice/{f}')
with open('/workspace/voice/out/index.html', 'w') as f:
    f.write('<html><meta name=viewport content="width=device-width"><body style="font-family:sans-serif"><h3>Valentina – Voiceovers (mix_3_fordernd)</h3>')
    for fn in sorted(os.listdir(OUT)): f.write(f'<p><b>{html.escape(fn[:-4])}</b><br><audio controls src="final/{fn}"></audio></p>')
    f.write('<p><a href="valentina_voice.zip">ZIP herunterladen</a></p></body></html>')
print('DONE')
