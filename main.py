import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramMigrateToChat

from config import BOT_TOKEN
from services.db import init_db
from handlers import upload, search

logging.basicConfig(level=logging.INFO)

BOT_COMMANDS = [
    BotCommand(command="start",  description="Introduction and how to use"),
    BotCommand(command="new",    description="Reset and start a new upload"),
    BotCommand(command="cancel", description="Cancel current upload"),
    BotCommand(command="done",   description="Finish sending files"),
    BotCommand(command="search", description="Search documents by keyword"),
    BotCommand(command="recent", description="Show last 5 uploads"),
]


async def main() -> None:
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    @dp.errors()
    async def migration_handler(event: ErrorEvent) -> bool:
        if isinstance(event.exception, TelegramMigrateToChat):
            new_id = event.exception.migrate_to_chat_id
            logging.critical(
                f"\n{'='*60}\n"
                f"GROUP MIGRATED TO SUPERGROUP!\n"
                f"New GROUP_ID = {new_id}\n"
                f"Update GROUP_ID in your .env file to: {new_id}\n"
                f"{'='*60}"
            )
            return True
        return False

    await bot.set_my_commands(BOT_COMMANDS)

    dp.include_router(upload.router)
    dp.include_router(search.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
