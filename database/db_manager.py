from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from database.models import Base
from config import DB_FILE

# Создаём движок
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)
SessionLocal = sessionmaker(bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Контекстный менеджер для безопасной работы с сессией SQLAlchemy.
    Гарантирует закрытие сессии даже при ошибках.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Инициализация базы данных: создание таблиц.
    Вызывается при старте бота.
    """
    Base.metadata.create_all(bind=engine)\n