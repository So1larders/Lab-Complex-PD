"""
RiskService — бізнес-логіка для сутності Ризик.
Analytics Service (частина): аналіз ризику портфеля.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.models.models import Risk, RiskLevel, Portfolio
from app.schemas.schemas import RiskCreate, RiskUpdate
from app.exceptions.handlers import NotFoundError


def _compute_risk_level(volatility: float, drawdown: float) -> RiskLevel:
    """
    Автоматичний розрахунок рівня ризику на основі волатильності та просадки.
    score < 0.30  → LOW
    score < 0.60  → MEDIUM
    score >= 0.60 → HIGH
    """
    score = (volatility * 0.6) + (drawdown / 100 * 0.4)
    if score < 0.30:
        return RiskLevel.LOW
    elif score < 0.60:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "id",
    sort_order: str = "asc",
    portfolio_id: Optional[int] = None,
    risk_level: Optional[str] = None,
) -> tuple[List[Risk], int]:
    query = db.query(Risk)

    if portfolio_id:
        if not db.query(Portfolio).filter(Portfolio.id == portfolio_id).first():
            raise NotFoundError("Портфель", portfolio_id)
        query = query.filter(Risk.portfolio_id == portfolio_id)

    if risk_level:
        query = query.filter(Risk.risk_level == risk_level)

    total = query.count()

    column = getattr(Risk, sort_by, Risk.id)
    order_fn = asc if sort_order == "asc" else desc
    query = query.order_by(order_fn(column))

    return query.offset(skip).limit(limit).all(), total


def get_by_id(db: Session, risk_id: int) -> Risk:
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        raise NotFoundError("Оцінка ризику", risk_id)
    return risk


def create(db: Session, data: RiskCreate) -> Risk:
    if not db.query(Portfolio).filter(Portfolio.id == data.portfolio_id).first():
        raise NotFoundError("Портфель", data.portfolio_id)

    risk_level = _compute_risk_level(data.volatility_score, data.max_drawdown_pct)
    risk = Risk(
        portfolio_id=data.portfolio_id,
        risk_level=risk_level,
        volatility_score=data.volatility_score,
        diversification_score=data.diversification_score,
        max_drawdown_pct=data.max_drawdown_pct,
        notes=data.notes,
        assessed_at=datetime.utcnow(),
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


def update(db: Session, risk_id: int, data: RiskUpdate) -> Risk:
    """PUT — перераховує risk_level після оновлення параметрів."""
    risk = get_by_id(db, risk_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(risk, field, value)

    # Перерахунок рівня ризику
    risk.risk_level = _compute_risk_level(risk.volatility_score, risk.max_drawdown_pct)
    risk.assessed_at = datetime.utcnow()

    db.commit()
    db.refresh(risk)
    return risk


def delete(db: Session, risk_id: int) -> None:
    risk = get_by_id(db, risk_id)
    db.delete(risk)
    db.commit()
