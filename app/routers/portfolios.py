"""
Router: Portfolios — Portfolio Service мікросервіс.
GET    /api/v1/portfolios/       — список (пагінація, фільтр за investor_id)
GET    /api/v1/portfolios/{id}   — деталі
POST   /api/v1/portfolios/       — створення
PUT    /api/v1/portfolios/{id}   — оновлення назви/опису
DELETE /api/v1/portfolios/{id}   — видалення (каскадно)
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse, PaginatedResponse
)
from app.services import portfolio_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[PortfolioResponse], status_code=200,
            summary="Список портфелів із пагінацією та фільтрацією за інвестором")
def list_portfolios(
    page:        int           = Query(1,  ge=1),
    size:        int           = Query(10, ge=1, le=100),
    sort_by:     str           = Query("id"),
    sort_order:  str           = Query("asc", pattern="^(asc|desc)$"),
    investor_id: Optional[int] = Query(None, description="Фільтр за ID інвестора"),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    items, total = portfolio_service.get_all(
        db, skip=skip, limit=size,
        sort_by=sort_by, sort_order=sort_order,
        investor_id=investor_id,
    )
    return {
        "items": items, "total": total,
        "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.get("/{portfolio_id}", response_model=PortfolioResponse, status_code=200,
            summary="Отримати портфель за ID")
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    return portfolio_service.get_by_id(db, portfolio_id)


@router.post("/", response_model=PortfolioResponse, status_code=201,
             summary="Створити новий портфель")
def create_portfolio(data: PortfolioCreate, db: Session = Depends(get_db)):
    return portfolio_service.create(db, data)


@router.put("/{portfolio_id}", response_model=PortfolioResponse, status_code=200,
            summary="Оновити портфель (PUT)")
def update_portfolio(portfolio_id: int, data: PortfolioUpdate, db: Session = Depends(get_db)):
    return portfolio_service.update(db, portfolio_id, data)


@router.delete("/{portfolio_id}", status_code=204,
               summary="Видалити портфель (каскадно: транзакції, ризики, звіти)")
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio_service.delete(db, portfolio_id)
