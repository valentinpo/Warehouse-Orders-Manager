import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_FILE = os.getenv("DB_FILE", "warehouse.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if not BOT_TOKEN:
    raise ValueError("❌ Не задан BOT_TOKEN в .env")\n