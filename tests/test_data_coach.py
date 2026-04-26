"""Tests for data_coach.py — progressive insight unlocking."""

from __future__ import annotations

import sys
import os

# Ensure scripts/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from data_coach import (
    get_available_insights,
    get_locked_insights,
    get_unlock_nudge,
    format_nudge,
)


# ── get_available_insights ────────────────────────────────────────────────────

def test_available_empty_profile():
    """Empty profile yields no available insights."""
    result = get_available_insights({})
    assert result == []


def test_available_none_profile():
    """None profile yields no available insights."""
    result = get_available_insights(None)
    assert result == []


def test_available_housing_affordability():
    """housing_affordability unlocks when income + housing cost are set."""
    profile = {
        "housing": {"monthly_cost": 1200},
        "employment": {"annual_gross": 60000},
    }
    result = get_available_insights(profile)
    ids = [i["id"] for i in result]
    assert "housing_affordability" in ids


def test_available_housing_not_unlocked_without_income():
    """housing_affordability requires both fields."""
    profile = {"housing": {"monthly_cost": 1200}}
    result = get_available_insights(profile)
    ids = [i["id"] for i in result]
    assert "housing_affordability" not in ids


# ── get_locked_insights ───────────────────────────────────────────────────────

def test_locked_all_on_empty_profile():
    """All insights are locked on an empty profile."""
    from data_coach import _INSIGHTS
    result = get_locked_insights({})
    assert len(result) == len(_INSIGHTS)


def test_locked_has_missing_field():
    """Each locked insight has a missing_field key."""
    result = get_locked_insights({})
    for item in result:
        assert "missing_field" in item


def test_locked_decreases_with_data():
    """Adding data reduces the locked count."""
    empty = get_locked_insights({})
    with_data = get_locked_insights({
        "housing": {"monthly_cost": 1200},
        "employment": {"annual_gross": 60000},
    })
    assert len(with_data) < len(empty)


# ── get_unlock_nudge ──────────────────────────────────────────────────────────

def test_nudge_returns_none_when_all_available(monkeypatch):
    """get_unlock_nudge returns None when there are no locked insights."""
    monkeypatch.setattr("data_coach.get_locked_insights", lambda p, conn=None: [])
    result = get_unlock_nudge({})
    assert result is None


def test_nudge_returns_valid_dict():
    """get_unlock_nudge returns a dict with required keys for a sparse profile."""
    nudge = get_unlock_nudge({})
    assert nudge is not None
    assert "add" in nudge
    assert "unlocks" in nudge
    assert "lead" in nudge
    assert "how" in nudge


def test_nudge_unlocks_is_list():
    """nudge['unlocks'] is a non-empty list of strings."""
    nudge = get_unlock_nudge({})
    assert isinstance(nudge["unlocks"], list)
    assert len(nudge["unlocks"]) >= 1
    assert all(isinstance(name, str) for name in nudge["unlocks"])


def test_nudge_prioritises_tax_domain():
    """With income but no tax class, nudge should target tax domain."""
    profile = {"employment": {"annual_gross": 65000}}
    nudge = get_unlock_nudge(profile)
    assert nudge is not None
    # tax_optimization needs tax_class — should surface tax nudge
    assert any("tax" in u.lower() or "steuer" in u.lower() for u in nudge["unlocks"] + [nudge["add"]])


# ── format_nudge ──────────────────────────────────────────────────────────────

def test_format_nudge_non_empty():
    """format_nudge returns a non-empty string for a valid nudge."""
    nudge = get_unlock_nudge({})
    assert nudge is not None
    result = format_nudge(nudge)
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_nudge_empty_dict():
    """format_nudge returns empty string for empty dict."""
    result = format_nudge({})
    assert result == ""


def test_format_nudge_contains_unlock_names():
    """format_nudge output mentions the insight names."""
    nudge = get_unlock_nudge({})
    assert nudge is not None
    result = format_nudge(nudge)
    # At least the first unlock name should appear
    assert nudge["unlocks"][0] in result or nudge["unlocks"][0].lower() in result.lower()
