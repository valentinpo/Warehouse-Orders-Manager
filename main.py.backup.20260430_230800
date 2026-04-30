import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db_manager import init_db
from handlers.start import router as start_router
from handlers.orders import router as orders_router
from handlers.warehouse import router as warehouse_router
from handlers.suppliers import router as suppliers_router
from handlers.customers import router as customers_router
from handlers.reports import router as reports_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрируем роутеры
dp.include_router(start_router)
dp.include_router(orders_router)
dp.include_router(warehouse_router)
dp.include_router(suppliers_router)
dp.include_router(customers_router)
dp.include_router(reports_router)

async def main():
    # Инициализация БД
    init_db()
    print("🤖 Бот запускается...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен")