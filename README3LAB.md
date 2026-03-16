# Лабораторна робота №3 — Розширений REST API + База даних

**Система управління інвестиційним портфелем**
Національний університет «Львівська політехніка»

---

## Що було зроблено у цій роботі

### 1. Підключення бази даних (SQLite через SQLAlchemy)

**Файл:** `app/database.py`

Замість in-memory словників (`storage.py`) підключено повноцінну реляційну БД.

| Spring Boot (Java)                    | Цей проєкт (Python/FastAPI)              |
|---------------------------------------|------------------------------------------|
| `spring-boot-starter-data-jpa`        | `sqlalchemy==2.0.30`                     |
| `H2` in-memory DB                     | `SQLite` (файл `investment_portfolio.db`)|
| `application.yml` → `datasource.url`  | `app/config.yml` → `database.url`        |
| `@Entity`                             | `class Model(Base)` + `mapped_column`    |
| `JpaRepository`                       | `Session` + query builder                |
| `@Transactional`                      | `db.commit()` / `db.rollback()` в сесії  |
| `spring.jpa.hibernate.ddl-auto=update`| `Base.metadata.create_all()` при старті  |

**Для переходу на PostgreSQL** достатньо змінити один рядок:
```python
# app/database.py
DATABASE_URL = "postgresql://user:password@localhost:5432/investment_portfolio"
```

---

### 2. ORM Entity-класи (аналог @Entity у Spring)

**Файл:** `app/models/models.py`

Переписано всі 6 сутностей із plain Python-класів на SQLAlchemy ORM-моделі:

| Сутність    | Таблиця        | Зв'язки                                   |
|-------------|----------------|-------------------------------------------|
| `Investor`  | `investors`    | 1 → * Portfolio (cascade delete)          |
| `Asset`     | `assets`       | 1 → * Transaction                         |
| `Portfolio` | `portfolios`   | * → 1 Investor, 1 → * Transaction/Risk/Report (cascade) |
| `Transaction`| `transactions`| * → 1 Portfolio, * → 1 Asset             |
| `Risk`      | `risks`        | * → 1 Portfolio                           |
| `Report`    | `reports`      | * → 1 Portfolio                           |

**ER-діаграма зв'язків:**
```
Investor ──< Portfolio ──< Transaction >── Asset
                │
                ├──< Risk
                └──< Report
```

---

### 3. Нові HTTP-методи: PUT та DELETE

До кожного ресурсу додано:

#### PUT — оновлення ресурсу
```
PUT /api/v1/investors/{id}    — оновлення даних інвестора
PUT /api/v1/assets/{id}       — оновлення активу (напр. поточної ціни)
PUT /api/v1/portfolios/{id}   — перейменування / зміна опису
PUT /api/v1/risks/{id}        — оновлення параметрів ризику
```
Особливість: для ризику (`Risk`) після PUT автоматично **перераховується** `risk_level`.

Транзакції (`Transaction`) навмисно не мають PUT — фінансові операції є незмінним журналом аудиту.

#### DELETE — видалення ресурсу
```
DELETE /api/v1/investors/{id}     — з каскадним видаленням портфелів
DELETE /api/v1/assets/{id}        — видалення активу
DELETE /api/v1/portfolios/{id}    — з каскадним видаленням транзакцій, ризиків, звітів
DELETE /api/v1/transactions/{id}  — скасування операції
DELETE /api/v1/risks/{id}         — видалення оцінки ризику
DELETE /api/v1/reports/{id}       — видалення звіту
```

---

### 4. Глобальна обробка винятків (аналог @ControllerAdvice)

**Файл:** `app/exceptions/handlers.py`

Реалізовано **єдиний формат відповіді про помилку** (вимога з умови завдання):

```json
{
  "timestamp": "2026-03-16T10:30:00.000Z",
  "status":    404,
  "message":   "Інвестор з id=999 не знайдено",
  "path":      "/api/v1/investors/999"
}
```

| Виняток               | HTTP-статус | Аналог у Spring                          |
|-----------------------|-------------|------------------------------------------|
| `NotFoundError`       | 404         | `@ResponseStatus(HttpStatus.NOT_FOUND)`  |
| `ConflictError`       | 409         | `@ResponseStatus(HttpStatus.CONFLICT)`   |
| `BusinessLogicError`  | 422         | `@ResponseStatus(UNPROCESSABLE_ENTITY)`  |
| `RequestValidationError` | 422      | `MethodArgumentNotValidException`        |
| `Exception` (інші)    | 500         | `@ExceptionHandler(Exception.class)`     |

---

### 5. Фільтрація та сортування запитів

Кожен endpoint списку підтримує query-параметри:

```
GET /api/v1/investors/?risk_tolerance=high
GET /api/v1/assets/?asset_type=stock&currency=USD&sort_by=current_price&sort_order=desc
GET /api/v1/transactions/?portfolio_id=1&transaction_type=buy
GET /api/v1/risks/?portfolio_id=2&risk_level=high
```

---

### 6. Пагінація

Всі колекції повертають `PaginatedResponse`:

```json
{
  "items": [...],
  "total": 42,
  "page":  2,
  "size":  10,
  "pages": 5
}
```

Параметри запиту: `?page=1&size=10&sort_by=id&sort_order=asc`

---

### 7. Транзакційність операцій

Кожен запит отримує власну сесію БД через `get_db()` (dependency injection).

- При успіху: `db.commit()`
- При помилці: автоматичний `rollback` при закритті сесії

**Перевірений сценарій:**  
Спроба продажу більше активів, ніж є у портфелі → виняток → `rollback` → стан БД не змінюється.

**Каскадні операції** (атомарні):  
Видалення `Investor` → одночасно видаляє всі його `Portfolio` → і всі їхні `Transaction`, `Risk`, `Report`.

---

### 8. Мікросервісна архітектура

Роутери згруповані за мікросервісами:

| Мікросервіс          | Endpoints                              | Відповідальність                        |
|----------------------|----------------------------------------|-----------------------------------------|
| **Portfolio Service**| `/investors`, `/portfolios`            | Управління інвесторами та портфелями    |
| **Asset Service**    | `/assets`                              | Управління фінансовими інструментами    |
| **Transaction Service** | `/transactions`                    | Купівля/продаж активів                  |
| **Analytics Service**| `/risks`, `/reports`                   | Аналіз ризику, розрахунок прибутковості |

---

### 9. Порівняльний аналіз: in-memory vs база даних

| Критерій              | In-memory (Лаб. №2)         | SQLite/SQLAlchemy (Лаб. №3)         |
|-----------------------|-----------------------------|-------------------------------------|
| Зберігання даних      | Тільки під час роботи       | Персистентне (файл на диску)        |
| Перезапуск сервера    | Всі дані втрачаються        | Дані зберігаються                   |
| Цілісність даних      | Немає FK, ручні перевірки   | Foreign Key + каскадні операції     |
| Транзакційність       | Відсутня                    | ACID-транзакції через SQLAlchemy    |
| Масштабованість       | Обмежена RAM                | Заміна URL → PostgreSQL/MySQL       |
| Тестування            | Очистка словників           | Окрема in-memory SQLite для тестів  |
| Архітектура           | Сервіс → dict               | Сервіс → Session → ORM → DB        |

---

### 10. Нові схеми (Pydantic)

Додано `*Update`-схеми для PUT-запитів (всі поля необов'язкові):
- `InvestorUpdate`
- `AssetUpdate`
- `PortfolioUpdate`
- `RiskUpdate`

Додано `PaginatedResponse[T]` — generic-обгортка для пагінованих списків.

---

## Структура проєкту

```
investment_portfolio/
├── app/
│   ├── main.py                  # Точка входу, реєстрація роутерів
│   ├── database.py              # ★ НОВИЙ — SQLAlchemy engine, Session, Base
│   ├── config.yml               # ★ НОВИЙ — аналог application.yml
│   ├── models/
│   │   └── models.py            # ★ ОНОВЛЕНО — ORM @Entity класи
│   ├── schemas/
│   │   └── schemas.py           # ★ ОНОВЛЕНО — *Update + PaginatedResponse
│   ├── exceptions/
│   │   └── handlers.py          # ★ ОНОВЛЕНО — timestamp/status/message/path
│   ├── routers/
│   │   ├── investors.py         # ★ ОНОВЛЕНО — PUT, DELETE, пагінація
│   │   ├── assets.py            # ★ ОНОВЛЕНО — PUT, DELETE, пагінація
│   │   ├── portfolios.py        # ★ ОНОВЛЕНО — PUT, DELETE, пагінація
│   │   ├── transactions.py      # ★ ОНОВЛЕНО — DELETE, пагінація
│   │   ├── risks.py             # ★ ОНОВЛЕНО — PUT, DELETE, пагінація
│   │   └── reports.py           # ★ ОНОВЛЕНО — DELETE, пагінація
│   └── services/
│       ├── investor_service.py  # ★ ОНОВЛЕНО — повний CRUD + DB
│       ├── asset_service.py     # ★ ОНОВЛЕНО — повний CRUD + DB
│       ├── portfolio_service.py # ★ ОНОВЛЕНО — повний CRUD + DB
│       ├── transaction_service.py # ★ ОНОВЛЕНО — повний CRUD + DB
│       ├── risk_service.py      # ★ ОНОВЛЕНО — повний CRUD + DB
│       └── report_service.py    # ★ ОНОВЛЕНО — повний CRUD + DB
├── tests/
│   └── test_api.py              # ★ ОНОВЛЕНО — 55 тестів
├── requirements.txt             # ★ ОНОВЛЕНО — додано sqlalchemy, alembic
└── README3LAB.md                # ★ НОВИЙ — цей файл
```

---

## Запуск

```bash
# Встановити залежності
pip install -r requirements.txt

# Запустити сервер (БД створюється автоматично)
uvicorn app.main:app --reload

# Документація API
http://localhost:8000/docs

# Запуск тестів
pytest tests/ -v
```

---

## Результати тестування

```
55 passed, 0 failed
```

Покрито:
- ✅ Повний CRUD для всіх 6 сутностей
- ✅ Бізнес-логіка купівлі/продажу
- ✅ Перевірка некоректних сценаріїв (404, 409, 422)
- ✅ Транзакційність (rollback при помилці)
- ✅ Каскадне видалення і цілісність даних
- ✅ Пагінація та фільтрація
- ✅ Єдиний формат помилки (timestamp/status/message/path)
