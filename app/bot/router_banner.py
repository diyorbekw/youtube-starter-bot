from aiogram import Router, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.bot.states import BannerGenerationStates
from app.utils import session_scope
from app.models import User, BannerJob
from openai import OpenAI
import os
import uuid
from datetime import datetime
from app.config import OPENAI_API_KEY
from PIL import Image, ImageOps
import requests

router = Router()

@router.message(Command("banner"))
async def banner_entry(m: Message, state: FSMContext):
    await state.set_state(BannerGenerationStates.waiting_description)
    await m.answer("🎨 Kanalingizda nima haqida video qo'yasiz?")

@router.message(BannerGenerationStates.waiting_description)
async def got_description_banner(m: Message, state: FSMContext):
    description = m.text.strip()
    await state.update_data(description=description)
    await state.set_state(BannerGenerationStates.waiting_style)
    await m.answer("🖌 Kanalingizning nomini kiriting")

@router.message(BannerGenerationStates.waiting_style)
async def got_style_banner(m: Message, state: FSMContext):
    style = m.text.strip()
    data = await state.get_data()
    description = data["description"]

    await state.update_data(style=style)

    full_prompt = f"Theme: {description}, Channel name: {style}. Generate the banner for this YouTube Channel."
    await state.update_data(full_prompt=full_prompt)
    await state.set_state(BannerGenerationStates.waiting_confirmation)

    await m.answer(
        f"🔍 Sizning so'rovingiz:\n\n"
        f"📝 Mavzu: {description}\n"
        f"🎨 Tavsif: {style}\n\n"
        f"✅ Banner yaratishni boshlaymi?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Ha"), KeyboardButton(text="Yo'q")]
            ]
        )
    )

@router.message(BannerGenerationStates.waiting_confirmation, F.text.lower() == "ha")
async def generate_banner(m: Message, state: FSMContext):
    data = await state.get_data()
    full_prompt = data["full_prompt"]
    description = data["description"]
    style = data["style"]

    await m.answer("🔄 Banner yaratilmoqda, iltimos kuting...")

    unique_id = uuid.uuid4().hex
    raw_filename = f"banners/{m.from_user.id}_{unique_id}_raw.png"
    final_filename = f"banners/{m.from_user.id}_{unique_id}.png"
    os.makedirs("banners", exist_ok=True)

    with session_scope() as db:
        user = db.query(User).filter(User.tg_id == str(m.from_user.id)).first()
        if not user:
            await state.clear()
            return await m.answer("❌ OpenAI API kaliti ulanmagan. Avval /connect_openai ni bosing.")

        client = OpenAI(api_key=OPENAI_API_KEY)

        job = BannerJob(
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
                size="1792x1024",
                quality="hd",
                n=1,
                response_format="url"
            )

            image_url = response.data[0].url

            r = requests.get(image_url)
            with open(raw_filename, "wb") as f:
                f.write(r.content)

            img = Image.open(raw_filename)
            target_size = (2560, 1440)
            img = ImageOps.contain(img, target_size) 
            new_img = Image.new("RGB", target_size, (255, 255, 255))
            paste_x = (target_size[0] - img.width) // 2
            paste_y = (target_size[1] - img.height) // 2
            new_img.paste(img, (paste_x, paste_y))
            new_img.save(final_filename, "PNG")

            job.image_url = image_url
            job.filename = final_filename
            job.status = "completed"


            with open(final_filename, 'rb') as file:
                photo_bytes = file.read()

            photo = BufferedInputFile(photo_bytes, filename=final_filename)

            await m.answer_photo(
                photo=photo,
                caption=(
                    f"🖼 Siz uchun yaratilgan banner!\n\n"
                    f"📝 Tavsif: {description}\n"
                    f"🎨 Uslub: {style}\n\n"
                    f"✅ Boshqa banner yaratish uchun /banner ni bosing."
                )
            )

        except Exception as e:
            job.status = "failed"
            await m.answer(f"❌ Banner yaratishda xato yuz berdi: {str(e)}")

    await state.clear()

@router.message(BannerGenerationStates.waiting_confirmation, F.text.lower() == "yo'q")
async def cancel_banner_generation(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("❌ Banner yaratish bekor qilindi. Qayta boshlash uchun /banner ni bosing.")
