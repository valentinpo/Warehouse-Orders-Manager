from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from database.db import add_led_module, get_stock_summary
from keyboards import get_main_menu, get_modules_menu
from utils.ocr import extract_text_from_image, detect_step_from_text, detect_serial_number
import os
from datetime import datetime

router = Router()

class ModuleForm(StatesGroup):
    waiting_for_photo = State()
    waiting_for_step = State()
    waiting_for_model = State()
    waiting_for_marking = State()
    waiting_for_quantity = State()
    waiting_for_location = State()

@router.callback_query(F.data == "module_add")
async def module_add_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "➕ **Добавление LED модуля**\n\n"
        "📸 **Шаг 1/6:** Отправьте **фотографию модуля**\n\n"
        "🤖 Бот попытается **автоматически распознать** маркировку\n\n"
        "❌ **Отмена** — для отмены",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(ModuleForm.waiting_for_photo)
    await callback.answer()

@router.message(ModuleForm.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    # Получаем фото
    photo = message.photo[-1]
    
    # Создаем папку для фото
    photo_folder = "photos/modules"
    os.makedirs(photo_folder, exist_ok=True)
    
    # Скачиваем фото
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"{photo_folder}/module_{timestamp}.jpg"
    
    await message.answer("🤖 **Обрабатываю фото...**\n\nПодождите несколько секунд...")
    
    try:
        # Скачиваем файл
        file = await bot.get_file(photo.file_id)
        await bot.download_file(file.file_path, file_path)
        
        # Запускаем OCR
        ocr_text = extract_text_from_image(file_path)
        
        # Пытаемся определить шаг и маркировку
        detected_step = detect_step_from_text(ocr_text) if ocr_text else None
        detected_marking = detect_serial_number(ocr_text) if ocr_text else None
        
        # Сохраняем данные в состояние
        await state.update_data(photo_path=file_path, ocr_text=ocr_text)
        
        # Формируем ответ
        if ocr_text:
            response = "✅ **Фото получено!**\n\n"
            response += "🤖 **OCR распознал:**\n"
            response += f"```\n{ocr_text[:200]}\n```"  # Показываем первые 200 символов
            
            if detected_step:
                response += f"\n\n📏 **Предлагаемый шаг:** `{detected_step}`"
            if detected_marking:
                response += f"\n🔖 **Предлагаемая маркировка:** `{detected_marking}`"
            
            response += "\n\n📏 **Шаг 2/6:** Подтвердите или введите шаг модуля:"
        else:
            response = "⚠️ **Не удалось распознать текст**\n\n"
            response += "📏 **Шаг 2/6:** Введите шаг модуля вручную:"
        
        # Кнопки с шагами
        steps = ["P2", "P2.5", "P3", "P4", "P5", "P6", "P8", "P10"]
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=steps[i]), KeyboardButton(text=steps[i+1])] for i in range(0, len(steps), 2)] + [[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
        
        await message.answer(response, reply_markup=keyboard)
        await state.set_state(ModuleForm.waiting_for_step)
        
    except Exception as e:
        await message.answer(f"❌ **Ошибка обработки фото:** {e}\n\nВведите шаг вручную:")
        await state.set_state(ModuleForm.waiting_for_step)

@router.message(ModuleForm.waiting_for_photo, F.document)
async def process_document(message: types.Message, state: FSMContext):
    doc = message.document
    
    if not doc.mime_type.startswith('image/'):
        await message.answer("❌ **Это не изображение!**\n\nОтправьте фото (JPG, PNG).")
        return
    
    # Обрабатываем как фото
    await process_photo(message, state)

@router.message(ModuleForm.waiting_for_step)
async def process_step(message: types.Message, state: FSMContext):
    step = message.text.strip().upper()
    
    if step == "❌ ОТМЕНА":
        await state.clear()
        await message.answer("❌ **Отменено**", reply_markup=get_main_menu())
        return
    
    await state.update_data(step=step)
    await message.answer("📝 **Шаг 3/6:** Введите модель (или **Пропустить**):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ModuleForm.waiting_for_model)

@router.message(ModuleForm.waiting_for_model)
async def process_model(message: types.Message, state: FSMContext):
    model = message.text.strip() or "Не указана"
    await state.update_data(model=model)
    await message.answer("📝 **Шаг 4/6:** Введите маркировку (или **Пропустить**):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ModuleForm.waiting_for_marking)

@router.message(ModuleForm.waiting_for_marking)
async def process_marking(message: types.Message, state: FSMContext):
    marking = message.text.strip() or "Не указана"
    await state.update_data(marking=marking)
    await message.answer("📦 **Шаг 5/6:** Введите количество:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ModuleForm.waiting_for_quantity)

@router.message(ModuleForm.waiting_for_quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text.strip())
        if quantity <= 0:
            raise ValueError
        await state.update_data(quantity=quantity)
        await message.answer("📍 **Шаг 6/6:** Введите местоположение:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(ModuleForm.waiting_for_location)
    except:
        await message.answer("❌ Введите число больше 0!")

@router.message(ModuleForm.waiting_for_location)
async def process_location(message: types.Message, state: FSMContext):
    location = message.text.strip() or "Не указано"
    data = await state.get_data()
    
    module_id = add_led_module(
        step=data.get('step'),
        model=data.get('model'),
        marking=data.get('marking'),
        quantity=data.get('quantity'),
        location=location,
        photo_path=data.get('photo_path', '')
    )
    
    if module_id:
        ocr_info = ""
        if data.get('ocr_text'):
            ocr_info = f"\n🤖 **OCR текст:** `{data.get('ocr_text')[:50]}...`"
        
        await message.answer(
            f"🎉 **Модуль добавлен!**\n\n"
            f"📏 Шаг: `{data.get('step')}`\n"
            f"📝 Модель: `{data.get('model')}`\n"
            f"🔖 Маркировка: `{data.get('marking')}`\n"
            f"📦 Количество: `{data.get('quantity')} шт.`\n"
            f"📍 Место: `{location}`"
            f"{ocr_info}",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer("❌ **Ошибка!**", reply_markup=get_main_menu())
    
    await state.clear()

@router.callback_query(F.data == "module_stock")
async def module_stock(callback: types.CallbackQuery):
    summary = get_stock_summary()
    if summary:
        text = "📦 **Остатки:**\n\n"
        for step, qty, _ in summary:
            text += f"📏 **{step}:** `{qty} шт.`\n"
        await callback.message.answer(text, reply_markup=get_modules_menu())
    else:
        await callback.message.answer("📦 Модулей нет", reply_markup=get_modules_menu())
    await callback.answer()

@router.callback_query(F.data == "module_search")
async def module_search(callback: types.CallbackQuery):
    await callback.message.answer("🔍 Поиск в разработке...", reply_markup=get_modules_menu())
    await callback.answer()

@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cancel_module(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено", reply_markup=get_main_menu())