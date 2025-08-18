from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.ai import gen_seo

router = Router()

class SeoStates(StatesGroup):
    waiting_topic = State()

@router.message(Command("seo"))
async def seo_entry(m: Message, state: FSMContext):
    await state.set_state(SeoStates.waiting_topic)
    await m.answer("📌 Mavzuni yuboring (masalan: “Premyera: Python FastAPI darsi 1”).")

@router.message(SeoStates.waiting_topic)
async def got_topic(m: Message, state: FSMContext):
    topic = m.text.strip()
    if not topic:
        return await m.answer("❌ Mavzu bo‘sh bo‘lishi mumkin emas.")

    data = gen_seo(topic)
    title = data.get("title", "")
    description = data.get("description", "")
    tags = ", ".join(data.get("tags", []))

    await m.answer(
        f"🎯 Title:\n{title}\n\n"
        f"📝 Description:\n{description}\n\n"
        f"🏷 Tags:\n{tags}",
        parse_mode=None
    )
    await state.clear()
