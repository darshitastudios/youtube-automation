# Architecture — Quizzy Daily Pipeline

```mermaid
flowchart LR
    subgraph GH["GitHub (darshitastudios/youtube-automation — public repo)"]
        CRON["Actions cron<br/>every 4h / Run-workflow button"]
        WF["Workflow<br/>post_video.yml<br/>Ubuntu runner:<br/>ffmpeg + pip deps"]
        DB[("automation.db<br/>SQLite — used riddles")]
        JSON["content/quizzes.json<br/>~164 riddles"]
        SEC[/"Repo Secrets<br/>YT_CLIENT_ID /<br/>YT_CLIENT_SECRET /<br/>YT_REFRESH_TOKEN"/]
        PAGES["GitHub Pages<br/>privacy + terms"]
    end

    subgraph PIPE["daily_run.py pipeline"]
        PICK["pick_unused()<br/>first unused riddle"]
        GEN["generate_short.py<br/>• slides.py (Pillow graphics)<br/>• edge-tts voice<br/>• audio_synth.py music/sfx<br/>• moviepy+ffmpeg → mp4 + thumbnail"]
        UP["upload.py<br/>resumable upload +<br/>custom thumbnail"]
        MARK["mark used in DB"]
    end

    subgraph GOOG["Google"]
        GCP["GCP project quizzy-daily<br/>OAuth client (published)<br/>YouTube Data API v3"]
        YT[("YouTube<br/>@QuizzyDaily-i8l")]
        SC["Search Console<br/>domain verified"]
    end

    CRON --> WF
    WF --> PICK
    JSON --> PICK
    DB -->|already used?| PICK
    PICK --> GEN
    GEN -->|mp4 + png + title/tags| UP
    SEC -->|env vars| UP
    UP -->|HTTPS upload| GCP
    GCP -->|video published| YT
    UP --> MARK
    MARK -->|git commit + push| DB
    PAGES -->|authorized domain| SC
    SC -->|keeps OAuth app published| GCP
    PAGES -.->|required links| GCP
```

**Files each step uses**

| Step | Files | Output |
|---|---|---|
| Pick | `state.py`, `content/quizzes.json`, `automation.db` | next unused riddle |
| Generate | `generate_short.py`, `slides.py`, `audio_synth.py`, `assets/fonts/` | `out/*.mp4`, `out/*.png`, metadata |
| Upload | `upload.py` + `YT_*` secrets | YouTube video URL |
| Track | `state.py` → `automation.db` | committed back to repo |

**Nothing runs on your Mac** — it only holds a git clone + `.env` backup.
