# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.x     | ✅ Yes    |
| < 3.0   | ❌ No     |

## Reporting a Vulnerability

Finance Assistant handles sensitive personal financial data. We take security seriously.

**Do not report security vulnerabilities through public GitHub issues.**

To report a vulnerability:

1. Email **security@[your-domain]** with subject: `[Finance Assistant] Security Report`
2. Include: description, reproduction steps, potential impact, and any suggested fix
3. We will acknowledge within 48 hours and provide a timeline for a fix

Alternatively, use [GitHub's private vulnerability reporting](https://github.com/googlarz/finance-assistant/security/advisories/new).

## Security Model

Finance Assistant is a local-first tool. All financial data stays on your machine:

- Data stored in `~/.finance/` — never uploaded anywhere
- Sensitive files encrypted at rest with Fernet (AES-128-CBC + HMAC)
- File permissions hardened to `chmod 600` / `chmod 700`
- No telemetry, no analytics, no external calls (except optional exchange rate fetches)
- SQLite WAL mode with `foreign_keys=ON`

## Known Limitations

- State and local taxes are not modeled (US locale covers federal only)
- Exchange rate data is fetched from external APIs — these calls can be intercepted on untrusted networks; use `FINANCE_OFFLINE=1` to disable
- PDF import uses local OCR only — no cloud OCR

## Dependency Updates

We aim to update dependencies within 30 days of a disclosed CVE. Pin your install with `pip install -r requirements.txt` to avoid unintentional upgrades.
