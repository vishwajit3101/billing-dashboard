from unittest.mock import MagicMock, patch

from app import update_db_lambda


def _build_mock_connection():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur


@patch("app.update_db_lambda.send_alert_email")
@patch("app.update_db_lambda._insert_tool_snapshot")
@patch("app.update_db_lambda._record_provider_usage_delta")
@patch("app.update_db_lambda._get_existing_tool_snapshots")
@patch("app.update_db_lambda.get_db_connection")
def test_fullenrich_does_not_infer_usage_from_balance_drop(
    mock_get_db_connection,
    mock_existing_snapshots,
    mock_record_provider_usage_delta,
    mock_insert_tool_snapshot,
    mock_send_alert_email,
):
    mock_conn, _ = _build_mock_connection()
    mock_get_db_connection.return_value = mock_conn
    mock_existing_snapshots.return_value = {
        "FullEnrich": {"credits_remaining": 50.0, "total_credits": 50.0}
    }

    payload = {
        "today_date": "2026-03-31",
        "aws_spend": {"total_aws": 0.0, "services": []},
        "history_data": {},
        "tools_data": [
            {
                "name": "FullEnrich",
                "credits_remaining": 0.0,
                "total_credits": 50.0,
                "daily_avg_usage": 0.0,
                "percent_remaining": 0.0,
                "current_24h_usage": 0.0,
            }
        ],
    }

    response = update_db_lambda.lambda_handler(payload, None)

    assert response["statusCode"] == 200
    mock_record_provider_usage_delta.assert_not_called()
    mock_insert_tool_snapshot.assert_called_once()
    mock_send_alert_email.assert_called_once()


@patch("app.update_db_lambda.send_alert_email")
@patch("app.update_db_lambda._get_recent_daily_usage", return_value=3.5)
@patch("app.update_db_lambda._insert_tool_snapshot")
@patch("app.update_db_lambda._record_provider_usage_delta")
@patch("app.update_db_lambda._get_existing_tool_snapshots")
@patch("app.update_db_lambda.get_db_connection")
def test_buyercaddy_still_uses_balance_delta_fallback(
    mock_get_db_connection,
    mock_existing_snapshots,
    mock_record_provider_usage_delta,
    mock_insert_tool_snapshot,
    mock_get_recent_daily_usage,
    mock_send_alert_email,
):
    mock_conn, _ = _build_mock_connection()
    mock_get_db_connection.return_value = mock_conn
    mock_existing_snapshots.return_value = {
        "Buyercaddy": {"credits_remaining": 100.0, "total_credits": 100.0}
    }

    payload = {
        "today_date": "2026-03-31",
        "aws_spend": {"total_aws": 0.0, "services": []},
        "history_data": {},
        "tools_data": [
            {
                "name": "Buyercaddy",
                "credits_remaining": 90.0,
                "total_credits": 100.0,
                "daily_avg_usage": 0.0,
                "percent_remaining": 90.0,
                "current_24h_usage": 0.0,
            }
        ],
    }

    response = update_db_lambda.lambda_handler(payload, None)

    assert response["statusCode"] == 200
    mock_record_provider_usage_delta.assert_called_once()
    mock_get_recent_daily_usage.assert_called_once()
    mock_insert_tool_snapshot.assert_called_once()
    mock_send_alert_email.assert_not_called()
