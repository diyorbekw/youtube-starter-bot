from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
from app.utils import session_scope
from app.models import User
import json
import pandas as pd
import logging
import io

router = Router()
logger = logging.getLogger(__name__)

def get_analytics_service(credentials):
    return build(
        'youtubeAnalytics',
        'v2',
        credentials=credentials,
        static_discovery=False
    )

def get_youtube_service(credentials):
    return build(
        'youtube',
        'v3',
        credentials=credentials,
        static_discovery=False
    )

@router.message(Command("stats"))
async def get_channel_stats(message: Message, days: int = 30):
    with session_scope() as db:
        user = db.query(User).filter(User.tg_id == str(message.from_user.id)).first()
        if not user or not user.google_token_json:
            return await message.answer("❌ Iltimos, avval /connect buyrug'i orqali Google hisobingizni ulang.")

        try:
            creds = Credentials.from_authorized_user_info(
                json.loads(user.google_token_json),
                scopes=[
                    "https://www.googleapis.com/auth/yt-analytics.readonly",
                    "https://www.googleapis.com/auth/youtube.readonly"
                ]
            )

            # Sana oralig'ini hisoblash
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)

            # Statistik ma'lumotlarni olish
            analytics = get_analytics_service(creds)
            report = analytics.reports().query(
                ids="channel==MINE",
                startDate=start_date.strftime("%Y-%m-%d"),
                endDate=end_date.strftime("%Y-%m-%d"),
                metrics="views,likes,subscribersGained",
                dimensions="day"
            ).execute()

            # Excel fayl yaratish
            if 'rows' in report:
                df = pd.DataFrame(
                    report['rows'],
                    columns=['Kun', 'Koʻrishlar', 'Layklar', 'Yangi obunachilar']
                )
                
                # BytesIO o'rniga to'g'ridan-to'g'ri baytlar yaratish
                excel_bytes = io.BytesIO()
                df.to_excel(excel_bytes, index=False, engine='openpyxl')
                excel_bytes.seek(0)
                
                # BufferedInputFile ishlatish
                excel_file = BufferedInputFile(
                    file=excel_bytes.getvalue(),
                    filename=f"youtube_stats_{days}kun.xlsx"
                )
                
                await message.answer_document(
                    document=excel_file,
                    caption=f"📊 YouTube statistikasi ({days} kun)"
                )
            else:
                await message.answer("❌ Statistika ma'lumotlari topilmadi.")

        except Exception as e:
            logger.error(f"Stats xatosi: {str(e)}")
            await message.answer(f"❌ Xato yuz berdi: {str(e)}")