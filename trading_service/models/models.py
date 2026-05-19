"""
ORM-сутності (Entity-класи) — аналог @Entity у Spring JPA.
Кожен клас відповідає таблиці в БД.

Зв'язки:
  Investor  1──* Portfolio  1──* Transaction
  Portfolio 1──* Risk
  Portfolio 1──* Report
  Asset     1──* Transaction
"""

from __future__ import annotations
from enum import Enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from trading_service.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────────

class AssetType(str, Enum):
    STOCK     = "stock"
    BOND      = "bond"
    CRYPTO    = "cryptocurrency"
    ETF       = "etf"
    COMMODITY = "commodity"


class TransactionType(str, Enum):
    BUY  = "buy"
    SELL = "sell"



# ─── Asset ───────────────────────────────────────────────────────────────────

class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str]       = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str]         = mapped_column(String(100), nullable=False)
    asset_type: Mapped[str]   = mapped_column(SAEnum(AssetType), nullable=False)
    current_price: Mapped[float]  = mapped_column(Float, nullable=False)
    currency: Mapped[str]     = mapped_column(String(3), default="USD", nullable=False)
    updated_at: Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="asset"
    )


# ─── Transaction ─────────────────────────────────────────────────────────────

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    asset_id: Mapped[int]     = mapped_column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(SAEnum(TransactionType), nullable=False)
    quantity: Mapped[float]       = mapped_column(Float, nullable=False)
    price_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[float]   = mapped_column(Float, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    asset: Mapped["Asset"]         = relationship("Asset", back_populates="transactions")
