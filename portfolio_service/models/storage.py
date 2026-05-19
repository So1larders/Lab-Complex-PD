"""
In-memory сховище даних (імітація БД за допомогою словників).
"""
from typing import Dict
from portfolio_service.models.models import Investor, Asset, Portfolio, Transaction, Risk, Report

investors: Dict[int, Investor] = {}
assets: Dict[int, Asset] = {}
portfolios: Dict[int, Portfolio] = {}
transactions: Dict[int, Transaction] = {}
risks: Dict[int, Risk] = {}
reports: Dict[int, Report] = {}

# Автоінкрементні лічильники
_counters: Dict[str, int] = {
    "investor": 0,
    "asset": 0,
    "portfolio": 0,
    "transaction": 0,
    "risk": 0,
    "report": 0,
}


def next_id(entity: str) -> int:
    _counters[entity] += 1
    return _counters[entity]
