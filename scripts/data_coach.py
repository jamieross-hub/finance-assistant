"""
Data Coach — progressive insight unlocking.

Maps what data the user has provided to insights available now,
and surfaces the single highest-value "add X → unlock Y" nudge.
"""

from __future__ import annotations

from typing import Optional

# ── Insight Catalog ───────────────────────────────────────────────────────────

_INSIGHTS = [
    {
        "id": "savings_rate_benchmark",
        "name": "Savings rate vs peers",
        "requires": ["employment.annual_gross", "transactions:1mo"],
        "unlocked_by": "one month of transactions",
        "teaser": "How your savings rate stacks up against people in your income bracket — and whether you're ahead or leaving money on the table.",
        "domain": "budget",
    },
    {
        "id": "tax_optimization",
        "name": "Tax optimization opportunities",
        "requires": ["employment.annual_gross", "tax_profile.tax_class"],
        "unlocked_by": "your Steuerklasse",
        "teaser": "Exactly how much you're leaving on the table in unclaimed deductions, and the 3 most valuable ones for your situation.",
        "domain": "tax",
    },
    {
        "id": "budget_vs_actual",
        "name": "Budget vs actual",
        "requires": ["budget", "transactions:1mo"],
        "unlocked_by": "one month of transactions",
        "teaser": "A category-by-category bar chart of what you planned vs what you actually spent — and which categories need attention.",
        "domain": "budget",
    },
    {
        "id": "fire_timeline",
        "name": "FIRE timeline",
        "requires": ["employment.annual_gross", "investments", "preferences.fire_target_age"],
        "unlocked_by": "your target retirement age",
        "teaser": "Your projected FIRE year and probability — including the exact monthly savings needed to hit your target age.",
        "domain": "investments",
    },
    {
        "id": "debt_avalanche",
        "name": "Debt payoff strategy",
        "requires": ["debts:2"],
        "unlocked_by": "a second debt entry",
        "teaser": "The optimal payoff order for your debts and exactly how much interest you save vs the minimum-payment path.",
        "domain": "debt",
    },
    {
        "id": "emergency_fund_adequacy",
        "name": "Emergency fund check",
        "requires": ["savings_balance", "monthly_expenses"],
        "unlocked_by": "your savings balance",
        "teaser": "How many months of expenses you can cover and whether you're in the danger zone, the safe zone, or over-saving on cash.",
        "domain": "cashflow",
    },
    {
        "id": "housing_affordability",
        "name": "Housing affordability",
        "requires": ["housing.monthly_cost", "employment.annual_gross"],
        "unlocked_by": "your housing cost",
        "teaser": "Your housing cost as a percentage of income — and whether you're in the comfort zone, stretched, or have room to breathe.",
        "domain": "housing",
    },
    {
        "id": "net_worth_trend",
        "name": "Net worth trajectory",
        "requires": ["transactions:3mo"],
        "unlocked_by": "three months of data",
        "teaser": "Your 12-month net worth trajectory — where you'll be if nothing changes, and what one habit shift would do.",
        "domain": "net_worth",
    },
    {
        "id": "investment_allocation",
        "name": "Investment allocation review",
        "requires": ["holdings:2"],
        "unlocked_by": "a second holding",
        "teaser": "Your current allocation pie and a specific rebalancing suggestion based on your risk profile and timeline.",
        "domain": "investments",
    },
    {
        "id": "cashflow_forecast",
        "name": "90-day cash flow forecast",
        "requires": ["transactions:2mo"],
        "unlocked_by": "two months of transactions",
        "teaser": "A 90-day projection of your account balance — including upcoming predictable expenses and your likely buffer at month-end.",
        "domain": "cashflow",
    },
    {
        "id": "category_spending",
        "name": "Spending trends by category",
        "requires": ["transactions:2mo"],
        "unlocked_by": "two months of transactions",
        "teaser": "Your top 5 spending categories with month-over-month trends — so you can see exactly where the creep is happening.",
        "domain": "cashflow",
    },
    {
        "id": "rent_vs_buy",
        "name": "Rent vs buy analysis",
        "requires": ["housing.monthly_cost", "employment.annual_gross", "goals:house"],
        "unlocked_by": "a home purchase goal",
        "teaser": "The break-even timeline for buying vs renting in your area — and what down payment you'd need to make buying worth it.",
        "domain": "housing",
    },
    {
        "id": "insurance_gap",
        "name": "Insurance coverage gaps",
        "requires": ["employment", "family", "insurance"],
        "unlocked_by": "your insurance details",
        "teaser": "The specific coverage gaps in your current setup and which ones expose you to meaningful financial risk.",
        "domain": "insurance",
    },
    {
        "id": "tax_refund_estimate",
        "name": "Tax refund estimate",
        "requires": ["employment.annual_gross", "tax_profile.tax_class", "meta.locale"],
        "unlocked_by": "your tax class",
        "teaser": "Your estimated tax refund for this year and the 3 deductions most people in your situation miss.",
        "domain": "tax",
    },
]

