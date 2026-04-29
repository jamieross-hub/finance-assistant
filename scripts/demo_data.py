"""
Demo data seeder for Finance Assistant.

Creates a realistic sample dataset for "Alex" — a Berlin-based renter.
Idempotent: skips if demo data already exists (detected by "DKB Demo" account).
"""

from __future__ import annotations

import os
import sys
import random

# Ensure scripts/ is importable when run standalone
sys.path.insert(0, os.path.dirname(__file__))

from profile_manager import update_profile
from account_manager import list_accounts, add_account
from transaction_logger import add_transaction
from goal_tracker import add_goal
from debt_optimizer import add_debt
from investment_tracker import add_holding


def seed_demo_data() -> bool:
    """Seed demo data. Returns True if seeded, False if already exists."""
    # Idempotency check
    accounts = list_accounts()
    if any(a.get("name") == "DKB Demo" for a in accounts):
        return False

    _seed_profile()
    account_ids = _seed_accounts()
    _seed_transactions(account_ids["checking"])
    _seed_goals(account_ids["savings"])
    _seed_debts()
    _seed_investments(account_ids["depot"])
    return True


def _seed_profile() -> None:
    update_profile({
        "personal": {"name": "Alex"},
        "employment": {"annual_gross": 58000},
        "housing": {"type": "renter", "monthly_cost": 1100, "city": "Berlin"},
        "tax_profile": {"filing_status": "single"},
        "meta": {"country": "DE", "locale": "de", "created": True},
    })


def _seed_accounts() -> dict:
    checking = add_account({
        "id": "dkb-demo",
        "name": "DKB Demo",
        "type": "checking",
        "current_balance": 4200.0,
        "currency": "EUR",
        "institution": "DKB",
    })
    savings = add_account({
        "id": "ing-savings-demo",
        "name": "ING Savings Demo",
        "type": "savings",
        "current_balance": 12800.0,
        "currency": "EUR",
        "institution": "ING",
    })
    depot = add_account({
        "id": "scalable-depot-demo",
        "name": "Scalable Depot Demo",
        "type": "investment",
        "current_balance": 24500.0,
        "currency": "EUR",
        "institution": "Scalable Capital",
    })
    return {
        "checking": checking["id"],
        "savings": savings["id"],
        "depot": depot["id"],
    }


def _seed_transactions(account_id: str) -> None:
    from datetime import date, timedelta

    today = date.today()
    # Generate 6 months of transactions
    monthly_data = [
        # (income, housing, groceries, transport, restaurants, subscriptions)
        (3100, 1100, 295, 89, 185, 45),
        (3100, 1100, 310, 89, 210, 45),
        (3100, 1100, 280, 89, 165, 45),
        (3100, 1100, 305, 89, 195, 45),
        (3100, 1100, 318, 89, 175, 45),
        (3100, 1100, 290, 89, 220, 45),
    ]

    for months_ago, (income, rent, groceries, transport, restaurants, subs) in enumerate(reversed(monthly_data)):
        # Approximate first of month
        month_offset = today.replace(day=15) - timedelta(days=months_ago * 30)
        ym = month_offset.strftime("%Y-%m")

        add_transaction(f"{ym}-01", "income", income, "salary", "Salary Alex", account_id)
        add_transaction(f"{ym}-02", "expense", -rent, "housing", "Miete Berlin", account_id)
        add_transaction(f"{ym}-05", "expense", -groceries, "groceries", "REWE Einkauf", account_id)
        add_transaction(f"{ym}-10", "expense", -transport, "transport", "BVG Ticket", account_id)
        add_transaction(f"{ym}-15", "expense", -restaurants, "restaurants", "Restaurant & Café", account_id)
        add_transaction(f"{ym}-20", "expense", -subs, "subscriptions", "Streaming & Cloud Abo", account_id)
        add_transaction(f"{ym}-25", "expense", -120, "miscellaneous", "Misc Ausgaben", account_id)


def _seed_goals(savings_account_id: str) -> None:
    add_goal({
        "id": "demo-emergency-fund",
        "name": "Emergency Fund",
        "type": "emergency_fund",
        "target_amount": 15000.0,
        "current_amount": 12800.0,
        "currency": "EUR",
        "monthly_contribution": 200.0,
        "linked_account_id": savings_account_id,
        "priority": "high",
    })
    add_goal({
        "id": "demo-japan-trip",
        "name": "Japan Trip",
        "type": "travel",
        "target_amount": 3000.0,
        "current_amount": 840.0,
        "currency": "EUR",
        "monthly_contribution": 140.0,
        "target_date": "2026-04-01",
        "priority": "medium",
    })


def _seed_debts() -> None:
    add_debt({
        "id": "demo-credit-card",
        "name": "Credit Card Demo",
        "type": "credit_card",
        "balance": 2100.0,
        "interest_rate": 18.9,
        "minimum_payment": 63.0,
        "currency": "EUR",
    })


def _seed_investments(depot_account_id: str) -> None:
    add_holding({
        "id": "demo-world-etf",
        "name": "World ETF",
        "symbol": "WORLD",
        "type": "etf",
        "units": 120.0,
        "cost_basis": 120 * 190.0,   # average cost basis ~190
        "current_value": 120 * 204.0,
        "currency": "EUR",
        "account_id": depot_account_id,
    })
