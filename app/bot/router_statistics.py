from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.utils import session_scope
from app.models import User
import datetime
import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

router = Router()

def get_youtube_service(user):
    creds = Credentials.from_authorized_user_info(json.loads(user.google_token_json))
    return build("youtube", "v3", credentials=creds)

def get_analytics_service(user):
    creds = Credentials.from_authorized_user_info(json.loads(user.google_token_json))
    return build("youtubeAnalytics", "v2", credentials=creds)

@router.message(Command("statistics"))
async def statistics_cmd(m: Message):
    with session_scope() as db:
        user = db.query(User).filter(User.tg_id == str(m.from_user.id)).first()
        if not user or not user.google_token_json:
            return await m.answer("❌ Google ulanmagan. Avval /connect buyrug‘ini bosing.")

        yt = get_youtube_service(user)
        ya = get_analytics_service(user)

        channel_resp = yt.channels().list(
            part="snippet,statistics,contentDetails",
            mine=True
        ).execute()

        if not channel_resp["items"]:
            return await m.answer("❌ Kanal topilmadi.")

        channel = channel_resp["items"][0]
        title = channel["snippet"]["title"]
        subs = channel["statistics"].get("subscriberCount", "0")
        views = channel["statistics"].get("viewCount", "0")
        videos_count = channel["statistics"].get("videoCount", "0")

        total_likes = 0
        total_comments = 0
        next_page = None
        while True:
            vids = yt.search().list(
                part="id",
                channelId=channel["id"],
                maxResults=50,
                pageToken=next_page,
                type="video"
            ).execute()

            if not vids.get("items"):
                break

            video_ids = [v["id"]["videoId"] for v in vids["items"]]
            stats_resp = yt.videos().list(
                part="statistics",
                id=",".join(video_ids)
            ).execute()

            for item in stats_resp.get("items", []):
                total_likes += int(item["statistics"].get("likeCount", 0))
                total_comments += int(item["statistics"].get("commentCount", 0))

            next_page = vids.get("nextPageToken")
            if not next_page:
                break

        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=28)

        analytics_resp = ya.reports().query(
            ids="channel==MINE",
            startDate=start_date.isoformat(),
            endDate=end_date.isoformat(),
            metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost,likes",
            dimensions="day",
            sort="day"
        ).execute()

        total_views_28 = 0
        total_minutes_28 = 0
        gained_28 = 0
        lost_28 = 0
        likes_28 = 0

        if "rows" in analytics_resp:
            for r in analytics_resp["rows"]:
                total_views_28 += int(r[1])
                total_minutes_28 += int(r[2])
                gained_28 += int(r[3])
                lost_28 += int(r[4])
                likes_28 += int(r[5])

        uploads_playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        playlist_items = yt.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist,
            maxResults=5
        ).execute()

        video_ids = [item["snippet"]["resourceId"]["videoId"] for item in playlist_items["items"]]

        stats_resp = yt.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids)
        ).execute()

        video_stats = []
        for item in stats_resp["items"]:
            v_title = item["snippet"]["title"]
            v_views = item["statistics"].get("viewCount", "0")
            v_likes = item["statistics"].get("likeCount", "0")
            v_comments = item["statistics"].get("commentCount", "0")
            video_stats.append(f"🎬 {v_title}\n👁 {v_views} | 👍 {v_likes} | 💬 {v_comments}")

        text = (
            f"📊 *Kanal statistikasi*\n"
            f"📌 Nomi: {title}\n"
            f"👥 Obunachilar: {subs}\n"
            f"👁 Ko‘rishlar: {views}\n"
            f"🎞 Videolar soni: {videos_count}\n"
            f"👍 Umumiy layklar: {total_likes}\n"
            f"💬 Umumiy kommentlar: {total_comments}\n\n"
            f"📈 *So‘nggi 28 kun*\n"
            f"👁 Ko‘rishlar: {total_views_28}\n"
            f"⏳ Tomosha vaqti: {total_minutes_28} daqiqa\n"
            f"📈 Obunachilar qo‘shildi: {gained_28}\n"
            f"📉 Obunachilar ketdi: {lost_28}\n"
            f"👍 Layklar: {likes_28}\n\n"
        )

        if video_stats:
            text += "🆕 *So‘nggi 5 video (real-time)*:\n" + "\n\n".join(video_stats)

        await m.answer(text, parse_mode="Markdown")
