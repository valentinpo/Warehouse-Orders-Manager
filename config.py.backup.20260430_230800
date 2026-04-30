import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

# Проверяем, загрузился ли токен
BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_FILE = os.getenv('DB_FILE')

# Отладочный вывод
if not BOT_TOKEN:
    print("ОШИБКА: BOT_TOKEN не найден в .env файле!")
    print(f"Путь к .env: {os.path.abspath('.env')}")
else:
    print("✅ Токен успешно загружен")