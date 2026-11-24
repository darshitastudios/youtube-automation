#!/usr/bin/env python3
"""Per-channel automation: pick an unused quiz -> generate -> upload -> mark used.

Run manually:   python3 daily_run.py --channel quizzydaily --dry-run
                python3 daily_run.py --channel quizzydaily
                python3 daily_run.py --channel quizfight
Scheduled via GitHub Actions workflows in .github/workflows/ (one per channel).
"""
import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "common"))

import generate_short
import state
import upload


def load_channel(name):
    cdir = os.path.join(BASE, "channels", name)
    cfg = json.load(open(os.path.join(cdir, "config.json")))
    cfg.setdefault("channel_name", cfg.get("name", name))
    cfg["quizzes_path"] = os.path.join(cdir, cfg.get("quizzes", "content/quizzes.json"))
    cfg["db_path"] = os.path.join(cdir, cfg.get("db", "automation.db"))
    return cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="quizzydaily", help="channel dir under channels/")
    ap.add_argument("--dry-run", action="store_true", help="generate but don't upload")
    ap.add_argument("--count", type=int, default=1, help="videos to produce this run")
    ap.add_argument("--publish-at", help="RFC3339 time to schedule publish")
    args = ap.parse_args()

    cfg = load_channel(args.channel)
    state.DB_PATH = cfg["db_path"]
    quizzes = json.load(open(cfg["quizzes_path"]))
    for _ in range(args.count):
        quiz = state.pick_unused(quizzes)
        if not quiz:
            print(f"[{args.channel}] No unused quizzes left — add more to {cfg['quizzes_path']}")
            break
        print(f"[{args.channel}/{quiz['id']}] generating...")
        meta = generate_short.generate(quiz, cfg=cfg)
        if args.dry_run:
            print(f"[{args.channel}/{quiz['id']}] dry run — generated {meta['video']}, not uploaded")
            continue
        print(f"[{args.channel}/{quiz['id']}] uploading...")
        resp = upload.upload(meta["video"], meta["title"], meta["description"],
                             meta["tags"], made_for_kids=False,
                             publish_at=args.publish_at,
                             thumbnail_path=meta.get("thumbnail"))
        vid = resp.get("id")
        state.mark_uploaded(quiz["id"], vid, meta["title"])
        print(f"[{args.channel}/{quiz['id']}] uploaded: https://youtu.be/{vid}")


if __name__ == "__main__":
    sys.exit(main())
