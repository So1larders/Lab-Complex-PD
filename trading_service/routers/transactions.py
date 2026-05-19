"""
Router: Transactions — Transaction Service мікросервіс.
GET    /api/v1/transactions/       — список (пагінація, фільтри)
GET    /api/v1/transactions/{id}   — деталі
POST   /api/v1/transactions/       — купівля або продаж активу
DELETE /api/v1/transactions/{id}   — скасування операції

Примітка: транзакції не редагуються (PUT відсутній) — фінансова операція
є незмінним записом (immutable audit log).
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from trading_service.database import get_db
from trading_service.schemas.schemas import (
    TransactionCreate, TransactionResponse, PaginatedResponse
)
from trading_service.services import transaction_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[TransactionResponse], status_code=200,
            summary="Список операцій із пагінацією та фільтрацією")
def list_transactions(
    page:             int           = Query(1,  ge=1),
    size:             int           = Query(10, ge=1, le=100),
    sort_by:          str           = Query("executed_at"),
    sort_order:       str           = Query("desc", pattern="^(asc|desc)$"),
    portfolio_id:     Optional[int] = Query(None, description="Фільтр за портфелем"),
    asset_id:         Optional[int] = Query(None, description="Фільтр за активом"),
    transaction_type: Optional[str] = Query(None, description="Фільтр: buy | sell"),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    items, total = transaction_service.get_all(
        db, skip=skip, limit=size,
        sort_by=sort_by, sort_order=sort_order,
        portfolio_id=portfolio_id,
        asset_id=asset_id,
        transaction_type=transaction_type,
    )
    return {
        "items": items, "total": total,
        "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.get("/{tx_id}", response_model=TransactionResponse, status_code=200,
            summary="Отримати операцію за ID")
def get_transaction(tx_id: int, db: Session = Depends(get_db)):
    return transaction_service.get_by_id(db, tx_id)


@router.post("/", response_model=TransactionResponse, status_code=201,
             summary="Виконати купівлю або продаж активу")
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    return transaction_service.create(db, data)


@router.delete("/{tx_id}", status_code=204,
               summary="Скасувати / видалити операцію")
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    transaction_service.delete(db, tx_id)
