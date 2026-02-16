"""
Risk logic: credit status (safe/warning/critical), AWS status, exhaustion.
PRD: >30% safe, 20–30% warning, <10% critical.
"""
from typing import Literal

Status = Literal["healthy", "warning", "critical"]


def compute_credit_status(credits_remaining: float, credits_total: float) -> Status:
    """Compute status from remaining/total credits (by percentage remaining)."""
    if credits_total <= 0:
        return "healthy"
    pct_remaining = (credits_remaining / credits_total) * 100
    if pct_remaining < 10:
        return "critical"
    if pct_remaining < 20:
        return "warning"
    return "healthy"


def compute_aws_status(current_spend: float, budget: float) -> Status:
    """Over budget = critical; >=90% = warning; else healthy."""
    if budget <= 0:
        return "healthy"
    pct = (current_spend / budget) * 100
    if current_spend > budget:
        return "critical"
    if pct >= 90:
        return "warning"
    return "healthy"


def compute_posthog_status(events_this_month: int, monthly_limit: int) -> Status:
    """>90% = critical, >70% = warning."""
    if monthly_limit <= 0:
        return "healthy"
    pct = (events_this_month / monthly_limit) * 100
    if pct > 90:
        return "critical"
    if pct > 70:
        return "warning"
    return "healthy"
