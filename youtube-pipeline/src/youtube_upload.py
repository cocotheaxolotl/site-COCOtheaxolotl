"""Upload a video to the Coco the Axolotl YouTube channel via YouTube Data API v3.

Setup (one-time):
  1. Create/use a Google Cloud project, enable YouTube Data API v3.
  2. Create OAuth 2.0 credentials (Desktop app), download the JSON.
  3. Save it to config/youtube_oauth.json.

First run opens a browser to authorize; the token is cached in
config/youtube_token.pickle for silent reuse.

NOTE: this MUST authorize the Coco channel — sign in with the Google account
that owns the Coco YouTube channel (likely cocotheaxolotl.book@gmail.com).
"""
import os
import sys
import pickle
from pathlib import Path
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "config" / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]
SECRETS_FILE = ROOT / os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "config/youtube_oauth.json")
TOKEN_FILE = ROOT / "config" / "youtube_token.pickle"


def get_service():
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not SECRETS_FILE.exists():
                raise FileNotFoundError(
                    f"Missing {SECRETS_FILE}. Download OAuth credentials from "
                    "Google Cloud Console (Desktop app) and save them there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)


def upload(video_path: Path, title: str, description: str = "",
           tags: list[str] | None = None, category_id: str = "24",
           privacy: str = "public", made_for_kids: bool = True,
           publish_at: str | None = None, thumbnail: Path | None = None) -> str:
    """Upload a video. Returns the YouTube video URL.

    For Coco channel:
      - default category 24 = Entertainment (kids content)
      - made_for_kids=True (COPPA — required for kids' content)
      - privacy: 'private' / 'public' / 'unlisted'
      - publish_at: ISO 8601 (e.g. '2026-04-30T18:00:00Z') for scheduled drop
    """
    yt = get_service()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": (tags or [])[:30],
            "categoryId": category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": "private" if publish_at else privacy,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }
    if publish_at:
        body["status"]["publishAt"] = publish_at

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    print(f"[yt] uploading {video_path.name} ({video_path.stat().st_size // 1024} KB)")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"[yt] {int(status.progress() * 100)}%")
    video_id = response["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"[yt] uploaded: {url}")

    if thumbnail and thumbnail.exists():
        print(f"[yt] uploading thumbnail {thumbnail.name}")
        yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumbnail))).execute()

    return url


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python youtube_upload.py <video.mp4> <title> [description] [tags,csv]")
        sys.exit(1)
    video = Path(sys.argv[1])
    title = sys.argv[2]
    desc = sys.argv[3] if len(sys.argv) > 3 else ""
    tags = sys.argv[4].split(",") if len(sys.argv) > 4 else []
    upload(video, title, desc, tags)
