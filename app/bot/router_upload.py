from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.bot.states import UploadStates
from app.utils import session_scope
from app.models import User, VideoJob
from app.ai import gen_seo
from app.thumbnail import make_simple_thumbnail
from app.youtube import upload_video, set_thumbnail
import os

router = Router()

@router.message(Command("upload"))
async def upload_entry(m: Message, state: FSMContext):
    await state.set_state(UploadStates.waiting_topic)
    await m.answer(
        "📌 Video mavzusini yuboring (masalan: C++ boshlang’ich dars).",
        parse_mode=None
    )

@router.message(UploadStates.waiting_topic)
async def got_topic(m: Message, state: FSMContext):
    topic = m.text.strip()
    await state.update_data(topic=topic)
    await state.set_state(UploadStates.waiting_video_file)
    await m.answer(
        "🔼 Endi video faylni yuboring (.mp4).",
        parse_mode=None
    )

@router.message(UploadStates.waiting_video_file, F.video | F.document)
async def got_video(m: Message, state: FSMContext):
    data = await state.get_data()
    topic = data["topic"]

    file = m.video or m.document
    file_name = f"uploads/{m.from_user.id}_{file.file_unique_id}.mp4"
    os.makedirs("uploads", exist_ok=True)
    file_obj = await m.bot.get_file(file.file_id)
    await m.bot.download_file(file_obj.file_path, destination=file_name)

    seo = gen_seo(topic)
    title = seo.get("title", topic)[:100]
    description = seo.get("description", "")
    tags = seo.get("tags", ["youtube", "video"])

    clean_tags = []
    for t in tags:
        cleaned = t.strip().replace(' ', '').replace("'", '').replace('ʼ', '')
        clean_tags.append(f"#{cleaned}")
    tags = clean_tags



    
    title = title + " | " + f"{', '.join(tags[:2])}"
    description = description + "\n\n" + f"{', '.join(tags[2:])}"

    thumb_path = f"uploads/{m.from_user.id}_{file.file_unique_id}.jpg"
    make_simple_thumbnail(title, thumb_path)

    with session_scope() as db:
        user = db.query(User).filter(User.tg_id == str(m.from_user.id)).first()
        if not user or not user.google_token_json:
            await state.clear()
            return await m.answer(
                "❌ Google ulanmagan. Avval /connect ni bosing.",
                parse_mode=None
            )

        job = VideoJob(
            user_id=user.id,
            topic=topic,
            title=title,
            description=description,
            tags=",".join(tags),
            file_path=file_name,
            thumbnail_path=thumb_path,
            status="draft"
        )
        db.add(job)
        db.flush()
        job_id = job.id

        try:
            yt_id = upload_video(db, user, file_name, title, description, tags)
            set_thumbnail(user, yt_id, thumb_path)
            job.yt_video_id = yt_id
            job.status = "uploaded"
            msg = f"✅ Yuklandi! YouTube video ID: {yt_id}"
        except Exception as e:
            job.status = "failed"
            msg = f"❌ Yuklashda xato: {e}"

    await state.clear()
    await m.answer(
        f"🎯 Mavzu: {topic}\n"
        f"🧠 Title: {title}\n"
        f"🏷 Tags: {', '.join(tags)}\n"
        f"{msg}",
        parse_mode=None
    )
