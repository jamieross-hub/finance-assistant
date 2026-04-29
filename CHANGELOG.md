# Changelog

## v3.1.2 — 2026-04-29

### Fixed
- **`data_coach` — 5 permanently-locked insights**: `fire_timeline` required `preferences.fire_target_age` (non-existent key, now `fire_target`); `emergency_fund_adequacy` required phantom profile keys `savings_balance`/`monthly_expenses` (now `transactions:1mo`); `tax_optimization` and `tax_refund_estimate` required `tax_profile.tax_class` (German-only, locked for all US/UK/FR/NL/PL users, now `meta.locale`); `insurance_gap` required always-truthy `"employment"` dict (now `employment.annual_gross`).
- **US Additional Medicare Tax ignored filing status**: `estimate_fica()` always applied the single-filer $200k threshold regardless of filing status. MFJ filers at $240k were incorrectly told they owed Additional Medicare Tax ($250k threshold applies). MFS filers at $130k were incorrectly exempt ($125k threshold applies).
- **SE tax missing Additional Medicare**: `estimate_self_employment_tax()` did not apply the 0.9% Additional Medicare surtax on high-income self-employed filers — silently understating SE tax for earners above the threshold.
- **`tax_engine` missing `get_social_contributions()`**: The gateway layer had no proxy for FICA/social contribution queries, leaving SKILL.md's tool contract with a dead end.
- **Profile locale defaulted to `"de"`**: New users who skipped onboarding got German tax routing silently. Now defaults to `None` (no locale until explicitly set).
- **`--version` hardcoded `3.1.0`**: Version string now reads `3.1.2`.
- **`_setup_db()` swallowed all errors silently**: DB bootstrap failures now print to stderr.

### Security / Ops
- **`--doctor` now checks for `cryptography` package**: Missing package caused an obscure `ImportError` on first encrypt/decrypt; now a clear `fail` with the install command.
- **CI adds `ruff` lint step**: Catches type and style regressions that were invisible before.

### Tests
- **14 new tests**: 6 US bank CSV format detection/parsing tests (Chase, BofA, Wells Fargo, Mint, Monarch, Capital One); 3 Additional Medicare edge case tests; 5 `data_coach` insight catalog correctness tests.

### Docs
- **SKILL.md**: Mode count corrected (18, not 11); onboarding wizard corrected (9 steps, not 7); US state tax out-of-scope note added; `data_coach` and `session_alerts` added to Tool Contract.

---

## v3.1.1 — 2026-04-29

### New
- **US bank import** — Chase, Bank of America, Wells Fargo, Mint, Monarch Money, and Capital One CSV formats now auto-detected and parsed. Handles split Debit/Credit columns (Capital One), positional no-header format (Wells Fargo), and Mint's `Transaction Type` debit/credit convention.
- **Submodule doctor check** — `--doctor` now detects an uninitialised `locales/` submodule and prints the exact fix command.
- **Troubleshooting docs** — README and CONTRIBUTING.md both document the submodule init step and locale contribution workflow.

---

## v3.1.0 — 2026-04-29

### New
- **US locale** — federal income tax calculator for 2024/2025: brackets, standard deductions, FICA/Medicare, SE tax, 401(k)/HSA/IRA contribution limits, filing deadlines (including quarterly estimated payments for self-employed filers). All rules sourced from IRS Rev. Procs with provenance tracking.
- **Data coach** — progressive insight unlocking: after each data addition, the skill now surfaces what's available now and leads the conversation toward the next most valuable thing to add.
- **Conversational onboarding** — 9-step guided setup with warm value previews at each step, resumable mid-wizard, locale-aware tax prompts (DE/UK/FR/NL/PL/US).
- **SKILL.md triggers** — skill now auto-loads on natural finance keywords (budget, tax, savings, debt, FIRE, net worth, investments, etc.) without requiring explicit invocation.
- **CONTRIBUTING.md** — full guide for adding new locales and CSV importers.
- **Interactive HTML dashboard** — `python3 skill.py --dashboard` generates a fully-populated `~/.finance/dashboard.html` from real data with Chart.js visualizations, spending heatmap, scenario comparison, and cashflow forecast.

### Fixed
- US locale not in `ALLOWED_LOCALES` in `tax_engine.py` — US users crashed on any tax question.
- Additional Medicare Tax threshold was always $200k regardless of filing status (correct: $250k for MFJ, $125k for MFS).
- `withheld` field in US tax calculator now documented as federal income tax only (W-2 Box 2), with backward-compatible key `withheld_federal`.
- `decrypt_file()` now uses atomic write (tmp → rename), matching `encrypt_file()`. Previously could corrupt data on interrupted write.
- `ensure_gitignore_protection()` now walks up to find the actual git repo root instead of always using the immediate parent directory.
- `get_step_prompt()` locale defaulted to `"de"` — non-German users got German tax questions. Now defaults to generic fallback.
- Benchmark messages now include source year ("based on ECB HFCS 2021 data") so users understand the reference point.
- Investment onboarding prompt now uses the user's actual currency instead of hardcoded `€`, and removes German-specific broker example.

### Security
- `decrypt_sensitive_files()` now returns a `reminder` field; SKILL.md instructs Claude to surface it after every decryption.
- SKILL.md passphrase handling guidance added: Claude will never echo a passphrase, and recommends the `FINANCE_CRED_PASSPHRASE` env var.

---

## v3.0.0 — 2026-04-20

- SQLite as primary store (WAL mode), JSON kept as human-readable backup
- Monte Carlo projections (1,000-run simulation, p10/p50/p90 outcomes)
- Timeline engine: trend, seasonality, correlation, anomaly detection
- Financial journal, accountability engine, life events tracker
- 5 locales: DE, UK, FR, NL, PL
- 861 tests
