# Contributing to Finance Assistant

Hey, glad you're here! This is an open project and contributions are very welcome. Here's everything you need to get started.

## Quick orientation

The project has two main extension points that tend to be the most useful:

1. **New locale** — add tax rules, filing deadlines, and deduction categories for a country
2. **New CSV importer** — teach the importer to recognise a bank's export format

Both are self-contained — you can add either without touching much else.

---

## Setting up locally

```bash
git clone --recurse-submodules https://github.com/googlarz/finance-assistant.git
cd finance-assistant
pip install -r requirements.txt
pip install pytest  # for running tests
```

Run the test suite to make sure everything's green before you start:

```bash
pytest
```

---

## Adding a new locale

Each country lives in `locales/<code>/` — look at `locales/de/` or `locales/uk/` as reference implementations. The US stub in `locales/us/` is a good starting point if you're adding the US locale.

### The files you need

```
locales/us/
├── __init__.py          ← the public interface (required)
├── tax_rules.py         ← rates, brackets, standard deductions by year
├── tax_calculator.py    ← compute refund/liability from a profile
├── tax_dates.py         ← filing deadlines
├── social_contributions.py  ← FICA, Medicare, etc.
├── claim_rules.py       ← which deductions apply given a profile
└── provenance.json      ← source URLs + verification dates for every rule
```

### The interface your `__init__.py` must export

```python
LOCALE_CODE = "us"
LOCALE_NAME = "United States"
SUPPORTED_YEARS = [2024, 2025]
CURRENCY = "USD"

def get_tax_rules(year: int) -> dict: ...
def calculate_tax(ctx, year: int = None) -> dict: ...
def get_filing_deadlines(year: int) -> list[dict]: ...
def get_social_contributions(gross: float, year: int) -> dict: ...
def get_deduction_categories() -> list[dict]: ...
def generate_tax_claims(ctx, year: int = None) -> list[dict]: ...
```

The `ctx` parameter is a `LocaleContext` (see `locales/context.py`) or a raw profile dict — your functions should handle both.

### provenance.json matters

Every numeric rule needs a source. Something like:

```json
{
  "standard_deduction_single_2024": {
    "value": 14600,
    "source": "IRS Rev. Proc. 2023-34",
    "url": "https://www.irs.gov/pub/irs-drop/rp-23-34.pdf",
    "verified": "2024-01-15"
  }
}
```

This isn't bureaucracy — it's what lets us update rules confidently year over year without playing telephone.

### Tests

Add a `locales/tests/test_locale_us.py`. At minimum, check:
- Tax calculation for a simple W-2 case (single, standard deduction)
- Filing deadline returns a date
- Social contributions returns FICA + Medicare split

Look at `locales/tests/test_locale_de.py` for the pattern.

---

## Adding a CSV importer

Bank CSV formats vary wildly — different delimiters, date formats, encodings, column names. The importer lives in `scripts/csv_importer.py`.

### Adding a new bank format

All you need is a format definition dict in `KNOWN_FORMATS`:

```python
KNOWN_FORMATS = {
    # ... existing formats ...
    "monarch_money": {
        "detect": ["Date", "Merchant", "Category", "Amount"],  # columns to fingerprint this format
        "date": "Date",
        "amount": "Amount",
        "description": "Original Statement",
        "payee": "Merchant",
        "category": "Category",
        "date_format": "%Y-%m-%d",
        "delimiter": ",",
        "encoding": "utf-8",
        "decimal": ".",
        "amount_sign": "signed",  # "signed" = negative is expense, or "debit_credit" for separate columns
    },
}
```

If your bank uses separate debit/credit columns or has quirks (skip rows, weird encodings), there's an escape hatch: add a `"parser": "custom"` key and a corresponding `_parse_<bankname>` function in the file. See `_parse_n26` for an example.

### Testing your importer

Drop a sanitised sample export (a few rows, no real account numbers) in `tests/fixtures/csv/` and add a test in `tests/test_import_csv.py`:

```python
def test_monarch_money_import():
    rows = import_csv("tests/fixtures/csv/monarch_money_sample.csv")
    assert len(rows) > 0
    assert rows[0]["amount"] < 0  # expenses are negative
    assert rows[0]["date"]  # ISO date string
```

### What "sanitised" means

Replace real merchant names with generic ones, zero out amounts if you want, but keep the structure and column layout intact. We just need something the parser can run against.

---

## Pull request checklist

- [ ] Tests pass locally (`pytest`)
- [ ] New code has tests
- [ ] `provenance.json` updated if you added/changed any financial rules
- [ ] No real personal data in fixtures

That's it. PRs don't need to be perfect — open early and we can iterate.

## Questions?

Just open an issue. Happy to help you get oriented.
