"""
Tests for risk calculator / compute usage Lambda (compute_usage).
Mocks: DB (get_cursor), event_credit_map.
"""
from unittest.mock import patch, MagicMock

import pytest

from src.jobs import compute_usage


@patch("src.jobs.compute_usage.get_event_credit_map")
@patch("src.jobs.compute_usage.get_cursor")
def test_handler_returns_ok(mock_get_cursor, mock_get_map, mock_cursor):
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = None
    mock_get_cursor.return_value = mock_cm
    mock_get_map.return_value = []  # empty mapping

    result = compute_usage.handler({}, None)

    assert result["status"] == "ok"
    assert "computed_at" in result
    mock_get_map.assert_called_once_with(load_from_db=True)
    mock_get_cursor.assert_called_once()


@patch("src.jobs.compute_usage.get_event_credit_map")
@patch("src.jobs.compute_usage.get_cursor")
def test_handler_uses_cursor(mock_get_cursor, mock_get_map, mock_cursor):
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = None
    mock_get_cursor.return_value = mock_cm
    mock_get_map.return_value = [{"event_name": "ai_workflow_run", "tool_id": 1, "credits_per_event": 5}]

    compute_usage.handler({}, None)

    mock_get_cursor.assert_called_once()
