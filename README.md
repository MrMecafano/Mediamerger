# Mediamerger Bot

Telegram bot that collects files (images + PDFs) from allowed users, merges them into one named PDF, sends it to a Telegram group, and lets users search past uploads by name or description.

---

## Project Status

**COMPLETED AND RUNNING — Bot is live and working.**

### Completed in this session:
- Core file merge + send to group flow ✅
- Per-user lock fix for simultaneous file uploads ✅
- `/start` greeting in Uzbek ✅
- `/new` command to reset mid-flow ✅
- Bot commands menu registered ✅
- `setup.bat` for easy new PC install ✅
- `start_bot.bat` for silent background startup ✅
- Task Scheduler instructions for auto-start on boot ✅

---

## What It Does

1. User sends files one by one (images or PDFs, can also forward from other chats)
2. User sends `/done` when finished
3. Bot asks for a **name** → user types it
4. Bot asks for a **description** → user types it
5. Bot merges all files into one PDF, sends it to the configured **GROUP** with name + description as caption
6. Saves to local SQLite DB (name, description, Telegram file_id, uploader_id, timestamp)
7. `/search <query>` — searches name + description, returns matching PDFs
8. `/recent` — returns last 5 uploaded documents
9. `/cancel` — cancels current flow and clears temp files
10. **Access restricted** — only user IDs listed in `ALLOWED_IDS` can use any command

---

## File Structure

```
Mediamerger/
├── main.py                  # Entry point — starts polling
├── config.py                # Loads .env: BOT_TOKEN, GROUP_ID, ALLOWED_IDS
├── states.py                # FSM states: collecting → waiting_name → waiting_description
├── handlers/
│   ├── __init__.py
│   ├── upload.py            # File collection, /done, name/desc flow, merge + send
│   └── search.py            # /search and /recent commands
├── services/
│   ├── __init__.py
│   ├── merger.py            # image→PDF conversion, PDF merge (Pillow + pypdf)
│   └── db.py                # aiosqlite: init_db, save_document, search_documents, recent_documents
├── .env.example             # Template — copy to .env and fill values
├── requirements.txt
└── README.md
```

---

## Setup (First Time)

### 1. Install Python dependencies

```bash
cd C:\Users\mecaf\OneDrive\Desktop\Mediamerger
pip install -r requirements.txt
```

### 2. Create your `.env` file

Copy `.env.example` to `.env` and fill in:

```
BOT_TOKEN=your_bot_token_here        # From @BotFather
GROUP_ID=-100123456789               # Telegram group ID (negative number for groups)
ALLOWED_IDS=111111111,222222222      # Comma-separated Telegram user IDs allowed to use the bot
```

**How to get GROUP_ID:**
- Add the bot to the group as admin
- Send a message in the group
- Visit: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
- Find `"chat": {"id": -100XXXXXXXXX}` — that is the GROUP_ID

**How to get your Telegram user ID:**
- Message @userinfobot on Telegram — it replies with your ID

### 3. Run

```bash
python main.py
```

---

## How to Use (As a User)

| Action | What to do |
|--------|-----------|
| See intro | `/start` |
| Start uploading | Just send a file (image or PDF) |
| Add more files | Keep sending files (can forward from other chats) |
| Finish | `/done` |
| Name the PDF | Type the name when asked |
| Add description | Type description when asked |
| Reset mid-flow | `/new` or `/cancel` |
| Search docs | `/search invoice march` |
| See recent uploads | `/recent` |

---

## Tech Stack

| Purpose | Library |
|---------|---------|
| Bot framework | `aiogram 3.13` |
| Conversation state | `aiogram.fsm` (MemoryStorage) |
| PDF merge | `pypdf 4.3` |
| Image → PDF | `Pillow 10.4` |
| Database | `aiosqlite 0.20` (SQLite) |
| Config | `python-dotenv 1.0` |

---

## Database

File: `documents.db` (auto-created on first run)

```sql
CREATE TABLE documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT NOT NULL,
    file_id     TEXT NOT NULL,   -- Telegram file_id, used to re-send without re-uploading
    uploader_id INTEGER NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Known Limitations / Future Work

- FSM uses `MemoryStorage` — states reset on bot restart. If persistence across restarts is needed, switch to `RedisStorage` or `aiosqlite`-based FSM storage.
- No admin commands yet (add/remove ALLOWED_IDS at runtime). Currently managed via `.env` restart.
- `/search` returns max 10 results. Adjustable in `services/db.py:search_documents`.
- Temp files are stored in `temp/<user_id>/` and cleaned up after each successful merge. If bot crashes mid-flow, temp files remain — safe to delete manually.

---

## Continuing Development (For Claude)

If resuming this project in a future session:

1. All core functionality is **complete and working**.
2. Next logical additions (if requested):
   - Admin command to add/remove ALLOWED_IDS without restarting (`/adduser`, `/removeuser`)
   - Persistent FSM storage (Redis or SQLite-backed) so states survive restarts
   - `/search` pagination if result count grows large
   - Webhook mode instead of polling for production deployment
3. The conversation flow FSM is in `states.py` with 3 states: `collecting → waiting_name → waiting_description`
4. All DB operations are async in `services/db.py`
5. File merging logic (images + PDFs) is in `services/merger.py`
