# ============================================
# БИЗНЕС-ЛОГИКА И ВАЛИДАЦИЯ
# ============================================

import re
from constants import VALIDATION, ERROR_MESSAGES
from database.db_manager import get_db
from database.models import Order, Supplier, Customer
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Исключение для ошибок валидации"""
    pass


class OrderService:
    """Сервис для работы с заказами"""
    
    @staticmethod
    def validate_order_number(order_number: str) -> bool:
        """Проверить формат номера заказа"""
        if not order_number or not isinstance(order_number, str):
            raise ValidationError("Номер заказа должен быть строкой")
        
        order_number = order_number.strip()
        
        min_len = VALIDATION["order_number_min_length"]
        max_len = VALIDATION["order_number_max_length"]
        
        if len(order_number) < min_len or len(order_number) > max_len:
            raise ValidationError(
                f"Номер заказа должен быть от {min_len} до {max_len} символов"
            )
        
        return True
    
    @staticmethod
    def check_order_number_exists(order_number: str) -> bool:
        """Проверить, существует ли заказ с таким номером"""
        try:
            with get_db() as db:
                existing = db.query(Order).filter(
                    Order.order_number == order_number.strip()
                ).first()
                return existing is not None
        except Exception as e:
            logger.error(f"Ошибка при проверке номера заказа: {e}")
            raise
    
    @staticmethod
    def validate_quantity(qty: str) -> int:
        """Валидация и преобразование количества"""
        try:
            qty_int = int(qty)
            min_qty = VALIDATION["quantity_min"]
            max_qty = VALIDATION["quantity_max"]
            
            if qty_int < min_qty or qty_int > max_qty:
                raise ValidationError(
                    f"Количество должно быть от {min_qty} до {max_qty}"
                )
            return qty_int
        except ValueError:
            raise ValidationError("Количество должно быть числом")
    
    @staticmethod
    def validate_dimensions(width: str, height: str) -> tuple:
        """Валидация размеров"""
        try:
            w = float(width)
            h = float(height)
            
            min_dim = VALIDATION["width_min"]
            max_dim = VALIDATION["width_max"]
            
            if w < min_dim or w > max_dim or h < min_dim or h > max_dim:
                raise ValidationError(
                    f"Размеры должны быть от {min_dim} до {max_dim}"
                )
            return (w, h)
        except ValueError:
            raise ValidationError("Размеры должны быть числами")


class SupplierService:
    """Сервис для работы с поставщиками"""
    
    @staticmethod
    def validate_supplier_name(name: str) -> bool:
        """Проверить имя поставщика"""
        if not name or not isinstance(name, str):
            raise ValidationError("Имя поставщика должно быть строкой")
        
        name = name.strip()
        min_len = VALIDATION["supplier_name_min_length"]
        max_len = VALIDATION["supplier_name_max_length"]
        
        if len(name) < min_len or len(name) > max_len:
            raise ValidationError(
                f"Имя поставщика должно быть от {min_len} до {max_len} символов"
            )
        return True
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Валидация номера телефона"""
        if not phone:
            return True  # Опциональное поле
        
        phone = re.sub(r'\D', '', phone)
        
        min_len = VALIDATION["phone_min_length"]
        max_len = VALIDATION["phone_max_length"]
        
        if len(phone) < min_len or len(phone) > max_len:
            raise ValidationError(
                f"Номер телефона должен быть от {min_len} до {max_len} символов"
            )
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Валидация email"""
        if not email:
            return True  # Опциональное поле
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            raise ValidationError("Некорректный email")
        
        if len(email) > VALIDATION["email_max_length"]:
            raise ValidationError(
                f"Email не должен превышать {VALIDATION['email_max_length']} символов"
            )
        return True


class CustomerService:
    """Сервис для работы с покупателями"""
    
    # Использует те же методы валидации, что и SupplierService
    validate_name = SupplierService.validate_supplier_name
    validate_phone = SupplierService.validate_phone
    validate_email = SupplierService.validate_email


def format_error_message(error: Exception) -> str:
    """Преобразовать исключение в сообщение об ошибке для пользователя"""
    if isinstance(error, ValidationError):
        return f"❌ {str(error)}"
    else:
        logger.error(f"Неожиданная ошибка: {error}")
        return ERROR_MESSAGES.get("unknown_error", "❌ Неизвестная ошибка")
