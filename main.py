import asyncio
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
        logging.getLogger(__name__).info("⛔ Бот остановлен вручную")\n