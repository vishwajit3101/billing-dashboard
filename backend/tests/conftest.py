"""
Pytest fixtures: mock DB cursor, mock API clients, shared test helpers.
"""
import json
from contextlib import contextmanager
from datetime import date, datetime
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_cursor():
    """Fake DB cursor that records execute() calls and returns configurable fetchall/fetchone."""
    cur = MagicMock()
    cur.execute = MagicMock()
    cur.fetchone = MagicMock(return_value=None)
    cur.fetchall = MagicMock(return_value=[])
    cur.__enter__ = MagicMock(return_value=cur)
    cur.__exit__ = MagicMock(return_value=None)
    return cur


@pytest.fixture
def mock_get_cursor(mock_cursor):
    """Context manager that yields mock_cursor when get_cursor() is used."""

    @contextmanager
    def _get_cursor(dict_cursor=True):
        yield mock_cursor

    return _get_cursor


@pytest.fixture
def sample_tools_rows():
    """Rows as returned by ai_tools / tools query (RealDictCursor style)."""
    return [
        {"id": 1, "slug": "anthropic", "name": "Anthropic", "description": "Claude API", "current_credits": 42350, "credits_total": 500000, "risk_level": "critical"},
        {"id": 2, "slug": "tavily", "name": "Tavily", "description": "Search API", "current_credits": 2800, "credits_total": 10000, "risk_level": "warning"},
    ]


@pytest.fixture
def sample_usage_rows():
    """Rows for usage_logs (tool_id, usage_date, credits_consumed)."""
    return [
        {"tool_id": 1, "usage_date": date(2025, 2, 10), "credits_consumed": 15000},
        {"tool_id": 1, "usage_date": date(2025, 2, 11), "credits_consumed": 16200},
    ]


@pytest.fixture
def api_gateway_event():
    """Minimal API Gateway (v2) event for GET /api/tools."""
    return {
        "version": "2.0",
        "routeKey": "GET /api/tools",
        "rawPath": "/api/tools",
        "requestContext": {"http": {"method": "GET"}},
        "pathParameters": None,
        "queryStringParameters": None,
    }
