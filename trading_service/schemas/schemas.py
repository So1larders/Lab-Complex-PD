"""
Pydantic-схеми для валідації запитів та серіалізації відповідей.
Додано *Update-схеми для HTTP PUT (часткове оновлення).
Додано PaginatedResponse для підтримки пагінації.
"""

from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from trading_service.models.models import AssetType, TransactionType

T = TypeVar("T")


# ─── Pagination ──────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    """Обгортка для пагінованих списків."""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int



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



# ─── Generic error ───────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    timestamp: str
    status:    int
    message:   str
    path:      str
