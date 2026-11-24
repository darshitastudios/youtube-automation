"""PIL slide renderers for 1080x1920 Shorts."""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")


def font(name, size):
    return ImageFont.truetype(f"{FONT_DIR}/{name}", size)


F_DISPLAY = "Anton-Regular.ttf"
F_BODY = "Nunito-Bold.ttf"

PALETTES = [
    {"bg1": (30, 12, 60), "bg2": (90, 24, 154), "accent": (255, 209, 102), "accent2": (255, 107, 107)},
    {"bg1": (6, 30, 60), "bg2": (20, 90, 160), "accent": (255, 214, 90), "accent2": (0, 230, 180)},
    {"bg1": (40, 8, 40), "bg2": (140, 30, 90), "accent": (120, 255, 214), "accent2": (255, 240, 120)},
    {"bg1": (10, 45, 40), "bg2": (20, 110, 90), "accent": (255, 180, 90), "accent2": (255, 110, 140)},
]


def make_background(palette, seed=0):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H), palette["bg1"])
    top = Image.new("RGB", (W, H))
    td = ImageDraw.Draw(top)
    for y in range(H):
        t = y / H
        c = tuple(int(palette["bg1"][i] + (palette["bg2"][i] - palette["bg1"][i]) * t) for i in range(3))
        td.line([(0, y), (W, y)], fill=c)
    img = top
    # soft glowing blobs
    blob = Image.new("RGB", (W, H), (0, 0, 0))
    bd = ImageDraw.Draw(blob)
    for _ in range(14):
        x, y = rng.randint(-200, W), rng.randint(-200, H)
        r = rng.randint(80, 260)
        col = rng.choice([palette["accent"], palette["accent2"], palette["bg2"]])
        bd.ellipse([x - r, y - r, x + r, y + r], fill=col)
    blob = blob.filter(ImageFilter.GaussianBlur(160))
    img = Image.blend(img, Image.blend(img, blob, 0.35), 0.0)
    img = Image.blend(img, blob, 0.22)
    # vignette
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-W * 0.35, -H * 0.25, W * 1.35, H * 1.25], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.composite(img, dark, vig)
    return img


def wrap_text(draw, text, fnt, max_w):
    lines = []
    for block in text.split("\n"):
        words = block.split()
        cur = ""
        for w_ in words:
            trial = (cur + " " + w_).strip()
            if draw.textlength(trial, font=fnt) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w_
        if cur:
            lines.append(cur)
    return lines


def text_center(draw, y, text, fnt, fill, stroke=(0, 0, 0), sw=6, max_w=940, line_gap=1.15):
    lines = wrap_text(draw, text, fnt, max_w)
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * line_gap)
    for i, ln in enumerate(lines):
        w_ = draw.textlength(ln, font=fnt)
        draw.text(((W - w_) / 2, y + i * lh), ln, font=fnt, fill=fill,
                  stroke_width=sw, stroke_fill=stroke)
    return y + len(lines) * lh


def badge(draw, text, accent):
    f = font(F_BODY, 40)
    tw = draw.textlength(text, font=f)
    pad = 28
    x0 = (W - tw) / 2 - pad
    y0 = 110
    draw.rounded_rectangle([x0, y0, x0 + tw + 2 * pad, y0 + 74], 37, fill=accent)
    draw.text((x0 + pad, y0 + 16), text, font=f, fill=(20, 10, 30))


def hook_slide(bg, category, hook_text, palette):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    badge(d, f"{category} QUIZ", palette["accent"])
    text_center(d, 620, hook_text, font(F_DISPLAY, 120), (255, 255, 255), sw=8)
    text_center(d, 1150, "Think you can solve it?", font(F_BODY, 52), palette["accent"], sw=4)
    return img


def question_slide(bg, category, question, palette, with_options=False):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    badge(d, category, palette["accent"])
    text_center(d, 380, "QUESTION", font(F_BODY, 44), palette["accent2"], sw=4)
    text_center(d, 470, question, font(F_BODY, 64), (255, 255, 255), sw=5, max_w=920)
    if not with_options:
        text_center(d, 1500, "Choose wisely...", font(F_BODY, 44), palette["accent"], sw=4)
    return img


