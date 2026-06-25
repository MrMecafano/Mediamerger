import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
GROUP_ID: int = int(os.getenv("GROUP_ID", "0"))

# Telegram user IDs allowed to use the bot
ALLOWED_IDS: list[int] = [
    int(x.strip())
    for x in os.getenv("ALLOWED_IDS", "").split(",")
    if x.strip()
]

DB_PATH: str = "documents.db"
TEMP_DIR: str = "temp"
