# ============================================
# КОНСТАНТЫ И КОНФИГУРАЦИЯ БОТА
# ============================================

# LED МОДУЛИ - ШАГИ ПИКСЕЛЬНОСТИ
LED_STEPS = [
    "P1.8", "P2", "P2.5", "P3", "P4", "P5", "P6", "P8", "P10"
]

LED_STEPS_WITH_OTHER = LED_STEPS + ["Другой"]

# ПАРАМЕТРЫ ВАЛИДАЦИИ
VALIDATION = {
    "order_number_min_length": 3,
    "order_number_max_length": 50,
    "supplier_name_min_length": 2,
    "supplier_name_max_length": 100,
    "customer_name_min_length": 2,
    "customer_name_max_length": 100,
    "phone_min_length": 10,
    "phone_max_length": 20,
    "email_max_length": 100,
    "quantity_min": 1,
    "quantity_max": 100000,
    "width_min": 0.1,
    "width_max": 1000,
    "height_min": 0.1,
    "height_max": 1000,
}

# СООБЩЕНИЯ ОБ ОШИБКАХ
ERROR_MESSAGES = {
    "invalid_input": "❌ Некорректный ввод. Пожалуйста, проверьте данные и попробуйте снова.",
    "db_error": "❌ Ошибка базы данных. Попробуйте позже.",
    "unknown_error": "❌ Неизвестная ошибка. Пожалуйста, обратитесь к администратору.",
    "access_denied": "❌ У вас нет доступа к этой функции.",
    "not_found": "❌ Данные не найдены.",
}

# СООБЩЕНИЯ ОБ УСПЕХЕ
SUCCESS_MESSAGES = {
    "created": "✅ Успешно создано!",
    "updated": "✅ Успешно обновлено!",
    "deleted": "✅ Успешно удалено!",
    "saved": "✅ Успешно сохранено!",
}

# ЭМОДЗИ
EMOJIS = {
    "order": "📦",
    "warehouse": "🔲",
    "supplier": "📚",
    "customer": "👥",
    "report": "📊",
    "settings": "⚙️",
    "add": "➕",
    "search": "🔍",
    "list": "📋",
    "back": "⬅️",
    "cancel": "❌",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "user": "👤",
    "database": "💾",
}

# ПУТИ ЭКСПОРТА
EXPORT_PATHS = {
    "reports_dir": "./reports",
    "excel_extension": ".xlsx",
}

# НАСТРОЙКИ ЛОГИРОВАНИЯ
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}
