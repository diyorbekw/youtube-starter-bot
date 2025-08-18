
# YouTuber Starter Bot (Dockerized Skeleton)

## Quick start
1) `.env.example` ni ko‘chirib `.env` yarating va `TELEGRAM_BOT_TOKEN` ni to‘ldiring.
2) Google Cloud’da **Web application** OAuth client yarating va `app/client_secret.json` faylini qo‘ying.
3) Ishga tushiring:
```
docker compose up --build
```
4) Brauzerda `http://localhost:8000/oauth/start` ga kiring, OAuth ni tugating.
5) Telegram’da botga: `/start`, keyin `/optimize <url>` yoki `/analyze <channel_id>`.

## Komandalar
- `/optimize <url>` — SEO sarlavha/desc/tags/hashtag/hook
- `/thumb <matn>` — PNG thumbnail maketi
- `/schedule` — postlash vaqtlari
- `/analyze <channel_id|/channel/...>` — kanal statistikasi (OAuth kerak)
# youtube-starter-bot