def options_slide(bg, category, question, options, palette, reveal=-1, dim=False):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    badge(d, category, palette["accent"])
    text_center(d, 240, question, font(F_BODY, 52), (255, 255, 255), sw=5, max_w=940)
    y = 700
    letters = "ABCD"
    for i, opt in enumerate(options):
        box_h = 150
        x0, x1 = 70, W - 70
        correct = (i == reveal)
        if dim and not correct:
            fill, tfill, lfill = (40, 40, 60), (150, 150, 170), (120, 120, 140)
        elif correct:
            fill, tfill, lfill = (46, 160, 90), (255, 255, 255), (20, 80, 40)
        else:
            fill, tfill, lfill = (255, 255, 255), (25, 20, 45), palette["accent2"]
        d.rounded_rectangle([x0, y, x1, y + box_h], 30, fill=fill)
        # letter chip
        cx = x0 + 75
        d.ellipse([cx - 46, y + box_h / 2 - 46, cx + 46, y + box_h / 2 + 46], fill=lfill)
        lf = font(F_DISPLAY, 52)
        lw = d.textlength(letters[i], font=lf)
        d.text((cx - lw / 2, y + box_h / 2 - 40), letters[i], font=lf, fill=(255, 255, 255))
        of = font(F_BODY, 46)
        ow = d.textlength(opt, font=of)
        d.text(((x0 + 160 + x1 - 30 - ow) / 2, y + box_h / 2 - 30), opt, font=of, fill=tfill)
        if correct:
            d.text((x1 - 80, y + box_h / 2 - 42), "✓", font=font(F_BODY, 70), fill=(255, 255, 255))
        y += box_h + 36
    return img


def countdown_frame(bg, category, question, options, palette, t_left, total):
    """Countdown frame: options stay visible; timer sits below them."""
    img = options_slide(bg, category, question, options, palette, dim=True)
    # darken only the strip below the last option so the number pops
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 1500, W, 1810], fill=(0, 0, 0, 130))
    img = Image.alpha_composite(img, overlay).convert("RGB")
    d = ImageDraw.Draw(img)
    secs = max(1, math.ceil(t_left))
    text_center(d, 1520, str(secs), font(F_DISPLAY, 200), (255, 255, 255), sw=8)
    text_center(d, 1730, "SECONDS LEFT", font(F_BODY, 40), palette["accent"], sw=4)
    # bar pinned to the very bottom
    frac = max(0.0, t_left / total)
    bw = int((W - 140) * frac)
    d.rounded_rectangle([70, 1840, W - 70, 1900], 30, fill=(50, 50, 70))
    if bw > 60:
        col = palette["accent"] if frac > 0.4 else palette["accent2"]
        d.rounded_rectangle([70, 1840, 70 + bw, 1900], 30, fill=col)
    return img


def answer_slide(bg, category, answer, explanation, palette):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    badge(d, category, palette["accent"])
    text_center(d, 330, "THE ANSWER IS", font(F_BODY, 52), palette["accent"], sw=4)
    y = text_center(d, 450, answer.upper(), font(F_DISPLAY, 110), (120, 255, 170), sw=8, max_w=940)
    text_center(d, y + 90, explanation, font(F_BODY, 50), (235, 235, 245), sw=4, max_w=900)
    return img


def cta_slide(bg, channel_name, palette):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    text_center(d, 600, "HOW DID YOU DO?", font(F_DISPLAY, 110), (255, 255, 255), sw=8)
    text_center(d, 900, "Drop your answer time in the comments", font(F_BODY, 48),
                palette["accent"], sw=4)
    # subscribe pill
    f = font(F_DISPLAY, 84)
    txt = "SUBSCRIBE"
    tw = d.textlength(txt, font=f)
    x0 = (W - tw) / 2 - 60
    d.rounded_rectangle([x0, 1200, x0 + tw + 120, 1330], 65, fill=(230, 33, 23))
    d.text((x0 + 60, 1218), txt, font=f, fill=(255, 255, 255))
    text_center(d, 1400, f"{channel_name} — a new quiz every day", font(F_BODY, 44),
                (220, 220, 235), sw=4)
    return img


def thumbnail(bg, category, question, palette):
    img = bg.copy().resize((1280, 720), Image.LANCZOS)
    # rebuild at proper 1280x720
    img = Image.new("RGB", (1280, 720), palette["bg1"])
    d = ImageDraw.Draw(img)
    for y in range(720):
        t = y / 720
        c = tuple(int(palette["bg1"][i] + (palette["bg2"][i] - palette["bg1"][i]) * t) for i in range(3))
        d.line([(0, y), (1280, y)], fill=c)
    bf = font(F_BODY, 30)
    bw_ = d.textlength(category, font=bf)
    d.rounded_rectangle([(1280 - bw_) / 2 - 24, 60, (1280 + bw_) / 2 + 24, 120], 30,
                        fill=palette["accent"])
    d.text(((1280 - bw_) / 2, 74), category, font=bf, fill=(20, 10, 30))
    lines = wrap_text(d, question, font(F_BODY, 56), 1100)
    y = 220
    for ln in lines[:4]:
        w_ = d.textlength(ln, font=font(F_BODY, 56))
        d.text(((1280 - w_) / 2, y), ln, font=font(F_BODY, 56), fill=(255, 255, 255),
               stroke_width=4, stroke_fill=(0, 0, 0))
        y += 72
    hf = font(F_DISPLAY, 90)
    ht = "CAN YOU SOLVE IT?"
    w_ = d.textlength(ht, font=hf)
    d.text(((1280 - w_) / 2, 560), ht, font=hf, fill=palette["accent"],
           stroke_width=5, stroke_fill=(0, 0, 0))
    return img
