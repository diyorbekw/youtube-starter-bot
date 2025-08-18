from aiogram import Router, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.bot.states import LogoGenerationStates
from app.utils import session_scope
from app.models import User, LogoJob
from openai import OpenAI
import os
import uuid
from datetime import datetime
from app.config import OPENAI_API_KEY

router = Router()

@router.message(Command("logo"))
async def logo_entry(m: Message, state: FSMContext):
    await state.set_state(LogoGenerationStates.waiting_description)
    await m.answer(
        "🎨 Mavzuni yuboring (masalan: “Dasturlash”).",
        parse_mode=None
    )

@router.message(LogoGenerationStates.waiting_description)
async def got_description(m: Message, state: FSMContext):
    description = m.text.strip()
    await state.update_data(description=description)
    await state.set_state(LogoGenerationStates.waiting_style)
    await m.answer(
        "🖌 Logoning tavsifini yozing."
        "(O'rtada noutbuk va noutbukda IT degan yozuv. Minimal, futiristik va zamonaviy dizayn)",
        parse_mode=None
    )

@router.message(LogoGenerationStates.waiting_style)
async def got_style(m: Message, state: FSMContext):
    style = m.text.strip()
    data = await state.get_data()
    description = data["description"]
    
    await state.update_data(style=style)
    
    full_prompt = f"Theme: {description}, Description: {style}. Generate the logo for this YouTube Channel."
    
    await state.update_data(full_prompt=full_prompt)
    await state.set_state(LogoGenerationStates.waiting_confirmation)
    
    await m.answer(
        f"🔍 Sizning so'rovingiz:\n\n"
        f"📝 Mavzu: {description}\n"
        f"🎨 Tavsif: {style}\n\n"
        f"✅ Logo yaratishni boshlaymi?\nPastdagi tugmalardan foydalaning.",
        parse_mode=None,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Ha"),
                    KeyboardButton(text="Yo'q")
                ]
            ]
        )
    )

@router.message(LogoGenerationStates.waiting_confirmation, F.text.lower() == "ha")
async def generate_logo(m: Message, state: FSMContext):
    data = await state.get_data()
    full_prompt = data["full_prompt"]
    description = data["description"]
    style = data["style"]
    
    await m.answer("🔄 Logo yaratilmoqda, iltimos kuting...")
    
    unique_id = uuid.uuid4().hex
    filename = f"logos/{m.from_user.id}_{unique_id}.png"
    os.makedirs("logos", exist_ok=True)
    
    with session_scope() as db:
        user = db.query(User).filter(User.tg_id == str(m.from_user.id)).first()
        if not user:
            await state.clear()
            return await m.answer(
                "❌ OpenAI API kaliti noto'g'ri yoki limiti tugagan.",
                parse_mode=None
            )
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        job = LogoJob(
            user_id=user.id,
            description=description,
            style=style,
            prompt=full_prompt,
            status="processing",
            created_at=datetime.now()
        )
        db.add(job)
        db.flush()
        job_id = job.id
        
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size="1024x1024",
                quality="hd",
                n=1,
                response_format="url"
            )
            
            image_url = response.data[0].url
            job.image_url = image_url
            job.filename = filename
            job.status = "completed"
            
            await m.answer_photo(
                image_url,
                caption=f"🖼 Siz uchun yaratilgan logo!\n\n"
                        f"📝 Tavsif: {description}\n"
                        f"🎨 Uslub: {style}\n\n"
                        f"✅ Boshqa logo yaratish uchun /logo ni bosing."
            )
            
        except Exception as e:
            job.status = "failed"
            await m.answer(
                f"❌ Logo yaratishda xato yuz berdi: {str(e)}\n\n"
                f"Qayta urinib ko'rish uchun /logo ni bosing."
            )
    
    await state.clear()

@router.message(LogoGenerationStates.waiting_confirmation, F.text.lower() == "yo'q")
async def cancel_logo_generation(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("❌ Logo yaratish bekor qilindi. Qayta boshlash uchun /logo ni bosing.")