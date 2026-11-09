# Maya1 (open source, Apache-2.0): voice designed from a text description, no real person, no cloning.
import torch, os, soundfile as sf
from transformers import AutoModelForCausalLM, AutoTokenizer
from snac import SNAC
OUT = '/workspace/voice/out/month'; os.makedirs(OUT, exist_ok=True)
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
 ("01_pov_legday", "Oh... you're skipping leg day? <chuckle> Cute. Four sets. Now. Vamos!"),
 ("02_discipline", "Motivation fades. Discipline doesn't. Get up. Every single day."),
 ("03_dayinmylife", "Six thirty. Coffee first. Then we run. Then we lift. And then... we earn the sunset."),
 ("04_dont_accept", "Things I don't accept as your coach. I'm too tired. I'll start Monday. Five more minutes. Follow me if you're done with excuses."),
 ("05_stop_scrolling", "Stop scrolling. Start lifting. New coach in town, and I don't do excuses."),
 ("06_one_more_set", "One more set. Yes, you. I'm watching."),
 ("07_excuse_left", "Your excuse just left the chat. <chuckle> Coffee first, then reps. Deal?"),
 ("08_plan", "You don't need motivation. You need a plan. And me."),
 ("09_before_breakfast", "Three things before breakfast. Water, sunlight, squats. No discussion."),
 ("10_not_on_my_watch", "You said you'd start tomorrow? Not on my watch."),
 ("11_sore", "Sore today? Good. That's yesterday saying hello."),
 ("12_rest_day", "Rest day doesn't mean couch day. Walk, stretch, breathe. Then come back stronger."),
 ("13_glutes", "Hip thrusts. Romanian deadlifts. Lunges. Glutes don't build themselves. Vamos!"),
 ("14_warm_up", "Warm up first. I don't want excuses, and I don't want injuries."),
 ("15_shoes_on", "Your playlist is ready. Your shoes are on. So why are you still here? Go!"),
 ("16_small_steps", "Small steps. Every day. That's the whole secret."),
 ("17_look_at_me", "Look at me. One more rep. Perfect. Again."),
 ("18_friday", "Friday night plans? Deadlifts. Then tacos. In that order. <chuckle>"),
 ("19_sunday_reset", "Sunday reset. Meal prep, stretch, plan your week. Monday doesn't stand a chance."),
 ("20_day_thirty", "Day thirty. Still here? I knew you would be. Proud of you."),
]
for name, text in LINES:
    sf.write(f'{OUT}/vo_{name}.wav', tts(DESC, text, 2), 24000); print('saved', name, flush=True)
import zipfile
with zipfile.ZipFile('/workspace/voice/out/valentina_voice_month.zip', 'w') as z:
    for f in sorted(os.listdir(OUT)): z.write(f'{OUT}/{f}', f'valentina_voice_month/{f}')
    z.writestr('valentina_voice_month/STIMME.txt', 'Modell: Maya1 (Apache-2.0)\nSeed: 2\nBeschreibung: ' + DESC + '\n')
print('DONE')
