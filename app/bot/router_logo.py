from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.bot.states import LogoGenerationStates
from app.utils import session_scope
from app.models import User, LogoJob
from openai import OpenAI
import os
import uuid
from datetime import datetime
from app.config import OPENAI_API_KEY, KIE_API_KEY
import requests
import time

router = Router()

def generate_logo(prompt: str) -> str:
    try:
        response = requests.post(
            "https://api.kie.ai/api/v1/gpt4o-image/generate",
            headers={
                "Authorization": f"Bearer {KIE_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": prompt,
                "enableTranslation": True,
                "aspectRatio": "3:4",
                "outputFormat": "png",
                "model": "gpt4o-image"
            }
        )
        response.raise_for_status()
        task_id = response.json()["data"]["taskId"]

        for _ in range(60):
            status_response = requests.get(
                "https://api.kie.ai/api/v1/gpt4o-image/record-info",
                headers={"Authorization": f"Bearer {KIE_API_KEY}"},
                params={"taskId": task_id}
            )
            status_response.raise_for_status()
            data = status_response.json().get("data", {})
            status = data.get("status")
            if status == "SUCCESS":
                break
            elif status in ("GENERATE_FAILED", "CREATE_TASK_FAILED"):
                return f"ERROR: {status}"
            time.sleep(2)

        result_urls = data.get("response", {}).get("resultUrls", [])
        return result_urls[0] if result_urls else "Image not generated."

    except Exception as e:
        return f"Error: {e}"

# Logo yaratish menyusi
@router.callback_query(F.data == "menu_logo")
async def logo_entry(callback: CallbackQuery, state: FSMContext):
    await state.set_state(LogoGenerationStates.waiting_description)
    await callback.message.edit_text(
        "🎨 Mavzuni yuboring (masalan: \"Dasturlash\").",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_back")]
        ])
    )
    await callback.answer()

@router.message(LogoGenerationStates.waiting_description)
async def got_description(m: Message, state: FSMContext):
    description = m.text.strip()
    await state.update_data(description=description)
    await state.set_state(LogoGenerationStates.waiting_style)
    await m.answer(
        "🖌 Logoning tavsifini yozing.\n"
        "(O'rtada noutbuk va noutbukda IT degan yozuv. Minimal, futiristik va zamonaviy dizayn)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_back")]
        ])
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
        f"✅ Logo yaratishni boshlaymi?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ha", callback_data="logo_confirm_yes")],
            [InlineKeyboardButton(text="❌ Yo'q", callback_data="logo_confirm_no")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_back")]
        ])
    )

@router.callback_query(F.data == "logo_confirm_yes")
async def generate_logo_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    full_prompt = data["full_prompt"]
    description = data["description"]
    style = data["style"]
    
    await callback.message.edit_text("🔄 Logo yaratilmoqda, iltimos kuting...")
    
    unique_id = uuid.uuid4().hex
    filename = f"logos/{callback.from_user.id}_{unique_id}.png"
    os.makedirs("logos", exist_ok=True)
    
    with session_scope() as db:
        user = db.query(User).filter(User.tg_id == str(callback.from_user.id)).first()
        if not user:
            await state.clear()
            return await callback.message.edit_text(
                "❌ OpenAI API kaliti noto'g'ri yoki limiti tugagan.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_back")]
                ])
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
            image_url = generate_logo(full_prompt)
            job.image_url = image_url
            job.filename = filename
            job.status = "completed"
            
            await callback.message.answer_photo(
                image_url,
                caption=f"🖼 Siz uchun yaratilgan logo!\n\n"
                        f"📝 Tavsif: {description}\n"
                        f"🎨 Uslub: {style}\n\n"
                        f"✅ Boshqa logo yaratish uchun /logo ni bosing.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="menu_back")]
                ])
            )
            
        except Exception as e:
            job.status = "failed"
            await callback.message.edit_text(
                f"❌ Logo yaratishda xato yuz berdi: {str(e)}\n\n"
                f"Qayta urinib ko'rish uchun /logo ni bosing.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="menu_back")]
                ])
            )
    
    await state.clear()

@router.callback_query(F.data == "logo_confirm_no")
async def cancel_logo_generation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Logo yaratish bekor qilindi.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="menu_back")]
        ])
    )
    await callback.answer()

# Eski komanda ham qolsin (agar kerak bo'lsa)
@router.message(Command("logo"))
async def logo_command(message: Message, state: FSMContext):
    await state.set_state(LogoGenerationStates.waiting_description)
    await message.answer(
        "🎨 Mavzuni yuboring (masalan: \"Dasturlash\").",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_back")]
        ])
    )