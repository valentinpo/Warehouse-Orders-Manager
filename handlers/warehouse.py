from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.main_menu import get_main_menu, get_cancel_keyboard, get_led_step_keyboard
from database.db_manager import get_db
from database.models import LEDModule, ModuleStatus
from services import OrderService, format_error_message
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

router = Router()

# ============================================
# МАШИНА СОСТОЯНИЙ
# ============================================

class ModuleAdd(StatesGroup):
    photo = State()
    step = State()
    quantity = State()
    dimensions = State()
    location = State()

# ============================================
# ГЛАВНОЕ МЕНЮ СКЛАДА
# ============================================

@router.message(F.text == "🔲 LED Модули")
async def menu_warehouse(message: types.Message):
    """Меню склада LED модулей"""
    try:
        keyboard = [
            [KeyboardButton(text="➕ Добавить модуль")],
            [KeyboardButton(text="🔍 Поиск модулей")],
            [KeyboardButton(text="📊 Остатки на складе")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
        await message.answer(
            "🔲 **Склад LED модулей**\n\nВыберите действие:",
            reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в menu_warehouse: {e}")
        await message.answer("❌ Ошибка загрузки меню")

# ============================================
# ДОБАВИТЬ МОДУЛЬ - НАЧАЛО
# ============================================

@router.message(Command("module_add"))
@router.message(F.text == "➕ Добавить модуль")
async def start_add_module(message: types.Message, state: FSMContext):
    """Начало добавления LED модуля"""
    try:
        await state.set_state(ModuleAdd.photo)
        await message.answer(
            "🔲 **Добавление LED модуля**\n\n"
            "📸 Отправьте **фотографию модуля**:\n\n"
            "❌ Отмена - для отмены",
            reply_markup=get_cancel_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в start_add_module: {e}")
        await message.answer("❌ Ошибка загрузки формы добавления модуля")

# ============================================
# ШАГ 1: ФОТО
# ============================================

@router.message(ModuleAdd.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Обработка фотографии модуля"""
    try:
        import pathlib
        
        # Получаем фото с наивысшим качеством
        photo = message.photo[-1]
        logger.debug(f"Получено фото с ID: {photo.file_id}, размер: {photo.file_size} bytes")
        
        # Создаём папку для фото
        folder = pathlib.Path("photos/modules")
        folder.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Папка для фото: {folder.absolute()}")
        
        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:20]
        file_path = folder / f"module_{timestamp}.jpg"
        
        logger.debug(f"Начинаем загрузку фото в: {file_path.absolute()}")
        
        # Загружаем фото
        await message.bot.download(photo, destination=str(file_path))
        
        # Проверяем, что файл был создан
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не был создан: {file_path}")
        
        file_size = file_path.stat().st_size
        logger.info(f"Фото успешно загружено: {file_path} ({file_size} bytes)")
        
        # Сохраняем относительный путь
        relative_path = str(file_path).replace("\\", "/")
        await state.update_data(photo_path=relative_path)
        await state.set_state(ModuleAdd.step)
        
        await message.answer(
            f"✅ Фото сохранено ({file_size} B)\n\n"
            "Выберите **шаг модуля**:",
            reply_markup=get_led_step_keyboard(),
            parse_mode="Markdown"
        )
        logger.debug("Пользователь переведена на выбор шага модуля")
        
    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {e}")
        await message.answer(f"❌ Ошибка: файл не был сохранен.\n\nУбедитесь что папка photos/modules доступна для записи.\n\nПопробуйте снова.")
    except PermissionError as e:
        logger.error(f"Нет прав доступа: {e}")
        await message.answer(f"❌ Нет прав доступа для сохранения фото.\n\nОбратитесь к администратору.")
    except Exception as e:
        logger.error(f"Ошибка при загрузке фото: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка загрузки фотографии:\n{str(e)[:100]}\n\nПопробуйте снова.")

@router.message(ModuleAdd.photo, F.text == "❌ Отмена")
async def cancel_photo(message: types.Message, state: FSMContext):
    try:
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка в cancel_photo: {e}")
        await message.answer("❌ Ошибка отмены", reply_markup=get_main_menu())

# ============================================
# ШАГ 2: ВЫБОР ШАГА (callback_query)
# ============================================

@router.callback_query(ModuleAdd.step, F.data.startswith("step_"))
async def process_step(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора шага модуля"""
    try:
        step = callback.data.replace("step_", "")
        await state.update_data(step=step)
        await state.set_state(ModuleAdd.quantity)
        
        await callback.message.answer(
            f"✅ Шаг: **{step}**\n\n"
            "Введите **количество штук** (число):\n\n"
            "❌ Отмена - для отмены",
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в process_step: {e}")
        await callback.answer("Ошибка обработки", show_alert=True)

# ============================================
# ШАГ 3: КОЛИЧЕСТВО
# ============================================

@router.message(ModuleAdd.quantity, F.text != "❌ Отмена")
async def process_quantity(message: types.Message, state: FSMContext):
    """Обработка количества"""
    try:
        quantity = int(message.text.strip())
        if quantity <= 0:
            await message.answer("⚠️ Количество должно быть больше 0. Попробуйте снова:")
            return
        
        await state.update_data(quantity=quantity)
        await state.set_state(ModuleAdd.dimensions)
        await message.answer(
            f"✅ Количество: **{quantity}**\n\n"
            "Введите **размеры** в формате: `ширина x высота` (мм)\n"
            "Пример: `320x160`\n\n"
            "❌ Отмена - для отмены",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer("⚠️ Введите число (например: 10). Попробуйте снова:")

@router.message(ModuleAdd.quantity, F.text == "❌ Отмена")
async def cancel_quantity(message: types.Message, state: FSMContext):
    try:
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка в cancel_quantity: {e}")
        await message.answer("❌ Ошибка отмены", reply_markup=get_main_menu())

# ============================================
# ШАГ 4: РАЗМЕРЫ
# ============================================

@router.message(ModuleAdd.dimensions, F.text != "❌ Отмена")
async def process_dimensions(message: types.Message, state: FSMContext):
    """Обработка размеров"""
    text = message.text.strip()
    
    try:
        if "x" in text.lower():
            parts = text.lower().replace(" ", "").split("x")
            width = float(parts[0])
            height = float(parts[1])
        else:
            parts = text.replace(",", ".").split()
            width = float(parts[0])
            height = float(parts[1])
        
        await state.update_data(width=width, height=height)
        await state.set_state(ModuleAdd.location)
        await message.answer(
            f"✅ Размеры: **{width} x {height} мм**\n\n"
            "Введите **местоположение** на складе:\n"
            "Пример: `Стеллаж А-2, Полка 3`\n\n"
            "❌ Отмена - для отмены",
            parse_mode="Markdown"
        )
    except (ValueError, IndexError):
        await message.answer("⚠️ Неверный формат. Пример: `320x160`. Попробуйте снова:")

@router.message(ModuleAdd.dimensions, F.text == "❌ Отмена")
async def cancel_dimensions(message: types.Message, state: FSMContext):
    try:
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка в cancel_dimensions: {e}")
        await message.answer("❌ Ошибка отмены", reply_markup=get_main_menu())

# ============================================
# ШАГ 5: МЕСТОПОЛОЖЕНИЕ + СОХРАНЕНИЕ В БД
# ============================================

@router.message(ModuleAdd.location, F.text != "❌ Отмена")
async def process_location(message: types.Message, state: FSMContext):
    """Обработка местоположения и сохранение в БД"""
    try:
        location = message.text.strip()
        await state.update_data(location=location)
        data = await state.get_data()
        
        # Валидация размеров
        w, h = OrderService.validate_dimensions(str(data['width']), str(data['height']))
        qty = OrderService.validate_quantity(str(data['quantity']))
        
        with get_db() as db:
            module = LEDModule(
                step=data['step'],
                quantity=qty,
                width=w,
                height=h,
                location=location,
                photo_path=data['photo_path'],
                status=ModuleStatus.IN_STOCK,
                received_date=datetime.utcnow()
            )
            db.add(module)
            db.commit()
            db.refresh(module)
        
        await state.clear()
        
        await message.answer(
            f"✅ **LED модуль добавлен!**\n\n"
            f"🔲 Шаг: **{data['step']}**\n"
            f"📦 Количество: **{qty} шт**\n"
            f"📏 Размеры: **{w} x {h} мм**\n"
            f"📍 Местоположение: **{location}**\n"
            f"📅 Дата: **{datetime.now().strftime('%d.%m.%Y %H:%M')}**",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в process_location: {e}")
        await message.answer(format_error_message(e))

@router.message(ModuleAdd.location, F.text == "❌ Отмена")
async def cancel_location(message: types.Message, state: FSMContext):
    try:
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка в cancel_location: {e}")
        await message.answer("❌ Ошибка отмены", reply_markup=get_main_menu())

# ============================================
# ПОИСК МОДУЛЕЙ
# ============================================

@router.message(F.text == "🔍 Поиск модулей")
async def search_modules(message: types.Message):
    """Поиск модулей по шагу"""
    try:
        keyboard = [
            [KeyboardButton(text="P1.8"), KeyboardButton(text="P2"), KeyboardButton(text="P2.5")],
            [KeyboardButton(text="P3"), KeyboardButton(text="P4"), KeyboardButton(text="P5")],
            [KeyboardButton(text="P6"), KeyboardButton(text="P8"), KeyboardButton(text="P10")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
        await message.answer(
            "🔍 **Поиск модулей по шагу**\n\nВыберите шаг:",
            reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в search_modules: {e}")
        await message.answer(format_error_message(e))

@router.message(F.text.in_(["P1.8", "P2", "P2.5", "P3", "P4", "P5", "P6", "P8", "P10"]))
async def show_modules_by_step(message: types.Message):
    """Показ модулей по выбранному шагу"""
    try:
        step = message.text
        
        with get_db() as db:
            modules = db.query(LEDModule).filter(LEDModule.step == step).limit(10).all()
            
            if not modules:
                await message.answer(f"❌ Модули с шагом **{step}** не найдены.")
                return
            
            result = f"🔲 **Модули с шагом {step}** (найдено: {len(modules)}):\n\n"
            for i, m in enumerate(modules, 1):
                result += f"{i}. **ID: `{m.id}`** | 📦 {m.quantity} шт | 📍 {m.location} | 📅 {m.received_date.strftime('%d.%m.%Y')}\n"
            
            result += "\n💡 *Для просмотра фото напишите ID модуля (например: `5`)*"
            
            await message.answer(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка в show_modules_by_step: {e}")
        await message.answer(format_error_message(e))

# ============================================
# ПРОСМОТР МОДУЛЯ ПО ID
# ============================================

@router.message(F.text.regexp(r"^\d+$"))
async def handle_module_id(message: types.Message, state: FSMContext):
    """Обработка ввода ID модуля (число)"""
    import asyncio
    
    # ⚠️ ВАЖНО: Если юзер в процессе добавления модуля, НЕ обрабатываем как ID
    current_state = await state.get_state()
    if current_state and current_state.startswith("ModuleAdd"):
        # Пропускаем обработку — пусть обработает ModuleAdd обработчик
        return
    
    try:
        module_id = int(message.text.strip())
    except ValueError:
        return
    
    try:
        with get_db() as db:
            module = db.query(LEDModule).filter(LEDModule.id == module_id).first()
            
            if not module:
                await message.answer(f"❌ Модуль с ID `{module_id}` не найден.", parse_mode="Markdown")
                return
            
            # Проверяем существование файла
            if module.photo_path and os.path.exists(module.photo_path):
                # Пробуем отправить фото до 3 раз
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await message.answer_photo(
                            photo=types.FSInputFile(module.photo_path),
                            caption=(
                                f"🔲 **LED Модуль #ID{module.id}**\n\n"
                                f"📏 Шаг: **{module.step}**\n"
                                f"📦 Количество: **{module.quantity} шт**\n"
                                f"📐 Размеры: **{module.width} x {module.height} мм**\n"
                                f"📍 Местоположение: **{module.location}**\n"
                                f"📅 Дата: **{module.received_date.strftime('%d.%m.%Y')}**"
                            ),
                            parse_mode="Markdown"
                        )
                        break  # ✅ Успешно отправили
                    except Exception as e:
                        if attempt == max_retries - 1:
                            # Последняя попытка не удалась — отправляем текст
                            await message.answer(
                                f"🔲 **LED Модуль #ID{module.id}**\n\n"
                                f"📏 Шаг: **{module.step}**\n"
                                f"📦 Количество: **{module.quantity} шт**\n"
                                f"📐 Размеры: **{module.width} x {module.height} мм**\n"
                                f"📍 Местоположение: **{module.location}**\n"
                                f"📅 Дата: **{module.received_date.strftime('%d.%m.%Y')}**\n\n"
                                f"⚠️ *Фото не удалось отправить (таймаут)*\n"
                                f"Путь: `{module.photo_path}`",
                                parse_mode="Markdown"
                            )
                        else:
                            await asyncio.sleep(2)  # Ждем 2 секунды перед повтором
            else:
                await message.answer(
                    f"🔲 **LED Модуль #ID{module.id}**\n\n"
                    f"📏 Шаг: **{module.step}**\n"
                    f"📦 Количество: **{module.quantity} шт**\n"
                    f"📐 Размеры: **{module.width} x {module.height} мм**\n"
                    f"📍 Местоположение: **{module.location}**\n"
                    f"📅 Дата: **{module.received_date.strftime('%d.%m.%Y')}**\n"
                    f"⚠️ *Фото не найдено*",
                    parse_mode="Markdown"
                )
    except Exception as e:
        logger.error(f"Ошибка в handle_module_id: {e}")
        await message.answer(format_error_message(e))

# ============================================
# ОСТАТКИ НА СКЛАДЕ
# ============================================

@router.message(F.text == "📊 Остатки на складе")
async def show_stock_remaining(message: types.Message):
    """Показать остатки по шагам модулей"""
    try:
        with get_db() as db:
            # Отладка: проверяем ВСЕ модули в БД
            all_modules = db.query(LEDModule).all()
            logger.debug(f"Всего модулей в БД: {len(all_modules)}")
            for m in all_modules:
                logger.debug(f"Модуль ID={m.id}, step={m.step}, qty={m.quantity}, status={m.status}")
            
            # Ищем модули со статусом IN_STOCK
            modules = db.query(LEDModule).filter(LEDModule.status == ModuleStatus.IN_STOCK).all()
            logger.debug(f"Модулей со статусом IN_STOCK: {len(modules)}")
            
            if not modules:
                all_count = len(all_modules)
                await message.answer(
                    f"❌ Нет модулей со статусом 'IN_STOCK'.\n\n"
                    f"ℹ️ Всего модулей в БД: {all_count}\n"
                    f"(Это отладка, скоро пофиксим)"
                )
                return
            
            stock_by_step = {}
            for m in modules:
                step = m.step
                if step not in stock_by_step:
                    stock_by_step[step] = 0
                stock_by_step[step] += m.quantity
            
            result = "📊 **Остатки на складе по шагам:**\n\n"
            for step, qty in sorted(stock_by_step.items()):
                result += f"🔲 **{step}**: {qty} шт\n"
            
            result += f"\n📦 **Всего модулей**: {len(modules)}\n"
            result += f"📈 **Общее количество**: {sum(stock_by_step.values())} шт"
            
            await message.answer(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка в show_stock_remaining: {e}")
        await message.answer(format_error_message(e))

# ============================================
# КНОПКА НАЗАД
# ============================================

@router.message(F.text == "⬅️ Назад")
async def menu_back(message: types.Message):
    """Кнопка Назад - возврат в главное меню"""
    try:
        from handlers.start import cmd_start
        await cmd_start(message)
    except Exception as e:
        logger.error(f"Ошибка в menu_back: {e}")
        await message.answer(format_error_message(e))