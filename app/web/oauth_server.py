from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
from app.db import init_db
from app.utils import session_scope
from app.models import User
import json
from datetime import datetime
import logging
from fastapi.responses import HTMLResponse

app = FastAPI(title="YouTube Analytics Bot OAuth Server")
init_db()
logger = logging.getLogger(__name__)

# YouTube API uchun ruxsatlar
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.upload"
]

@app.get("/health")
async def health_check():
    return {"status": "ok", "time": datetime.now().isoformat()}

@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    try:
        code = request.query_params.get("code")
        if not code:
            return PlainTextResponse("Authorization code kerak", status_code=400)

        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI]
                }
            },
            scopes=YOUTUBE_SCOPES
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        flow.fetch_token(code=code)

        creds = flow.credentials
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
            "expiry": creds.expiry.isoformat() if creds.expiry else None
        }

        tg_user_id = request.query_params.get("state")
        if not tg_user_id:
            return PlainTextResponse("Google ulandi! Botga qayting.", status_code=200)

        with session_scope() as db:
            user = db.query(User).filter(User.tg_id == tg_user_id).first()
            if not user:
                user = User(
                    tg_id=tg_user_id,
                    created_at=datetime.utcnow(),
                    google_connected=True
                )
                db.add(user)
            else:
                user.google_connected = True  
                user.updated_at = datetime.now()
            user.google_token_json = json.dumps(token_data)
   
        bot_link = f"https://t.me/youtube_starter_bot?start=1"
        html_content = f"""
        <html>
            <head>
                <meta charset="utf-8" />
                <meta http-equiv="refresh" content="5;url={bot_link}" />
                <title>Google ulandi</title>
            </head>
            <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 100px;">
                <h2>✅ Sizning Google akkauntingiz muvaffaqiyatli ulandi!</h2>
                <p>Davom etish uchun quyidagi tugmani bosing:</p>
                <a href="{bot_link}" 
                style="display: inline-block; padding: 12px 20px; background: #0088cc; 
                        color: white; text-decoration: none; border-radius: 8px; font-size: 16px;">
                ➡️ Botga qaytish
                </a>
                <p style="margin-top:20px; color: gray; font-size: 14px;">
                    (Agar avtomatik ochilmasa, tugmani ustiga bosing)
                </p>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        logger.error(f"OAuth xatosi: {str(e)}")
        return PlainTextResponse(f"Xato: {str(e)}", status_code=400) 