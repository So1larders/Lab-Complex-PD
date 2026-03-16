"""
Pydantic-схеми для валідації запитів та серіалізації відповідей.
Додано *Update-схеми для HTTP PUT (часткове оновлення).
Додано PaginatedResponse для підтримки пагінації.
"""

from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from app.models.models import RiskLevel, AssetType, TransactionType

T = TypeVar("T")


# ─── Pagination ──────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    """Обгортка для пагінованих списків."""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


# ─── Investor ────────────────────────────────────────────────────────────────

class InvestorCreate(BaseModel):
    full_name:      str       = Field(..., min_length=2, max_length=100, example="Іван Петренко")
    email:          EmailStr  = Field(..., example="ivan@example.com")
    phone:          Optional[str] = Field(None, pattern=r"^\+?\d{7,15}$", example="+380671234567")
    risk_tolerance: RiskLevel = Field(..., example=RiskLevel.MEDIUM)


class InvestorUpdate(BaseModel):
    """PUT — всі поля необов'язкові (часткове оновлення)."""
    full_name:      Optional[str]       = Field(None, min_length=2, max_length=100)
    email:          Optional[EmailStr]  = None
    phone:          Optional[str]       = Field(None, pattern=r"^\+?\d{7,15}$")
    risk_tolerance: Optional[RiskLevel] = None


class InvestorResponse(BaseModel):
    id:             int
    full_name:      str
    email:          str
    phone:          Optional[str]
    risk_tolerance: RiskLevel
    created_at:     datetime

    class Config:
        from_attributes = True


# ─── Asset ───────────────────────────────────────────────────────────────────

class AssetCreate(BaseModel):
    ticker:        str       = Field(..., min_length=1, max_length=10, example="AAPL")
    name:          str       = Field(..., min_length=2, max_length=100, example="Apple Inc.")
    asset_type:    AssetType = Field(..., example=AssetType.STOCK)
    current_price: float     = Field(..., gt=0, example=185.50)
    currency:      str       = Field("USD", min_length=3, max_length=3, example="USD")


class AssetUpdate(BaseModel):
    name:          Optional[str]       = Field(None, min_length=2, max_length=100)
    asset_type:    Optional[AssetType] = None
    current_price: Optional[float]     = Field(None, gt=0)
    currency:      Optional[str]       = Field(None, min_length=3, max_length=3)


class AssetResponse(BaseModel):
    id:            int
    ticker:        str
    name:          str
    asset_type:    AssetType
    current_price: float
    currency:      str
    updated_at:    datetime

    class Config:
        from_attributes = True


# ─── Portfolio ────────────────────────────────────────────────────────────────

class PortfolioCreate(BaseModel):
    investor_id: int            = Field(..., gt=0, example=1)
    name:        str            = Field(..., min_length=2, max_length=100, example="Агресивний портфель")
    description: Optional[str]  = Field(None, max_length=500, example="Орієнтований на зростання")


class PortfolioUpdate(BaseModel):
    name:        Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class PortfolioResponse(BaseModel):
    id:          int
    investor_id: int
    name:        str
    description: Optional[str]
    created_at:  datetime

    class Config:
        from_attributes = True


# ─── Transaction ─────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    portfolio_id:     int             = Field(..., gt=0, example=1)
    asset_id:         int             = Field(..., gt=0, example=1)
    transaction_type: TransactionType = Field(..., example=TransactionType.BUY)
    quantity:         float           = Field(..., gt=0, example=10.0)
    price_per_unit:   float           = Field(..., gt=0, example=185.50)

    @field_validator("quantity")
    @classmethod
    def quantity_precision(cls, v: float) -> float:
        if round(v, 8) != v:
            raise ValueError("Кількість може мати не більше 8 знаків після коми")
        return v


class TransactionResponse(BaseModel):
    id:               int
    portfolio_id:     int
    asset_id:         int
    transaction_type: TransactionType
    quantity:         float
    price_per_unit:   float
    total_amount:     float
    executed_at:      datetime

    class Config:
        from_attributes = True


# ─── Risk ─────────────────────────────────────────────────────────────────────

class RiskCreate(BaseModel):
    portfolio_id:         int            = Field(..., gt=0, example=1)
    volatility_score:     float          = Field(..., ge=0.0, le=1.0, example=0.65)
    diversification_score: float         = Field(..., ge=0.0, le=1.0, example=0.80)
    max_drawdown_pct:     float          = Field(..., ge=0.0, le=100.0, example=15.5)
    notes:                Optional[str]  = Field(None, max_length=500, example="Висока концентрація в IT")


class RiskUpdate(BaseModel):
    volatility_score:      Optional[float] = Field(None, ge=0.0, le=1.0)
    diversification_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_drawdown_pct:      Optional[float] = Field(None, ge=0.0, le=100.0)
    notes:                 Optional[str]   = Field(None, max_length=500)


class RiskResponse(BaseModel):
    id:                    int
    portfolio_id:          int
    risk_level:            RiskLevel
    volatility_score:      float
    diversification_score: float
    max_drawdown_pct:      float
    notes:                 Optional[str]
    assessed_at:           datetime

    class Config:
        from_attributes = True


# ─── Report ───────────────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    id:              int
    portfolio_id:    int
    total_invested:  float
    current_value:   float
    profit_loss:     float
    profit_loss_pct: float
    generated_at:    datetime

    class Config:
        from_attributes = True


# ─── Generic error ───────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    timestamp: str
    status:    int
    message:   str
    path:      str