# Domain priority for nudge ranking (lower index = higher priority)
_DOMAIN_PRIORITY = ["tax", "debt", "investments", "cashflow", "budget", "goals", "housing", "net_worth", "insurance"]


# ── Field Checkers ────────────────────────────────────────────────────────────

def _get_nested(profile: dict, path: str):
    """Traverse a dotted path like 'employment.annual_gross'."""
    parts = path.split(".")
    obj = profile
    for part in parts:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def _check_field(profile: dict, field: str, db_conn=None) -> bool:
    """Check if a required field is satisfied."""
    # Special: "transactions:Nmo" — needs N+ months of transactions
    if field.startswith("transactions:"):
        months_needed = int(field.split(":")[1].replace("mo", ""))
        try:
            if db_conn is None:
                try:
                    from db import get_conn
                    with get_conn() as conn:
                        return _check_transactions_months(conn, months_needed)
                except Exception:
                    return False
            return _check_transactions_months(db_conn, months_needed)
        except Exception:
            return False

    # Special: "goals:N" — needs at least N active goals (or type like "goals:house")
    if field.startswith("goals:"):
        suffix = field.split(":", 1)[1]
        try:
            if suffix.isdigit():
                count_needed = int(suffix)
                if db_conn is None:
                    try:
                        from db import get_conn
                        with get_conn() as conn:
                            return _check_goals_count(conn, count_needed)
                    except Exception:
                        return False
                return _check_goals_count(db_conn, count_needed)
            else:
                # Named goal type — check profile goals list
                goals = profile.get("goals", [])
                return any(
                    suffix.lower() in str(g.get("name", "")).lower()
                    or suffix.lower() in str(g.get("type", "")).lower()
                    for g in (goals if isinstance(goals, list) else [])
                )
        except Exception:
            return False

    # Special: "debts:N" — needs at least N debt entries
    if field.startswith("debts:"):
        count_needed = int(field.split(":")[1])
        try:
            if db_conn is None:
                try:
                    from db import get_conn
                    with get_conn() as conn:
                        return _check_debts_count(conn, count_needed)
                except Exception:
                    # Fall back to profile
                    debts = profile.get("debts", [])
                    return len(debts if isinstance(debts, list) else []) >= count_needed
            return _check_debts_count(db_conn, count_needed)
        except Exception:
            return False

    # Special: "holdings:N" — needs at least N investment holdings
    if field.startswith("holdings:"):
        count_needed = int(field.split(":")[1])
        try:
            if db_conn is None:
                try:
                    from db import get_conn
                    with get_conn() as conn:
                        return _check_holdings_count(conn, count_needed)
                except Exception:
                    investments = profile.get("investments", [])
                    return len(investments if isinstance(investments, list) else []) >= count_needed
            return _check_holdings_count(db_conn, count_needed)
        except Exception:
            return False

    # Simple top-level keys (no dot)
    if "." not in field:
        val = profile.get(field)
        if val is None:
            return False
        if isinstance(val, (list, dict)):
            return len(val) > 0
        if isinstance(val, bool):
            return val
        return bool(val)

    # Dotted path
    val = _get_nested(profile, field)
    if val is None:
        return False
    if isinstance(val, (list, dict)):
        return len(val) > 0
    if isinstance(val, bool):
        return val
    return bool(val)


def _check_transactions_months(conn, months_needed: int) -> bool:
    try:
        cursor = conn.execute(
            "SELECT COUNT(DISTINCT strftime('%Y-%m', date)) FROM transactions"
        )
        row = cursor.fetchone()
        return row is not None and (row[0] or 0) >= months_needed
    except Exception:
        return False


def _check_goals_count(conn, count_needed: int) -> bool:
    try:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM goals WHERE status = 'active'"
        )
        row = cursor.fetchone()
        return row is not None and (row[0] or 0) >= count_needed
    except Exception:
        return False


def _check_debts_count(conn, count_needed: int) -> bool:
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM debts")
        row = cursor.fetchone()
        return row is not None and (row[0] or 0) >= count_needed
    except Exception:
        return False


def _check_holdings_count(conn, count_needed: int) -> bool:
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM holdings")
        row = cursor.fetchone()
        return row is not None and (row[0] or 0) >= count_needed
    except Exception:
        return False


# ── Public API ────────────────────────────────────────────────────────────────

def get_available_insights(profile: dict, conn=None) -> list[dict]:
    """Return all insights whose requirements are fully met."""
    if not profile:
        return []
    available = []
    for insight in _INSIGHTS:
        if all(_check_field(profile, req, conn) for req in insight["requires"]):
            available.append(insight)
    return available


def get_locked_insights(profile: dict, conn=None) -> list[dict]:
    """Return insights not yet available, with missing_field attached."""
    if not profile:
        return [dict(insight, missing_field=insight["requires"][0]) for insight in _INSIGHTS]
    locked = []
    for insight in _INSIGHTS:
        missing = [req for req in insight["requires"] if not _check_field(profile, req, conn)]
        if missing:
            locked.append(dict(insight, missing_field=missing[0], missing_count=len(missing)))
    return locked


