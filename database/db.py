import sqlite3
from datetime import datetime

DB_NAME = "warehouse.db"

def init_db():
    """Создаёт таблицы в базе данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            supplier TEXT NOT NULL,
            customer TEXT NOT NULL,
            status TEXT DEFAULT 'created',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            description TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS led_modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            step TEXT NOT NULL,
            model TEXT,
            marking TEXT,
            quantity INTEGER DEFAULT 1,
            width INTEGER,
            height INTEGER,
            location TEXT,
            photo_path TEXT,
            status TEXT DEFAULT 'in_stock',
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            contact_person TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            contact_person TEXT,
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована!")

def create_order(order_number, supplier, customer):
    """Создаёт новый заказ"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO orders (order_number, supplier, customer, status)
            VALUES (?, ?, ?, 'created')
        ''', (order_number, supplier, customer))
        conn.commit()
        order_id = cursor.lastrowid
        return order_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_order_by_number(order_number):
    """Находит заказ по номеру"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, order_number, supplier, customer, status, created_at
        FROM orders
        WHERE order_number = ?
    ''', (order_number,))
    
    order = cursor.fetchone()
    conn.close()
    return order

def get_all_orders():
    """Получает все заказы"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, order_number, supplier, customer, status, created_at
        FROM orders
        ORDER BY created_at DESC
    ''')
    
    orders = cursor.fetchall()
    conn.close()
    return orders

def update_order_status(order_id, status):
    """Обновляет статус заказа"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE orders
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, order_id))
    
    conn.commit()
    conn.close()

def add_order_photo(order_id, file_path, description=""):
    """Добавляет фотографию к заказу"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO order_photos (order_id, file_path, description)
        VALUES (?, ?, ?)
    ''', (order_id, file_path, description))
    
    conn.commit()
    photo_id = cursor.lastrowid
    conn.close()
    return photo_id

def get_order_photos(order_id):
    """Получает все фотографии заказа"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, file_path, description, uploaded_at
        FROM order_photos
        WHERE order_id = ?
    ''', (order_id,))
    
    photos = cursor.fetchall()
    conn.close()
    return photos

def get_order_with_photos(order_id):
    """Получает заказ со всеми фотографиями"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, order_number, supplier, customer, status, created_at
        FROM orders
        WHERE id = ?
    ''', (order_id,))
    
    order = cursor.fetchone()
    
    cursor.execute('''
        SELECT id, file_path, description, uploaded_at
        FROM order_photos
        WHERE order_id = ?
    ''', (order_id,))
    
    photos = cursor.fetchall()
    conn.close()
    
    return order, photos

def get_order_photo_count(order_id):
    """Получает количество фотографий заказа"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM order_photos WHERE order_id = ?
    ''', (order_id,))
    
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ========================================
#   ← ДОБАВЬ ЭТИ ФУНКЦИИ!
# ========================================

def get_all_suppliers():
    """Получает всех поставщиков"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name FROM suppliers ORDER BY name')
    suppliers = cursor.fetchall()
    conn.close()
    return suppliers

def get_all_customers():
    """Получает всех покупателей"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name FROM customers ORDER BY name')
    customers = cursor.fetchall()
    conn.close()
    return customers

def get_db_stats():
    """Получает статистику по базе данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute('SELECT COUNT(*) FROM orders')
    stats['orders'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM led_modules WHERE status = "in_stock"')
    stats['modules'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM suppliers')
    stats['suppliers'] = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM customers')
    stats['customers'] = cursor.fetchone()[0]
    
    conn.close()
    return stats
# ========================================
#   LED МОДУЛИ (LED MODULES)
# ========================================

def add_led_module(step, model, marking, quantity, location, photo_path=""):
    """Добавляет LED модуль на склад"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO led_modules (step, model, marking, quantity, location, photo_path, status)
        VALUES (?, ?, ?, ?, ?, ?, 'in_stock')
    ''', (step, model, marking, quantity, location, photo_path))
    
    conn.commit()
    module_id = cursor.lastrowid
    conn.close()
    return module_id

def get_all_modules():
    """Получает все модули"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, step, model, marking, quantity, location, status, received_at
        FROM led_modules
        ORDER BY received_at DESC
    ''')
    
    modules = cursor.fetchall()
    conn.close()
    return modules

def get_modules_by_step(step):
    """Находит модули по шагу (P3, P4 и т.д.)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, step, model, marking, quantity, location, status
        FROM led_modules
        WHERE step = ?
        ORDER BY received_at DESC
    ''', (step,))
    
    modules = cursor.fetchall()
    conn.close()
    return modules

def get_modules_by_marking(search_text):
    """Поиск модулей по маркировке"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, step, model, marking, quantity, location, status
        FROM led_modules
        WHERE marking LIKE ? OR model LIKE ?
        ORDER BY received_at DESC
    ''', (f'%{search_text}%', f'%{search_text}%'))
    
    modules = cursor.fetchall()
    conn.close()
    return modules

def get_module_by_id(module_id):
    """Получает модуль по ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, step, model, marking, quantity, location, photo_path, status, received_at
        FROM led_modules
        WHERE id = ?
    ''', (module_id,))
    
    module = cursor.fetchone()
    conn.close()
    return module

def update_module_quantity(module_id, quantity):
    """Обновляет количество модулей"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE led_modules
        SET quantity = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (quantity, module_id))
    
    conn.commit()
    conn.close()

def get_stock_summary():
    """Получает сводку по остаткам (по шагам)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT step, SUM(quantity) as total_qty, COUNT(*) as total_modules
        FROM led_modules
        WHERE status = 'in_stock'
        GROUP BY step
        ORDER BY step
    ''')
    
    summary = cursor.fetchall()
    conn.close()
    return summaryS