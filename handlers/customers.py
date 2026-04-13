from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards.main_menu import get_main_menu, get_cancel_keyboard
from database.db_manager import get_db
from database.models import Customer
from services import CustomerService, format_error_message
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = Router()

# Машина состояний для добавления покупателя
class CustomerAdd(StatesGroup):
    name = State()
    contact_person = State()
    phone = State()
    email = State()
    address = State()

# ============================================
# МЕНЮ ПОКУПАТЕЛЕЙ
# ============================================

@router.message(F.text == "👥 Покупатели")
async def menu_customers(message: types.Message):
    """Меню справочника покупателей"""
    keyboard = [
        [KeyboardButton(text="➕ Добавить покупателя")],
        [KeyboardButton(text="📋 Список покупателей")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    await message.answer(
        "👥 **Покупатели**\n\nВыберите действие:",
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )

# ============================================
# ДОБАВИТЬ ПОКУПАТЕЛЯ
# ============================================

@router.message(F.text == "➕ Добавить покупателя")
async def start_add_customer(message: types.Message, state: FSMContext):
    """Начало добавления покупателя"""
    await state.set_state(CustomerAdd.name)
    await message.answer(
        "👥 **Добавление покупателя**\n\n"
        "Введите **название организации**:\n\n"
        "❌ Отмена - для отмены",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )

@router.message(CustomerAdd.name, F.text != "❌ Отмена")
async def process_name(message: types.Message, state: FSMContext):
    """Обработка названия"""
    await state.update_data(name=message.text.strip())
    await state.set_state(CustomerAdd.contact_person)
    await message.answer(
        f"✅ Название: **{message.text.strip()}**\n\n"
        "Введите **контактное лицо** (или пропустите):\n\n"
        "❌ Отмена - для отмены",
        parse_mode="Markdown"
    )

@router.message(CustomerAdd.contact_person, F.text != "❌ Отмена")
async def process_contact(message: types.Message, state: FSMContext):
    """Обработка контактного лица"""
    await state.update_data(contact_person=message.text.strip())
    await state.set_state(CustomerAdd.phone)
    await message.answer(
        f"✅ Контакт: **{message.text.strip()}**\n\n"
        "Введите **телефон** (или пропустите):\n\n"
        "❌ Отмена - для отмены",
        parse_mode="Markdown"
    )

@router.message(CustomerAdd.phone, F.text != "❌ Отмена")
async def process_phone(message: types.Message, state: FSMContext):
    """Обработка телефона"""
    await state.update_data(phone=message.text.strip())
    await state.set_state(CustomerAdd.email)
    await message.answer(
        f"✅ Телефон: **{message.text.strip()}**\n\n"
        "Введите **email** (или пропустите):\n\n"
        "❌ Отмена - для отмены",
        parse_mode="Markdown"
    )

@router.message(CustomerAdd.email, F.text != "❌ Отмена")
async def process_email(message: types.Message, state: FSMContext):
    """Обработка email"""
    await state.update_data(email=message.text.strip())
    await state.set_state(CustomerAdd.address)
    await message.answer(
        f"✅ Email: **{message.text.strip()}**\n\n"
        "Введите **адрес** (или пропустите):\n\n"
        "❌ Отмена - для отмены",
        parse_mode="Markdown"
    )

@router.message(CustomerAdd.address, F.text != "❌ Отмена")
async def process_address(message: types.Message, state: FSMContext):
    """Обработка адреса и сохранение в БД"""
    try:
        address = message.text.strip()
        await state.update_data(address=address)
        data = await state.get_data()
        
        # Валидация
        CustomerService.validate_name(data['name'])
        if data.get('phone'):
            CustomerService.validate_phone(data['phone'])
        if data.get('email'):
            CustomerService.validate_email(data['email'])
        
        with get_db() as db:
            customer = Customer(
                name=data['name'],
                contact_person=data.get('contact_person', ''),
                phone=data.get('phone', ''),
                email=data.get('email', ''),
                address=data.get('address', '')
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
        
        await state.clear()
        
        await message.answer(
            f"✅ **Покупатель добавлен!**\n\n"
            f"👥 Название: **{data['name']}**\n"
            f"👤 Контакт: **{data.get('contact_person', 'Н/Д')}**\n"
            f"📞 Телефон: **{data.get('phone', 'Н/Д')}**\n"
            f"📧 Email: **{data.get('email', 'Н/Д')}**\n"
            f"📍 Адрес: **{data.get('address', 'Н/Д')}**\n"
            f"📅 Дата: **{datetime.now().strftime('%d.%m.%Y %H:%M')}**\n\n"
            f"🆔 ID: `{customer.id}` (для использования в заказах)",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в process_address: {e}")
        await message.answer(format_error_message(e))

@router.message(CustomerAdd.name, F.text == "❌ Отмена")
@router.message(CustomerAdd.contact_person, F.text == "❌ Отмена")
@router.message(CustomerAdd.phone, F.text == "❌ Отмена")
@router.message(CustomerAdd.email, F.text == "❌ Отмена")
@router.message(CustomerAdd.address, F.text == "❌ Отмена")
async def cancel_customer(message: types.Message, state: FSMContext):
    """Отмена добавления покупателя"""
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_main_menu())

# ============================================
# СПИСОК ПОКУПАТЕЛЕЙ
# ============================================

@router.message(F.text == "📋 Список покупателей")
async def list_customers(message: types.Message):
    """Показать всех покупателей"""
    try:
        with get_db() as db:
            customers = db.query(Customer).limit(20).all()
            
            if not customers:
                await message.answer("❌ Покупатели не найдены.\n\nДобавьте первого покупателя!")
                return
            
            result = "👥 **Все покупатели** (показано 20):\n\n"
            for i, c in enumerate(customers, 1):
                result += f"{i}. **ID: `{c.id}`** | {c.name}\n"
                if c.phone:
                    result += f"   📞 {c.phone}\n"
            
            result += "\n💡 *Используйте ID при создании заказа*"
            
            await message.answer(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка в list_customers: {e}")
        await message.answer(format_error_message(e))

# ============================================
# КНОПКА НАЗАД
# ============================================

@router.message(F.text == "⬅️ Назад")
async def menu_back(message: types.Message):
    """Кнопка Назад - возврат в главное меню"""
    from handlers.start import cmd_start
    await cmd_start(message)