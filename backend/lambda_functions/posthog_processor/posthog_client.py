"""
PostHog API client: fetch event counts by event name for a time range.
Uses PostHog Query API (HogQL) for aggregation.
"""
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)

POSTHOG_HOST = os.environ.get("POSTHOG_HOST", "https://us.posthog.com").rstrip("/")
POSTHOG_PROJECT_ID = os.environ.get("POSTHOG_PROJECT_ID", "")
POSTHOG_API_KEY = os.environ.get("POSTHOG_API_KEY", "")  # Personal API key with Query read


def get_event_counts_last_24h() -> dict[str, int]:
    """
    Query PostHog for event counts in the last 24 hours, grouped by event name.
    Returns dict: event_name -> count (only events that exist; missing events are omitted).
    """
    if not POSTHOG_PROJECT_ID or not POSTHOG_API_KEY:
        logger.warning("POSTHOG_PROJECT_ID or POSTHOG_API_KEY not set")
        return {}

    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=24)
    start_str = start.strftime("%Y-%m-%d %H:%M:%S")
    end_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # HogQL: count events by name in the time window
    query = f"""
        SELECT event, count() AS event_count
        FROM events
        WHERE timestamp >= toDateTime('{start_str}')
          AND timestamp < toDateTime('{end_str}')
        GROUP BY event
        LIMIT 1000
    """
    url = f"{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/query/"
    headers = {
        "Authorization": f"Bearer {POSTHOG_API_KEY}",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {
        "kind": "HogQLQuery",
        "query": query.strip(),
    }

    try:
        logger.info("PostHog query: last 24h event counts")
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        logger.exception("PostHog API request failed: %s", e)
        return {}
    except ValueError as e:
        logger.warning("PostHog API invalid JSON: %s", e)
        return {}

    # Parse result: columns ["event", "event_count"], rows list of lists
    result = data.get("results") or []
    columns = data.get("columns") or []
    try:
        event_idx = columns.index("event") if "event" in columns else 0
        count_idx = columns.index("event_count") if "event_count" in columns else 1
    except (ValueError, AttributeError):
        event_idx, count_idx = 0, 1

    out: dict[str, int] = {}
    for row in result:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        event_name = str(row[event_idx]) if row[event_idx] is not None else ""
        try:
            count = int(row[count_idx])
        except (TypeError, ValueError):
            count = 0
        if event_name:
            out[event_name] = count
    logger.info("PostHog returned %d event types, total events=%d", len(out), sum(out.values()))
    return out


def get_event_counts_for_date(target_date: "date") -> dict[str, int]:
    """
    Query PostHog for event counts for a single calendar day (UTC).
    Returns dict: event_name -> count.
    """
    if not POSTHOG_PROJECT_ID or not POSTHOG_API_KEY:
        logger.warning("POSTHOG_PROJECT_ID or POSTHOG_API_KEY not set")
        return {}

    from datetime import date as date_type
    if isinstance(target_date, date_type):
        start_dt = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)
    else:
        start_dt = target_date
        end_dt = target_date + timedelta(days=1) if hasattr(target_date, "__add__") else target_date

    start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    query = f"""
        SELECT event, count() AS event_count
        FROM events
        WHERE timestamp >= toDateTime('{start_str}')
          AND timestamp < toDateTime('{end_str}')
        GROUP BY event
        LIMIT 1000
    """
    url = f"{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/query/"
    headers = {
        "Authorization": f"Bearer {POSTHOG_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {"kind": "HogQLQuery", "query": query.strip()}

    try:
        logger.info("PostHog query: event counts for %s", start_str[:10])
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        logger.exception("PostHog API request failed: %s", e)
        return {}
    except ValueError as e:
        logger.warning("PostHog API invalid JSON: %s", e)
        return {}

    result = data.get("results") or []
    columns = data.get("columns") or []
    try:
        event_idx = columns.index("event") if "event" in columns else 0
        count_idx = columns.index("event_count") if "event_count" in columns else 1
    except (ValueError, AttributeError):
        event_idx, count_idx = 0, 1

    out = {}
    for row in result:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        event_name = str(row[event_idx]) if row[event_idx] is not None else ""
        try:
            count = int(row[count_idx])
        except (TypeError, ValueError):
            count = 0
        if event_name:
            out[event_name] = count
    return out
