"""
Credit exhaustion and risk calculation logic.
Uses datetime for date arithmetic.
"""
from datetime import date, timedelta
from typing import Literal

RiskLevel = Literal["safe", "warning", "critical"]


def compute_risk_level(credits_remaining: float, credits_total: float | None) -> RiskLevel:
    """
    Determine risk from percentage remaining.
    >30% = Safe, 20-30% = Warning, <20% = Critical.
    """
    if credits_total is None or credits_total <= 0:
        return "safe"
    pct_remaining = (credits_remaining / credits_total) * 100
    if pct_remaining > 30:
        return "safe"
    if pct_remaining > 20:
        return "warning"
    return "critical"


def compute_days_left(credits_remaining: float, avg_daily_usage: float) -> float | None:
    """
    days_left = credits_remaining / avg_daily_usage.
    Returns None if avg_daily_usage <= 0 (infinite or undefined).
    """
    if avg_daily_usage <= 0:
        return None
    return credits_remaining / avg_daily_usage


def compute_exhaustion_date(
    current_date: date,
    credits_remaining: float,
    avg_daily_usage: float,
) -> date | None:
    """
    exhaustion_date = current_date + days_left (whole days).
    Returns None if avg_daily_usage <= 0.
    """
    days = compute_days_left(credits_remaining, avg_daily_usage)
    if days is None:
        return None
    days_int = max(0, int(round(days)))
    return current_date + timedelta(days=days_int)


def compute_all(
    credits_remaining: float,
    credits_total: float | None,
    avg_daily_usage: float,
    current_date: date,
) -> dict:
    """
    Return dict with risk_level, percent_remaining, days_left, exhaustion_date.
    """
    risk_level = compute_risk_level(credits_remaining, credits_total)
    percent_remaining = (
        (credits_remaining / credits_total * 100) if credits_total and credits_total > 0 else None
    )
    days_left = compute_days_left(credits_remaining, avg_daily_usage)
    exhaustion_date = compute_exhaustion_date(current_date, credits_remaining, avg_daily_usage)
    return {
        "risk_level": risk_level,
        "percent_remaining": round(percent_remaining, 2) if percent_remaining is not None else None,
        "days_left": round(days_left, 2) if days_left is not None else None,
        "exhaustion_date": exhaustion_date.isoformat() if exhaustion_date else None,
        "avg_daily_usage": round(avg_daily_usage, 2),
    }
