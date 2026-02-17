"""
Tests for alert engine Lambda (check_alerts).
Mocks: DB (get_cursor), risk helpers.
"""
from unittest.mock import patch, MagicMock

import pytest

from src.jobs import check_alerts


@patch("src.jobs.check_alerts.get_cursor")
def test_handler_returns_ok(mock_get_cursor, mock_cursor):
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = None
    mock_get_cursor.return_value = mock_cm

    result = check_alerts.handler({}, None)

    assert result["status"] == "ok"
    assert "checked_at" in result
    # Handler may or may not call get_cursor depending on implementation (TODO in check_alerts)


@patch("src.jobs.check_alerts.get_cursor")
def test_handler_accepts_empty_event(mock_get_cursor, mock_cursor):
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = None
    mock_get_cursor.return_value = mock_cm

    result = check_alerts.handler({}, None)
    assert result["status"] == "ok"

    result2 = check_alerts.handler({"source": "eventbridge"}, None)
    assert result2["status"] == "ok"
