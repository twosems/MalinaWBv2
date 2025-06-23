"""
models.py — SQLAlchemy ORM-модели для хранения данных пользователей в базе PostgreSQL.

В этом файле описана основная модель:
- UserAccess — хранит информацию о доступе пользователя, пробном периоде и API-ключе Wildberries.

Поля:
    - user_id: ID пользователя Telegram (PRIMARY KEY, BigInteger)
    - paid_until: до какого времени оплачен доступ (DateTime, nullable)
    - trial_until: до какого времени активен пробный период (DateTime, nullable)
    - trial_activated: был ли активирован пробный доступ (Boolean, default=False)
    - api_key: строка с API-ключом Wildberries (String, nullable)
"""

from sqlalchemy import Column, BigInteger, DateTime, Boolean, String
from .db import Base

class UserAccess(Base):
    __tablename__ = "user_access"
    user_id = Column(BigInteger, primary_key=True, index=True)  # <-- BigInteger для user_id Telegram
    paid_until = Column(DateTime, nullable=True)
    trial_until = Column(DateTime, nullable=True)
    trial_activated = Column(Boolean, default=False)
    api_key = Column(String, nullable=True)
