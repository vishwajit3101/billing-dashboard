"""
Integration-style test: full pipeline flow with mocked DB and APIs.
Runs billing_fetcher -> posthog_processor -> compute_usage -> check_alerts in sequence
with shared mocks to simulate one hourly cycle.
"""
from unittest.mock import patch, MagicMock

import pytest

from src.jobs import fetch_billing, fetch_posthog, compute_usage, check_alerts


@pytest.fixture
def mock_cursor():
    cur = MagicMock()
    cur.execute = MagicMock()
    cur.fetchone = MagicMock(return_value={"id": 1})
    cur.fetchall = MagicMock(return_value=[])
    return cur


@pytest.fixture
def mock_cm(mock_cursor):
    cm = MagicMock()
    cm.__enter__.return_value = mock_cursor
    cm.__exit__.return_value = None
    return cm


@patch("src.jobs.check_alerts.get_cursor")
@patch("src.jobs.compute_usage.get_cursor")
@patch("src.jobs.compute_usage.get_event_credit_map")
@patch("src.jobs.fetch_posthog.posthog_client")
@patch("src.jobs.fetch_posthog.get_cursor")
@patch("src.jobs.fetch_billing.get_cursor")
@patch("src.jobs.fetch_billing.aws_cost_explorer")
@patch("src.jobs.fetch_billing.anthropic_billing")
@patch("src.jobs.fetch_billing.tavily_billing")
@patch("src.jobs.fetch_billing.fullenrich_billing")
@patch("src.jobs.fetch_billing.buyercaddy_billing")
def test_full_pipeline_flow(
    mock_buyercaddy,
    mock_fullenrich,
    mock_tavily,
    mock_anthropic,
    mock_aws,
    mock_get_cursor_fb,
    mock_get_cursor_fp,
    mock_posthog,
    mock_get_map,
    mock_get_cursor_cu,
    mock_get_cursor_ca,
    mock_cm,
    mock_cursor,
):
    """Run all four job handlers in order; each returns ok."""
    mock_get_cursor_fb.return_value = mock_cm
    mock_get_cursor_fp.return_value = mock_cm
    mock_get_cursor_cu.return_value = mock_cm
    mock_get_cursor_ca.return_value = mock_cm

    mock_anthropic.fetch_anthropic_billing.return_value = {"credits_remaining": 42350, "credits_total": 500000, "cost_this_month_usd": 4280.0}
    mock_tavily.fetch_tavily_billing.return_value = {"credits_remaining": 2800, "credits_total": 10000, "cost_this_month_usd": None}
    mock_fullenrich.fetch_fullenrich_billing.return_value = {"credits_remaining": 500, "credits_total": 5000, "cost_this_month_usd": None}
    mock_buyercaddy.fetch_buyercaddy_billing.return_value = {"credits_remaining": 6800, "credits_total": 8000, "cost_this_month_usd": None}
    mock_aws.fetch_aws_current_month_spend.return_value = {"period_start": "2025-02-01", "period_end": "2025-02-28", "total_spend_usd": 14100.0}
    mock_aws.fetch_aws_service_breakdown.return_value = [{"service_name": "EC2", "cost_usd": 5200.0}]

    mock_posthog.fetch_posthog_event_counts.return_value = [{"event_name": "ai_workflow_run", "date": __import__("datetime").date(2025, 2, 10), "count": 100}]
    mock_posthog.fetch_posthog_quota.return_value = {"events_today": 12450, "events_this_month": 847000, "monthly_limit": 1000000}
    mock_posthog.fetch_posthog_top_events.return_value = [{"name": "page_view", "count": 325000}]

    mock_get_map.return_value = [{"event_name": "ai_workflow_run", "tool_id": 1, "credits_per_event": 5}]

    r1 = fetch_billing.handler({}, None)
    assert r1["status"] == "ok"

    r2 = fetch_posthog.handler({}, None)
    assert r2["status"] == "ok"

    r3 = compute_usage.handler({}, None)
    assert r3["status"] == "ok"

    r4 = check_alerts.handler({}, None)
    assert r4["status"] == "ok"
