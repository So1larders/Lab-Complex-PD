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

import httpx
from portfolio_service.models.models import Report, Portfolio
from portfolio_service.exceptions.handlers import BusinessLogicError
from portfolio_service.schemas.schemas import ReportResponse
from portfolio_service.exceptions.handlers import NotFoundError


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

    TRADING_SERVICE_URL = "http://localhost:8002/api/v1"
    
    try:
        # Fetch transactions
        txs_resp = httpx.get(f"{TRADING_SERVICE_URL}/transactions/?portfolio_id={portfolio_id}&size=1000", timeout=5.0)
        if txs_resp.status_code != 200:
            raise BusinessLogicError("Не вдалося отримати транзакції з Trading Service")
        txs_data = txs_resp.json().get("items", [])
        
        total_invested = 0.0
        holdings: dict[int, float] = {}

        for tx in txs_data:
            if tx.get("transaction_type") == "buy":
                total_invested += tx.get("total_amount", 0.0)
                holdings[tx.get("asset_id")] = holdings.get(tx.get("asset_id"), 0.0) + tx.get("quantity", 0.0)
            else:
                holdings[tx.get("asset_id")] = holdings.get(tx.get("asset_id"), 0.0) - tx.get("quantity", 0.0)

        current_value = 0.0
        for asset_id, qty in holdings.items():
            if qty > 0:
                asset_resp = httpx.get(f"{TRADING_SERVICE_URL}/assets/{asset_id}", timeout=2.0)
                if asset_resp.status_code == 200:
                    asset = asset_resp.json()
                    current_value += qty * asset.get("current_price", 0.0)
    except httpx.RequestError:
        raise BusinessLogicError("Trading Service недоступний")

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
