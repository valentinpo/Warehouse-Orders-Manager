from aiogram import Bot as AioBot
from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, InputFile
from database.db import (
    create_order, get_all_suppliers, get_all_customers, 
    get_order_by_number, add_order_photo, get_order_photos,
    get_order_with_photos, update_order_status
)
from keyboards import get_main_menu, get_orders_menu
import os
from datetime import datetime

# ========================================
#   РОУТЕР
# ========================================
router = Router()

# ========================================
#   СОСТОЯНИЯ (FSM)
# ========================================

class OrderForm(StatesGroup):
    """Состояния формы создания заказа"""
    waiting_for_order_number = State()
    waiting_for_supplier = State()
    waiting_for_customer = State()
    waiting_for_photo = State()

# ========================================
#   КНОПКА "СОЗДАТЬ ЗАКАЗ"
# ========================================

@router.callback_query(F.data == "order_create")
async def order_create_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания заказа"""
    await state.clear()
    
    await callback.message.answer(
        "➕ **Создание нового заказа**\n\n"
        "📝 **Шаг 1/4:** Введите **номер заказа**\n\n"
        "Пример: `ORD-2024-001` или `12345`\n\n"
        "⚠️ Номер должен быть уникальным!",
        reply_markup=ReplyKeyboardRemove()
    )
    
    await state.set_state(OrderForm.waiting_for_order_number)
    await callback.answer()

# ========================================
#   ШАГ 1: НОМЕР ЗАКАЗА
# ========================================

@router.message(OrderForm.waiting_for_order_number)
async def process_order_number(message: types.Message, state: FSMContext):
    """Обработка номера заказа"""
    order_number = message.text.strip()
    
    existing_order = get_order_by_number(order_number)
    if existing_order:
        await message.answer(
            "❌ **Заказ с таким номером уже существует!**\n\n"
            f"Номер: `{order_number}`\n\n"
            "Пожалуйста, введите другой номер:",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    await state.update_data(order_number=order_number)
    
    suppliers = get_all_suppliers()
    
    if suppliers:
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=supplier[1])] for supplier in suppliers
            ] + [[KeyboardButton(text="➕ Добавить нового поставщика")],
                 [KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
        
        await message.answer(
            "📝 **Шаг 2/4:** Выберите **поставщика**\n\n"
            "Нажмите на кнопку или введите название вручную:",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            "📝 **Шаг 2/4:** Введите название **поставщика**\n\n"
            "Пример: `ООО Светотехника` или `ИП Иванов`",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.set_state(OrderForm.waiting_for_supplier)

# ========================================
#   ШАГ 2: ПОСТАВЩИК
# ========================================

@router.message(OrderForm.waiting_for_supplier)
async def process_supplier(message: types.Message, state: FSMContext):
    """Обработка поставщика"""
    supplier = message.text.strip()
    
    if supplier == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ **Форма отменена**\n\n"
            "Вы вернулись в главное меню.",
            reply_markup=get_main_menu()
        )
        return
    
    if supplier == "➕ Добавить нового поставщика":
        await message.answer(
            "Введите название **нового поставщика**:",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    await state.update_data(supplier=supplier)
    
    customers = get_all_customers()
    
    if customers:
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=customer[1])] for customer in customers
            ] + [[KeyboardButton(text="➕ Добавить нового покупателя")],
                 [KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
        
        await message.answer(
            "📝 **Шаг 3/4:** Выберите **покупателя**\n\n"
            "Нажмите на кнопку или введите название вручную:",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            "📝 **Шаг 3/4:** Введите название **покупателя**\n\n"
            "Пример: `ООО СтройМастер` или `ИП Петров`",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.set_state(OrderForm.waiting_for_customer)

# ========================================
#   ШАГ 3: ПОКУПАТЕЛЬ
# ========================================

@router.message(OrderForm.waiting_for_customer)
async def process_customer(message: types.Message, state: FSMContext):
    """Обработка покупателя"""
    customer = message.text.strip()
    
    if customer == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ **Форма отменена**\n\n"
            "Вы вернулись в главное меню.",
            reply_markup=get_main_menu()
        )
        return
    
    if customer == "➕ Добавить нового покупателя":
        await message.answer(
            "Введите название **нового покупателя**:",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    await state.update_data(customer=customer)
    
    data = await state.get_data()
    order_number = data['order_number']
    supplier = data['supplier']
    
    order_id = create_order(order_number, supplier, customer)
    
    if order_id:
        await state.update_data(order_id=order_id)
        
        await message.answer(
            "✅ **Заказ успешно создан!**\n\n"
            f"📦 **Номер:** `{order_number}`\n"
            f"📚 **Поставщик:** `{supplier}`\n"
            f"👤 **Покупатель:** `{customer}`\n\n"
            "📸 **Шаг 4/4:** Добавьте фотографии к заказу\n\n"
            "📷 Отправьте фото **как документ** или **как изображение**\n\n"
            "✅ **Готово** — когда закончите добавлять фото\n"
            "❌ **Пропустить** — чтобы завершить без фото",
            reply_markup=ReplyKeyboardRemove()
        )
        
        await state.set_state(OrderForm.waiting_for_photo)
    else:
        await message.answer(
            "❌ **Ошибка при создании заказа!**\n\n"
            "Попробуйте снова.",
            reply_markup=get_main_menu()
        )
        await state.clear()

# ========================================
#   ШАГ 4: ЗАГРУЗКА ФОТО
# ========================================

@router.message(OrderForm.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Обработка фотографии"""
    data = await state.get_data()
    order_id = data['order_id']
    order_number = data['order_number']
    
    photo = message.photo[-1]
    
    order_folder = f"photos/orders/{order_number}"
    os.makedirs(order_folder, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"photo_{timestamp}.jpg"
    file_path = f"{order_folder}/{file_name}"
    
    bot = AioBot.get_current()
    await bot.download(photo, destination=file_path)
    
    photo_id = add_order_photo(order_id, file_path, message.caption or "")
    
    description = message.caption if message.caption else "Без описания"
    
    await message.answer(
        f"✅ **Фото добавлено!**\n\n"
        f"📁 Файл: `{file_name}`\n"
        f"📝 Описание: `{description}`\n\n"
        "📷 Отправьте ещё фото или напишите **Готово**",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(OrderForm.waiting_for_photo, F.document)
async def process_document(message: types.Message, state: FSMContext):
    """Обработка документа (фото как файл)"""
    data = await state.get_data()
    order_id = data['order_id']
    order_number = data['order_number']
    
    doc = message.document
    
    if not doc.mime_type.startswith('image/'):
        await message.answer(
            "❌ **Это не изображение!**\n\n"
            "Пожалуйста, отправьте фото (JPG, PNG).",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    order_folder = f"photos/orders/{order_number}"
    os.makedirs(order_folder, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"photo_{timestamp}.jpg"
    file_path = f"{order_folder}/{file_name}"
    
    await bot.download(doc, destination=file_path)
    
    add_order_photo(order_id, file_path, message.caption or "")
    
    await message.answer(
        f"✅ **Фото добавлено!**\n\n"
        "📷 Отправьте ещё фото или напишите **Готово**",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(OrderForm.waiting_for_photo, F.text)
async def process_photo_complete(message: types.Message, state: FSMContext):
    """Завершение загрузки фото"""
    text = message.text.strip().lower()
    
    if text in ["готово", "готово!", "ok", "👍"]:
        data = await state.get_data()
        order_id = data['order_id']
        order_number = data['order_number']
        
        photos = get_order_photos(order_id)
        
        await message.answer(
            "🎉 **Заказ полностью оформлен!**\n\n"
            f"📦 **Номер:** `{order_number}`\n"
            f"📸 **Фотографий:** `{len(photos)}`\n\n"
            "✅ Вы можете просмотреть заказ в разделе **📋 Все заказы**",
            reply_markup=get_main_menu()
        )
        
        await state.clear()
        
    elif text in ["пропустить", "без фото", "дальше"]:
        await message.answer(
            "✅ **Заказ создан без фотографий**\n\n"
            "Вы можете добавить фото позже через просмотр заказа.",
            reply_markup=get_main_menu()
        )
        await state.clear()
        
    else:
        await message.answer(
            "📷 **Ожидание фотографий...**\n\n"
            "Отправьте фото или напишите **Готово** для завершения:",
            reply_markup=ReplyKeyboardRemove()
        )

# ========================================
#   ПРОСМОТР ЗАКАЗА С ФОТО
# ========================================

@router.callback_query(F.data.startswith("order_view_"))
async def order_view(callback: types.CallbackQuery, state: FSMContext):
    """Просмотр заказа с фотографиями"""
    order_id = int(callback.data.replace("order_view_", ""))
    
    order, photos = get_order_with_photos(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден!", show_alert=True)
        return
    
    order_id_db, order_number, supplier, customer, status, created_at = order
    
    text = (
        f"📦 **Заказ: `{order_number}`**\n\n"
        f"📚 **Поставщик:** `{supplier}`\n"
        f"👤 **Покупатель:** `{customer}`\n"
        f"📊 **Статус:** `{status}`\n"
        f"📅 **Создан:** `{created_at}`\n\n"
        f"📸 **Фотографий:** `{len(photos)}`\n"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    photo_buttons = []
    for i, photo in enumerate(photos):
        photo_id, file_path, description, uploaded_at = photo
        photo_buttons.append([
            InlineKeyboardButton(
                text=f"📷 Фото {i+1}",
                callback_data=f"photo_{order_id}_{photo_id}"
            )
        ])
    
    control_buttons = [
        [InlineKeyboardButton(text="🔄 Обновить статус", callback_data=f"status_{order_id}")],
        [InlineKeyboardButton(text="📋 Все заказы", callback_data="order_list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")]
    ]
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=photo_buttons + control_buttons
    )
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("photo_"))
async def view_photo(callback: types.CallbackQuery):
    """Просмотр конкретной фотографии"""
    parts = callback.data.replace("photo_", "").split("_")
    order_id = int(parts[0])
    photo_id = int(parts[1])
    
    order, photos = get_order_with_photos(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден!", show_alert=True)
        return
    
    photo_data = None
    for photo in photos:
        if photo[0] == photo_id:
            photo_data = photo
            break
    
    if not photo_data:
        await callback.answer("❌ Фото не найдено!", show_alert=True)
        return
    
    _, file_path, description, uploaded_at = photo_data
    
    if not os.path.exists(file_path):
        await callback.answer("❌ Файл не найден на диске!", show_alert=True)
        return
    
    from aiogram import Bot
    bot = Bot.get_current()
    
    photo_file = InputFile(file_path)
    
    caption = f"📸 **Фотография**\n\n📝 Описание: `{description or 'Без описания'}`\n📅 Загружено: `{uploaded_at}`"
    
    await callback.message.answer_photo(photo=photo_file, caption=caption)
    await callback.answer()

@router.callback_query(F.data.startswith("status_"))
async def change_status(callback: types.CallbackQuery):
    """Изменение статуса заказа"""
    order_id = int(callback.data.replace("status_", ""))
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Создан", callback_data=f"set_status_{order_id}_created")],
            [InlineKeyboardButton(text="🚚 Отгружен", callback_data=f"set_status_{order_id}_shipped")],
            [InlineKeyboardButton(text="✅ Доставлен", callback_data=f"set_status_{order_id}_delivered")],
            [InlineKeyboardButton(text="❌ Отменён", callback_data=f"set_status_{order_id}_cancelled")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"order_view_{order_id}")]
        ]
    )
    
    await callback.message.answer(
        "📊 **Выберите новый статус заказа:**",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("set_status_"))
async def set_status(callback: types.CallbackQuery):
    """Установка статуса заказа"""
    parts = callback.data.replace("set_status_", "").split("_")
    order_id = int(parts[0])
    new_status = parts[1]
    
    update_order_status(order_id, new_status)
    
    status_names = {
        "created": "📝 Создан",
        "shipped": "🚚 Отгружен",
        "delivered": "✅ Доставлен",
        "cancelled": "❌ Отменён"
    }
    
    await callback.message.answer(
        f"✅ **Статус изменён!**\n\n"
        f"Новый статус: `{status_names.get(new_status, new_status)}`",
        reply_markup=get_orders_menu()
    )
    await callback.answer()

# ========================================
#   ОТМЕНА ФОРМЫ
# ========================================

@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cancel_form(message: types.Message, state: FSMContext):
    """Отмена создания заказа"""
    await state.clear()
    await message.answer(
        "❌ **Форма отменена**\n\n"
        "Вы вернулись в главное меню.",
        reply_markup=get_main_menu()
    )