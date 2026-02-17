"""
Tests for PostHog processor Lambda (fetch_posthog).
Mocks: DB (get_cursor), PostHog client.
"""
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from src.jobs import fetch_posthog


@pytest.fixture
def mock_posthog_counts():
    """Mock event counts from PostHog API."""
    return [
        {"event_name": "search_performed", "date": date(2025, 2, 10), "count": 100},
        {"event_name": "ai_workflow_run", "date": date(2025, 2, 10), "count": 50},
    ]


@pytest.fixture
def mock_posthog_quota():
    return {"events_today": 12450, "events_this_month": 847000, "monthly_limit": 1000000}


@pytest.fixture
def mock_posthog_top_events():
    return [
        {"name": "page_view", "count": 325000},
        {"name": "api_call", "count": 247000},
    ]


@patch("src.jobs.fetch_posthog.posthog_client")
@patch("src.jobs.fetch_posthog.get_cursor")
def test_handler_returns_ok(
    mock_get_cursor,
    mock_posthog,
    mock_cursor,
    mock_posthog_counts,
    mock_posthog_quota,
    mock_posthog_top_events,
):
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = None
    mock_get_cursor.return_value = mock_cm

    mock_posthog.fetch_posthog_event_counts.return_value = mock_posthog_counts
    mock_posthog.fetch_posthog_quota.return_value = mock_posthog_quota
    mock_posthog.fetch_posthog_top_events.return_value = mock_posthog_top_events

    result = fetch_posthog.handler({}, None)

    assert result["status"] == "ok"
    assert "snapshot_at" in result
    mock_posthog.fetch_posthog_event_counts.assert_called_once()
    mock_posthog.fetch_posthog_quota.assert_called_once()
    mock_posthog.fetch_posthog_top_events.assert_called_once()
    assert mock_cursor.execute.call_count >= 1


@patch("src.jobs.fetch_posthog.posthog_client")
@patch("src.jobs.fetch_posthog.get_cursor")
def test_handler_calls_db_with_event_counts(
    mock_get_cursor,
    mock_posthog,
    mock_cursor,
    mock_posthog_counts,
    mock_posthog_quota,
    mock_posthog_top_events,
):
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = None
    mock_get_cursor.return_value = mock_cm
    mock_posthog.fetch_posthog_event_counts.return_value = mock_posthog_counts
    mock_posthog.fetch_posthog_quota.return_value = mock_posthog_quota
    mock_posthog.fetch_posthog_top_events.return_value = mock_posthog_top_events

    fetch_posthog.handler({}, None)

    # Should INSERT event counts (ON CONFLICT DO UPDATE), quota, top events
    calls = [str(c) for c in mock_cursor.execute.call_args_list]
    assert any("posthog_event_counts" in c or "event_name" in c for c in calls)
