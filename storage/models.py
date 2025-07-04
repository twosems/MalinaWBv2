"""
models.py — SQLAlchemy ORM-модели для хранения данных пользователей и складов в базе PostgreSQL.

UserAccess — основная модель, расширенная для хранения seller_name и trade_mark.
Warehouse — модель для кэширования складов Wildberries.
WarehouseCacheInfo — модель для хранения информации о последнем обновлении кеша складов.
"""

from sqlalchemy import Column, BigInteger, DateTime, Boolean, String, Integer, func
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
    is_archived = Column(Boolean, default=False, nullable=False)
    balance = Column(Integer, default=0)            # Для хранения суммы в рублях
    last_billing = Column(DateTime, nullable=True)  # Для отслеживания даты последнего списания
    created_at = Column(DateTime, default=func.now())

class Warehouse(Base):
    __tablename__ = "warehouses"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String, nullable=True)
    workTime = Column("worktime", String, nullable=True)
    acceptsQR = Column("acceptsqr", Boolean, nullable=True)
    isActive = Column("isactive", Boolean, nullable=True)
    updated_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Warehouse(id={self.id}, name={self.name})>"

class WarehouseCacheInfo(Base):
    __tablename__ = "warehouse_cache_info"

    id = Column(Integer, primary_key=True)
    updated_at = Column(DateTime, default=func.now(), nullable=False)
    updated_by = Column(BigInteger, nullable=True)  # user_id, который обновил кэш
