# Система управління інвестиційним портфелем — REST API

> Лабораторна робота №2 · FastAPI · Python 3.11+  
> Національний університет «Львівська політехніка»

---

## Запуск

```bash
# 1. Встановити залежності
pip install -r requirements.txt

# 2. Запустити сервер
uvicorn app.main:app --reload --port 8000

# 3. Swagger UI (документація)
http://localhost:8000/docs
```

---

## Структура пакетів

```
investment_portfolio/
├── app/
│   ├── main.py                  # Точка входу FastAPI
│   ├── models/
│   │   ├── models.py            # Класи сутностей
│   │   └── storage.py           # In-memory сховище
│   ├── schemas/
│   │   └── schemas.py           # Pydantic-схеми (DTO)
│   ├── services/
│   │   ├── investor_service.py  # Бізнес-логіка інвесторів
│   │   ├── asset_service.py     # Бізнес-логіка активів
│   │   ├── portfolio_service.py # Бізнес-логіка портфелів
│   │   ├── transaction_service.py # Купівля/продаж
│   │   ├── risk_service.py      # Аналіз ризику
│   │   └── report_service.py    # Формування звітів
│   ├── routers/
│   │   ├── investors.py
│   │   ├── assets.py
│   │   ├── portfolios.py
│   │   ├── transactions.py
│   │   ├── risks.py
│   │   └── reports.py
│   └── exceptions/
│       └── handlers.py          # Обробка помилок
└── tests/
    └── test_api.py              # Автоматичні тести
```

---

## Таблиця REST-ендпоінтів

| Метод  | URL                                        | Призначення                              | Код відповіді |
|--------|--------------------------------------------|------------------------------------------|---------------|
| GET    | /api/v1/investors/                         | Список усіх інвесторів                  | 200           |
| GET    | /api/v1/investors/{id}                     | Інвестор за ID                           | 200 / 404     |
| POST   | /api/v1/investors/                         | Створити інвестора                       | 201 / 409 / 422 |
| GET    | /api/v1/assets/                            | Список активів                           | 200           |
| GET    | /api/v1/assets/{id}                        | Актив за ID                              | 200 / 404     |
| POST   | /api/v1/assets/                            | Додати актив                             | 201 / 409 / 422 |
| GET    | /api/v1/portfolios/                        | Список портфелів (фільтр ?investor_id=) | 200           |
| GET    | /api/v1/portfolios/{id}                    | Портфель за ID                           | 200 / 404     |
| POST   | /api/v1/portfolios/                        | Створити портфель                        | 201 / 404 / 422 |
| GET    | /api/v1/transactions/                      | Список транзакцій (?portfolio_id=)       | 200           |
| GET    | /api/v1/transactions/{id}                  | Транзакція за ID                         | 200 / 404     |
| POST   | /api/v1/transactions/                      | Купити / продати актив                   | 201 / 404 / 422 |
| GET    | /api/v1/risks/                             | Список оцінок ризику (?portfolio_id=)    | 200           |
| GET    | /api/v1/risks/{id}                         | Оцінка ризику за ID                      | 200 / 404     |
| POST   | /api/v1/risks/                             | Оцінити ризик портфеля                   | 201 / 404 / 422 |
| GET    | /api/v1/reports/                           | Список звітів                            | 200           |
| GET    | /api/v1/reports/{id}                       | Звіт за ID                               | 200 / 404     |
| POST   | /api/v1/reports/generate/{portfolio_id}    | Сформувати звіт про дохідність           | 201 / 404     |

---

## Приклади curl-запитів

### 1. Створити інвестора
```bash
curl -X POST http://localhost:8000/api/v1/investors/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Іван Петренко",
    "email": "ivan@example.com",
    "phone": "+380671234567",
    "risk_tolerance": "medium"
  }'
```
**Відповідь 201:**
```json
{
  "id": 1,
  "full_name": "Іван Петренко",
  "email": "ivan@example.com",
  "phone": "+380671234567",
  "risk_tolerance": "medium",
  "created_at": "2026-03-15T10:00:00"
}
```

---

### 2. Отримати список інвесторів
```bash
curl http://localhost:8000/api/v1/investors/
```

---

