import os
import shutil
from datetime import datetime

# === НАСТРОЙКИ ===
PROJECT_ROOT = "."  # Путь к корню проекта (меняйте при необходимости)

# Словарь с путями и новым содержимым файлов
FILES_TO_UPDATE = {
    "database/db_manager.py": '''from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from database.models import Base
from config import DB_FILE

# Создаём движок
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)
SessionLocal = sessionmaker(bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Контекстный менеджер для безопасной работы с сессией SQLAlchemy.
    Гарантирует закрытие сессии даже при ошибках.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Инициализация базы данных: создание таблиц.
    Вызывается при старте бота.
    """
    Base.metadata.create_all(bind=engine)
''',

    "main.py": '''import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, LOG_LEVEL
from database.db_manager import init_db
from handlers.start import router as start_router
from handlers.orders import router as orders_router
from handlers.warehouse import router as warehouse_router
from handlers.suppliers import router as suppliers_router
from handlers.customers import router as customers_router
from handlers.reports import router as reports_router

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():
    try:
        init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.critical(f"❌ Не удалось инициализировать БД: {e}")
        return

    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(orders_router)
    dp.include_router(warehouse_router)
    dp.include_router(suppliers_router)
    dp.include_router(customers_router)
    dp.include_router(reports_router)

    logger.info("🚀 Бот запускается...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("🛑 Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("⛔ Бот остановлен вручную")
''',

    "config.py": '''import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_FILE = os.getenv("DB_FILE", "warehouse.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if not BOT_TOKEN:
    raise ValueError("❌ Не задан BOT_TOKEN в .env")
''',
}

# === ФУНКЦИЯ ОБНОВЛЕНИЯ ФАЙЛОВ ===
def backup_file(file_path):
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup.{timestamp}"
        shutil.copy(file_path, backup_path)
        print(f"    🔁 Создана резервная копия: {backup_path}")
        return backup_path
    return None


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        print(f"    📂 Создана папка: {directory}")


def update_file(relative_path, content):
    full_path = os.path.join(PROJECT_ROOT, relative_path)
    print(f"📝 Обновляем: {relative_path}")

    # Резервная копия
    backup_file(full_path)

    # Создаём папку, если нужно
    ensure_dir(full_path)

    # Записываем новый контент
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\\n')

    print(f"    ✅ Успешно обновлён!")


# === ЗАПУСК ===
if __name__ == "__main__":
    print("🚀 Запущено обновление проекта...")
    print(f"Корень проекта: {os.path.abspath(PROJECT_ROOT)}\\n")

    for file_path, new_content in FILES_TO_UPDATE.items():
        try:
            update_file(file_path, new_content)
        except Exception as e:
            print(f"    ❌ Ошибка при обновлении {file_path}: {e}")

    print("\\n🎉 Все файлы обновлены!")
    print("💡 Теперь можно запустить бота: python main.py")