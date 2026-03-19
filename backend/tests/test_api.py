# tests/test_api.py
# PRD Requirements: FR7, FR9, FR10, AC-01, AC-03, AC-05

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from datetime import date, timedelta
import json

client = TestClient(app)

MOCK_TOOLS_DB = [
    ("Anthropic",  8000.0, 80.0, 50.0, 10000.0),
    ("Tavily",     1500.0, 15.0, 20.0, 10000.0),
    ("FullEnrich",  900.0,  9.0, 10.0, 10000.0),
    ("Buyercaddy", 5000.0, 50.0, 30.0, 10000.0),
]

MOCK_AWS = {
    "current_spend": 120.0, 
    "budget": 174.56, 
    "budget_pct": 68.7,
    "monthly_trend": [{"month": "2026-03", "label": "Mar", "spend": 120.0}], 
    "cost_by_service": [
        {"service": "EC2", "amount": 60.0},
        {"service": "RDS", "amount": 40.0}
    ],
    "status": "Safe", 
    "weekly_change": 5.0,
}

def get_fresh_mock_db():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    # first call fetchall() returns tools_rows, second call history_rows
    mock_cur.fetchall.side_effect = [MOCK_TOOLS_DB, []] 
    mock_conn.cursor.return_value = mock_cur
    return mock_conn

@patch("app.main.get_db_connection")
@patch("app.aws_cost.get_aws_data")
@patch("app.main.send_alert_email")
@patch("app.buyercaddy.get_buyercaddy_usage_metrics")
@patch("app.buyercaddy.get_buyercaddy_history")
def test_get_dashboard(mock_bc_history, mock_bc_metrics, mock_email, mock_aws, mock_db):
    mock_db.side_effect = get_fresh_mock_db
    mock_aws.return_value = MOCK_AWS
    mock_bc_metrics.return_value = {"avg_daily_usage": 30.0}
    mock_bc_history.return_value = []

    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.json()

    # Response has keys
    expected_keys = {"tools", "aws", "alerts", "alert_count", "last_updated", "filtered_days", "date_range"}
    assert all(k in data for k in expected_keys)

    # All 4 tool names present
    tool_names = [t["name"] for t in data["tools"]]
    assert all(name in tool_names for name in ["Anthropic", "Tavily", "FullEnrich", "Buyercaddy"])

    # Each tool has fields
    for tool in data["tools"]:
        assert "credits_remaining" in tool
        assert "percent_remaining" in tool
        assert "daily_avg_usage" in tool
        assert "predicted_exhaustion" in tool
        assert "status" in tool
        assert "history" in tool

    # AWS has fields
    assert "current_spend" in data["aws"]
    assert "budget" in data["aws"]
    assert "budget_pct" in data["aws"]
    assert "cost_by_service" in data["aws"]

    # Status check
    tavily = next(t for t in data["tools"] if t["name"] == "Tavily")
    assert tavily["status"] == "Warning" # 15%
    fullenrich = next(t for t in data["tools"] if t["name"] == "FullEnrich")
    assert fullenrich["status"] == "Critical" # 9%
    anthropic = next(t for t in data["tools"] if t["name"] == "Anthropic")
    assert anthropic["status"] == "Safe" # 80%

    # Alert count
    assert data["alert_count"] > 0
    assert len(data["alerts"]) == data["alert_count"]

    # PostHog invisibility AC-05
    assert "posthog" not in response.text.lower()

@patch("app.main.get_db_connection")
@patch("app.aws_cost.get_aws_data")
def test_dashboard_days_filter(mock_aws, mock_db):
    mock_db.side_effect = get_fresh_mock_db
    mock_aws.return_value = MOCK_AWS

    # ?days=7
    response = client.get("/dashboard?days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["filtered_days"] == 7
    expected_from = (date.today() - timedelta(days=6)).isoformat()
    assert data["date_range"]["from"] == expected_from

    # ?days=30
    response = client.get("/dashboard?days=30")
    assert response.json()["filtered_days"] == 30

    # ?days=0 -> 422
    assert client.get("/dashboard?days=0").status_code == 422
    # ?days=91 -> 422
    assert client.get("/dashboard?days=91").status_code == 422

@patch("app.main.get_db_connection")
@patch("app.aws_cost.get_aws_data")
@patch("app.main.send_alert_email")
def test_get_alerts(mock_email, mock_aws, mock_db):
    mock_db.side_effect = get_fresh_mock_db
    mock_aws.return_value = MOCK_AWS

    response = client.get("/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert "count" in data
    assert "timestamp" in data

    # send_alert_email called exactly once when alerts exist
    mock_email.assert_called_once()
    
    # posthog invisibility
    assert "posthog" not in response.text.lower()

@patch("app.main.get_db_connection")
@patch("app.aws_cost.get_aws_data")
def test_get_alerts_critical_only(mock_aws, mock_db):
    mock_db.side_effect = get_fresh_mock_db
    mock_aws.return_value = MOCK_AWS

    response = client.get("/alerts?critical_only=true")
    data = response.json()
    for alert in data["alerts"]:
        assert alert["severity"] == "critical"

@patch("app.main.get_db_connection")
@patch("app.aws_cost.get_aws_data")
def test_export_report(mock_aws, mock_db):
    mock_db.side_effect = get_fresh_mock_db
    mock_aws.return_value = MOCK_AWS

    # format=json
    response_json = client.get("/export?format=json")
    assert response_json.status_code == 200
    assert "posthog" not in response_json.text.lower()

    # format=csv
    response_csv = client.get("/export?format=csv")
    assert response_csv.status_code == 200
    assert "text/csv" in response_csv.headers["content-type"]
    assert "attachment" in response_csv.headers["content-disposition"]
    assert ".csv" in response_csv.headers["content-disposition"]
    
    csv_text = response_csv.text
    # All 4 tool names in body text
    assert all(name in csv_text for name in ["Anthropic", "Tavily", "FullEnrich", "Buyercaddy"])
    # EC2 and RDS in body text
    assert "EC2" in csv_text
    assert "RDS" in csv_text
    # First line headers (individual parts)
    assert "Type" in csv_text
    assert "Name/Service" in csv_text
    assert "Credits/Amount" in csv_text
    assert "Status" in csv_text

    # format=xml -> 422
    assert client.get("/export?format=xml").status_code == 422

    # format=xml -> 422
    assert client.get("/export?format=xml").status_code == 422
