"""
Router: Reports — Analytics Service (звітність / прибутковість).
GET    /api/v1/reports/                      — список звітів (пагінація)
GET    /api/v1/reports/{id}                  — деталі звіту
POST   /api/v1/reports/generate/{portfolio_id} — згенерувати звіт
DELETE /api/v1/reports/{id}                  — видалити звіт
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from portfolio_service.database import get_db
from portfolio_service.schemas.schemas import ReportResponse, PaginatedResponse
from portfolio_service.services import report_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ReportResponse], status_code=200,
            summary="Список звітів із пагінацією та фільтрацією")
def list_reports(
    page:         int           = Query(1,  ge=1),
    size:         int           = Query(10, ge=1, le=100),
    sort_by:      str           = Query("generated_at"),
    sort_order:   str           = Query("desc", pattern="^(asc|desc)$"),
    portfolio_id: Optional[int] = Query(None, description="Фільтр за портфелем"),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    items, total = report_service.get_all(
        db, skip=skip, limit=size,
        sort_by=sort_by, sort_order=sort_order,
        portfolio_id=portfolio_id,
    )
    return {
        "items": items, "total": total,
        "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.get("/{report_id}", response_model=ReportResponse, status_code=200,
            summary="Отримати звіт за ID")
def get_report(report_id: int, db: Session = Depends(get_db)):
    return report_service.get_by_id(db, report_id)


@router.post("/generate/{portfolio_id}", response_model=ReportResponse, status_code=201,
             summary="Сформувати звіт про дохідність портфеля")
def generate_report(portfolio_id: int, db: Session = Depends(get_db)):
    return report_service.generate(db, portfolio_id)


@router.delete("/{report_id}", status_code=204,
               summary="Видалити звіт")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report_service.delete(db, report_id)
