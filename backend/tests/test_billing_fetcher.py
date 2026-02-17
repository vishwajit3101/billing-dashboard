"""
Tests for billing fetcher Lambda (fetch_billing).
Mocks: DB (get_cursor), tool billing APIs, AWS Cost Explorer.
"""
from datetime import date, datetime
from unittest.mock import patch, MagicMock

import pytest

# Handler under test: src.jobs.fetch_billing (used by Terraform)
from src.jobs import fetch_billing


@pytest.fixture
def mock_tool_ids(mock_cursor):
    """Cursor returns tool id for each slug."""
    def fetchone():
        # Simulate one row per slug
        if mock_cursor.execute.call_count <= 4:
            return {"id": 1}
        return None
    mock_cursor.fetchone.side_effect = fetchone
    return mock_cursor


@pytest.fixture
def mock_billing_apis():
    """Mock tool billing API responses."""
    return {
        "anthropic": {"credits_remaining": 42350, "credits_total": 500000, "cost_this_month_usd": 4280.0},
        "tavily": {"credits_remaining": 2800, "credits_total": 10000, "cost_this_month_usd": None},
        "fullenrich": {"credits_remaining": 500, "credits_total": 5000, "cost_this_month_usd": None},
        "buyercaddy": {"credits_remaining": 6800, "credits_total": 8000, "cost_this_month_usd": None},
    }


@pytest.fixture
def mock_aws_spend():
    """Mock AWS Cost Explorer response."""
    return {
        "period_start": "2025-02-01",
        "period_end": "2025-02-28",
        "total_spend_usd": 14100.0,
    }


@pytest.fixture
def mock_aws_breakdown():
    return [
        {"service_name": "EC2", "cost_usd": 5200.0},
        {"service_name": "RDS", "cost_usd": 3800.0},
        {"service_name": "Other", "cost_usd": 5100.0},
    ]


@patch("src.jobs.fetch_billing.aws_cost_explorer")
@patch("src.jobs.fetch_billing.anthropic_billing")
@patch("src.jobs.fetch_billing.tavily_billing")
@patch("src.jobs.fetch_billing.fullenrich_billing")
@patch("src.jobs.fetch_billing.buyercaddy_billing")
@patch("src.jobs.fetch_billing.get_cursor")
def test_handler_returns_ok(
    mock_get_cursor,
    mock_buyercaddy,
    mock_fullenrich,
    mock_tavily,
    mock_anthropic,
    mock_aws,
    mock_cursor,
    mock_tool_ids,
    mock_billing_apis,
    mock_aws_spend,
    mock_aws_breakdown,
):
    mock_cursor.fetchone.return_value = {"id": 1}
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = None
    mock_get_cursor.return_value = mock_cm

    mock_anthropic.fetch_anthropic_billing.return_value = mock_billing_apis["anthropic"]
    mock_tavily.fetch_tavily_billing.return_value = mock_billing_apis["tavily"]
    mock_fullenrich.fetch_fullenrich_billing.return_value = mock_billing_apis["fullenrich"]
    mock_buyercaddy.fetch_buyercaddy_billing.return_value = mock_billing_apis["buyercaddy"]
    mock_aws.fetch_aws_current_month_spend.return_value = mock_aws_spend
    mock_aws.fetch_aws_service_breakdown.return_value = mock_aws_breakdown

    result = fetch_billing.handler({}, None)

    assert result["status"] == "ok"
    assert "snapshot_at" in result
    assert mock_cursor.execute.call_count >= 4  # tool snapshots + aws
    mock_anthropic.fetch_anthropic_billing.assert_called_once()
    mock_aws.fetch_aws_current_month_spend.assert_called_once()
    mock_aws.fetch_aws_service_breakdown.assert_called_once()


@patch("src.jobs.fetch_billing.aws_cost_explorer")
@patch("src.jobs.fetch_billing.anthropic_billing")
@patch("src.jobs.fetch_billing.tavily_billing")
@patch("src.jobs.fetch_billing.fullenrich_billing")
@patch("src.jobs.fetch_billing.buyercaddy_billing")
@patch("src.jobs.fetch_billing.get_cursor")
def test_handler_skips_missing_tools(
    mock_get_cursor,
    mock_buyercaddy,
    mock_fullenrich,
    mock_tavily,
    mock_anthropic,
    mock_aws,
    mock_cursor,
    mock_billing_apis,
    mock_aws_spend,
    mock_aws_breakdown,
):
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = None
    mock_get_cursor.return_value = mock_cm
    # First two slugs return id=1/2, rest None; then AWS INSERT RETURNING id
    mock_cursor.fetchone.side_effect = [{"id": 1}, {"id": 2}, None, None, {"id": 1}]

    mock_anthropic.fetch_anthropic_billing.return_value = mock_billing_apis["anthropic"]
    mock_tavily.fetch_tavily_billing.return_value = mock_billing_apis["tavily"]
    mock_fullenrich.fetch_fullenrich_billing.return_value = mock_billing_apis["fullenrich"]
    mock_buyercaddy.fetch_buyercaddy_billing.return_value = mock_billing_apis["buyercaddy"]
    mock_aws.fetch_aws_current_month_spend.return_value = mock_aws_spend
    mock_aws.fetch_aws_service_breakdown.return_value = mock_aws_breakdown

    result = fetch_billing.handler({}, None)

    assert result["status"] == "ok"
    mock_anthropic.fetch_anthropic_billing.assert_called_once()
    mock_tavily.fetch_tavily_billing.assert_called_once()
