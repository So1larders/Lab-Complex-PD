"""
PortfolioService — бізнес-логіка для сутності Портфель.
Portfolio Service мікросервіс: управління інвестиційними портфелями.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from portfolio_service.models.models import Portfolio, Investor
from portfolio_service.schemas.schemas import PortfolioCreate, PortfolioUpdate
from portfolio_service.exceptions.handlers import NotFoundError


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "id",
    sort_order: str = "asc",
    investor_id: Optional[int] = None,
) -> tuple[List[Portfolio], int]:
    query = db.query(Portfolio)

    if investor_id:
        # Перевірка існування інвестора
        if not db.query(Investor).filter(Investor.id == investor_id).first():
            raise NotFoundError("Інвестор", investor_id)
        query = query.filter(Portfolio.investor_id == investor_id)

    total = query.count()

    column = getattr(Portfolio, sort_by, Portfolio.id)
    order_fn = asc if sort_order == "asc" else desc
    query = query.order_by(order_fn(column))

    return query.offset(skip).limit(limit).all(), total


def get_by_id(db: Session, portfolio_id: int) -> Portfolio:
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise NotFoundError("Портфель", portfolio_id)
    return portfolio


def create(db: Session, data: PortfolioCreate) -> Portfolio:
    if not db.query(Investor).filter(Investor.id == data.investor_id).first():
        raise NotFoundError("Інвестор", data.investor_id)

    portfolio = Portfolio(
        investor_id=data.investor_id,
        name=data.name,
        description=data.description,
        created_at=datetime.utcnow(),
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


def update(db: Session, portfolio_id: int, data: PortfolioUpdate) -> Portfolio:
    portfolio = get_by_id(db, portfolio_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(portfolio, field, value)

    db.commit()
    db.refresh(portfolio)
    return portfolio


def delete(db: Session, portfolio_id: int) -> None:
    """DELETE — видалення портфеля (каскадно: транзакції, ризики, звіти)."""
    portfolio = get_by_id(db, portfolio_id)
    db.delete(portfolio)
    db.commit()
