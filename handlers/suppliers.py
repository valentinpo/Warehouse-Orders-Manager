from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards.main_menu import get_main_menu, get_cancel_keyboard
from database.db_manager import get_db
from database.models import Supplier
from services import SupplierService, format_error_message
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = Router()

# Машина состояний для добавления поставщика
class SupplierAdd(StatesGroup):
    name = State()
    contact_person = State()
    phone = State()
    email = State()
    address = State()

# ============================================
# МЕНЮ ПОСТАВЩИКОВ
# ============================================

@router.message(F.text == "📚 Поставщики")
async def menu_suppliers(message: types.Message):
    """Меню справочника поставщиков"""
    keyboard = [
        [KeyboardButton(text="➕ Добавить поставщика")],
        [KeyboardButton(text="📋 Список поставщиков")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    await message.answer(
        "📚 **Поставщики**\n\nВыберите действие:",
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )

# ============================================
# ДОБАВИТЬ ПОСТАВЩИКА
# ============================================

@router.message(F.text == "➕ Добавить поставщика")
async def start_add_supplier(message: types.Message, state: FSMContext):
    """Начало добавления поставщика"""
    await state.set_state(SupplierAdd.name)
    await message.answer(
        "📚 **Добавление поставщика**\n\n"
        "Введите **название организации**:\n\n"
        "❌ Отмена - для отмены",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )

@router.message(SupplierAdd.name, F.text != "❌ Отмена")
async def process_name(message: types.Message, state: FSMContext):
    """Обработка названия"""
    await state.update_data(name=message.text.strip())
    await state.set_state(SupplierAdd.contact_person)
    await message.answer(
        f"✅ Название: **{message.text.strip()}**\n\n"
        "Введите **контактное лицо** (или пропустите):\n\n"
        "❌ Отмена - для отмены",
        parse_mode="Markdown"
    )

@router.message(SupplierAdd.contact_person, F.text != "❌ Отмена")
async def process_contact(message: types.Message, state: FSMContext):
    """Обработка контактного лица"""
    await state.update_data(contact_person=message.text.strip())
    await state.set_state(SupplierAdd.phone)
    await message.answer(
        f"✅ Контакт: **{message.text.strip()}**\n\n"
        "Введите **телефон** (или пропустите):\n\n"
        "❌ Отмена - для отмены",
        parse_mode="Markdown"
    )

@router.message(SupplierAdd.phone, F.text != "❌ Отмена")
async def process_phone(message: types.Message, state: FSMContext):
    """Обработка телефона"""
    await state.update_data(phone=message.text.strip())
    await state.set_state(SupplierAdd.email)
    await message.answer(
        f"✅ Телефон: **{message.text.strip()}**\n\n"
        "Введите **email** (или пропустите):\n\n"
        "❌ Отмена - для отмены",
        parse_mode="Markdown"
    )

@router.message(SupplierAdd.email, F.text != "❌ Отмена")
async def process_email(message: types.Message, state: FSMContext):
    """Обработка email"""
    await state.update_data(email=message.text.strip())
    await state.set_state(SupplierAdd.address)
    await message.answer(
        f"✅ Email: **{message.text.strip()}**\n\n"
        "Введите **адрес** (или пропустите):\n\n"
        "❌ Отмена - для отмены",
        parse_mode="Markdown"
    )

@router.message(SupplierAdd.address, F.text != "❌ Отмена")
async def process_address(message: types.Message, state: FSMContext):
    """Обработка адреса и сохранение в БД"""
    try:
        address = message.text.strip()
        await state.update_data(address=address)
        data = await state.get_data()
        
        # Валидация
        SupplierService.validate_supplier_name(data['name'])
        if data.get('phone'):
            SupplierService.validate_phone(data['phone'])
        if data.get('email'):
            SupplierService.validate_email(data['email'])
        
        with get_db() as db:
            supplier = Supplier(
                name=data['name'],
                contact_person=data.get('contact_person', ''),
                phone=data.get('phone', ''),
                email=data.get('email', ''),
                address=data.get('address', '')
            )
            db.add(supplier)
            db.commit()
            db.refresh(supplier)
        
        await state.clear()
        
        await message.answer(
            f"✅ **Поставщик добавлен!**\n\n"
            f"📚 Название: **{data['name']}**\n"
            f"👤 Контакт: **{data.get('contact_person', 'Н/Д')}**\n"
            f"📞 Телефон: **{data.get('phone', 'Н/Д')}**\n"
            f"📧 Email: **{data.get('email', 'Н/Д')}**\n"
            f"📍 Адрес: **{data.get('address', 'Н/Д')}**\n"
            f"📅 Дата: **{datetime.now().strftime('%d.%m.%Y %H:%M')}**\n\n"
            f"🆔 ID: `{supplier.id}` (для использования в заказах)",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в process_address: {e}")
        await message.answer(format_error_message(e))

@router.message(SupplierAdd.name, F.text == "❌ Отмена")
@router.message(SupplierAdd.contact_person, F.text == "❌ Отмена")
@router.message(SupplierAdd.phone, F.text == "❌ Отмена")
@router.message(SupplierAdd.email, F.text == "❌ Отмена")
@router.message(SupplierAdd.address, F.text == "❌ Отмена")
async def cancel_supplier(message: types.Message, state: FSMContext):
    """Отмена добавления поставщика"""
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_main_menu())

# ============================================
# СПИСОК ПОСТАВЩИКОВ
# ============================================

@router.message(F.text == "📋 Список поставщиков")
async def list_suppliers(message: types.Message):
    """Показать всех поставщиков"""
    try:
        with get_db() as db:
            suppliers = db.query(Supplier).limit(20).all()
            
            if not suppliers:
                await message.answer("❌ Поставщики не найдены.\n\nДобавьте первого поставщика!")
                return
            
            result = "📚 **Все поставщики** (показано 20):\n\n"
            for i, s in enumerate(suppliers, 1):
                result += f"{i}. **ID: `{s.id}`** | {s.name}\n"
                if s.phone:
                    result += f"   📞 {s.phone}\n"
            
            result += "\n💡 *Используйте ID при создании заказа*"
            
            await message.answer(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка в list_suppliers: {e}")
        await message.answer(format_error_message(e))

# ============================================
# КНОПКА НАЗАД
# ============================================

@router.message(F.text == "⬅️ Назад")
async def menu_back(message: types.Message):
    """Кнопка Назад - возврат в главное меню"""
    from handlers.start import cmd_start
    await cmd_start(message)