# app/bot/routers/base.py
from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.markdown import html_decoration as hd
from app.config import GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI, YOUTUBE_SCOPES, BOT_TOKEN
from app.utils import session_scope
from app.models import User
from urllib.parse import quote
from datetime import datetime


router = Router()

bot = Bot(token=BOT_TOKEN)

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

# Asosiy menyu tugmalarini yaratish
def create_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Video Yuklash", callback_data="menu_upload"),
            InlineKeyboardButton(text="📊 Statistika", callback_data="menu_statistics")
        ],
        [
            InlineKeyboardButton(text="🔍 SEO Tavsiyalari", callback_data="menu_seo"),
            InlineKeyboardButton(text="ℹ️ Yordam", callback_data="menu_help")
        ],
        [
            InlineKeyboardButton(text="👤 Akkaunt", callback_data="menu_myinfo"),
        ]
    ])

# Asosiy menyuni ko'rsatish
async def show_main_menu(message: Message):
    menu_text = ("<b>🏠 Asosiy menyu</b>\n\n"
                 "Quyidagi tugmalar orqali kerakli bo'limni tanlang:")
    
    await message.answer(menu_text, parse_mode="HTML", reply_markup=create_main_menu_keyboard())

# Yordam menyusi uchun handler
@router.callback_query(F.data == "menu_help")
async def help_callback_handler(callback: CallbackQuery):
    help_text = ("<b>🆘 Yordam menyusi</b>\n\n"
                 "<b>📊 Statistika</b> — Kanal statistikasi (tomosha, obunachilar, daromad bo‘yicha ko‘rsatkichlar)\n"
                 "<b>🎬 Video Yuklash</b> — Video yuklash: sarlavha, ta'rif, teglar va maxfiylik sozlamalari\n"
                 "<b>🖼️ Banner Yaratish</b> — Kanal banneri (tezkor shablonlar va sozlamalar)\n"
                 "<b>🆔 Logo Yaratish</b> — Brendingiz uchun tez logo generator\n"
                 "<b>🔍 SEO Tavsiyalari</b> — Video uchun SEO tavsiyalari va optimallashtirish\n"
                 "<b>🔗 Google Ulash</b> — Google hisobini qayta ulash yoki tasdiqlash\n\n"
                 "<i>Har bir bo'lim haqida batafsil ko‘rsatmalarni olmoqchi bo‘lsangiz, bo'lim nomini tanlang.</i>")
    
    await callback.message.edit_text(
        help_text, 
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_back")]
        ])
    )
    await callback.answer()

# Orqaga qaytish handler
@router.callback_query(F.data == "menu_back")
async def back_callback_handler(callback: CallbackQuery):
    menu_text = ("<b>🏠 Asosiy menyu</b>\n\n"
                 "Quyidagi tugmalar orqali kerakli bo'limni tanlang:")
    
    await callback.message.edit_text(
        menu_text, 
        parse_mode="HTML", 
        reply_markup=create_main_menu_keyboard()
    )
    await callback.answer()

# Start komandasi
@router.message(Command("start"))
async def start_command(message: Message):
    msg = await message.answer(text="Iltimos, sabr qiling — ma'lumotlar yuklanmoqda…\n\n<b>⚡ Tez orada asosiy menyu ochiladi.</b>\n<i>Bu jarayon sizning hisobingiz va kanal ma'lumotlarini xavfsiz tekshirish uchun kerak.</i>",
                         parse_mode="HTML")
    
    msg_id = msg.message_id
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
        await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        await show_main_menu(message)
    else:
        auth_url = create_google_auth_url(user_id)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Google bilan ulanish", url=auth_url)]
        ])
        
        await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        await message.answer(
            ("<b>👋 Assalomu alaykum!</b>\n\n"
"Botdan to‘liq foydalanishingiz uchun Google hisobingizni bog‘lang. "
"Bu sizga kanal statistikasi, video yuklash va dizayn vositalaridan foydalanish imkonini beradi.\n\n"
"<i>Maxfiylik haqida:</i> biz parolingizni so‘ramaymiz — faqat zarur ruxsatlar olinadi.\n\n"
"<b>Quyidagi tugmaga bosib, xavfsiz tarzda ulanishingiz mumkin:</b>"),
            reply_markup=keyboard,
            parse_mode="HTML"
        )

# Connect komandasi
@router.message(Command("connect"))
async def connect_command(message: Message):
    user_id = str(message.from_user.id)
    
    if await is_google_connected(user_id):
        await message.answer("<b>✅ Muvaffaqiyatli:</b> Siz allaqachon Google hisobingizni ulagansiz. "
"Kerak bo‘lsa /statistics yoki boshqa buyruqlardan foydalaning.", parse_mode="HTML")
        return
        
    auth_url = create_google_auth_url(user_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Google bilan ulanish", url=auth_url)]
    ])
    
    await message.answer(
        "<b>🔐 Google bilan ulanish</b>\n\n"
"Quyidagi tugma orqali rasmiy Google avtorizatsiyasi oynasiga yo‘naltirilasiz. "
"Ulanish yakunlangach, barcha funksiyalar ishga tushadi.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "menu_myinfo")
async def myinfo_command(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    
    with session_scope() as db:
        user = db.query(User).filter(User.tg_id == user_id).first()
        if user:
            response = (
                "<b>👤 Siz haqingizda ma'lumot</b>\n\n"
f"<b>🆔 ID:</b> {user.id}\n"
f"<b>🔗 TG ID:</b> {user.tg_id}\n"
f"<b>🔌 Google ulangan:</b> {'Ha' if user.google_connected else 'Yoq'}\n"
f"<b>🕒 Ro'yxatdan o'tgan:</b> {user.created_at.strftime('%d/%m/%y')}\n"
            )
        else:
            response = ("<b>❌ Siz ro'yxatdan o'tmagansiz.</b>\n\n"
"Ro'yxatdan o‘tish uchun /start buyrug‘ini bering yoki /connect tugmasi orqali Google bilan ulang.")
    
    await callback.message.edit_text(response, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_back")]
        ]))