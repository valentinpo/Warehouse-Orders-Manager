from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from constants import LED_STEPS_WITH_OTHER

def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    keyboard = [
        [KeyboardButton(text="📦 Заказы")],
        [KeyboardButton(text="🔲 LED Модули")],
        [KeyboardButton(text="📊 Отчеты")],
        [KeyboardButton(text="📚 Справочники")],
        [KeyboardButton(text="⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура отмены"""
    keyboard = [
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

def get_led_step_keyboard() -> InlineKeyboardMarkup:
    """Кнопки выбора шага LED модуля"""
    keyboard = [[InlineKeyboardButton(text=step, callback_data=f"step_{step}")] for step in LED_STEPS_WITH_OTHER]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
