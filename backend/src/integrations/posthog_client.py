"""
PostHog API client: event counts by name and by day, quota (events today, this month, limit).
"""
import os
from datetime import date, timedelta
from typing import Any

def fetch_posthog_event_counts(
    project_id: str | None = None,
    api_key: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[dict[str, Any]]:
    """Fetch daily event counts per event name. Returns list of { event_name, date, count }."""
    # TODO: call PostHog Query API or export for event counts by day
    # https://posthog.com/docs/api
    return []


def fetch_posthog_quota(project_id: str | None = None, api_key: str | None = None) -> dict[str, Any]:
    """Events today, events this month, monthly limit (if available from PostHog or config)."""
    # TODO: from PostHog or app config
    return {
        "events_today": 12_450,
        "events_this_month": 847_320,
        "monthly_limit": 1_000_000,
    }


def fetch_posthog_top_events(
    project_id: str | None = None,
    api_key: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Top events by count for current month. Returns list of { name, count }."""
    # TODO: PostHog query
    return [
        {"name": "page_view", "count": 324_500},
        {"name": "button_click", "count": 186_200},
        {"name": "form_submit", "count": 89_400},
        {"name": "api_call", "count": 247_220},
    ]
