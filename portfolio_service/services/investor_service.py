"""
InvestorService — бізнес-логіка для сутності Інвестор.
Аналог @Service у Spring.  Всі операції виконуються в рамках
переданої сесії БД (транзакційність забезпечується SQLAlchemy).
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from portfolio_service.models.models import Investor
from portfolio_service.schemas.schemas import InvestorCreate, InvestorUpdate
from portfolio_service.exceptions.handlers import NotFoundError, ConflictError


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "id",
    sort_order: str = "asc",
    risk_tolerance: Optional[str] = None,
) -> tuple[List[Investor], int]:
    """Повертає список інвесторів із пагінацією, сортуванням та фільтрацією."""
    query = db.query(Investor)

    # Фільтрація за рівнем ризику
    if risk_tolerance:
        query = query.filter(Investor.risk_tolerance == risk_tolerance)

    total = query.count()

    # Сортування
    column = getattr(Investor, sort_by, Investor.id)
    order_fn = asc if sort_order == "asc" else desc
    query = query.order_by(order_fn(column))

    items = query.offset(skip).limit(limit).all()
    return items, total


def get_by_id(db: Session, investor_id: int) -> Investor:
    investor = db.query(Investor).filter(Investor.id == investor_id).first()
    if not investor:
        raise NotFoundError("Інвестор", investor_id)
    return investor


def create(db: Session, data: InvestorCreate) -> Investor:
    existing = db.query(Investor).filter(Investor.email == data.email).first()
    if existing:
        raise ConflictError(f"Інвестор з email '{data.email}' вже існує")

    investor = Investor(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        risk_tolerance=data.risk_tolerance,
        created_at=datetime.utcnow(),
    )
    db.add(investor)
    db.commit()
    db.refresh(investor)
    return investor


def update(db: Session, investor_id: int, data: InvestorUpdate) -> Investor:
    """PUT — оновлення інвестора. Оновлюються лише передані поля."""
    investor = get_by_id(db, investor_id)

    if data.email is not None and data.email != investor.email:
        conflict = db.query(Investor).filter(Investor.email == data.email).first()
        if conflict:
            raise ConflictError(f"Інвестор з email '{data.email}' вже існує")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(investor, field, value)

    db.commit()
    db.refresh(investor)
    return investor


def delete(db: Session, investor_id: int) -> None:
    """DELETE — видалення інвестора (каскадно видаляє його портфелі)."""
    investor = get_by_id(db, investor_id)
    db.delete(investor)
    db.commit()
