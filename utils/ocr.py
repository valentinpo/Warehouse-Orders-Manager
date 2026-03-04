import pytesseract
from PIL import Image
import cv2
import numpy as np
import os

# Путь к Tesseract (для Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path):
    """
    Извлекает текст из изображения с помощью OCR
    """
    try:
        # Проверяем, существует ли файл
        if not os.path.exists(image_path):
            return None
        
        # Открываем изображение
        img = cv2.imread(image_path)
        
        # Конвертируем в оттенки серого
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Применяем бинаризацию для улучшения качества
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Сохраняем временный файл для обработки
        temp_path = image_path.replace('.jpg', '_processed.png')
        cv2.imwrite(temp_path, thresh)
        
        # Распознаем текст
        text = pytesseract.image_to_string(temp_path, lang='eng+rus', config='--psm 6')
        
        # Удаляем временный файл
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Очищаем текст
        text = text.strip()
        text = ' '.join(text.split())  # Удаляем лишние пробелы
        
        return text if text else None
        
    except Exception as e:
        print(f"❌ OCR ошибка: {e}")
        return None

def detect_step_from_text(text):
    """
    Пытается определить шаг модуля (P3, P4 и т.д.) из текста
    """
    if not text:
        return None
    
    text = text.upper()
    
    # Шаблоны для поиска шага
    steps = ['P2', 'P2.5', 'P3', 'P4', 'P5', 'P6', 'P8', 'P10']
    
    for step in steps:
        if step in text:
            return step
    
    return None

def detect_serial_number(text):
    """
    Пытается найти серийный номер в тексте
    """
    if not text:
        return None
    
    # Ищем паттерны типа SN-XXXX, S/N: XXXX, Serial: XXXX
    import re
    
    patterns = [
        r'SN[-:\s]?([A-Z0-9-]+)',
        r'S/N[-:\s]?([A-Z0-9-]+)',
        r'SERIAL[-:\s]?([A-Z0-9-]+)',
        r'([A-Z]{2,4}-\d{4,})',
        r'(\d{8,})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1) if len(match.groups()) > 0 else match.group(0)
    
    return None