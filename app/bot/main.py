import asyncio
from aiogram import Bot, Dispatcher
from app.config import BOT_TOKEN
from app.db import init_db
from app.bot.router_base import router as base_router
from app.bot.router_seo import router as seo_router
from app.bot.router_upload import router as upload_router
from app.bot.router_statistics import router as statistics_router
from app.bot.router_logo import router as logo_router
from app.bot.router_banner import router as banner_router
from logging import basicConfig, INFO

basicConfig(level=INFO)

async def main():
    init_db()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(base_router)
    dp.include_router(seo_router)
    dp.include_router(upload_router)
    dp.include_router(statistics_router)
    dp.include_router(logo_router)
    dp.include_router(banner_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
