"""
Router: Investors — повний CRUD + пагінація + фільтрація.
GET    /api/v1/investors/          — список (пагінація, фільтр за risk_tolerance)
GET    /api/v1/investors/{id}      — деталі
POST   /api/v1/investors/          — створення
PUT    /api/v1/investors/{id}      — оновлення
DELETE /api/v1/investors/{id}      — видалення
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    InvestorCreate, InvestorUpdate, InvestorResponse, PaginatedResponse
)
from app.services import investor_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[InvestorResponse], status_code=200,
            summary="Список інвесторів із пагінацією та фільтрацією")
def list_investors(
    page:           int           = Query(1,  ge=1,  description="Номер сторінки"),
    size:           int           = Query(10, ge=1, le=100, description="Розмір сторінки"),
    sort_by:        str           = Query("id", description="Поле сортування"),
    sort_order:     str           = Query("asc", pattern="^(asc|desc)$"),
    risk_tolerance: Optional[str] = Query(None, description="Фільтр: low | medium | high"),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    items, total = investor_service.get_all(
        db, skip=skip, limit=size,
        sort_by=sort_by, sort_order=sort_order,
        risk_tolerance=risk_tolerance,
    )
    return {
        "items": items, "total": total,
        "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.get("/{investor_id}", response_model=InvestorResponse, status_code=200,
            summary="Отримати інвестора за ID")
def get_investor(investor_id: int, db: Session = Depends(get_db)):
    return investor_service.get_by_id(db, investor_id)


@router.post("/", response_model=InvestorResponse, status_code=201,
             summary="Створити нового інвестора")
def create_investor(data: InvestorCreate, db: Session = Depends(get_db)):
    return investor_service.create(db, data)


@router.put("/{investor_id}", response_model=InvestorResponse, status_code=200,
            summary="Оновити інвестора (PUT)")
def update_investor(investor_id: int, data: InvestorUpdate, db: Session = Depends(get_db)):
    return investor_service.update(db, investor_id, data)


@router.delete("/{investor_id}", status_code=204,
               summary="Видалити інвестора (і всі його портфелі)")
def delete_investor(investor_id: int, db: Session = Depends(get_db)):
    investor_service.delete(db, investor_id)
