# Maya1 (open source, Apache-2.0): voice designed from a text description, no real person, no cloning.
import torch, os, soundfile as sf
from transformers import AutoModelForCausalLM, AutoTokenizer
from snac import SNAC
M = 'maya-research/maya1'
tok = AutoTokenizer.from_pretrained(M)
model = AutoModelForCausalLM.from_pretrained(M, torch_dtype=torch.bfloat16, device_map='cuda').eval()
snac = SNAC.from_pretrained('hubertsiuzdak/snac_24khz').eval().to('cuda')
SOH, EOH, SOA, BOS, EOT, SOS, EOS = 128259, 128260, 128261, 128000, 128009, 128257, 128258
SMIN, SMAX = 128266, 156937
def tts(desc, text, seed):
    torch.manual_seed(seed)
    p = f'<description="{desc}"> {text}'
    ids = [SOH, BOS] + tok.encode(p, add_special_tokens=False) + [EOT, EOH, SOA, SOS]
    x = torch.tensor([ids], device='cuda')
    with torch.no_grad():
        g = model.generate(x, attention_mask=torch.ones_like(x), max_new_tokens=2500, min_new_tokens=28, temperature=0.4,
                           top_p=0.9, repetition_penalty=1.1, do_sample=True, eos_token_id=EOS)
    t = [v for v in g[0, len(ids):].tolist() if SMIN <= v <= SMAX]
    n = len(t) // 7; t = t[:n * 7]
    l1, l2, l3 = [], [], []
    for i in range(n):
        s = [(v - SMIN) % 4096 for v in t[i*7:(i+1)*7]]
        l1.append(s[0]); l2 += [s[1], s[4]]; l3 += [s[2], s[3], s[5], s[6]]
    codes = [torch.tensor(l, device='cuda').unsqueeze(0) for l in (l1, l2, l3)]
    with torch.no_grad():
        a = snac.decoder(snac.quantizer.from_codes(codes))[0, 0].float().cpu().numpy()
    return a[2048:]
DESC = "Female voice, 25 years old, Spanish accent in English, demanding and intense drill-sergeant style fitness coach but still playful, medium pitch, warm breathy timbre, fast punchy pacing, high energy."
LINES = [
 [
  "v4a_1",
  "Step-ups are the most underrated leg exercise."
 ],
 [
  "v4a_2",
  "Whole foot on the bench."
 ],
 [
  "v4a_3",
  "Drive through the heel. Don't push off the back leg."
 ],
 [
  "v4a_4",
  "Stand tall at the top. Control the way down."
 ],
 [
  "v4a_5",
  "Ten each side. Save it. Vamos!"
 ],
 [
  "v4b_2",
  "Bench press. Goblet squats. Shoulder press. Curls."
 ],
 [
  "v4b_4",
  "Full body done. Follow for more."
 ]
]

OUT3 = '/workspace/runpod-slim/ComfyUI/output/voice3'; os.makedirs(OUT3, exist_ok=True)
for name, text in LINES:
    for seed in (2, 7):
        sf.write(f'{OUT3}/vo_{name}_s{seed}.wav', tts(DESC, text, seed), 24000); print('saved', name, seed, flush=True)
print('MAYA4_DONE')
