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
"r4_1",
"Leg day in five moves. Stop skipping it."
],
[
"r4_2",
"Squats. Lunges. Leg press. Romanian deadlifts. Goblet squats."
],
[
"r4_3",
"Slow down. Full range. Every rep clean."
],
[
"r4_4",
"That's leg day. Now you can complain. Vamos!"
],
[
"r5_1",
"Your squat is lying to you. Three mistakes."
],
[
"r5_2",
"One. Knees caving in. Push them out."
],
[
"r5_3",
"Two. Heels coming up. Keep your whole foot down."
],
[
"r5_4",
"Three. Chest dropping. Brace and stay tall."
],
[
"r5_5",
"Fix these, and your squat stops lying. Save it."
],
[
"r6_1",
"Ten sets of chest. Zero for your back?"
],
[
"r6_2",
"I see you. Lat pulldowns. Cable rows. Pull-ups. Romanian deadlifts."
],
[
"r6_3",
"Pull with your elbows, not your hands."
],
[
"r6_4",
"Strong back, better posture. Follow for more."
],
[
"r7_1",
"Your shoulders need three angles, not one."
],
[
"r7_2",
"Press overhead. Raise to the side. Push the floor away."
],
[
"r7_3",
"Light weight. Strict reps. No swinging."
],
[
"r7_4",
"Three angles, every week. Save it."
],
[
"r8_1",
"No hour needed. Twenty minutes. Four moves."
],
[
"r8_2",
"Kettlebell swings. Lunges. Push-ups. Battle ropes."
],
[
"r8_3",
"Forty seconds on, twenty off. Four rounds."
],
[
"r8_4",
"Twenty minutes. No more excuses. Vamos!"
],
[
"r9_1",
"Week two is where most people quit. Not you."
],
[
"r9_2",
"The soreness fades. The habit stays."
],
[
"r9_3",
"Show up tired. Show up slow. Just show up."
],
[
"r9_4",
"Week three is waiting. Follow, and I'll see you there."
],
[
"r10_1",
"Nobody tells you glutes need heavy hinges, not kickbacks."
],
[
"r10_2",
"Romanian deadlifts. Lunges. Goblet squats. Leg press. Kettlebell swings."
],
[
"r10_3",
"Hips back. Flat back. Squeeze at the top."
],
[
"r10_4",
"Heavy hinges, every week. Vamos!"
],
[
"r11_1",
"Only curls? That's why your arms look the same."
],
[
"r11_2",
"Curls for biceps. Pushdowns for triceps."
],
[
"r11_3",
"Triceps are most of your arm. Train them."
],
[
"r11_4",
"Not just curls. Save this for arm day."
],
[
"r12_1",
"Thirty days. Same rules next month. Follow, and we keep going."
]
]

OUT2 = '/workspace/voice/out/month2'; os.makedirs(OUT2, exist_ok=True)
for name, text in LINES:
    sf.write(f'{OUT2}/vo2_{name}.wav', tts(DESC, text, 2), 24000); print('saved', name, flush=True)
print('DONE')
