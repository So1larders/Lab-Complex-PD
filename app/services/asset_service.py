"""
AssetService — бізнес-логіка для сутності Актив.
Asset Service мікросервіс: управління фінансовими інструментами.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.models.models import Asset, AssetType
from app.schemas.schemas import AssetCreate, AssetUpdate
from app.exceptions.handlers import NotFoundError, ConflictError


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "id",
    sort_order: str = "asc",
    asset_type: Optional[str] = None,
    currency: Optional[str] = None,
) -> tuple[List[Asset], int]:
    """Повертає список активів із пагінацією, сортуванням та фільтрацією."""
    query = db.query(Asset)

    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    if currency:
        query = query.filter(Asset.currency == currency.upper())

    total = query.count()

    column = getattr(Asset, sort_by, Asset.id)
    order_fn = asc if sort_order == "asc" else desc
    query = query.order_by(order_fn(column))

    return query.offset(skip).limit(limit).all(), total


def get_by_id(db: Session, asset_id: int) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise NotFoundError("Актив", asset_id)
    return asset


def create(db: Session, data: AssetCreate) -> Asset:
    ticker_upper = data.ticker.upper()
    if db.query(Asset).filter(Asset.ticker == ticker_upper).first():
        raise ConflictError(f"Актив з тікером '{ticker_upper}' вже існує")

    asset = Asset(
        ticker=ticker_upper,
        name=data.name,
        asset_type=data.asset_type,
        current_price=data.current_price,
        currency=data.currency.upper(),
        updated_at=datetime.utcnow(),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def update(db: Session, asset_id: int, data: AssetUpdate) -> Asset:
    """PUT — оновлення активу (наприклад, зміна поточної ціни)."""
    asset = get_by_id(db, asset_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    asset.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(asset)
    return asset


def delete(db: Session, asset_id: int) -> None:
    """DELETE — видалення активу."""
    asset = get_by_id(db, asset_id)
    db.delete(asset)
    db.commit()
