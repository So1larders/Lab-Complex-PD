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
from portfolio_service.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"





# ─── Investor ────────────────────────────────────────────────────────────────

class Investor(Base):
    __tablename__ = "investors"

    id: Mapped[int]              = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str]       = mapped_column(String(100), nullable=False)
    email: Mapped[str]           = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    risk_tolerance: Mapped[str]  = mapped_column(SAEnum(RiskLevel), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    portfolios: Mapped[List["Portfolio"]] = relationship(
        "Portfolio", back_populates="investor", cascade="all, delete-orphan"
    )



# ─── Portfolio ────────────────────────────────────────────────────────────────

class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    investor_id: Mapped[int]  = mapped_column(Integer, ForeignKey("investors.id"), nullable=False, index=True)
    name: Mapped[str]         = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]       = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    investor: Mapped["Investor"]          = relationship("Investor", back_populates="portfolios")
    risks: Mapped[List["Risk"]]     = relationship(
        "Risk", back_populates="portfolio", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report", back_populates="portfolio", cascade="all, delete-orphan"
    )



# ─── Risk ─────────────────────────────────────────────────────────────────────

class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    risk_level: Mapped[str]   = mapped_column(SAEnum(RiskLevel), nullable=False)
    volatility_score: Mapped[float]      = mapped_column(Float, nullable=False)
    diversification_score: Mapped[float] = mapped_column(Float, nullable=False)
    max_drawdown_pct: Mapped[float]      = mapped_column(Float, nullable=False)
    notes: Mapped[Optional[str]]         = mapped_column(Text, nullable=True)
    assessed_at: Mapped[datetime]        = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="risks")


# ─── Report ───────────────────────────────────────────────────────────────────

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    total_invested: Mapped[float]  = mapped_column(Float, nullable=False)
    current_value: Mapped[float]   = mapped_column(Float, nullable=False)
    profit_loss: Mapped[float]     = mapped_column(Float, nullable=False)
    profit_loss_pct: Mapped[float] = mapped_column(Float, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="reports")
