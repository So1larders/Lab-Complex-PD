"""
TransactionService — бізнес-логіка для сутності Операція.
Transaction Service мікросервіс: купівля/продаж активів.

Транзакційність:
  Кожен метод отримує db: Session.  При успішному завершенні
  викликається db.commit(); якщо виникає виняток — SQLAlchemy
  автоматично робить rollback при закритті сесії (через get_db()).
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.models.models import Transaction, Portfolio, Asset, TransactionType
from app.schemas.schemas import TransactionCreate
from app.exceptions.handlers import NotFoundError, BusinessLogicError


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "executed_at",
    sort_order: str = "desc",
    portfolio_id: Optional[int] = None,
    asset_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
) -> tuple[List[Transaction], int]:
    query = db.query(Transaction)

    if portfolio_id:
        if not db.query(Portfolio).filter(Portfolio.id == portfolio_id).first():
            raise NotFoundError("Портфель", portfolio_id)
        query = query.filter(Transaction.portfolio_id == portfolio_id)

    if asset_id:
        query = query.filter(Transaction.asset_id == asset_id)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)

    total = query.count()

    column = getattr(Transaction, sort_by, Transaction.executed_at)
    order_fn = asc if sort_order == "asc" else desc
    query = query.order_by(order_fn(column))

    return query.offset(skip).limit(limit).all(), total


def get_by_id(db: Session, tx_id: int) -> Transaction:
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise NotFoundError("Транзакція", tx_id)
    return tx


def create(db: Session, data: TransactionCreate) -> Transaction:
    """
    Купівля або продаж активу.
    При продажу перевіряє наявність достатньої кількості активу в портфелі.
    Вся операція атомарна — виконується в одній транзакції БД.
    """
    if not db.query(Portfolio).filter(Portfolio.id == data.portfolio_id).first():
        raise NotFoundError("Портфель", data.portfolio_id)
    if not db.query(Asset).filter(Asset.id == data.asset_id).first():
        raise NotFoundError("Актив", data.asset_id)

    if data.transaction_type == TransactionType.SELL:
        held = _calculate_holdings(db, data.portfolio_id, data.asset_id)
        if held < data.quantity:
            raise BusinessLogicError(
                f"Недостатньо активу для продажу. "
                f"В портфелі: {held:.4f}, запит: {data.quantity:.4f}"
            )

    total = round(data.quantity * data.price_per_unit, 2)
    tx = Transaction(
        portfolio_id=data.portfolio_id,
        asset_id=data.asset_id,
        transaction_type=data.transaction_type,
        quantity=data.quantity,
        price_per_unit=data.price_per_unit,
        total_amount=total,
        executed_at=datetime.utcnow(),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def delete(db: Session, tx_id: int) -> None:
    """DELETE — видалення транзакції (скасування операції)."""
    tx = get_by_id(db, tx_id)
    db.delete(tx)
    db.commit()


def _calculate_holdings(db: Session, portfolio_id: int, asset_id: int) -> float:
    """Розраховує поточну кількість активу у портфелі."""
    txs = db.query(Transaction).filter(
        Transaction.portfolio_id == portfolio_id,
        Transaction.asset_id == asset_id,
    ).all()
    held = 0.0
    for tx in txs:
        if tx.transaction_type == TransactionType.BUY:
            held += tx.quantity
        else:
            held -= tx.quantity
    return held
