from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.main_menu import get_main_menu, get_cancel_keyboard
from database.db_manager import get_db
from database.models import Order, OrderPhoto, OrderStatus, Supplier, Customer
from services import OrderService, SupplierService, format_error_message
from sqlalchemy.orm import joinedload
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

router = Router()

# ============================================
# МАШИНА СОСТОЯНИЙ
# ============================================

class OrderCreate(StatesGroup):
    number = State()
    supplier = State()
    customer = State()
    photos = State()
    confirm = State()

# ============================================
# МЕНЮ ЗАКАЗОВ
# ============================================

@router.message(F.text == "📦 Заказы")
async def menu_orders(message: types.Message):
    """Меню модуля заказов"""
    try:
        keyboard = [
            [KeyboardButton(text="➕ Новый заказ")],
            [KeyboardButton(text="🔍 Поиск заказа")],
            [KeyboardButton(text="📋 Список заказов")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
        await message.answer(
            "📦 **Заказы**\n\nВыберите действие:",
            reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в menu_orders: {e}")
        await message.answer("❌ Ошибка загрузки меню")

# ============================================
# НОВЫЙ ЗАКАЗ - НАЧАЛО
# ============================================

@router.message(Command("order_new"))
@router.message(F.text == "➕ Новый заказ")
async def start_new_order(message: types.Message, state: FSMContext):
    """Начало создания нового заказа"""
    await state.set_state(OrderCreate.number)
    await message.answer(
        "📦 **Создание нового заказа**\n\n"
        "Введите **номер заказа**:\n"
        "Пример: `ЗАК-2026-001`\n\n"
        "❌ Отмена - для отмены",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )

# ============================================
# ШАГ 1: НОМЕР ЗАКАЗА
# ============================================

@router.message(OrderCreate.number, F.text != "❌ Отмена")
async def process_order_number(message: types.Message, state: FSMContext):
    """Обработка номера заказа"""
    try:
        order_number = message.text.strip()
        
        # Валидация номера заказа
        OrderService.validate_order_number(order_number)
        
        # Проверка дублирования
        if OrderService.check_order_number_exists(order_number):
            await message.answer("❌ Заказ с таким номером уже существует!")
            return
        
        await state.update_data(order_number=order_number)
        await state.set_state(OrderCreate.supplier)
        
        with get_db() as db:
            suppliers = db.query(Supplier).limit(10).all()
            
            if not suppliers:
                await message.answer(
                    "⚠️ **Поставщики не найдены!**\n\n"
                    "Сначала добавьте поставщика:\n"
                    "📚 Поставщики → ➕ Добавить поставщика",
                    parse_mode="Markdown"
                )
                await message.answer(
                    "Введите **название поставщика** вручную:\n\n"
                    "❌ Отмена - для отмены",
                    reply_markup=get_cancel_keyboard()
                )
                return
            
            keyboard = []
            for s in suppliers:
                keyboard.append([InlineKeyboardButton(
                    text=f"{s.name} (ID: {s.id})",
                    callback_data=f"supplier_{s.id}"
                )])
            keyboard.append([InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="supplier_manual")])
            
            await message.answer(
                "📚 **Выберите поставщика**:\n"
                "Нажмите на кнопку или введите название вручную:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка в process_order_number: {e}")
        error_msg = format_error_message(e)
        await message.answer(error_msg)

@router.message(OrderCreate.number, F.text == "❌ Отмена")
async def cancel_order_number(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_main_menu())

# ============================================
# ШАГ 2: ВЫБОР ПОСТАВЩИКА
# ============================================

@router.callback_query(OrderCreate.supplier, F.data.startswith("supplier_"))
async def process_supplier_select(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора поставщика"""
    try:
        data = callback.data
        
        if data == "supplier_manual":
            await callback.message.answer(
                "Введите **название поставщика** вручную:\n\n"
                "❌ Отмена - для отмены",
                reply_markup=get_cancel_keyboard()
            )
            await callback.answer()
            return
        
        supplier_id = int(data.replace("supplier_", ""))
        await state.update_data(supplier_id=supplier_id)
        
        with get_db() as db:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            supplier_name = supplier.name if supplier else f"ID:{supplier_id}"
        
        await state.set_state(OrderCreate.customer)
        
        with get_db() as db:
            customers = db.query(Customer).limit(10).all()
            
            if not customers:
                await callback.message.answer(
                    "⚠️ **Покупатели не найдены!**\n\n"
                    "Сначала добавьте покупателя:\n"
                    "👥 Покупатели → ➕ Добавить покупателя",
                    parse_mode="Markdown"
                )
                await callback.message.answer(
                    "Введите **название покупателя** вручную:\n\n"
                    "❌ Отмена - для отмены",
                    reply_markup=get_cancel_keyboard()
                )
                return
            
            keyboard = []
            for c in customers:
                keyboard.append([InlineKeyboardButton(
                    text=f"{c.name} (ID: {c.id})",
                    callback_data=f"customer_{c.id}"
                )])
            keyboard.append([InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="customer_manual")])
            
            await callback.message.answer(
                f"✅ Поставщик: **{supplier_name}**\n\n"
                "👥 **Выберите покупателя**:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="Markdown"
            )
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в process_supplier_select: {e}")
        await callback.answer("❌ Ошибка")
        await callback.message.answer(format_error_message(e))

@router.message(OrderCreate.supplier, F.text != "❌ Отмена")
async def process_supplier_manual(message: types.Message, state: FSMContext):
    """Ручной ввод поставщика"""
    try:
        supplier_name = message.text.strip()
        SupplierService.validate_supplier_name(supplier_name)
        
        await state.update_data(supplier_name=supplier_name)
        await state.set_state(OrderCreate.customer)
        
        with get_db() as db:
            customers = db.query(Customer).limit(10).all()
            
            if not customers:
                await message.answer(
                    "⚠️ **Покупатели не найдены!**\n"
                    "Введите **название покупателя** вручную:",
                    parse_mode="Markdown"
                )
                return
            
            keyboard = []
            for c in customers:
                keyboard.append([InlineKeyboardButton(
                    text=f"{c.name} (ID: {c.id})",
                    callback_data=f"customer_{c.id}"
                )])
            keyboard.append([InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="customer_manual")])
            
            await message.answer(
                f"✅ Поставщик: **{supplier_name}**\n\n"
                "👥 **Выберите покупателя**:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка в process_supplier_manual: {e}")
        await message.answer(format_error_message(e))

@router.message(OrderCreate.supplier, F.text == "❌ Отмена")
async def cancel_supplier(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_main_menu())

# ============================================
# ШАГ 3: ВЫБОР ПОКУПАТЕЛЯ
# ============================================

@router.callback_query(OrderCreate.customer, F.data.startswith("customer_"))
async def process_customer_select(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора покупателя"""
    data = callback.data
    
    if data == "customer_manual":
        await callback.message.answer(
            "Введите **название покупателя** вручную:\n"
            "❌ Отмена - для отмены",
            reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
        return
    
    customer_id = int(data.replace("customer_", ""))
    await state.update_data(customer_id=customer_id)
    
    try:
        with get_db() as db:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            customer_name = customer.name if customer else f"ID:{customer_id}"
        
        await state.set_state(OrderCreate.photos)
        
        await callback.message.answer(
            f"✅ Покупатель: **{customer_name}**\n\n"
            "📸 Отправьте **фотографии заказа** (1-10 шт):\n"
            "Когда закончите — напишите **готово**\n\n"
            "❌ Отмена - для отмены",
            reply_markup=get_cancel_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в process_customer_select: {e}")
        await callback.answer(format_error_message(e), show_alert=True)
    
    await callback.answer()

@router.message(OrderCreate.customer, F.text != "❌ Отмена")
async def process_customer_manual(message: types.Message, state: FSMContext):
    """Ручной ввод покупателя"""
    await state.update_data(customer_name=message.text.strip())
    await state.set_state(OrderCreate.photos)
    
    await message.answer(
        f"✅ Покупатель: **{message.text.strip()}**\n\n"
        "📸 Отправьте **фотографии заказа** (1-10 шт):\n"
        "Когда закончите — напишите **готово**\n\n"
        "❌ Отмена - для отмены",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )

@router.message(OrderCreate.customer, F.text == "❌ Отмена")
async def cancel_customer(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_main_menu())

# ============================================
# ШАГ 4: ФОТОГРАФИИ
# ============================================

@router.message(OrderCreate.photos, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Обработка фотографии заказа"""
    photo = message.photo[-1]
    folder = "photos/orders"
    os.makedirs(folder, exist_ok=True)
    file_path = f"{folder}/order_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    
    await message.bot.download(photo, destination=file_path)
    
    data = await state.get_data()
    photos = data.get('photos', [])
    photos.append(file_path)
    await state.update_data(photos=photos)
    
    count = len(photos)
    if count < 10:
        await message.answer(
            f"✅ Фото #{count} сохранено\n\n"
            "Отправьте ещё фото или напишите **готово**:",
            reply_markup=get_cancel_keyboard()
        )
    else:
        await message.answer(
            "✅ Максимум фото (10) достигнуто!\n"
            "Напишите **готово** для завершения:",
            reply_markup=get_cancel_keyboard()
        )

@router.message(OrderCreate.photos, F.text.lower() == "готово")
async def finish_photos(message: types.Message, state: FSMContext):
    """Завершение загрузки фото и сохранение заказа"""
    data = await state.get_data()
    photos = data.get('photos', [])
    
    if not photos:
        await message.answer("⚠️ Добавьте хотя бы одно фото!")
        return
    
    try:
        with get_db() as db:
            supplier_id = data.get('supplier_id')
            customer_id = data.get('customer_id')
        
        supplier_name = "Не указан"
        if supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if supplier:
                supplier_name = supplier.name
        elif data.get('supplier_name'):
            supplier_name = data['supplier_name']
        
        customer_name = "Не указан"
        if customer_id:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                customer_name = customer.name
        elif data.get('customer_name'):
            customer_name = data['customer_name']
        
        order = Order(
            order_number=data['order_number'],
            supplier_id=supplier_id,
            customer_id=customer_id,
            status=OrderStatus.CREATED,
            created_by=message.from_user.id,
            created_at=datetime.utcnow()
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        for photo_path in photos:
            order_photo = OrderPhoto(
                order_id=order.id,
                file_path=photo_path
            )
            db.add(order_photo)
        
        db.commit()
        
        order_id = order.id
        
    except Exception as e:
        logger.error(f"Ошибка в confirm_order: {e}")
        await message.answer(format_error_message(e))
        return
    
    await state.clear()
    
    await message.answer(
        f"✅ **Заказ создан!**\n\n"
        f"📦 Номер: **{data['order_number']}**\n"
        f"📚 Поставщик: **{supplier_name}**\n"
        f"👥 Покупатель: **{customer_name}**\n"
        f"📸 Фото: **{len(photos)} шт**\n"
        f"📅 Дата: **{datetime.now().strftime('%d.%m.%Y %H:%M')}**\n\n"
        f"🆔 ID заказа: `{order_id}`",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@router.message(OrderCreate.photos, F.text == "❌ Отмена")
async def cancel_photos(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_main_menu())

# ============================================
# СПИСОК ЗАКАЗОВ
# ============================================

@router.message(F.text == "📋 Список заказов")
async def list_orders(message: types.Message):
    """Показать последние заказы"""
    try:
        with get_db() as db:
            orders = (db.query(Order)
                      .options(
                          joinedload(Order.supplier),
                          joinedload(Order.customer)
                      )
                      .order_by(Order.created_at.desc())
                      .limit(10)
                      .all())
        
        if not orders:
            await message.answer("❌ Заказы не найдены.")
            return
        
        keyboard = []
        result = "📦 **Последние заказы** (10 шт):\n\n"
        
        for i, o in enumerate(orders, 1):
            supplier_name = o.supplier.name if o.supplier else "Н/Д"
            customer_name = o.customer.name if o.customer else "Н/Д"
            
            result += f"{i}. **ID: `{o.id}`** | {o.order_number}\n"
            result += f"   📚 {supplier_name} → 👥 {customer_name}\n"
            result += f"   📅 {o.created_at.strftime('%d.%m.%Y')}\n\n"
            
            keyboard.append([InlineKeyboardButton(
                text=f"📦 {o.order_number} ({supplier_name})",
                callback_data=f"order_details_{o.id}"
            )])
        
        keyboard.append([InlineKeyboardButton(text="🔄 Обновить список", callback_data="orders_list")])
        
        await message.answer(
            result,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в process_customer_manual: {e}")
        await message.answer(format_error_message(e))

# ============================================
# ПРОСМОТР ДЕТАЛЕЙ ЗАКАЗА
# ============================================

@router.callback_query(F.data.startswith("order_details_"))
async def view_order_details(callback: types.CallbackQuery):
    """Просмотр деталей заказа"""
    try:
        order_id = int(callback.data.replace("order_details_", ""))
        
        with get_db() as db:
            order = (db.query(Order)
                     .options(
                         joinedload(Order.supplier),
                         joinedload(Order.customer),
                         joinedload(Order.photos)
                     )
                     .filter(Order.id == order_id)
                     .first())
        
        if not order:
            await callback.answer("❌ Заказ не найден", show_alert=True)
            return
        
        supplier_name = order.supplier.name if order.supplier else "Не указан"
        customer_name = order.customer.name if order.customer else "Не указан"
        
        status_emoji = {
            OrderStatus.CREATED: "📝",
            OrderStatus.IN_PROGRESS: "⚙️",
            OrderStatus.SHIPPED: "🚚",
            OrderStatus.COMPLETED: "✅",
            OrderStatus.CANCELLED: "❌"
        }.get(order.status, "📦")
        
        photos_count = len(order.photos) if order.photos else 0
        
        result = (
            f"📦 **Заказ #{order.order_number}**\n\n"
            f"🆔 ID: `{order.id}`\n"
            f"📚 Поставщик: **{supplier_name}**\n"
            f"👥 Покупатель: **{customer_name}**\n"
            f"📦 Статус: **{status_emoji} {order.status.value}**\n"
            f"📅 Создан: **{order.created_at.strftime('%d.%m.%Y %H:%M')}**\n"
        )
        
        if order.ship_date:
            result += f"🚚 Отгружен: **{order.ship_date.strftime('%d.%m.%Y')}**\n"
        
        result += f"📸 Фото: **{photos_count} шт**\n"
        
        keyboard = []
        
        if order.photos:
            keyboard.append([InlineKeyboardButton(
                text=f"📸 Просмотреть фото ({photos_count})",
                callback_data=f"order_photos_{order_id}"
            )])
        
        keyboard.append([
            InlineKeyboardButton(text="🔄 Изменить статус", callback_data=f"order_status_{order_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"order_delete_{order_id}")
        ])
        
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="orders_list")])
        
        await callback.message.answer(
            result,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в process_supplier_select: {e}")
        await callback.answer(format_error_message(e), show_alert=True)
    
    await callback.answer()

# ============================================
# ПРОСМОТР ФОТО ЗАКАЗА
# ============================================

@router.callback_query(F.data.startswith("order_photos_"))
async def view_order_photos(callback: types.CallbackQuery):
    """Просмотр всех фото заказа"""
    try:
        order_id = int(callback.data.replace("order_photos_", ""))
        
        with get_db() as db:
            order = (db.query(Order)
                     .options(joinedload(Order.photos))
                     .filter(Order.id == order_id)
                     .first())
        
        if not order or not order.photos:
            await callback.answer("❌ Фото не найдены", show_alert=True)
            return
        
        for i, photo in enumerate(order.photos, 1):
            if os.path.exists(photo.file_path):
                await callback.message.answer_photo(
                    photo=types.FSInputFile(photo.file_path),
                    caption=f"📸 Фото #{i} из {len(order.photos)}\n"
                           f"📦 Заказ: {order.order_number}\n"
                           f"📅 Загружено: {photo.uploaded_at.strftime('%d.%m.%Y %H:%M')}",
                    parse_mode="Markdown"
                )
            else:
                await callback.message.answer(
                    f"⚠️ Фото #{i} не найдено по пути: `{photo.file_path}`",
                    parse_mode="Markdown"
                )
        
        keyboard = [[InlineKeyboardButton(
            text="⬅️ Назад к заказу",
            callback_data=f"order_details_{order_id}"
        )]]
        
        await callback.message.answer(
            f"✅ Отправлено {len(order.photos)} фото",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в view_order_details: {e}")
        await callback.answer(format_error_message(e), show_alert=True)
    
    await callback.answer()

# ============================================
# ИЗМЕНЕНИЕ СТАТУСА ЗАКАЗА
# ============================================

@router.callback_query(F.data.startswith("order_status_"))
async def change_order_status(callback: types.CallbackQuery):
    """Изменение статуса заказа"""
    order_id = int(callback.data.replace("order_status_", ""))
    
    keyboard = [
        [
            InlineKeyboardButton(text="📝 Создан", callback_data=f"set_status_{order_id}_created"),
            InlineKeyboardButton(text="⚙️ В работе", callback_data=f"set_status_{order_id}_in_progress")
        ],
        [
            InlineKeyboardButton(text="🚚 Отгружен", callback_data=f"set_status_{order_id}_shipped"),
            InlineKeyboardButton(text="✅ Завершен", callback_data=f"set_status_{order_id}_completed")
        ],
        [
            InlineKeyboardButton(text="❌ Отменен", callback_data=f"set_status_{order_id}_cancelled")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"order_details_{order_id}")
        ]
    ]
    
    await callback.message.answer(
        "🔄 **Изменение статуса заказа**\n\nВыберите новый статус:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("set_status_"))
async def set_order_status(callback: types.CallbackQuery):
    """Установка статуса заказа"""
    parts = callback.data.split("_")
    order_id = int(parts[2])
    status_name = parts[3]
    
    status_map = {
        "created": OrderStatus.CREATED,
        "in_progress": OrderStatus.IN_PROGRESS,
        "shipped": OrderStatus.SHIPPED,
        "completed": OrderStatus.COMPLETED,
        "cancelled": OrderStatus.CANCELLED
    }
    
    new_status = status_map.get(status_name)
    if not new_status:
        await callback.answer("❌ Неверный статус", show_alert=True)
        return
    
    try:
        with get_db() as db:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                await callback.answer("❌ Заказ не найден", show_alert=True)
                return
        
        order.status = new_status
        
        if new_status == OrderStatus.SHIPPED:
            order.ship_date = datetime.utcnow()
        
        db.commit()
        
        status_emoji = {
            OrderStatus.CREATED: "📝",
            OrderStatus.IN_PROGRESS: "⚙️",
            OrderStatus.SHIPPED: "🚚",
            OrderStatus.COMPLETED: "✅",
            OrderStatus.CANCELLED: "❌"
        }.get(new_status, "📦")
        
        await callback.answer(f"✅ Статус изменен: {status_emoji} {new_status.value}", show_alert=True)
        
        await callback.message.delete()
        
    except Exception as e:
        logger.error(f"Ошибка в update_order_status: {e}")
        await callback.answer(format_error_message(e), show_alert=True)

# ============================================
# УДАЛЕНИЕ ЗАКАЗА
# ============================================

@router.callback_query(F.data.startswith("order_delete_"))
async def delete_order_confirm(callback: types.CallbackQuery):
    """Подтверждение удаления заказа"""
    order_id = int(callback.data.replace("order_delete_", ""))
    
    keyboard = [
        [
            InlineKeyboardButton(text="❌ Да, удалить", callback_data=f"delete_confirm_{order_id}"),
            InlineKeyboardButton(text="✅ Отмена", callback_data=f"order_details_{order_id}")
        ]
    ]
    
    await callback.message.answer(
        "⚠️ **Удаление заказа**\n\n"
        "Вы уверены? Это действие нельзя отменить!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_confirm_"))
async def delete_order_execute(callback: types.CallbackQuery):
    """Удаление заказа"""
    try:
        order_id = int(callback.data.replace("delete_confirm_", ""))
        
        with get_db() as db:
            order = db.query(Order).filter(Order.id == order_id).first()
            order_number = order.order_number if order else f"#{order_id}"
        
        if order:
            for photo in order.photos:
                if os.path.exists(photo.file_path):
                    os.remove(photo.file_path)
            
            db.delete(order)
            db.commit()
        
        await callback.message.delete()
        await callback.message.answer(
            f"✅ Заказ **{order_number}** удален",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в delete_order_execute: {e}")
        await callback.answer(format_error_message(e), show_alert=True)
    
    await callback.answer()

# ============================================
# КНОПКА НАЗАД К СПИСКУ
# ============================================

@router.callback_query(F.data == "orders_list")
async def back_to_orders_list(callback: types.CallbackQuery):
    """Возврат к списку заказов"""
    await callback.message.delete()
    await list_orders(callback.message)
    await callback.answer()

# ============================================
# КНОПКА НАЗАД
# ============================================

@router.message(F.text == "⬅️ Назад")
async def menu_back(message: types.Message):
    """Кнопка Назад - возврат в главное меню"""
    from handlers.start import cmd_start
    await cmd_start(message)