### 3. Отримати інвестора за ID
```bash
curl http://localhost:8000/api/v1/investors/1
```

---

### 4. Помилка — неіснуючий інвестор (404)
```bash
curl http://localhost:8000/api/v1/investors/999
```
**Відповідь 404:**
```json
{
  "detail": "Інвестор з id=999 не знайдено",
  "status_code": 404
}
```

---

### 5. Додати актив
```bash
curl -X POST http://localhost:8000/api/v1/assets/ \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "name": "Apple Inc.",
    "asset_type": "stock",
    "current_price": 185.50,
    "currency": "USD"
  }'
```

---

### 6. Створити портфель
```bash
curl -X POST http://localhost:8000/api/v1/portfolios/ \
  -H "Content-Type: application/json" \
  -d '{
    "investor_id": 1,
    "name": "Агресивний портфель",
    "description": "Орієнтований на зростання"
  }'
```

---

### 7. Купити актив (транзакція BUY)
```bash
curl -X POST http://localhost:8000/api/v1/transactions/ \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "asset_id": 1,
    "transaction_type": "buy",
    "quantity": 10,
    "price_per_unit": 185.50
  }'
```
**Відповідь 201:**
```json
{
  "id": 1,
  "portfolio_id": 1,
  "asset_id": 1,
  "transaction_type": "buy",
  "quantity": 10.0,
  "price_per_unit": 185.5,
  "total_amount": 1855.0,
  "executed_at": "2026-03-15T10:05:00"
}
```

---

### 8. Продати актив (транзакція SELL)
```bash
curl -X POST http://localhost:8000/api/v1/transactions/ \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "asset_id": 1,
    "transaction_type": "sell",
    "quantity": 5,
    "price_per_unit": 200.00
  }'
```

---

### 9. Помилка — продати більше ніж є (422)
```bash
curl -X POST http://localhost:8000/api/v1/transactions/ \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "asset_id": 1,
    "transaction_type": "sell",
    "quantity": 999,
    "price_per_unit": 200.00
  }'
```
**Відповідь 422:**
```json
{
  "detail": "Недостатньо активу для продажу. В портфелі: 10.0000, запит: 999.0000",
  "status_code": 422
}
```

---

### 10. Оцінити ризик портфеля
```bash
curl -X POST http://localhost:8000/api/v1/risks/ \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "volatility_score": 0.65,
    "diversification_score": 0.80,
    "max_drawdown_pct": 15.5,
    "notes": "Висока концентрація в IT-секторі"
  }'
```
**Відповідь 201:**
```json
{
  "id": 1,
  "portfolio_id": 1,
  "risk_level": "medium",
  "volatility_score": 0.65,
  "diversification_score": 0.8,
  "max_drawdown_pct": 15.5,
  "notes": "Висока концентрація в IT-секторі",
  "assessed_at": "2026-03-15T10:10:00"
}
```

---

### 11. Сформувати звіт про дохідність
```bash
curl -X POST http://localhost:8000/api/v1/reports/generate/1
```
**Відповідь 201:**
```json
{
  "id": 1,
  "portfolio_id": 1,
  "total_invested": 1855.0,
  "current_value": 1855.0,
  "profit_loss": 0.0,
  "profit_loss_pct": 0.0,
  "generated_at": "2026-03-15T10:15:00"
}
```

---

## Запуск тестів

```bash
pytest tests/ -v
```

---

## Бізнес-логіка

| Функція | Де реалізовано |
|---|---|
| Купівля активу | `transaction_service.create()` — тип BUY |
| Продаж активу | `transaction_service.create()` — тип SELL + перевірка залишку |
| Розрахунок дохідності | `report_service.generate()` — P&L, % прибутку |
| Аналіз ризику | `risk_service.create()` — автоматичний `RiskLevel` з формули |
| Формування звіту | `report_service.generate()` — ринкова вартість позицій |

---

## Коди статусів

| Код | Ситуація |
|-----|----------|
| 200 | Успішний GET |
| 201 | Успішний POST (ресурс створено) |
| 404 | Ресурс не знайдено |
| 409 | Конфлікт (дублікат email/ticker) |
| 422 | Помилка валідації / бізнес-логіки |
