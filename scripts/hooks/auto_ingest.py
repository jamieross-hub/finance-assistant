#!/usr/bin/env python3
"""
UserPromptSubmit hook — auto-detect and ingest financial data from user prompts.

Runs before Claude sees the message. Parses structured data, saves it,
then injects a summary into Claude's context via additionalContext.
No tmp files. No Stop hook needed.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

# Add scripts dir to path
_SCRIPTS = Path(__file__).parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


# ── Finance keyword detection ─────────────────────────────────────────────────

_TRANSACTION = re.compile(
    r"\b(spent|paid|bought|purchased|charged|cost|fee|expense|bill|invoice|"
    r"received|earned|income|salary|bonus|refund|cashback)\b",
    re.IGNORECASE,
)
_BALANCE = re.compile(
    r"\b(balance|account|savings?|checking|current account|isa|401k|pension|"
    r"portfolio|holding|asset|net worth)\b",
    re.IGNORECASE,
)
_DEBT = re.compile(
    r"\b(mortgage|loan|debt|credit card|overdraft|owe|owing|repay|installment)\b",
    re.IGNORECASE,
)
_INVESTMENT = re.compile(
    r"\b(shares?|stocks?|etf|fund|units?|bonds?|crypto|btc|eth|invested?|"
    r"dividend|yield|return|gain|loss)\b",
    re.IGNORECASE,
)
_AMOUNT = re.compile(
    r"(?:€|\$|£|PLN|EUR|USD|GBP)\s*\d+|\d+\s*(?:€|\$|£|PLN|EUR|USD|GBP)|"
    r"\b\d{1,3}(?:[,\.]\d{3})*(?:\.\d{1,2})?\b",
)

def classify(text: str) -> list[str]:
    types = []
    if _TRANSACTION.search(text):
        types.append("transaction")
    if _BALANCE.search(text):
        types.append("balance")
    if _DEBT.search(text):
        types.append("debt")
    if _INVESTMENT.search(text):
        types.append("investment")
    # Only flag if there's an actual amount too — avoids false positives
    if types and not _AMOUNT.search(text):
        types = []
    return types


# ── Extraction helpers ────────────────────────────────────────────────────────

_AMOUNT_RE = re.compile(
    r"(€|\$|£|PLN|EUR|USD|GBP)?\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?)\s*(€|\$|£|PLN|EUR|USD|GBP)?",
    re.IGNORECASE,
)
_DATE_RE = re.compile(
    r"\b(today|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?)\b",
    re.IGNORECASE,
)
_CATEGORY_RE = re.compile(
    r"\b(groceries?|food|supermarket|restaurant|cafe|coffee|transport|"
    r"uber|taxi|fuel|petrol|rent|utilities|gas|electricity|water|"
    r"subscriptions?|netflix|spotify|gym|health|pharmacy|doctor|"
    r"clothing|shopping|entertainment|travel|hotel|flight|insurance)\b",
    re.IGNORECASE,
)

def extract_amount(text: str) -> tuple[float | None, str]:
    m = _AMOUNT_RE.search(text)
    if not m:
        return None, "EUR"
    raw = m.group(2).replace(",", "").replace(" ", "")
    currency_sym = m.group(1) or m.group(3) or ""
    currency_map = {"€": "EUR", "$": "USD", "£": "GBP"}
    currency = currency_map.get(currency_sym, currency_sym.upper() or "EUR")
    try:
        return float(raw), currency
    except ValueError:
        return None, currency

def extract_category(text: str) -> str:
    m = _CATEGORY_RE.search(text)
    return m.group(1).lower() if m else "other"

def extract_description(text: str) -> str:
    # First sentence or first 60 chars
    first = re.split(r"[.!?]", text)[0].strip()
    return first[:60] if len(first) > 60 else first


# ── Ingestion ─────────────────────────────────────────────────────────────────

def ingest(prompt: str, types: list[str]) -> list[str]:
    saved = []

    if "transaction" in types:
        try:
            from transaction_logger import add_transaction
            amount, currency = extract_amount(prompt)
            if amount is not None:
                category = extract_category(prompt)
                description = extract_description(prompt)
                # Expenses are negative
                sign = -1 if _TRANSACTION.search(prompt).group(1).lower() in (
                    "spent", "paid", "bought", "purchased", "charged", "cost",
                    "fee", "expense", "bill", "invoice"
                ) else 1
                add_transaction(
                    date.today().isoformat(),
                    "expense" if sign < 0 else "income",
                    round(sign * amount, 2),
                    category,
                    description,
                )
                saved.append(
                    f"transaction saved: {sign * amount:+.2f} {currency} "
                    f"({category}) — \"{description}\""
                )
        except Exception:
            pass

    return saved


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        return

    prompt = (data.get("prompt") or data.get("message") or "").strip()
    if not prompt or len(prompt) < 8:
        return

    types = classify(prompt)
    if not types:
        return

    saved = ingest(prompt, types)

    if saved:
        context = "Auto-saved from your message:\n" + "\n".join(f"  • {s}" for s in saved)
        out = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        }
        print(json.dumps(out))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # Never block the session
