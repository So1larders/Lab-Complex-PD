"""
ReportService — бізнес-логіка для сутності Звіт.
Analytics Service (частина): розрахунок прибутковості портфеля.

Бізнес-логіка:
  total_invested  — сума всіх BUY-транзакцій
  current_value   — qty * current_price для кожного активу, що залишився
  profit_loss     — current_value - total_invested
  profit_loss_pct — (profit_loss / total_invested) * 100
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.models.models import Report, Portfolio, Transaction, Asset, TransactionType
from app.schemas.schemas import ReportResponse
from app.exceptions.handlers import NotFoundError


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "generated_at",
    sort_order: str = "desc",
    portfolio_id: Optional[int] = None,
) -> tuple[List[Report], int]:
    query = db.query(Report)

    if portfolio_id:
        if not db.query(Portfolio).filter(Portfolio.id == portfolio_id).first():
            raise NotFoundError("Портфель", portfolio_id)
        query = query.filter(Report.portfolio_id == portfolio_id)

    total = query.count()

    column = getattr(Report, sort_by, Report.generated_at)
    order_fn = asc if sort_order == "asc" else desc
    query = query.order_by(order_fn(column))

    return query.offset(skip).limit(limit).all(), total


def get_by_id(db: Session, report_id: int) -> Report:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise NotFoundError("Звіт", report_id)
    return report


def generate(db: Session, portfolio_id: int) -> Report:
    """
    Генерує аналітичний звіт по портфелю.
    Читає всі транзакції та поточні ціни активів із БД.
    Вся операція виконується в одній транзакції БД (атомарно).
    """
    if not db.query(Portfolio).filter(Portfolio.id == portfolio_id).first():
        raise NotFoundError("Портфель", portfolio_id)

    txs = db.query(Transaction).filter(
        Transaction.portfolio_id == portfolio_id
    ).all()

    total_invested = 0.0
    holdings: dict[int, float] = {}

    for tx in txs:
        if tx.transaction_type == TransactionType.BUY:
            total_invested += tx.total_amount
            holdings[tx.asset_id] = holdings.get(tx.asset_id, 0.0) + tx.quantity
        else:
            holdings[tx.asset_id] = holdings.get(tx.asset_id, 0.0) - tx.quantity

    current_value = 0.0
    for asset_id, qty in holdings.items():
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if asset and qty > 0:
            current_value += qty * asset.current_price

    profit_loss = round(current_value - total_invested, 2)
    profit_loss_pct = (
        round((profit_loss / total_invested) * 100, 2) if total_invested > 0 else 0.0
    )

    report = Report(
        portfolio_id=portfolio_id,
        total_invested=round(total_invested, 2),
        current_value=round(current_value, 2),
        profit_loss=profit_loss,
        profit_loss_pct=profit_loss_pct,
        generated_at=datetime.utcnow(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def delete(db: Session, report_id: int) -> None:
    report = get_by_id(db, report_id)
    db.delete(report)
    db.commit()
