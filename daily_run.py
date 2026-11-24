#!/usr/bin/env python3
"""Daily automation: pick an unused quiz -> generate -> upload -> mark used.

Run manually:   python3 daily_run.py --dry-run   (generate only, no upload)
                python3 daily_run.py            (generate + upload)
Scheduled:      cron / Task Scheduler runs `python3 daily_run.py` once a day.
"""
import argparse
import json
import os
import sys

import generate_short
import state
import upload

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="generate but don't upload")
    ap.add_argument("--count", type=int, default=1, help="videos to produce this run")
    ap.add_argument("--publish-at", help="RFC3339 time to schedule publish")
    args = ap.parse_args()

    quizzes = json.load(open(os.path.join(BASE, "content", "quizzes.json")))
    for _ in range(args.count):
        quiz = state.pick_unused(quizzes)
        if not quiz:
            print("No unused quizzes left — add more to content/quizzes.json")
            break
        print(f"[{quiz['id']}] generating...")
        meta = generate_short.generate(quiz)
        if args.dry_run:
            print(f"[{quiz['id']}] dry run — generated {meta['video']}, not uploaded")
            continue
        print(f"[{quiz['id']}] uploading...")
        resp = upload.upload(meta["video"], meta["title"], meta["description"],
                             meta["tags"], made_for_kids=False,
                             publish_at=args.publish_at,
                             thumbnail_path=meta.get("thumbnail"))
        vid = resp.get("id")
        state.mark_uploaded(quiz["id"], vid, meta["title"])
        print(f"[{quiz['id']}] uploaded: https://youtu.be/{vid}")


if __name__ == "__main__":
    sys.exit(main())
