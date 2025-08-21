from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.ai import gen_seo

router = Router()

class SeoStates(StatesGroup):
    waiting_topic = State()

# SEO tavsiyalari menyusi
@router.callback_query(F.data == "menu_seo")
async def seo_entry(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SeoStates.waiting_topic)
    await callback.message.edit_text(
        "📌 Mavzuni yuboring (masalan: \"Premyera: Python FastAPI darsi 1\").",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_back")]
        ])
    )
    await callback.answer()

@router.message(SeoStates.waiting_topic)
async def got_topic(m: Message, state: FSMContext):
    topic = m.text.strip()
    if not topic:
        return await m.answer(
            "❌ Mavzu bo'sh bo'lishi mumkin emas.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_back")]
            ])
        )

    data = gen_seo(topic)
    title = data.get("title", "")
    description = data.get("description", "")
    tags = ", ".join(data.get("tags", []))

    await m.answer(
        f"🎯 Title:\n{title}\n\n"
        f"📝 Description:\n{description}\n\n"
        f"🏷 Tags:\n{tags}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="menu_back")]
        ])
    )
    await state.clear()

# Eski komanda ham qolsin (agar kerak bo'lsa)
@router.message(Command("seo"))
async def seo_command(message: Message, state: FSMContext):
    await state.set_state(SeoStates.waiting_topic)
    await message.answer(
        "📌 Mavzuni yuboring (masalan: \"Premyera: Python FastAPI darsi 1\").",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_back")]
        ])
    )