import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from app.models import User
from sqlalchemy.orm import Session

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.upload"
]


def creds_from_user(user: User):
    if not user.google_token_json:
        return None
    data = json.loads(user.google_token_json)
    return Credentials.from_authorized_user_info(data, scopes=YOUTUBE_SCOPES)

def yt_service(user: User):
    creds = creds_from_user(user)
    if not creds:
        return None
    return build("youtube", "v3", credentials=creds)

def upload_video(db: Session, user: User, file_path: str, title: str, description: str, tags: list[str]):
    service = yt_service(user)
    if not service:
        raise RuntimeError("Google account ulangan emas. /connect bosing.")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22" 
        },
        "status": {"privacyStatus": "public"}
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    req = service.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = req.execute()
    return resp.get("id")

def set_thumbnail(user: User, yt_video_id: str, thumbnail_path: str):
    service = yt_service(user)
    if not service:
        raise RuntimeError("Google account ulangan emas.")
    media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
    return service.thumbnails().set(videoId=yt_video_id, media_body=media).execute()

def get_basic_stats(user: User):
    service = yt_service(user)
    if not service:
        raise RuntimeError("Google account ulangan emas.")
    chans = service.channels().list(part="statistics,snippet", mine=True).execute()
    return chans
