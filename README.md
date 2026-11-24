# Quizzy Daily — Automated YouTube Shorts Pipeline

Fully automated pipeline that generates and uploads quiz/riddle Shorts to the
**Quizzy Daily** channel ([@QuizzyDaily-i8l](https://www.youtube.com/@QuizzyDaily-i8l))
with **$0/month** cost and zero manual steps.

## How it works

```
GitHub Actions (every 4h)  →  daily_run.py  →  pick unused quiz
   → generate_short.py (TTS + slides + sfx → mp4 + thumbnail + metadata)
   → upload.py (YouTube Data API resumable upload + custom thumbnail)
   → state.py marks quiz used in automation.db
   → workflow commits automation.db back to this repo
```

| Piece | Tech | Cost |
|---|---|---|
| Voice | edge-tts (Microsoft neural voices) | free |
| Visuals | Pillow + moviepy, programmatic slides | free |
| Music/SFX | synthesized in `audio_synth.py` | free |
| Encode | ffmpeg | free |
| Upload | YouTube Data API v3 | free, ~6 uploads/day quota |
| Scheduler | GitHub Actions | free (public repo) |
| State | `automation.db` (SQLite) **committed in this repo** | free |

## Where state lives

`automation.db` is the single source of truth for "which riddles were already
posted". It is **tracked in git** — each Actions run commits the updated DB back
to `main`. There is no DB on the Mac anymore; the old local copy and the macOS
scheduler were removed (2026-11-24). Never run `daily_run.py` from two places
against different DBs — that caused the duplicate "echo" video.

## Commands

```bash
python3 daily_run.py --dry-run      # generate a video locally, don't upload
python3 daily_run.py                # pick + generate + upload one video
python3 daily_run.py --count 3      # up to ~6/day (API quota)
python3 daily_run.py --publish-at 2026-12-01T15:00:00Z   # scheduled publish
```

Instant upload without waiting for cron: GitHub → **Actions → Post video →
Run workflow**.

## Configuration

- `content/quizzes.json` — the question bank (~164 items). Add riddles as JSON.
- Repo **Secrets** (Settings → Secrets → Actions): `YT_CLIENT_ID`,
  `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` (OAuth for darshitastudios@gmail.com).
- Schedule: `cron` line in `.github/workflows/post_video.yml`
  (currently `13 */4 * * *` = every 4 hours for the test phase;
  planned steady state: `13 3,15 * * *` = twice daily).
- Legal/OAuth pages: `index.html` served via GitHub Pages at
  https://darshitastudios.github.io/youtube-automation/ (required so the OAuth
  app stays published and the refresh token never expires).

## Git branching strategy

- `main` — releases only. Tagged milestones.
- `dev` — integration branch; all work lands here first.
- `feature/<name>` — one branch per change, merged into `dev`, then `dev` → `main`.
- The Actions workflow only runs from `main`, so experiments on `dev` can't
  accidentally post videos.

Tag `v1.0.0` marks the first fully-working end-to-end pipeline (first automated
upload from GitHub Actions, OAuth app published, Mac-free operation).

## History / plan

1. Built the video engine (slides + TTS + ffmpeg) — samples approved.
2. Manual first upload from the user's Mac (`launchd` at 10 AM) — video 1 live.
3. Migrated to GitHub Actions — video 2+ uploaded with no Mac.
4. Published the OAuth app (GitHub Pages + Search Console verification) so the
   refresh token is permanent.

Roadmap: twice-daily posting, auto-refill of the riddle bank (free Gemini API),
more channels on the same Google account.
