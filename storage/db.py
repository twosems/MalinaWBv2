"""
db.py — инициализация асинхронного движка SQLAlchemy для работы с PostgreSQL.

Принцип работы:
- Используется строка подключения (DSN) из config.py (POSTGRES_DSN), которая берётся из .env.
- Подключение осуществляется через asyncpg и create_async_engine для асинхронной работы с базой данных.
- Определён sessionmaker для создания асинхронных сессий (AsyncSessionLocal).
- Базовый класс ORM-моделей — Base (используется в models.py).

Использование:
- Импортируй engine и Base для создания таблиц и работы с сессиями в других частях проекта.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import POSTGRES_DSN  # Импорт строки подключения из config.py

# Создание асинхронного движка SQLAlchemy для PostgreSQL
engine = create_async_engine(POSTGRES_DSN, echo=False, future=True)

# Создание фабрики асинхронных сессий
AsyncSessionLocal = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Базовый класс для всех ORM моделей
Base = declarative_base()
