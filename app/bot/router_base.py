# app/bot/routers/base.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.markdown import html_decoration as hd
from app.config import GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI, YOUTUBE_SCOPES
from app.utils import session_scope
from app.models import User
from urllib.parse import quote
from datetime import datetime

router = Router()

# Foydalanuvchi Google bilan ulanganligini tekshirish
async def is_google_connected(user_id: str) -> bool:
    with session_scope() as db:
        user = db.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return False
        # Explicitly convert to boolean in case it's None
        return bool(user.google_connected)

# Google avtorizatsiya havolasini yaratish
def create_google_auth_url(user_id: str) -> str:
    return (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={quote(GOOGLE_REDIRECT_URI)}"
        "&response_type=code"
        "&access_type=offline"
        "&prompt=consent"
        f"&scope={'%20'.join(YOUTUBE_SCOPES)}"
        f"&state={user_id}"
    )

# Asosiy menyuni ko'rsatish
async def show_main_menu(message: Message):
    menu_text = hd.bold("🏠 Asosiy menyu") + "\n\n" + "\n".join([
        "📊 Kanal statistikasi - /statistics",
        "🎬 Video yuklash - /upload",
        "🖼️ Banner yaratish - /banner",
        "🆔 Logo yaratish - /logo",
        "🔍 SEO optimallashtirish - /seo",
        "ℹ️ Yordam - /help"
    ])
    
    await message.answer(menu_text, parse_mode="HTML")

# Start komandasi
@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(text="Iltimos, ozgina kutib turing. Ma'lumotlar yuklanmoqda...")
    
    user_id = str(message.from_user.id)
    print(f"Start command from {user_id}")  # Debug
    
    with session_scope() as db:
        user = db.query(User).filter(User.tg_id == user_id).first()
        print(f"User exists: {user is not None}")  # Debug
        if user:
            print(f"Google connected: {user.google_connected}")  # Debug
        if not user:
            user = User(
                tg_id=user_id,
                created_at=datetime.now(),
                google_connected=False
            )
            db.add(user)
            db.flush()  # Ensure user is created immediately
    
    connected = await is_google_connected(user_id)
    print(f"Is connected: {connected}")  # Debug
    
    if connected:
        await show_main_menu(message)
    else:
        auth_url = create_google_auth_url(user_id)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Google bilan ulanish", url=auth_url)]
        ])
        
        await message.answer(
            "👋 Assalomu alaykum! Botdan to'liq foydalanish uchun "
            "Google hisobingizni ulashing:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

# Connect komandasi
@router.message(Command("connect"))
async def connect_command(message: Message):
    user_id = str(message.from_user.id)
    
    if await is_google_connected(user_id):
        await message.answer("✅ Siz allaqachon Google hisobingizni ulagansiz!")
        return
        
    auth_url = create_google_auth_url(user_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Google bilan ulanish", url=auth_url)]
    ])
    
    await message.answer(
        "Google hisobingizni ulash uchun quyidagi tugmani bosing:",
        reply_markup=keyboard
    )

# Yordam menyusi
@router.message(Command("help"))
async def help_command(message: Message):
    if not await is_google_connected(str(message.from_user.id)):
        await message.answer("ℹ️ Avval Google hisobingizni ulashing: /connect")
        return
        
    help_text = hd.bold("🆘 Yordam menyusi") + "\n\n" + "\n".join([
        "/stats - Kanal statistikasini ko'rish",
        "/upload - YouTube'ga video yuklash",
        "/banner - Kanal uchun banner yaratish",
        "/logo - Kanal uchun logo yaratish",
        "/seo - Video uchun SEO optimallashtirish",
        "/connect - Google hisobini ulash"
    ])
    
    await message.answer(help_text)

@router.message(Command("myinfo"))
async def myinfo_command(message: Message):
    user_id = str(message.from_user.id)
    
    with session_scope() as db:
        user = db.query(User).filter(User.tg_id == user_id).first()
        if user:
            response = (
                f"🆔 ID: {user.id}\n"
                f"🔗 TG ID: {user.tg_id}\n"
                f"🔌 Google Connected: {user.google_connected}\n"
                f"🕒 Created: {user.created_at}\n"
                f"🔄 Updated: {getattr(user, 'updated_at', 'N/A')}"
            )
        else:
            response = "❌ Siz ro'yxatdan o'tmagansiz"
    
    await message.answer(response)