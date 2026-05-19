"""
Router: Assets — Asset Service мікросервіс.
GET    /api/v1/assets/       — список (пагінація, фільтр за типом та валютою)
GET    /api/v1/assets/{id}   — деталі
POST   /api/v1/assets/       — створення
PUT    /api/v1/assets/{id}   — оновлення ціни / назви
DELETE /api/v1/assets/{id}   — видалення
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from trading_service.database import get_db
from trading_service.schemas.schemas import (
    AssetCreate, AssetUpdate, AssetResponse, PaginatedResponse
)
from trading_service.services import asset_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[AssetResponse], status_code=200,
            summary="Список активів із пагінацією та фільтрацією")
def list_assets(
    page:       int           = Query(1,  ge=1),
    size:       int           = Query(10, ge=1, le=100),
    sort_by:    str           = Query("id"),
    sort_order: str           = Query("asc", pattern="^(asc|desc)$"),
    asset_type: Optional[str] = Query(None, description="Фільтр: stock | bond | cryptocurrency | etf | commodity"),
    currency:   Optional[str] = Query(None, description="Фільтр за валютою, напр. USD"),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    items, total = asset_service.get_all(
        db, skip=skip, limit=size,
        sort_by=sort_by, sort_order=sort_order,
        asset_type=asset_type, currency=currency,
    )
    return {
        "items": items, "total": total,
        "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.get("/{asset_id}", response_model=AssetResponse, status_code=200,
            summary="Отримати актив за ID")
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    return asset_service.get_by_id(db, asset_id)


@router.post("/", response_model=AssetResponse, status_code=201,
             summary="Додати новий актив")
def create_asset(data: AssetCreate, db: Session = Depends(get_db)):
    return asset_service.create(db, data)


@router.put("/{asset_id}", response_model=AssetResponse, status_code=200,
            summary="Оновити актив — наприклад, поточну ціну (PUT)")
def update_asset(asset_id: int, data: AssetUpdate, db: Session = Depends(get_db)):
    return asset_service.update(db, asset_id, data)


@router.delete("/{asset_id}", status_code=204,
               summary="Видалити актив")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset_service.delete(db, asset_id)
