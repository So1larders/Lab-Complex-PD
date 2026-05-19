"""
Router: Risks — Analytics Service (аналіз ризику).
GET    /api/v1/risks/       — список (пагінація, фільтри)
GET    /api/v1/risks/{id}   — деталі
POST   /api/v1/risks/       — нова оцінка ризику
PUT    /api/v1/risks/{id}   — оновлення параметрів ризику
DELETE /api/v1/risks/{id}   — видалення оцінки
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from portfolio_service.database import get_db
from portfolio_service.schemas.schemas import (
    RiskCreate, RiskUpdate, RiskResponse, PaginatedResponse
)
from portfolio_service.services import risk_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[RiskResponse], status_code=200,
            summary="Список оцінок ризику із пагінацією та фільтрацією")
def list_risks(
    page:         int           = Query(1,  ge=1),
    size:         int           = Query(10, ge=1, le=100),
    sort_by:      str           = Query("id"),
    sort_order:   str           = Query("asc", pattern="^(asc|desc)$"),
    portfolio_id: Optional[int] = Query(None, description="Фільтр за портфелем"),
    risk_level:   Optional[str] = Query(None, description="Фільтр: low | medium | high"),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    items, total = risk_service.get_all(
        db, skip=skip, limit=size,
        sort_by=sort_by, sort_order=sort_order,
        portfolio_id=portfolio_id,
        risk_level=risk_level,
    )
    return {
        "items": items, "total": total,
        "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.get("/{risk_id}", response_model=RiskResponse, status_code=200,
            summary="Отримати оцінку ризику за ID")
def get_risk(risk_id: int, db: Session = Depends(get_db)):
    return risk_service.get_by_id(db, risk_id)


@router.post("/", response_model=RiskResponse, status_code=201,
             summary="Додати оцінку ризику для портфеля")
def create_risk(data: RiskCreate, db: Session = Depends(get_db)):
    return risk_service.create(db, data)


@router.put("/{risk_id}", response_model=RiskResponse, status_code=200,
            summary="Оновити параметри ризику (risk_level перераховується автоматично)")
def update_risk(risk_id: int, data: RiskUpdate, db: Session = Depends(get_db)):
    return risk_service.update(db, risk_id, data)


@router.delete("/{risk_id}", status_code=204,
               summary="Видалити оцінку ризику")
def delete_risk(risk_id: int, db: Session = Depends(get_db)):
    risk_service.delete(db, risk_id)
