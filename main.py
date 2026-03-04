import asyncio
import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импорт клавиатур
from keyboards import get_main_menu, get_orders_menu, get_modules_menu

# Импорт функций БД
from database.db import init_db, get_db_stats, create_order, get_order_by_number, get_all_orders, update_order_status

# Импорт роутеров
from handlers.orders import router as orders_router
from handlers.modules import router as modules_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загружаем переменные из .env
load_dotenv()

# Получаем токен
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    print("❌ ОШИБКА: Токен не найден! Проверь файл .env")
    exit()

# Создаем бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Регистрируем роутеры
dp.include_router(orders_router)
dp.include_router(modules_router)

# ========================================
# КОМАНДЫ БОТА
# ========================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    stats = get_db_stats()
    await message.answer(
        f"👋 Привет! Я бот для управления складом!\n\n"
        f"📊 Статистика:\n"
        f"• Заказов: {stats['orders']}\n"
        f"• Модулей на складе: {stats['modules']}\n"
        f"• Поставщиков: {stats['suppliers']}\n"
        f"• Покупателей: {stats['customers']}\n\n"
        f"Выберите раздел в меню ниже 👇",
        reply_markup=get_main_menu()
    )

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    stats = get_db_stats()
    await message.answer(
        f"📊 Статистика базы данных:\n\n"
        f"📦 Заказы: {stats['orders']}\n"
        f"🔲 LED модули: {stats['modules']}\n"
        f"📚 Поставщики: {stats['suppliers']}\n"
        f"👥 Покупатели: {stats['customers']}"
    )

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message):
    await message.answer("❌ Форма отменена", reply_markup=get_main_menu())

# ========================================
# МЕНЮ (ТЕКСТОВЫЕ КНОПКИ)
# ========================================

@dp.message(F.text == "📦 Заказы")
async def orders_menu(message: types.Message):
    await message.answer(
        "📦 Управление заказами\n\nВыберите действие:",
        reply_markup=get_orders_menu()
    )

@dp.message(F.text == "🔲 LED Модули")
async def modules_menu(message: types.Message):
    await message.answer(
        "🔲 Склад LED модулей\n\nВыберите действие:",
        reply_markup=get_modules_menu()
    )

@dp.message(F.text == "📊 Отчеты")
async def reports_menu(message: types.Message):
    stats = get_db_stats()
    await message.answer(
        f"📊 Отчеты\n\n"
        f"📦 Всего заказов: {stats['orders']}\n"
        f"🔲 Модулей на складе: {stats['modules']}\n\n"
        f"⚠️ Детальные отчеты в разработке...",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "📚 Справочники")
async def references_menu(message: types.Message):
    await message.answer(
        "📚 Справочники\n\n⚠️ Этот раздел в разработке...",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "⚙️ Настройки")
async def settings_menu(message: types.Message):
    await message.answer(
        "⚙️ Настройки\n\n⚠️ Этот раздел в разработке...",
        reply_markup=get_main_menu()
    )

# ========================================
# CALLBACK (INLINE КНОПКИ)
# ========================================

@dp.callback_query(F.data == "menu_back")
async def menu_back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 Главное меню\n\nВыберите раздел:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "order_search")
async def order_search(callback: types.CallbackQuery):
    await callback.message.answer(
        "🔍 Поиск заказа\n\n⚠️ В разработке...",
        reply_markup=get_orders_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "order_list")
async def order_list(callback: types.CallbackQuery):
    orders = get_all_orders()
    if orders:
        text = "📋 Список заказов:\n\n"
        keyboard_buttons = []
        
        for order in orders[:20]:
            order_id, order_number, supplier, customer, status, created_at = order
            text += f"📦 #{order_number} — {customer}\n"
            text += f"   Поставщик: {supplier}\n"
            text += f"   Статус: {status}\n\n"
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"👁️ Просмотреть #{order_number}",
                    callback_data=f"order_view_{order_id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")
        ])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.answer(text, reply_markup=keyboard)
    else:
        await callback.message.answer(
            "📋 **Заказов пока нет**\n\nСоздайте первый заказ!",
            reply_markup=get_orders_menu()
        )
    await callback.answer()

# ========================================
# ЗАПУСК БОТА
# ========================================

async def main():
    init_db()
    logging.info("🚀 Бот запущен...")
    logging.info("📱 Откройте Telegram и нажмите /start")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")