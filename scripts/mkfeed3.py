"""Feed (1080x1350) + story (1080x1920) images in the existing Valentina style.
Usage: python3 -I mkfeed3.py <photos_dir> <out_dir>"""
import sys, os, json
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
F = "/usr/share/fonts/truetype/google-fonts/"
BOLD, SEMI, MED = F + "Poppins-Bold.ttf", F + "Poppins-SemiBold.ttf", F + "Poppins-Medium.ttf"
if not os.path.exists(SEMI):
    SEMI = BOLD

PICKS = [  # (key, photo, story subtitle)
    ("22", "f_hike_autumn", "Active rest. Move today."),
    ("23", "f_rack_chalk", "Bar's loaded. Your turn."),
    ("25", "f_selfie_mirror", "Mid-week check-in."),
    ("27", "f_dumbbells_rack", "Friday is not a skip day."),
    ("29", "f_restday_sofa", "Rest day, not lazy day."),
    ("30", "f_bike", "Warm up first."),
    ("02", "f_walk_city", "Cold is not an excuse."),
    ("04", "f_plank", "How long can you hold it?"),
    ("06", "f_sunrise_stretch", "Sunday reset."),
]


def cover(im, w, h):
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def text_c(d, y, s, font, fill=(255, 255, 255), stroke=0):
    w = d.textlength(s, font=font)
    d.text(((1080 - w) / 2, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))


for key, name, sub in PICKS:
    src = Image.open(f"{SRC}/{name}.png").convert("RGB")
    feed = cover(src, 1080, 1350)
    feed.save(f"{OUT}/feed3_{key}.jpg", quality=92)
    bg = cover(src, 1080, 1920).filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    card = cover(src, 920, 1150)
    mask = Image.new("L", card.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, 919, 1149], radius=32, fill=255)
    bg.paste(card, (80, 420), mask)
    d = ImageDraw.Draw(bg)
    text_c(d, 220, "NEW POST", ImageFont.truetype(BOLD, 96), stroke=3)
    text_c(d, 325, sub, ImageFont.truetype(SEMI, 46), stroke=2)
    d.text((60, 1820), "AI-generated", font=ImageFont.truetype(MED, 36), fill=(255, 255, 255))
    bg.save(f"{OUT}/story_feed3_{key}.jpg", quality=92)
    print(key, name)
