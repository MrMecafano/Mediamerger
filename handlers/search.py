from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command

from config import ALLOWED_IDS
from services.db import search_documents, recent_documents

router = Router()


def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_IDS


@router.message(Command("search"))
async def search(message: Message, bot: Bot) -> None:
    if not is_allowed(message.from_user.id):
        return

    query = (message.text or "").removeprefix("/search").strip()
    if not query:
        await message.reply("Usage: /search <keywords>")
        return

    results = await search_documents(query)
    if not results:
        await message.reply(f'No documents found for "{query}".')
        return

    await message.reply(f"Found {len(results)} result(s):")
    for doc in results:
        caption = f"📄 *{doc['name']}*\n{doc['description']}\n_Uploaded: {doc['created_at']}_"
        await bot.send_document(
            chat_id=message.chat.id,
            document=doc["file_id"],
            caption=caption,
            parse_mode="Markdown",
        )


@router.message(Command("recent"))
async def recent(message: Message, bot: Bot) -> None:
    if not is_allowed(message.from_user.id):
        return

    results = await recent_documents(limit=5)
    if not results:
        await message.reply("No documents uploaded yet.")
        return

    await message.reply(f"Last {len(results)} document(s):")
    for doc in results:
        caption = f"📄 *{doc['name']}*\n{doc['description']}\n_Uploaded: {doc['created_at']}_"
        await bot.send_document(
            chat_id=message.chat.id,
            document=doc["file_id"],
            caption=caption,
            parse_mode="Markdown",
        )
