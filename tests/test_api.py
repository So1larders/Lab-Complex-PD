"""
Тести для REST API — Лабораторна робота №3.
Покриття: повний CRUD, некоректні сценарії, транзакційність.

Запуск: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# ─── In-memory SQLite для тестів ─────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///./test_investment.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Перед кожним тестом — чиста БД."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _investor(email="test@example.com", risk="medium"):
    return client.post("/api/v1/investors/", json={
        "full_name": "Тест Тестенко",
        "email": email,
        "risk_tolerance": risk,
    })


def _asset(ticker="AAPL", price=185.5):
    return client.post("/api/v1/assets/", json={
        "ticker": ticker,
        "name": "Apple Inc.",
        "asset_type": "stock",
        "current_price": price,
        "currency": "USD",
    })


def _portfolio(investor_id=1, name="Тестовий портфель"):
    return client.post("/api/v1/portfolios/", json={
        "investor_id": investor_id,
        "name": name,
    })


def _buy(portfolio_id=1, asset_id=1, qty=10.0, price=100.0):
    return client.post("/api/v1/transactions/", json={
        "portfolio_id": portfolio_id,
        "asset_id": asset_id,
        "transaction_type": "buy",
        "quantity": qty,
        "price_per_unit": price,
    })


def _sell(portfolio_id=1, asset_id=1, qty=5.0, price=120.0):
    return client.post("/api/v1/transactions/", json={
        "portfolio_id": portfolio_id,
        "asset_id": asset_id,
        "transaction_type": "sell",
        "quantity": qty,
        "price_per_unit": price,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# INVESTORS
# ═══════════════════════════════════════════════════════════════════════════════

class TestInvestorsCRUD:

    # ── CREATE ────────────────────────────────────────────────────────────────

    def test_create_investor_201(self):
        r = _investor()
        assert r.status_code == 201
        d = r.json()
        assert d["email"] == "test@example.com"
        assert d["id"] == 1
        assert d["risk_tolerance"] == "medium"

    def test_create_investor_duplicate_email_409(self):
        _investor()
        r = _investor()
        assert r.status_code == 409
        assert "status" in r.json()
        assert "timestamp" in r.json()
        assert "path" in r.json()

    def test_create_investor_invalid_email_422(self):
        r = client.post("/api/v1/investors/", json={
            "full_name": "Іван", "email": "not-email", "risk_tolerance": "low",
        })
        assert r.status_code == 422

    # ── READ ──────────────────────────────────────────────────────────────────

    def test_get_investor_200(self):
        _investor()
        r = client.get("/api/v1/investors/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_investor_not_found_404(self):
        r = client.get("/api/v1/investors/999")
        assert r.status_code == 404
        body = r.json()
        assert body["status"] == 404
        assert "timestamp" in body
        assert "path" in body

    def test_list_investors_paginated(self):
        for i in range(5):
            _investor(email=f"u{i}@test.com")
        r = client.get("/api/v1/investors/?page=1&size=3")
        assert r.status_code == 200
        d = r.json()
        assert d["total"] == 5
        assert len(d["items"]) == 3
        assert d["pages"] == 2

    def test_list_investors_filter_risk(self):
        _investor("low@t.com", "low")
        _investor("high@t.com", "high")
        r = client.get("/api/v1/investors/?risk_tolerance=low")
        assert r.status_code == 200
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["risk_tolerance"] == "low"

    def test_list_investors_sort_desc(self):
        _investor("a@t.com")
        _investor("b@t.com")
        r = client.get("/api/v1/investors/?sort_by=id&sort_order=desc")
        assert r.status_code == 200
        ids = [i["id"] for i in r.json()["items"]]
        assert ids == sorted(ids, reverse=True)

    # ── UPDATE (PUT) ──────────────────────────────────────────────────────────

    def test_update_investor_200(self):
        _investor()
        r = client.put("/api/v1/investors/1", json={"full_name": "Нове Ім'я"})
        assert r.status_code == 200
        assert r.json()["full_name"] == "Нове Ім'я"

    def test_update_investor_email_conflict_409(self):
        _investor("a@t.com")
        _investor("b@t.com")
        r = client.put("/api/v1/investors/1", json={"email": "b@t.com"})
        assert r.status_code == 409

    def test_update_investor_not_found_404(self):
        r = client.put("/api/v1/investors/999", json={"full_name": "Неіснуючий Інвестор"})
        assert r.status_code == 404

    # ── DELETE ────────────────────────────────────────────────────────────────

    def test_delete_investor_204(self):
        _investor()
        r = client.delete("/api/v1/investors/1")
        assert r.status_code == 204
        assert client.get("/api/v1/investors/1").status_code == 404

    def test_delete_investor_not_found_404(self):
        r = client.delete("/api/v1/investors/999")
        assert r.status_code == 404

    def test_delete_investor_cascades_portfolios(self):
        """Видалення інвестора → каскадно видаляє портфелі."""
        _investor()
        _portfolio(investor_id=1)
        client.delete("/api/v1/investors/1")
        r = client.get("/api/v1/portfolios/1")
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# ASSETS
# ═══════════════════════════════════════════════════════════════════════════════

class TestAssetsCRUD:

    def test_create_asset_201(self):
        r = _asset()
        assert r.status_code == 201
        assert r.json()["ticker"] == "AAPL"

    def test_create_asset_ticker_uppercase(self):
        r = client.post("/api/v1/assets/", json={
            "ticker": "msft", "name": "Microsoft",
            "asset_type": "stock", "current_price": 400.0, "currency": "usd",
        })
        assert r.status_code == 201
        assert r.json()["ticker"] == "MSFT"
        assert r.json()["currency"] == "USD"

    def test_create_asset_duplicate_ticker_409(self):
        _asset()
        r = _asset()
        assert r.status_code == 409

    def test_get_asset_not_found_404(self):
        r = client.get("/api/v1/assets/999")
        assert r.status_code == 404

    def test_list_assets_filter_type(self):
        _asset("AAPL", 185.5)
        client.post("/api/v1/assets/", json={
            "ticker": "BTC", "name": "Bitcoin",
            "asset_type": "cryptocurrency", "current_price": 60000.0, "currency": "USD",
        })
        r = client.get("/api/v1/assets/?asset_type=cryptocurrency")
        assert r.status_code == 200
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["ticker"] == "BTC"

    def test_update_asset_price_200(self):
        _asset("AAPL", 185.5)
        r = client.put("/api/v1/assets/1", json={"current_price": 200.0})
        assert r.status_code == 200
        assert r.json()["current_price"] == 200.0

    def test_delete_asset_204(self):
        _asset()
        r = client.delete("/api/v1/assets/1")
        assert r.status_code == 204
        assert client.get("/api/v1/assets/1").status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIOS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPortfoliosCRUD:

    def setup_method(self):
        _investor()

    def test_create_portfolio_201(self):
        r = _portfolio()
        assert r.status_code == 201
        assert r.json()["investor_id"] == 1

    def test_create_portfolio_investor_not_found_404(self):
        r = _portfolio(investor_id=999)
        assert r.status_code == 404

    def test_list_portfolios_filter_investor(self):
        _investor("b@t.com")
        _portfolio(investor_id=1, name="P1")
        _portfolio(investor_id=2, name="P2")
        r = client.get("/api/v1/portfolios/?investor_id=1")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_update_portfolio_200(self):
        _portfolio()
        r = client.put("/api/v1/portfolios/1", json={"name": "Оновлений"})
        assert r.status_code == 200
        assert r.json()["name"] == "Оновлений"

    def test_delete_portfolio_204(self):
        _portfolio()
        r = client.delete("/api/v1/portfolios/1")
        assert r.status_code == 204

    def test_delete_portfolio_cascades_transactions(self):
        """Видалення портфеля → каскадно видаляє транзакції."""
        _portfolio()
        _asset()
        _buy()
        client.delete("/api/v1/portfolios/1")
        r = client.get("/api/v1/transactions/1")
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSACTIONS (бізнес-логіка купівлі/продажу)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTransactions:

    def setup_method(self):
        _investor()
        _portfolio()
        _asset()

    def test_buy_201(self):
        r = _buy(qty=10.0, price=100.0)
        assert r.status_code == 201
        d = r.json()
        assert d["transaction_type"] == "buy"
        assert d["total_amount"] == 1000.0

    def test_sell_after_buy_201(self):
        _buy(qty=10.0, price=100.0)
        r = _sell(qty=5.0, price=120.0)
        assert r.status_code == 201
        assert r.json()["transaction_type"] == "sell"

    def test_sell_more_than_held_422(self):
        """Бізнес-правило: не можна продати більше, ніж є."""
        _buy(qty=5.0, price=100.0)
        r = _sell(qty=10.0, price=120.0)
        assert r.status_code == 422
        assert "Недостатньо" in r.json()["message"]

    def test_sell_without_holdings_422(self):
        r = _sell(qty=1.0, price=100.0)
        assert r.status_code == 422

    def test_buy_portfolio_not_found_404(self):
        r = _buy(portfolio_id=999)
        assert r.status_code == 404

    def test_buy_asset_not_found_404(self):
        r = _buy(asset_id=999)
        assert r.status_code == 404

    def test_list_transactions_filter_portfolio(self):
        _buy()
        r = client.get("/api/v1/transactions/?portfolio_id=1")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_transactions_filter_type(self):
        _buy(qty=10.0, price=100.0)
        _sell(qty=3.0, price=110.0)
        r = client.get("/api/v1/transactions/?transaction_type=sell")
        assert r.json()["total"] == 1

    def test_delete_transaction_204(self):
        _buy()
        r = client.delete("/api/v1/transactions/1")
        assert r.status_code == 204

    def test_get_transaction_not_found_404(self):
        r = client.get("/api/v1/transactions/999")
        assert r.status_code == 404

    def test_total_amount_calculated_correctly(self):
        r = _buy(qty=7.5, price=200.0)
        assert r.json()["total_amount"] == 1500.0


# ═══════════════════════════════════════════════════════════════════════════════
# RISKS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRisks:

    def setup_method(self):
        _investor()
        _portfolio()

    def _risk(self, vol=0.7, div=0.5, draw=20.0):
        return client.post("/api/v1/risks/", json={
            "portfolio_id": 1,
            "volatility_score": vol,
            "diversification_score": div,
            "max_drawdown_pct": draw,
        })

    def test_create_risk_auto_level_high(self):
        """Висока волатильність → HIGH."""
        r = self._risk(vol=0.9, draw=50.0)
        assert r.status_code == 201
        assert r.json()["risk_level"] == "high"

    def test_create_risk_auto_level_low(self):
        """Низька волатильність → LOW."""
        r = self._risk(vol=0.1, draw=5.0)
        assert r.status_code == 201
        assert r.json()["risk_level"] == "low"

    def test_create_risk_portfolio_not_found_404(self):
        r = client.post("/api/v1/risks/", json={
            "portfolio_id": 999,
            "volatility_score": 0.5,
            "diversification_score": 0.5,
            "max_drawdown_pct": 10.0,
        })
        assert r.status_code == 404

    def test_update_risk_recalculates_level(self):
        """PUT → risk_level перераховується автоматично."""
        self._risk(vol=0.1, draw=5.0)   # LOW
        r = client.put("/api/v1/risks/1", json={"volatility_score": 0.95, "max_drawdown_pct": 60.0})
        assert r.status_code == 200
        assert r.json()["risk_level"] == "high"

    def test_list_risks_filter_level(self):
        self._risk(vol=0.1, draw=5.0)   # low
        self._risk(vol=0.9, draw=50.0)  # high
        r = client.get("/api/v1/risks/?risk_level=high")
        assert r.json()["total"] == 1

    def test_delete_risk_204(self):
        self._risk()
        r = client.delete("/api/v1/risks/1")
        assert r.status_code == 204


# ═══════════════════════════════════════════════════════════════════════════════
# REPORTS (аналітика прибутковості)
# ═══════════════════════════════════════════════════════════════════════════════

class TestReports:

    def setup_method(self):
        _investor()
        _portfolio()
        _asset("AAPL", 200.0)  # поточна ціна 200

    def test_generate_report_profit(self):
        """Купили по 100, зараз 200 → прибуток."""
        _buy(qty=10.0, price=100.0)
        r = client.post("/api/v1/reports/generate/1")
        assert r.status_code == 201
        d = r.json()
        assert d["total_invested"] == 1000.0
        assert d["current_value"] == 2000.0
        assert d["profit_loss"] == 1000.0
        assert d["profit_loss_pct"] == 100.0

    def test_generate_report_loss(self):
        """Купили по 250, зараз 200 → збиток."""
        _buy(qty=10.0, price=250.0)
        r = client.post("/api/v1/reports/generate/1")
        assert r.status_code == 201
        d = r.json()
        assert d["profit_loss"] < 0

    def test_generate_report_empty_portfolio(self):
        """Порожній портфель → нульові показники."""
        r = client.post("/api/v1/reports/generate/1")
        assert r.status_code == 201
        assert r.json()["total_invested"] == 0.0
        assert r.json()["profit_loss"] == 0.0

    def test_generate_report_after_sell(self):
        """Продали частину → поточна вартість лише залишку."""
        _buy(qty=10.0, price=100.0)
        _sell(qty=4.0, price=100.0)    # залишилось 6
        r = client.post("/api/v1/reports/generate/1")
        d = r.json()
        # поточна ціна 200, тримаємо 6 → 1200
        assert d["current_value"] == pytest.approx(1200.0, abs=0.01)

    def test_generate_report_portfolio_not_found_404(self):
        r = client.post("/api/v1/reports/generate/999")
        assert r.status_code == 404

    def test_list_reports_filter_portfolio(self):
        _buy(qty=5.0, price=100.0)
        client.post("/api/v1/reports/generate/1")
        r = client.get("/api/v1/reports/?portfolio_id=1")
        assert r.json()["total"] == 1

    def test_delete_report_204(self):
        client.post("/api/v1/reports/generate/1")
        r = client.delete("/api/v1/reports/1")
        assert r.status_code == 204


# ═══════════════════════════════════════════════════════════════════════════════
# ТРАНЗАКЦІЙНІСТЬ
# ═══════════════════════════════════════════════════════════════════════════════

class TestTransactionality:

    def test_sell_rollback_on_insufficient_funds(self):
        """
        Перевірка транзакційності: невдалий SELL не змінює стан БД.
        Кількість транзакцій до і після спроби продажу — однакова.
        """
        _investor()
        _portfolio()
        _asset()
        _buy(qty=5.0, price=100.0)

        before = client.get("/api/v1/transactions/?portfolio_id=1").json()["total"]
        _sell(qty=100.0, price=120.0)  # має провалитись
        after = client.get("/api/v1/transactions/?portfolio_id=1").json()["total"]

        assert before == after == 1

    def test_cascade_delete_integrity(self):
        """
        Цілісність каскадного видалення:
        Investor → Portfolio → Transactions + Risks + Reports
        """
        _investor()
        _portfolio()
        _asset()
        _buy(qty=5.0, price=100.0)
        client.post("/api/v1/risks/", json={
            "portfolio_id": 1, "volatility_score": 0.5,
            "diversification_score": 0.5, "max_drawdown_pct": 10.0,
        })
        client.post("/api/v1/reports/generate/1")

        # Видаляємо інвестора
        client.delete("/api/v1/investors/1")

        # Всі залежні записи мають зникнути
        assert client.get("/api/v1/portfolios/1").status_code == 404
        assert client.get("/api/v1/transactions/1").status_code == 404
        assert client.get("/api/v1/risks/1").status_code == 404
        assert client.get("/api/v1/reports/1").status_code == 404

    def test_error_response_format_has_all_fields(self):
        """
        Перевірка єдиного формату помилки:
        timestamp, status, message, path — всі поля присутні.
        """
        r = client.get("/api/v1/investors/999")
        body = r.json()
        assert "timestamp" in body
        assert "status" in body
        assert "message" in body
        assert "path" in body
        assert body["status"] == 404
        assert body["path"] == "/api/v1/investors/999"

    def test_pagination_second_page(self):
        """Перевірка коректності пагінації — друга сторінка."""
        for i in range(7):
            _investor(email=f"inv{i}@test.com")
        r = client.get("/api/v1/investors/?page=2&size=5")
        d = r.json()
        assert d["total"] == 7
        assert len(d["items"]) == 2
        assert d["page"] == 2
        assert d["pages"] == 2
