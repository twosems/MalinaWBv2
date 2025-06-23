"""
models.py — SQLAlchemy ORM-модели для хранения данных пользователей в базе PostgreSQL.

UserAccess — основная модель, расширенная для хранения seller_name и trade_mark.
"""

from sqlalchemy import Column, BigInteger, DateTime, Boolean, String
from .db import Base

class UserAccess(Base):
    __tablename__ = "user_access"
    user_id = Column(BigInteger, primary_key=True, index=True)  # Telegram user_id
    paid_until = Column(DateTime, nullable=True)
    trial_until = Column(DateTime, nullable=True)
    trial_activated = Column(Boolean, default=False)
    api_key = Column(String, nullable=True)
    seller_name = Column(String, nullable=True)   # Наименование организации (из seller-info)
    trade_mark = Column(String, nullable=True)    # Бренд (из seller-info)
