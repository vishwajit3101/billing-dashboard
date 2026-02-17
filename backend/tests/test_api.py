"""
Tests for dashboard API Lambda: routing, endpoints (get_tools, get_aws_spend, get_alerts, get_export).
Mocks: DB (get_cursor). Integration-style tests for full request/response.
"""
import json
from datetime import date
from unittest.mock import patch, MagicMock

import pytest

# Add backend to path so we can import handler and endpoints
import sys
import os
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# Import after path fix
from lambda_functions.dashboard_api import handler as api_handler
from lambda_functions.dashboard_api import endpoints


@pytest.fixture
def mock_cursor_for_api():
    cur = MagicMock()
    cur.execute = MagicMock()
    cur.fetchone = MagicMock(return_value=None)
    cur.fetchall = MagicMock(return_value=[])
    return cur


@pytest.fixture
def mock_get_cursor_api(mock_cursor_for_api):
    def _get_cursor(dict_cursor=True):
        cm = MagicMock()
        cm.__enter__.return_value = mock_cursor_for_api
        cm.__exit__.return_value = None
        return cm
    return _get_cursor, mock_cursor_for_api


@patch("lambda_functions.dashboard_api.endpoints.get_cursor")
def test_get_tools_returns_structure(mock_get_cursor, mock_get_cursor_api):
    get_cursor_fn, cur = mock_get_cursor_api
    mock_get_cursor.side_effect = get_cursor_fn
    # Tools from ai_tools joined with credit_snapshots; then avg_daily from usage_logs
    cur.fetchall.side_effect = [
        [{"id": 1, "slug": "anthropic", "name": "Anthropic", "description": "Claude", "risk_level": "critical", "credits_remaining": 42350, "credits_total": 500000, "cost_usd": 100.5}],
        [],  # avg_daily
    ]

    result = endpoints.get_tools()

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert "tools" in body
    assert "meta" in body
    assert body["meta"]["count"] >= 0


@patch("lambda_functions.dashboard_api.endpoints.get_cursor")
def test_get_tool_trend_404_unknown_tool(mock_get_cursor, mock_get_cursor_api):
    get_cursor_fn, cur = mock_get_cursor_api
    mock_get_cursor.side_effect = get_cursor_fn
    cur.fetchone.return_value = None  # tool not found

    result = endpoints.get_tool_trend("unknown_tool", 7)

    assert result["statusCode"] == 404
    body = json.loads(result["body"])
    assert body.get("error") == "tool_not_found"


@patch("lambda_functions.dashboard_api.endpoints.get_cursor")
def test_get_tool_trend_returns_trend(mock_get_cursor, mock_get_cursor_api):
    get_cursor_fn, cur = mock_get_cursor_api
    mock_get_cursor.side_effect = get_cursor_fn
    cur.fetchone.return_value = {"id": 1}
    cur.fetchall.return_value = [
        {"date": date(2025, 2, 10), "value": 15000},
        {"date": date(2025, 2, 11), "value": 16200},
    ]

    result = endpoints.get_tool_trend("anthropic", 7)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["tool_id"] == "anthropic"
    assert "trend" in body
    assert len(body["trend"]) == 2


@patch("lambda_functions.dashboard_api.endpoints.get_cursor")
def test_get_aws_spend_returns_structure(mock_get_cursor, mock_get_cursor_api):
    get_cursor_fn, cur = mock_get_cursor_api
    mock_get_cursor.side_effect = get_cursor_fn
    # Order: current_spend, prev_spend, budget, then 6x trend fetchone
    cur.fetchone.side_effect = [
        {"total": 14100.0},
        {"total": 12000.0},
        {"monthly_limit_usd": 12000.0},
    ] + [{"total": 1000.0}] * 6
    cur.fetchall.return_value = [
        {"service": "EC2", "cost": 5200.0},
        {"service": "RDS", "cost": 3800.0},
    ]

    result = endpoints.get_aws_spend()

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert "current_spend_usd" in body
    assert "budget_usd" in body
    assert "cost_by_service" in body
    assert "status" in body


@patch("lambda_functions.dashboard_api.endpoints.get_cursor")
def test_get_alerts_returns_list(mock_get_cursor, mock_get_cursor_api):
    from datetime import datetime
    get_cursor_fn, cur = mock_get_cursor_api
    mock_get_cursor.side_effect = get_cursor_fn
    cur.fetchall.return_value = [
        {"id": 1, "tool_id": 1, "tool_slug": "anthropic", "tool_name": "Anthropic", "alert_type": "credits_critical", "message": "Credits Critical", "threshold": 10, "triggered_at": datetime(2025, 2, 10, 12, 0), "payload": None},
    ]

    result = endpoints.get_alerts()

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert "alerts" in body
    assert "meta" in body


@patch("lambda_functions.dashboard_api.endpoints.get_cursor")
def test_get_export_returns_csv(mock_get_cursor, mock_get_cursor_api):
    get_cursor_fn, cur = mock_get_cursor_api
    mock_get_cursor.side_effect = get_cursor_fn
    cur.fetchall.side_effect = [
        [{"slug": "anthropic", "name": "Anthropic", "current_credits": 42350}],
        [],
    ]

    result = endpoints.get_export(range_param="7d", fmt="csv")

    assert result["statusCode"] == 200
    assert "text/csv" in result.get("headers", {}).get("Content-Type", "")
    assert "tool" in result["body"] or "credits" in result["body"].lower()


# --- Handler routing (API Gateway event) ---
@patch("lambda_functions.dashboard_api.handler.get_tools")
def test_handler_routes_get_tools(mock_get_tools):
    mock_get_tools.return_value = {"statusCode": 200, "headers": {}, "body": "{}"}
    event = {"rawPath": "/api/tools", "requestContext": {"http": {"method": "GET"}}, "pathParameters": None, "queryStringParameters": None}

    result = api_handler.handler(event, None)

    assert result["statusCode"] == 200
    mock_get_tools.assert_called_once()


@patch("lambda_functions.dashboard_api.handler.get_aws_spend")
def test_handler_routes_get_aws_spend(mock_get_aws_spend):
    mock_get_aws_spend.return_value = {"statusCode": 200, "headers": {}, "body": "{}"}
    event = {"rawPath": "/api/aws/spend", "requestContext": {"http": {"method": "GET"}}, "pathParameters": None, "queryStringParameters": None}

    result = api_handler.handler(event, None)

    assert result["statusCode"] == 200
    mock_get_aws_spend.assert_called_once()


def test_handler_returns_404_unknown_path():
    event = {"rawPath": "/api/unknown", "requestContext": {"http": {"method": "GET"}}, "pathParameters": None, "queryStringParameters": None}

    result = api_handler.handler(event, None)

    assert result["statusCode"] == 404
    body = json.loads(result["body"])
    assert body.get("error") == "not_found"


def test_handler_options_returns_204():
    event = {"requestContext": {"http": {"method": "OPTIONS"}}}

    result = api_handler.handler(event, None)

    assert result["statusCode"] == 204
    assert "Access-Control-Allow-Origin" in result.get("headers", {})
