from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

# ============================================
# ENUMS
# ============================================

class OrderStatus(enum.Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ModuleStatus(enum.Enum):
    IN_STOCK = "in_stock"
    RESERVED = "reserved"
    SOLD = "sold"
    DEFECTIVE = "defective"

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    WAREHOUSE = "warehouse"
    VIEWER = "viewer"

# ============================================
# МОДЕЛИ
# ============================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="user")

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="supplier")

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="customer")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.CREATED)
    ship_date = Column(DateTime)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="orders")
    supplier = relationship("Supplier", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    photos = relationship("OrderPhoto", back_populates="order")

class OrderPhoto(Base):
    __tablename__ = "order_photos"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    file_path = Column(String, nullable=False)
    description = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="photos")

class LEDModule(Base):
    __tablename__ = "led_modules"
    
    id = Column(Integer, primary_key=True)
    step = Column(String, nullable=False)
    model = Column(String)
    marking_ocr = Column(Text)
    quantity = Column(Integer, default=0)
    width = Column(Float)
    height = Column(Float)
    location = Column(String)
    photo_path = Column(String)
    status = Column(SQLEnum(ModuleStatus), default=ModuleStatus.IN_STOCK)
    received_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class WarehouseCell(Base):
    __tablename__ = "warehouse_cells"
    
    id = Column(Integer, primary_key=True)
    shelf = Column(String)
    row = Column(String)
    cell = Column(String)
    description = Column(String)