import asyncio
import os
import re
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from config import ALLOWED_IDS, GROUP_ID, TEMP_DIR
from states import UploadFlow
from services.merger import merge_to_pdf
from services.db import save_document

router = Router()

# Per-user lock to prevent race conditions when multiple files arrive simultaneously
_user_locks: dict[int, asyncio.Lock] = {}


def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_IDS


def get_user_lock(user_id: int) -> asyncio.Lock:
    if user_id not in _user_locks:
        _user_locks[user_id] = asyncio.Lock()
    return _user_locks[user_id]


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:60]


async def download_file(bot: Bot, message: Message, dest_dir: str) -> str | None:
    os.makedirs(dest_dir, exist_ok=True)

    if message.document:
        mime = message.document.mime_type or ""
        if "pdf" in mime or "image" in mime:
            file = await bot.get_file(message.document.file_id)
            ext = os.path.splitext(message.document.file_name or "file")[1] or ".pdf"
            dest = os.path.join(dest_dir, f"{message.document.file_id}{ext}")
            await bot.download_file(file.file_path, dest)
            return dest

    elif message.photo:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        dest = os.path.join(dest_dir, f"{photo.file_id}.jpg")
        await bot.download_file(file.file_path, dest)
        return dest

    return None


# ── /start ───────────────────────────────────────────────────────────────────

@router.message(Command("start"))
async def start(message: Message) -> None:
    if not is_allowed(message.from_user.id):
        return
    await message.answer(
        "👋 Salom! Men <b>Media Merger</b>man.\n\n"
        "Men sizning rasmlaringiz va PDF-fayllaringizni bitta PDF faylga birlashtirib, guruhga yuborishim mumkin.\n\n"
        "<b>Mendan qanday foydalanish mumkin:</b>\n"
        "1. Menga fayllaringizni (rasm yoki PDF) birma-bir yuboring\n"
        "2. Tugatganingizdan so'ng /done yuboring\n"
        "3. Men sizdan <b>nom</b> va <b>tavsif</b> so'rayman\n"
        "4. Men hamma narsani birlashtiraman va avtomatik ravishda guruhga yuboraman\n\n"
        "<b>Boshqa buyruqlar:</b>\n"
        "/new — yangidan boshlash\n"
        "/search — hujjatlarni qidirish\n"
        "/recent — oxirgi 5 ta yuklangan fayl\n\n"
        "Tayyor! Birinchi faylingizni yuboring 📎",
        parse_mode="HTML"
    )


# ── Start collecting ──────────────────────────────────────────────────────────

@router.message(F.document | F.photo)
async def receive_file(message: Message, state: FSMContext, bot: Bot) -> None:
    if not is_allowed(message.from_user.id):
        return

    async with get_user_lock(message.from_user.id):
        current = await state.get_state()
        if current not in (None, UploadFlow.collecting):
            await message.reply("Siz hozir boshqa jarayondasiz. Qaytadan boshlash uchun /new yuboring.")
            return

        data = await state.get_data()
        files: list[str] = data.get("files", [])
        session_dir = data.get("session_dir") or os.path.join(TEMP_DIR, str(message.from_user.id))

        path = await download_file(bot, message, session_dir)
        if path:
            files.append(path)
            await state.update_data(files=files, session_dir=session_dir)
            await state.set_state(UploadFlow.collecting)
            await message.reply(f"Qabul qilindi ({len(files)} ta fayl). Yana yuboring yoki /done yozing.")
        else:
            await message.reply("Faqat rasm va PDF fayllar qabul qilinadi.")


# ── /done ─────────────────────────────────────────────────────────────────────

@router.message(Command("done"), UploadFlow.collecting)
async def done_collecting(message: Message, state: FSMContext) -> None:
    if not is_allowed(message.from_user.id):
        return

    data = await state.get_data()
    files: list[str] = data.get("files", [])

    if not files:
        await message.reply("Hali hech qanday fayl yuborilmagan. Avval fayl yuboring.")
        return
    if len(files) < 2:
        await message.reply("Tugatish uchun kamida 2 ta fayl yuboring.")
        return

    await state.set_state(UploadFlow.waiting_name)
    await message.reply(f"{len(files)} ta fayl qabul qilindi. Bu PDF faylni qanday nomlash kerak?")


# ── Name input ────────────────────────────────────────────────────────────────

@router.message(UploadFlow.waiting_name, F.text)
async def receive_name(message: Message, state: FSMContext) -> None:
    if not is_allowed(message.from_user.id):
        return

    name = message.text.strip()
    if not name:
        await message.reply("Nom bo'sh bo'lishi mumkin emas. Qaytadan kiriting.")
        return

    await state.update_data(pdf_name=name)
    await state.set_state(UploadFlow.waiting_description)
    await message.reply("Zo'r! Endi hujjat uchun tavsif kiriting.")


# ── Description input → merge → send ─────────────────────────────────────────

@router.message(UploadFlow.waiting_description, F.text)
async def receive_description(message: Message, state: FSMContext, bot: Bot) -> None:
    if not is_allowed(message.from_user.id):
        return

    description = message.text.strip()
    if not description:
        await message.reply("Tavsif bo'sh bo'lishi mumkin emas. Qaytadan kiriting.")
        return

    data = await state.get_data()
    files: list[str] = data.get("files", [])
    pdf_name: str = data.get("pdf_name", "document")
    session_dir: str = data.get("session_dir", TEMP_DIR)

    await message.reply("Fayllar birlashtirilmoqda, iltimos kuting...")

    try:
        slug = slugify(pdf_name)
        output_path = os.path.join(session_dir, f"{slug}.pdf")

        merge_to_pdf(files, output_path)

        caption = f"📄 *{pdf_name}*\n\n{description}"
        sent = await bot.send_document(
            chat_id=GROUP_ID,
            document=FSInputFile(output_path, filename=f"{slug}.pdf"),
            caption=caption,
            parse_mode="Markdown",
        )

        await save_document(
            name=pdf_name,
            description=description,
            file_id=sent.document.file_id,
            uploader_id=message.from_user.id,
        )

        for f in files:
            try:
                os.remove(f)
            except OSError:
                pass
        try:
            os.remove(output_path)
        except OSError:
            pass

        await state.clear()
        await message.reply(f'Tayyor! "{pdf_name}" guruhga yuborildi. ✅')

    except Exception as e:
        import traceback
        await message.reply(f"ERROR:\n{traceback.format_exc()[-1000:]}")
        await state.clear()


# ── /new and /cancel ──────────────────────────────────────────────────────────

async def reset_state(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    for f in data.get("files", []):
        try:
            os.remove(f)
        except OSError:
            pass
    await state.clear()
    await message.reply("Yangilandi. Fayllaringizni yuborishni boshlang. 📎")


@router.message(Command("new"))
async def new_upload(message: Message, state: FSMContext) -> None:
    if not is_allowed(message.from_user.id):
        return
    await reset_state(message, state)


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    if not is_allowed(message.from_user.id):
        return
    await reset_state(message, state)
