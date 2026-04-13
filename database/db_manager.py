from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from config import DB_FILE
from database.models import Base, User, UserRole
import logging

logger = logging.getLogger(__name__)

# Создаем движок БД (SQLite для разработки)
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)

# Создаем сессия
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Инициализация БД - создание всех таблиц"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise

@contextmanager
def get_db():
    """Контекстный менеджер для безопасной работы с сессией БД"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_db_session():
    """Генератор сессии БД для использования в зависимостях"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функции для работы с пользователями
def get_or_create_user(telegram_id: int, username: str = None):
    """Получить или создать пользователя (синхронная функция)"""
    try:
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    role=UserRole.VIEWER
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"👤 Новый пользователь: {username} (ID: {telegram_id})")
            return user
    except Exception as e:
        logger.error(f"Ошибка при создании/получении пользователя: {e}")
        raise