from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards.main_menu import get_main_menu
from database.db_manager import get_or_create_user
import logging

logger = logging.getLogger(__name__)

router = Router()



@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Главное меню бота"""
    try:
        # Создаём или получаем пользователя
        user = get_or_create_user(message.from_user.id, message.from_user.username)
        logger.info(f"Пользователь {user.username} (ID: {user.telegram_id}) запустил бота")
        
        keyboard = [
            [KeyboardButton(text="📦 Заказы"), KeyboardButton(text="🔲 LED Модули")],
            [KeyboardButton(text="📚 Поставщики"), KeyboardButton(text="👥 Покупатели")],
            [KeyboardButton(text="📊 Отчеты"), KeyboardButton(text="⚙️ Настройки")]
        ]
        await message.answer(
            f"👋 **Привет, {message.from_user.first_name}!**\n\n"
            "🤖 **Warehouse Helper Bot**\n\n"
            "Выберите раздел:",
            reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}")
        await message.answer("❌ Ошибка при загрузке главного меню. Попробуйте позже.")

@router.message(F.text == "📦 Заказы")
async def menu_orders(message: types.Message):
    """Меню заказов"""
    try:
        keyboard = [
            [KeyboardButton(text="➕ Новый заказ")],
            [KeyboardButton(text="🔍 Найти заказ")],
            [KeyboardButton(text="📋 Список заказов")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
        await message.answer(
            "📦 **Меню заказов**\n\nВыберите действие:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в menu_orders: {e}")
        await message.answer("❌ Ошибка загрузки меню")

@router.message(F.text == "🔲 LED Модули")
async def menu_warehouse(message: types.Message):
    """Меню склада"""
    try:
        keyboard = [
            [KeyboardButton(text="➕ Добавить модуль")],
            [KeyboardButton(text="🔍 Поиск модулей")],
            [KeyboardButton(text="📊 Остатки на складе")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
        await message.answer(
            "🔲 **Склад LED модулей**\n\nВыберите действие:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в menu_warehouse: {e}")
        await message.answer("❌ Ошибка загрузки меню")



@router.message(F.text == "📚 Справочники")
async def menu_directory(message: types.Message):
    """Меню справочников"""
    try:
        keyboard = [
            [KeyboardButton(text="📚 Поставщики")],
            [KeyboardButton(text="👥 Покупатели")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
        await message.answer(
            "📚 **Справочники**\n\nВыберите раздел:",
            reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в menu_directory: {e}")
        await message.answer("❌ Ошибка загрузки меню")

@router.message(F.text == "⚙️ Настройки")
async def menu_settings(message: types.Message):
    """Меню настроек"""
    try:
        await message.answer("⚙️ **Раздел настроек** в разработке... Скоро будет доступен!", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка в menu_settings: {e}")
        await message.answer("❌ Ошибка загрузки меню")

@router.message(F.text == "⬅️ Назад")
async def menu_back(message: types.Message):
    """Вернуться в главное меню"""
    try:
        await cmd_start(message)
    except Exception as e:
        logger.error(f"Ошибка в menu_back: {e}")
        await message.answer("❌ Ошибка при возврате в главное меню")