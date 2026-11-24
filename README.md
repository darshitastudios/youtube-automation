# Quizzy Daily — Automated YouTube Shorts Pipeline

Fully automated pipeline that generates and uploads quiz/riddle Shorts to the
**Quizzy Daily** channel ([@QuizzyDaily-i8l](https://www.youtube.com/@QuizzyDaily-i8l))
with **$0/month** cost and zero manual steps.

## Quick links

- **Channel**: https://www.youtube.com/@QuizzyDaily-i8l
- **Actions (runs + Run-workflow button)**: https://github.com/darshitastudios/youtube-automation/actions
- **Schedule configs**: `.github/workflows/post_video_<channel>.yml` (cron line)
- **Repo Secrets**: https://github.com/darshitastudios/youtube-automation/settings/secrets/actions
- **Riddle bank**: `channels/quizzydaily/content/quizzes.json`
- **State DBs**: `channels/*/automation.db` (committed, auto-updated)
- **Architecture diagram**: `ARCHITECTURE.md`
- **Accounts inventory**: `ACCOUNTS-QUIZZY-DAILY.md`
- **Privacy/terms site**: https://darshitastudios.github.io/youtube-automation/
- **GCP console**: https://console.cloud.google.com/apis/dashboard?project=dark-depth-515715-n0
- **YouTube Studio**: https://studio.youtube.com

## How it works

```
GitHub Actions (2x/day)  →  daily_run.py  →  pick unused quiz
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

Each channel has its own `automation.db` — the single source of truth for "which riddles were already
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

- `channels/<name>/content/quizzes.json` — per-channel question bank. Add riddles as JSON.
- Repo **Secrets** (Settings → Secrets → Actions): `YT_CLIENT_ID`,
  `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` (OAuth for darshitastudios@gmail.com).
- Schedule: `cron` line in `.github/workflows/post_video.yml`
  (quizzydaily: `13 3,15 * * *` = twice daily, ~8:45 AM + 8:45 PM IST).
- Legal/OAuth pages: `index.html` served via GitHub Pages at
  https://darshitastudios.github.io/youtube-automation/ (required so the OAuth
  app stays published and the refresh token never expires).

## Repo layout

```
common/            shared engine: slides, tts, music, upload, state
  assets/fonts/
channels/<name>/   one dir per YouTube channel
  config.json      voice, language, title format, tags
  content/quizzes.json
  automation.db
.github/workflows/post_video_<name>.yml
out/  work/        generated videos (gitignored)
```

Add channel N+1 = new `channels/<name>/` dir + one workflow file + one
`YT_REFRESH_TOKEN_<NAME>` secret.

## Git branching strategy

- `main` — releases only. Tagged milestones.
- `dev` — integration branch; all work lands here first.
- `feature/<name>` — one branch per change, merged into `dev`, then `dev` → `main`.
- The Actions workflow only runs from `main`, so experiments on `dev` can't
  accidentally post videos.
- **Rule**: every code/feature change gets a local sample video generated
  (`python3 daily_run.py --dry-run`) and eyeballed before merging to `main`.
  Main must always be in a state that produces a good video.

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
