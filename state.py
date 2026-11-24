"""Tiny SQLite state store: which quizzes are used, what was uploaded."""
import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "automation.db")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute(
        """CREATE TABLE IF NOT EXISTS uploads (
               quiz_id TEXT PRIMARY KEY,
               uploaded_at TEXT,
               youtube_video_id TEXT,
               title TEXT
           )"""
    )
    c.commit()
    return c


def is_used(quiz_id):
    with _conn() as c:
        return c.execute("SELECT 1 FROM uploads WHERE quiz_id=?", (quiz_id,)).fetchone() is not None


def mark_uploaded(quiz_id, youtube_video_id, title):
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO uploads VALUES (?,?,?,?)",
            (quiz_id, datetime.now(timezone.utc).isoformat(), youtube_video_id, title),
        )


def mark_used_without_upload(quiz_id):
    mark_uploaded(quiz_id, None, None)


def pick_unused(quizzes):
    for q in quizzes:
        if not is_used(q["id"]):
            return q
    return None


def stats():
    with _conn() as c:
        rows = c.execute("SELECT quiz_id, uploaded_at, youtube_video_id FROM uploads ORDER BY uploaded_at").fetchall()
    return rows
