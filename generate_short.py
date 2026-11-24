#!/usr/bin/env python3
"""Generate a quiz Short end-to-end: TTS + slides + sfx + music -> mp4 + thumbnail."""
import argparse
import asyncio
import json
import os
import random

import edge_tts
import numpy as np
from PIL import Image
Image.ANTIALIAS = Image.Resampling.LANCZOS  # moviepy 1.0.3 + Pillow>=10

from moviepy.editor import (
    AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip,
    VideoClip, concatenate_videoclips,
)

import audio_synth as syn
import slides

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "out")
WORK = os.path.join(BASE, "work")
CHANNEL_NAME = "Quizzy Daily"
VOICE = "en-US-ChristopherNeural"
RATE = "+12%"
COUNTDOWN_S = 8

os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)


async def tts(text, path):
    await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
    return path


def dur(path):
    with AudioFileClip(path) as c:
        return c.duration


def options_speech(options):
    parts = [f"{l}, {o}" for l, o in zip("ABCD", options)]
    return "  ".join(parts[:-1]) + f",   or {parts[-1]}?"


def generate(quiz, out_path=None, seed=None):
    seed = seed if seed is not None else random.randrange(10 ** 6)
    palette = random.Random(seed).choice(slides.PALETTES)
    tag = quiz["id"]
    work = os.path.join(WORK, tag)
    os.makedirs(work, exist_ok=True)
    out_path = out_path or os.path.join(OUT, f"{tag}.mp4")

    hook_text = "ONLY 1% GET THIS RIGHT"
    letters = "ABCD"

    # ---------- TTS ----------
    lines = {
        "q": quiz["question"],
        "o": options_speech(quiz["options"]),
        "a": f"The answer is {letters[quiz['answer_index']]}, {quiz['options'][quiz['answer_index']]}!",
        "e": quiz["explanation"],
        "c": "Comment your time below, and subscribe for a new quiz every day!",
    }
    paths = {}
    async def gen_all():
        for k, v in lines.items():
            p = os.path.join(work, f"tts_{k}.mp3")
            await tts(v, p)
            paths[k] = p
    asyncio.run(gen_all())
    durs = {k: dur(p) for k, p in paths.items()}

    # ---------- timeline ----------
    t = 0.0
    segs = []

    def seg(name, length):
        nonlocal t
        segs.append((name, t, length))
        t += length
        return t - length

    seg("hook", 1.9)
    seg("question", durs["q"] + 0.45)
    seg("options", durs["o"] + 0.9)
    seg("countdown", COUNTDOWN_S)
    seg("reveal", durs["a"] + durs["e"] + 1.0)
    seg("cta", durs["c"] + 0.6)
    total = t
    at = {name: start for name, start, _ in segs}

    # ---------- visuals ----------
    bg = slides.make_background(palette, seed=seed)
    q = quiz
    static = {
        "hook": slides.hook_slide(bg, q["category"], hook_text, palette),
        "question": slides.question_slide(bg, q["category"], q["question"], palette),
        "options": slides.options_slide(bg, q["category"], q["question"], q["options"], palette),
        "reveal": slides.answer_slide(bg, q["category"],
                                      q["options"][q["answer_index"]], q["explanation"], palette),
        "cta": slides.cta_slide(bg, CHANNEL_NAME, palette),
    }
    pngs = {k: os.path.join(work, f"slide_{k}.png") for k in static}
    for k, im in static.items():
        im.save(pngs[k])

    clips = []
    for name, start, length in segs:
        if name == "countdown":
            def mf(tt):
                img = slides.countdown_frame(bg, q["category"], q["question"],
                                             q["options"], palette,
                                             COUNTDOWN_S - tt, COUNTDOWN_S)
                return np.asarray(img)
            clips.append(VideoClip(mf, duration=length))
        else:
            c = (ImageClip(pngs[name], duration=length)
                 .resize(lambda tt: 1.0 + 0.018 * tt)
                 .set_position("center"))
            clips.append(c)
    video = concatenate_videoclips([c.set_duration(c.duration) for c in clips],
                                   method="compose")
    video = CompositeVideoClip([video], size=(slides.W, slides.H))

    # ---------- audio ----------
    tracks = []
    for k, segname in [("q", "question"), ("o", "options"), ("a", "reveal"),
                       ("e", "reveal"), ("c", "cta")]:
        start = at[segname]
        if k == "e":
            start += durs["a"] + 0.25
        tracks.append(AudioFileClip(paths[k]).set_start(start))
    # ticks each countdown second + final buzz
    tick_w = os.path.join(work, "tick.wav")
    syn.save_wav(tick_w, syn.tick())
    for s in range(COUNTDOWN_S):
        tracks.append(AudioFileClip(tick_w).set_start(at["countdown"] + s))
    buzz_w = os.path.join(work, "buzz.wav")
    syn.save_wav(buzz_w, syn.buzz())
    tracks.append(AudioFileClip(buzz_w).set_start(at["countdown"] + COUNTDOWN_S - 0.45))
    ding_w = os.path.join(work, "ding.wav")
    syn.save_wav(ding_w, syn.ding())
    tracks.append(AudioFileClip(ding_w).set_start(at["reveal"]))
    whoosh_w = os.path.join(work, "whoosh.wav")
    syn.save_wav(whoosh_w, syn.whoosh())
    tracks.append(AudioFileClip(whoosh_w).set_start(0))
    tracks.append(AudioFileClip(whoosh_w).set_start(at["reveal"]))
    music_w = os.path.join(work, "music.wav")
    syn.save_wav(music_w, syn.music_bed(total, vol=0.32))
    tracks.append(AudioFileClip(music_w).set_start(0).volumex(0.55))

    video = video.set_audio(CompositeAudioClip(tracks).set_duration(total))
    video = video.set_duration(total).set_fps(24)

    video.write_videofile(out_path, codec="libx264", audio_codec="aac",
                          preset="medium", threads=4, bitrate="6000k",
                          ffmpeg_params=["-pix_fmt", "yuv420p"], logger=None)

    thumb = slides.thumbnail(bg, q["category"], q["question"], palette)
    thumb_path = os.path.join(OUT, f"{tag}_thumb.jpg")
    thumb.save(thumb_path, quality=90)

    title = f"{q['category'].title()} Quiz: Can You Solve This? #shorts"
    desc = (f"{q['question']}\n\nComment your answer before the reveal! "
            f"New quiz every day on {CHANNEL_NAME}.\n#quiz #riddle #trivia #shorts")
    meta = {"id": tag, "title": title, "description": desc,
            "tags": ["quiz", "riddle", "trivia", "brain teaser", "shorts"],
            "video": out_path, "thumbnail": thumb_path, "duration": total}
    with open(out_path.replace(".mp4", ".json"), "w") as f:
        json.dump(meta, f, indent=2)
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", help="quiz id from content/quizzes.json")
    ap.add_argument("--all", action="store_true", help="generate every quiz")
    ap.add_argument("--seed", type=int)
    args = ap.parse_args()

    quizzes = json.load(open(os.path.join(BASE, "content", "quizzes.json")))
    if args.all:
        targets = quizzes
    elif args.id:
        targets = [q for q in quizzes if q["id"] == args.id]
    else:
        targets = [random.choice(quizzes)]
    if not targets:
        raise SystemExit(f"unknown id {args.id}")
    for qz in targets:
        meta = generate(qz, seed=args.seed)
        print(f"OK {meta['id']}: {meta['video']} ({meta['duration']:.1f}s)")
