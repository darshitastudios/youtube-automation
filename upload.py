"""Upload a video to YouTube via Data API v3 using a stored OAuth refresh token.

Credentials come from environment variables (set in .env or CI secrets):
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
"""
import json
import os
import urllib.parse
import urllib.request

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


def _post(url, data, headers=None, raw=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    if raw is None:
        req.data = urllib.parse.urlencode(data).encode() if isinstance(data, dict) else data
        req.headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def access_token():
    return _post(TOKEN_URL, {
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    })["access_token"]


def set_thumbnail(token, video_id, png_path):
    with open(png_path, "rb") as f:
        data = f.read()
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/thumbnails/set?"
        + urllib.parse.urlencode({"videoId": video_id, "uploadType": "media"}),
        data=data,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "image/png",
                 "Content-Length": str(len(data))},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def upload(video_path, title, description, tags, made_for_kids=False, publish_at=None,
           thumbnail_path=None):
    """Resumable upload. publish_at: RFC3339 string to schedule, else private=False public."""
    token = access_token()
    size = os.path.getsize(video_path)
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": "private" if publish_at else "public",
            "selfDeclaredMadeForKids": made_for_kids,
            **({"publishAt": publish_at} if publish_at else {}),
        },
    }
    req = urllib.request.Request(
        UPLOAD_URL + "?" + urllib.parse.urlencode(
            {"uploadType": "resumable", "part": "snippet,status"}),
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(size),
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        session_uri = r.headers["Location"]
    with open(video_path, "rb") as f:
        req = urllib.request.Request(session_uri, data=f.read(),
                                     headers={"Content-Type": "video/mp4",
                                              "Content-Length": str(size)},
                                     method="PUT")
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read())  # contains "id"
    if thumbnail_path and resp.get("id"):
        try:
            set_thumbnail(token, resp["id"], thumbnail_path)
        except Exception as e:
            print(f"thumbnail upload failed (non-fatal): {e}")
    return resp
