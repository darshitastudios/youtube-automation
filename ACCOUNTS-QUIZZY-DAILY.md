# Quizzy Daily — Accounts & Credentials Inventory
_Last updated: 2026-11-24. This file intentionally contains NO secret values — only names and locations._

## Accounts

| # | Service | Login / email | What it holds | Set up by |
|---|---------|---------------|---------------|-----------|
| 1 | Google account | **darshitastudios@gmail.com** | Umbrella account — YouTube channel(s), GCP project, AdSense later | You (manual) |
| 2 | YouTube channel | **Quizzy Daily** — @QuizzyDaily-i8l | The channel videos get posted to | You (manual) |
| 3 | Google Cloud project | quizzy-daily (id `dark-depth-515715-n0`) | OAuth credentials + YouTube Data API | Devin |
| 4 | GitHub account | **darshitastudios** | Repo + automation | You |
| 5 | GitHub repo | `darshitastudios/youtube-automation` (PUBLIC) | Code, SQLite state DB, Actions workflow, Pages site | Devin |
| 6 | GitHub Pages | https://darshitastudios.github.io/youtube-automation/ | Privacy/Terms page (keeps OAuth app published) | Devin |
| 7 | Search Console | property `darshitastudios.github.io/youtube-automation/` | Domain verification for OAuth | Devin |
| 8 | Google Sites | sites.google.com/view/quizzydaily | Early draft — unused, can delete | Devin |

## Secrets — names and locations only

| Secret | Where it lives | Purpose |
|--------|----------------|---------|
| Google password | your password manager | Login to the Google account |
| `YT_CLIENT_ID` / `YT_CLIENT_SECRET` / `YT_REFRESH_TOKEN` | GitHub repo Secrets + Mac `.env` | YouTube upload auth (permanent — OAuth app is published) |
| GitHub PAT | git remote config on Mac + Devin VM | Push/pull; expires ~Feb 2026, renew at github.com/settings/tokens?type=beta |
| `automation.db` | in this repo | used-riddle tracking (not a secret) |

## Renewal reminders
- GitHub PAT: ~every 90 days. Everything else is permanent.