def get_unlock_nudge(profile: dict, conn=None) -> Optional[dict]:
    """
    Return the single highest-value unlock opportunity.

    Priority:
    1. Insights that need only 1 more data point
    2. Higher-domain priority: tax > debt > investments > cashflow > budget > goals > housing

    Returns a dict with keys: add, unlocks, lead, how
    Returns None if all insights are already available.
    """
    if not profile:
        profile = {}

    locked = get_locked_insights(profile, conn)
    if not locked:
        return None

    # Focus on insights that need just 1 more field
    one_away = [i for i in locked if i.get("missing_count", len(i["requires"])) == 1]
    candidates = one_away if one_away else locked

    # Group by missing_field so we can show all insights unlocked by the same addition
    from collections import defaultdict
    by_missing: dict[str, list] = defaultdict(list)
    for insight in candidates:
        by_missing[insight["missing_field"]].append(insight)

    # Score each missing field: domain priority of best insight in the group
    def _best_priority(insights_list):
        best = len(_DOMAIN_PRIORITY)  # lower is better
        for ins in insights_list:
            try:
                p = _DOMAIN_PRIORITY.index(ins["domain"])
            except ValueError:
                p = len(_DOMAIN_PRIORITY)
            best = min(best, p)
        return best

    best_field = min(by_missing.keys(), key=lambda f: _best_priority(by_missing[f]))
    group = by_missing[best_field]

    # Build human-readable "add" description from the missing field
    add_label = _field_to_human(best_field)
    unlock_names = [i["name"] for i in group]

    # Lead sentence: use the teaser of the highest-priority insight
    best_insight = min(group, key=lambda i: _DOMAIN_PRIORITY.index(i["domain"])
                       if i["domain"] in _DOMAIN_PRIORITY else 99)
    lead = best_insight["teaser"]
    if len(unlock_names) > 1:
        others = unlock_names[1:]
        plural = "insight" if len(others) == 1 else "insights"
        lead += f" Plus {len(others)} more {plural}: {', '.join(others)}."

    return {
        "add": add_label,
        "unlocks": unlock_names,
        "lead": lead,
        "how": _field_to_how(best_field),
    }


def format_nudge(nudge: dict) -> str:
    """Format nudge for display in conversation."""
    if not nudge:
        return ""
    unlocks_str = ", ".join(nudge["unlocks"])
    lines = [
        f"**Unlock more insights:** Add {nudge['add']} and I can show you: {unlocks_str}.",
        nudge["lead"],
    ]
    if nudge.get("how"):
        lines.append(f"_{nudge['how']}_")
    return "\n".join(lines)


# ── Human-readable labels ─────────────────────────────────────────────────────

_FIELD_LABELS = {
    "employment.annual_gross": "your gross annual income",
    "employment": "your employment details",
    "tax_profile.tax_class": "your Steuerklasse (tax class)",
    "meta.locale": "your country/region",
    "housing.monthly_cost": "your monthly housing cost",
    "preferences.fire_target_age": "your target retirement age",
    "investments": "at least one investment or holding",
    "budget": "a monthly budget",
    "savings_balance": "your current savings balance",
    "monthly_expenses": "your average monthly expenses",
    "family": "your family/household details",
    "insurance": "your insurance policies",
    "transactions:1mo": "one month of bank transactions",
    "transactions:2mo": "two months of bank transactions",
    "transactions:3mo": "three months of bank transactions",
    "goals:1": "at least one savings goal",
    "goals:house": "a home purchase goal",
    "debts:2": "a second debt entry",
    "holdings:2": "a second investment holding",
}

_FIELD_HOW = {
    "employment.annual_gross": "Say 'my salary is €X/year' or update your employment details.",
    "tax_profile.tax_class": "Say 'my Steuerklasse is X' (1–6) to set your tax class.",
    "housing.monthly_cost": "Say 'my rent is €X/month' or 'my mortgage is €X/month'.",
    "preferences.fire_target_age": "Say 'I want to retire at 45' (or any age).",
    "investments": "Say 'I have €X in ETFs' or 'add holding [name] €X'.",
    "budget": "Say 'set up a budget' and I'll walk you through it.",
    "savings_balance": "Say 'my savings account has €X'.",
    "transactions:1mo": "Say 'import [filename]' or 'log [transaction]' to start.",
    "transactions:2mo": "Import or log transactions for at least 2 months.",
    "transactions:3mo": "Import or log transactions for at least 3 months.",
    "goals:1": "Say 'I want to save for X by Y' to add your first goal.",
    "goals:house": "Say 'I want to buy a house' to add a home purchase goal.",
    "debts:2": "Say 'add debt [name] €X at X%' to add another debt.",
    "holdings:2": "Say 'add holding [name] €X' to add another investment.",
    "tax_profile.tax_class": "Say 'my Steuerklasse is X' (1–6).",
    "meta.locale": "Say 'I'm in Germany' or 'set country to DE'.",
}


def _field_to_human(field: str) -> str:
    return _FIELD_LABELS.get(field, field.replace(".", " → ").replace("_", " "))


def _field_to_how(field: str) -> str:
    return _FIELD_HOW.get(field, "Update your profile to add this data.")
