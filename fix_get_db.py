#!/usr/bin/env python3
"""
Скрипт для автоматического исправления next(get_db()) -> with get_db()
во всех файлах обработчиков
"""

import re
import os

def fix_file(filepath):
    """Исправляет файл, заменяя next(get_db()) на with get_db()"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Шаблон для поиска: db = next(get_db()) ... finally: db.close()
    # Сначала заменим простые случаи
    
    # Паттерн 1:простой случай с try/finally
    pattern1 = r'(\s+)db = next\(get_db\(\)\)\n(\s+)try:'
    replacement1 = r'\1try:\n\1with get_db() as db:'
    content = re.sub(pattern1, replacement1, content)
    
    # Паттерн 2: пустые строки после finally db.close()
    pattern2 = r'(\s+)finally:\n(\s+)db\.close\(\)'
    replacement2 = ''  # Удалим, так как finally будет управляться with
    # На самом деле это сложнее, нужно быть осторожнее
    
    # Простой подход: замени все next(get_db()) и попытайся выделить блоки
    # на самом деле это слишком сложно. Давайте сделаем вручную несколько важных мест
    
    if "with get_db()" not in content and "next(get_db())" in content:
        print(f"⚠️ ВНИМАНИЕ: {filepath} содержит next(get_db()) и требует ручного исправления")
        # Выведем количество предложений
        count = content.count("next(get_db())")
        print(f"   Найдено {count} использований next(get_db())")
    
    # Простая замена - оставим try внутри блока with
    # ЭТО ЯВЛЯЕТСЯ ВРЕМЕННЫМ РЕШЕНИЕМ
    # Лучше будет вручную обновить основные методы
    
    return content == original

files_to_fix = [
    'handlers/orders.py',
    'handlers/customers.py',
    'handlers/warehouse.py',
]

if __name__ == '__main__':
    print("🔧 Проверяю файлы на предмет next(get_db())...\n")
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            print(f"📎 {filepath}")
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            count = content.count("next(get_db())")
            print(f"   ✓ Осталось исправить: {count} использований\n")
        else:
            print(f"   ✗ Файл не найден\n")
    
    print("ℹ️  Рекомендуется вручную обновить оставшиеся места")
    print("   либо запустить автоматическое исправление с большей осторожностью.")
