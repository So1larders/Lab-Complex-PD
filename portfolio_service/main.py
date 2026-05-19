"""
Точка входу FastAPI-застосунку — Лабораторна робота №3.
Система управління інвестиційним портфелем.

Мікросервісна архітектура (в межах одного монорепо):
  Portfolio Service  → /api/v1/portfolios,  /api/v1/investors
  Asset Service      → /api/v1/assets
  Transaction Service→ /api/v1/transactions
  Analytics Service  → /api/v1/risks,       /api/v1/reports
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from portfolio_service.database import create_tables
from portfolio_service.routers import investors, portfolios, risks, reports
from portfolio_service.exceptions.handlers import register_exception_handlers

import os
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Виконується один раз при старті.
    Створює таблиці в БД, якщо їх ще немає.
    Аналог schema auto-creation у Spring Boot (spring.jpa.hibernate.ddl-auto=update).
    """
    create_tables()
    
    # Initialize Redis caching
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis = aioredis.from_url(redis_url, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="portfolio-cache")
    
    yield


app = FastAPI(
    title="Investment Portfolio Management API",
    description=(
        "REST API для системи управління інвестиційним портфелем.\n\n"
        "**Лабораторна робота №3** — розширений REST API:\n"
        "- Повний CRUD (GET / POST / PUT / DELETE)\n"
        "- Підключення SQLite через SQLAlchemy (аналог Spring Data JPA + H2)\n"
        "- Repository layer (Session як аналог JpaRepository)\n"
        "- Глобальна обробка винятків (аналог @ControllerAdvice)\n"
        "- Єдиний формат помилки: timestamp / status / message / path\n"
        "- Пагінація та сортування всіх колекцій\n"
        "- Фільтрація за ключовими полями\n"
        "- Транзакційність операцій\n\n"
        "**Мікросервіси:** Portfolio · Asset · Transaction · Analytics"
    ),
    version="2.0.0",
    contact={"name": "Львівська Політехніка"},
    lifespan=lifespan,
)

register_exception_handlers(app)

# ─── Portfolio Service ────────────────────────────────────────────────────────
app.include_router(investors.router,    prefix="/api/v1/investors",    tags=["Portfolio Service – Investors"])
app.include_router(portfolios.router,   prefix="/api/v1/portfolios",   tags=["Portfolio Service – Portfolios"])

# ─── Analytics Service ───────────────────────────────────────────────────────
app.include_router(risks.router,        prefix="/api/v1/risks",        tags=["Analytics Service – Risks"])
app.include_router(reports.router,      prefix="/api/v1/reports",      tags=["Analytics Service – Reports"])


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Investment Portfolio Management API v2.0",
        "lab":     "Лабораторна робота №3 — розширений REST API + БД",
        "docs":    "/docs",
        "redoc":   "/redoc",
    }


@app.get("/health", tags=["Root"])
def health():
    """Перевірка стану сервісу."""
    return {"status": "ok", "version": "2.0.0"}
