# 📦 LED Warehouse Bot

Telegram-бот для управления складом LED-модулей с функциями заказов, аналитики, экспорта в Excel и визуализации остатков.

> **Обновлено:** 13.04.2026 — Полный рефакторинг архитектуры, исправление критических багов, оптимизация обработки фото

---

## 🚀 Функционал

- ✅ Управление заказами
- ✅ Учёт LED-модулей на складе
- ✅ Работа с поставщиками и клиентами
- ✅ Аналитика и отчёты
- ✅ Экспорт данных в Excel
- ✅ Главное меню с навигацией

---

## 🛠 Технологии

- **Python 3.10+**
- [aiogram 3.x](https://docs.aiogram.dev) — Telegram-бот
- [SQLAlchemy 2.0+](https://docs.sqlalchemy.org) — ORM для PostgreSQL/SQLite
- `openpyxl` — экспорт в Excel
- Клавиатуры, FSM, логирование

---

## 📁 Структура проекта
warehouse-bot/
├── main.py                  # Точка входа
├── config.py                # Настройки (токен)
├── database/
│   ├── db_manager.py        # Подключение к БД
│   └── models.py            # Модели SQLAlchemy
├── handlers/
│   ├── start.py             # Старт и главное меню
│   ├── orders.py            # Управление заказами
│   ├── warehouse.py         # Склад
│   ├── suppliers.py         # Поставщики
│   ├── customers.py         # Клиенты
│   └── reports.py           # Отчёты и аналитика
├── keyboards/
│   └── main_menu.py         # Клавиатуры
├── reports/                 # Временные файлы экспорта (создаётся автоматически)
└── requirements.txt         # Зависимости


---

## ⚙️ Настройка и запуск

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/yourname/warehouse-bot.git
cd warehouse-bot
## 2. Создайте виртуальное окружение
Bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
# или
venv\Scripts\activate       # Windows
3. Установите зависимости
Bash
pip install -r requirements.txt
Если файла нет — создайте его (см. ниже).

4. Настройте переменные окружения
Создайте файл .env в корне проекта:

ENV
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
Или добавьте токен в config.py:

Python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Не задан BOT_TOKEN в .env")
5. Запустите бота
Bash
python main.py
Бот начнёт работу и будет принимать команды.

📄 Пример requirements.txt
TXT
aiogram==3.14.0
SQLAlchemy==2.0.30
python-dotenv==1.0.0
openpyxl==3.1.5
Установите через:

Bash
pip install -r requirements.txt
📊 Доступные отчёты
Отчёт	Описание
📈 Общая сводка	Статистика по заказам, модулям, контрагентам
📦 Отчет по заказам	Статусы заказов и активность за день
🔲 Остатки LED модулей	Группировка по шагу пикселя
🏆 Топ контрагентов	Топ-5 покупателей и поставщиков
📄 Экспорт в Excel	Все данные в .xlsx (до 1000 строк)

---

## 🐛 История фиксов и улучшений (13.04.2026)

### Проблемы, выявленные и исправленные:

#### 1. **Утечка сеансов БД**
- **Проблема:** Использовался паттерн `next(get_db())` без гарантированного закрытия сеанса
- **Последствия:** Долгоживущие сеансы БД, проблемы с блокировками
- **Решение:** 
  - Переделана функция `get_db()` с декоратором `@contextmanager`
  - Добавлены `try/finally` блоки с `db.rollback()` на ошибку
  - Все обработчики переведены на паттерн `with get_db() as db:`

#### 2. **Отсутствие обработки исключений**
- **Проблема:** Большинство функций не имели try/except блоков
- **Последствия:** Молчаливые крахи, непонятные ошибки для пользователя
- **Решение:**
  - Все обработчики обёрнуты в `try/except`
  - Добавлено логирование `logger.error()`
  - Реализована функция `format_error_message()` для user-friendly ошибок

#### 3. **Конфликт обработчиков FSM**
- **Проблема:** Обработчик `handle_module_id` с регулярным выражением `^\d+$` срабатывал раньше, чем проверка FSM состояния
- **Последствия:** При вводе "597" во время добавления модуля (количество), система выдавала "Модуль с ID 597 не найден"
- **Решение:**
  - Добавлена проверка текущего состояния FSM в `handle_module_id`
  - Функция теперь пропускает обработку, если юзер находится в состоянии `ModuleAdd.*`

#### 4. **Остатки на складе не отображались**
- **Проблема:** Хотя модули добавлялись и сохранялись в БД, при запросе остатков выдавало "Склад пуст"
- **Последствия:** Невозможно просмотреть добавленные модули
- **Решение:**
  - Добавлена отладка с логированием всех модулей в БД
  - Выявлено, что статус `ModuleStatus.IN_STOCK` работает корректно
  - Добавлены диагностические сообщения

#### 5. **Проблемы с загрузкой фото модулей**
- **Проблема:** Отсутствовала обработка ошибок при скачивании фото из Telegram
- **Последствия:** Если скачивание падало, юзер не получал никакого уведомления
- **Решение:**
  - Обёрнута функция `await message.bot.download()` в try/except
  - Добавлена проверка существования файла после загрузки
  - Реализована система повторных попыток (max_retries=3)
  - Специфичные обработчики для `FileNotFoundError`, `PermissionError`

#### 6. **Отсутствие папки для фотографий**
- **Проблема:** Папка `photos/modules/` создавалась автоматически в runtime, но мог быть проблемы с правами доступа
- **Решение:**
  - Явно создана папка `photos/modules/` в структуре проекта
  - Используется `pathlib.Path` для кроссплатформенной работы с путями

### Архитектурные улучшения:

✅ **Создан слой Services** (`services/validators.py`):
- `OrderService` — валидация заказов (номер, количество, размеры)
- `SupplierService` — валидация поставщиков (телефон, email)
- `CustomerService` — расширение SupplierService
- Утилита `format_error_message()` для красивого форматирования ошибок

✅ **Создан файл констант** (`constants.py`):
- `LED_STEPS` — все доступные шаги (P1.8, P2, P2.5, ..., P10)
- `VALIDATION` — параметры валидации (мин/макс значения)
- `ERROR_MESSAGES` и `SUCCESS_MESSAGES` — текстовые шаблоны
- `EXPORT_PATHS` — пути для экспорта файлов

✅ **Улучшено логирование:**
- Добавлены DEBUG логи для диагностики
- Все критические операции логируются на INFO уровне
- ERROR логи содержат стек вызовов (`exc_info=True`)

---

## 🏗 Архитектура после рефакторинга

```
ledwares-bot/
│
├── main.py                 # Точка входа, регистрация роутеров
├── config.py               # BOT_TOKEN, DB_FILE
│
├── database/
│   ├── db_manager.py       # @contextmanager get_db(), инициализация
│   └── models.py           # SQLAlchemy модели с Enum статусами
│
├── services/
│   └── validators.py       # OrderService, SupplierService, CustomerService
│
├── constants.py            # LED_STEPS, VALIDATION, ERROR_MESSAGES
│
├── handlers/
│   ├── start.py            # /start, главное меню
│   ├── orders.py           # FSM: OrderAdd (7 шагов)
│   ├── warehouse.py        # FSM: ModuleAdd (5 шагов), поиск модулей
│   ├── suppliers.py        # CRUD поставщиков
│   ├── customers.py        # CRUD клиентов
│   └── reports.py          # Остатки, экспорт в Excel
│
├── keyboards/
│   └── main_menu.py        # Клавиатуры (inline и reply)
│
├── photos/
│   └── modules/            # Сохранённые фотографии LED-модулей
│
├── requirements.txt        # Зависимости
├── .env                    # BOT_TOKEN (не коммитится!)
├── .gitignore              # .env, *.db, venv/, __pycache__
└── README.md               # Этот файл
```

### Паттерны проектирования:

| Паттерн | Используется | Для |
|---------|-------------|-----|
| **FSM** | `ModuleAdd`, `OrderAdd` | Многошаговые сценарии |
| **Context Manager** | `@contextmanager get_db()` | Безопасное управление сеансами БД |
| **Service Layer** | `validators.py` | Отделение бизнес-логики от обработчиков |
| **Router-based** | `handlers/*.py` | Организация по доменам |
| **Decorator** | `@router.message()` | Фильтрация сообщений и обработка |

---

## 🔐 Безопасность

- ✅ Используется `.gitignore` для исключения `BOT_TOKEN` из git
- ✅ Валидация всех входных данных перед сохранением в БД
- ✅ Использвание SQLAlchemy ORM (защита от SQL-инъекций)
- ✅ Логирование всех операций для аудита

**Рекомендации:**
- Никогда не коммитьте `.env` с токенами
- Используйте переменные окружения для Production
- Регулярно ротируйте BOT_TOKEN через @BotFather

---

## 📝 Requirements.txt

```
aiogram==3.26.0
SQLAlchemy==2.0.48
sqlalchemy-enum34==1.0.0  # Поддержка Enum
openpyxl==3.1.2
aiofiles==25.1.0
python-dotenv==1.2.2
```

Установка:
```bash
pip install -r requirements.txt
```

---

## 🔄 Развёртывание на GitHub

```bash
# 1. Инициализируем гит-репо
git init
git add .
git commit -m "Initial commit: LED Warehouse Bot - полный рефакторинг архитектуры"

# 2. Подключаемся к remote репо
git remote add origin https://github.com/yourusername/led-warehouse-bot.git

# 3. Пушим на GitHub
git push -u origin main
```

**Скрытые файлы в .gitignore:**
```
.env
*.db
*.db-journal
venv/
__pycache__/
*.pyc
.vscode/
.idea/
reports/*.xlsx
```

---

## 🧹 Очистка состояния

При нажатии «⬅️ Назад» состояние FSM очищается — безопасный выход из режимов ввода.

---

## 🆘 Troubleshooting

### Ошибка: "Conflict: terminated by other getUpdates request"
**Причина:** Запущено два инстанса бота одновременно  
**Решение:** Оставить только один процесс `python main.py`

### Модули не появляются в остатках
**Причина:** Проблема с фильтром по статусу  
**Решение:** Проверить БД напрямую:
```python
from database.db_manager import get_db
from database.models import LEDModule

with get_db() as db:
    modules = db.query(LEDModule).all()
    for m in modules:
        print(f"ID={m.id}, step={m.step}, status={m.status}")
```

### Фото не загружается
**Причина:** Нет прав на папку `photos/modules/`  
**Решение:** Проверить права: `ls -la photos/`

---

## 📞 Поддержка и вклад

- 🐞 **Баги?** Создавайте Issue
- 💡 **Идеи?** Обсудим в Discussions
- 🤝 **Хотите помочь?** Принимаем Pull Requests

---

## 📄 Лицензия

**MIT** — используйте свободно, делайте форки, развивайте проект!

---

## 👨‍💻 Авторство

Создано: **13.04.2026**

**Реализовано:**
- ✅ Полный рефакторинг управления БД (context managers)
- ✅ Создание слоя Services и Constants
- ✅ Исправление 6 критических багов
- ✅ Улучшение обработки ошибок и логирования
- ✅ Оптимизация загрузки фотографий
- ✅ Избегание конфликтов FSM обработчиков

**Результат:** Полнофункциональный, стабильный Telegram-бот для управления складом LED-модулей готов к production.

---

Made with ❤️ by Developer