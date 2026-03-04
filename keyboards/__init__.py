from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Заказы"), KeyboardButton(text="🔲 LED Модули")],
            [KeyboardButton(text="📊 Отчеты"), KeyboardButton(text="📚 Справочники")],
            [KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_orders_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать заказ", callback_data="order_create")],
            [InlineKeyboardButton(text="🔍 Найти заказ", callback_data="order_search")],
            [InlineKeyboardButton(text="📋 Все заказы", callback_data="order_list")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
        ]
    )
    return keyboard

def get_modules_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить модуль", callback_data="module_add")],
            [InlineKeyboardButton(text="🔍 Найти модуль", callback_data="module_search")],
            [InlineKeyboardButton(text="📦 Остатки на складе", callback_data="module_stock")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
        ]
    )
    return keyboard

def get_back_button():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="menu_back")]
        ]
    )
    return keyboard

# ← НОВАЯ ФУНКЦИЯ для отмены формы
def get_cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboardSS