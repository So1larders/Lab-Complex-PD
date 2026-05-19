import urllib.request
import json
import random

base_url = "http://localhost:8888/api/v1"

def post(endpoint, data):
    req = urllib.request.Request(f"{base_url}{endpoint}", data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        # Ignore errors for duplicate inserts and continue
        return None

print("=== Додавання нових Інвесторів (5 шт) ===")
investors_data = [
    {"full_name": "Павло Зібров", "email": "pablo@example.com", "phone": "+380671112233", "risk_tolerance": "high"},
    {"full_name": "Анна Романенко", "email": "anna@example.com", "phone": "+380501112233", "risk_tolerance": "low"},
    {"full_name": "Дмитро Марченко", "email": "dima@example.com", "phone": "+380931112233", "risk_tolerance": "medium"},
    {"full_name": "Тетяна Бойко", "email": "tanya@example.com", "phone": "+380991112233", "risk_tolerance": "medium"},
    {"full_name": "Віктор Мельник", "email": "viktor@example.com", "phone": "+380661112233", "risk_tolerance": "high"},
]
investor_ids = [1, 2] # previously created
for d in investors_data:
    resp = post("/investors/", d)
    if resp and "id" in resp:
        investor_ids.append(resp["id"])
        print(f"Created investor: {resp['full_name']}")

print("\n=== Додавання нових Портфелів (10 шт) ===")
portfolios_data = [
    {"name": "Пенсійні заощадження", "description": "На довгу перспективу"},
    {"name": "Спекулятивний криптопортфель", "description": "Лише високий ризик"},
    {"name": "Дивідендний", "description": "Акції з високими дивідендами"},
    {"name": "Тех сектора", "description": "Інвестиції в NASD"},
    {"name": "Міжнародний", "description": "ETFs з усього світу"},
    {"name": "Захисний портфель", "description": "Держоблігації та золото"},
    {"name": "Експериментальний", "description": "Штучний інтелект та робототехніка"},
    {"name": "Для дітей", "description": "Помірний ризик, довгострок"},
    {"name": "Синтетичний", "description": "Складні деривативи"},
    {"name": "Індексний портфель", "description": "S&P 500"},
]
portfolio_ids = [3, 4] # from previous script
for d in portfolios_data:
    d["investor_id"] = random.choice(investor_ids)
    resp = post("/portfolios/", d)
    if resp and "id" in resp:
        portfolio_ids.append(resp["id"])
        print(f"Created portfolio: {resp['name']}")

print("\n=== Додавання нових Активів (3 шт) ===")
assets_data = [
    {"ticker": "TSLA", "name": "Tesla Inc.", "asset_type": "stock", "current_price": 180.2, "currency": "USD"},
    {"ticker": "GLD", "name": "Gold ETF", "asset_type": "etf", "current_price": 215.1, "currency": "USD"},
    {"ticker": "ETH", "name": "Ethereum", "asset_type": "cryptocurrency", "current_price": 3100.5, "currency": "USD"},
]
asset_ids = [1, 2, 3] # from previous
for d in assets_data:
    resp = post("/assets/", d)
    if resp and "id" in resp:
        asset_ids.append(resp["id"])
        print(f"Created asset: {resp['name']}")

print("\n=== Додавання нових Транзакцій (20 шт) ===")
for i in range(20):
    t_type = random.choice(["buy", "sell"])
    data = {
        "portfolio_id": random.choice(portfolio_ids),
        "asset_id": random.choice(asset_ids),
        "transaction_type": t_type,
        "quantity": round(random.uniform(0.1, 15.0), 4),
        "price_per_unit": round(random.uniform(50.0, 3000.0), 2)
    }
    resp = post("/transactions/", data)
    if resp and "id" in resp:
        print(f"Created transaction: {t_type.upper()} {data['quantity']} units of asset {data['asset_id']} to portfolio {data['portfolio_id']}")

print("\n=== Усі додаткові дані успішно завантажені ===")
