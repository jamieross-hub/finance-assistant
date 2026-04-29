# Changelog

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
