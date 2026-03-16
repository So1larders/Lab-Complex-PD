"""
Налаштування бази даних SQLite через SQLAlchemy.
Аналог Spring Data JPA + H2 у Java-проєктах.

Архітектура:
  engine       — підключення до SQLite-файлу (аналог DataSource)
  SessionLocal — фабрика сесій       (аналог EntityManager / JPA Session)
  Base         — базовий клас ORM-моделей (аналог @Entity + JPA mappings)
  get_db()     — dependency injection сесії в роутери (аналог @Transactional)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

# SQLite-файл поруч із кодом; для PostgreSQL замінити рядок підключення:
# DATABASE_URL = "postgresql://user:password@localhost:5432/investment_portfolio"
DATABASE_URL = "sqlite:///./investment_portfolio.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},   # потрібно лише для SQLite
    echo=False,                                   # True → SQL-лог у консолі
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Базовий клас для всіх ORM-сутностей."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Dependency — відкриває сесію БД і гарантовано закриває її.
    Аналог @Transactional у Spring: кожен запит отримує власну сесію,
    при виході вона автоматично закривається (rollback якщо не commit).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Створює всі таблиці (якщо ще не існують). Викликається при старті."""
    Base.metadata.create_all(bind=engine)
