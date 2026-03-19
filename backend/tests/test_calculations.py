# tests/test_calculations.py
# PRD Requirements: FR3, FR4, FR5, FR6, AC-02, AC-03, AC-04, AC-05, Section 11

import pytest
from datetime import date, timedelta
from app.calculations import calculate_exhaustion_date, calculate_risk_status, generate_alerts
from app.posthog import EVENT_CREDIT_MAPPING

def test_calculate_exhaustion_date_basic():
    # Basic: 1000 credits / 100 per day = 10 days from today
    today = date.today()
    expected = (today + timedelta(days=10)).isoformat()
    assert calculate_exhaustion_date(1000, 100) == expected

def test_calculate_exhaustion_date_rounding():
    # Partial day (1.1 days) must round UP to 2 days
    today = date.today()
    expected = (today + timedelta(days=2)).isoformat()
    assert calculate_exhaustion_date(110, 100) == expected

def test_calculate_exhaustion_date_zero_usage():
    assert calculate_exhaustion_date(1000, 0) is None
    assert calculate_exhaustion_date(1000, -10) is None

def test_calculate_exhaustion_date_zero_credits():
    assert calculate_exhaustion_date(0, 100) == date.today().isoformat()

def test_calculate_exhaustion_date_far_future():
    # Large credits / tiny usage = far future date
    # 10,000 days is about 27 years, safe for datetime.date
    res = calculate_exhaustion_date(1000, 0.1)
    assert res is not None
    assert int(res[:4]) > date.today().year + 20

def test_anthropic_exhaustion_scenario():
    # Anthropic scenario: 100 events × 5 credits = 500/day
    # 3500 credits / 500 per day = 7 days
    today = date.today()
    expected = (today + timedelta(days=7)).isoformat()
    assert calculate_exhaustion_date(3500, 100 * 5) == expected

def test_calculate_risk_status():
    # PRD Section 11: > 30% Safe, 10-30% Warning, < 10% Critical
    assert calculate_risk_status(80) == "Safe"
    assert calculate_risk_status(31) == "Safe"
    assert calculate_risk_status(30) == "Warning" # boundary
    assert calculate_risk_status(25) == "Warning"
    assert calculate_risk_status(10) == "Warning"
    assert calculate_risk_status(9) == "Critical"
    assert calculate_risk_status(0) == "Critical"

def test_generate_alerts_no_alerts():
    tools = [
        {"name": "Anthropic", "percent_remaining": 80, "daily_avg_usage": 100, "current_24h_usage": 50, "predicted_exhaustion": "2026-12-31"},
    ]
    aws = {"budget_pct": 50, "weekly_change": 5.0}
    assert generate_alerts(tools, aws) == []

def test_generate_alerts_low_credits():
    tools = [
        {"name": "FullEnrich", "percent_remaining": 9, "daily_avg_usage": 10},
        {"name": "Tavily", "percent_remaining": 19, "daily_avg_usage": 20}
    ]
    aws = {"budget_pct": 50}
    alerts = generate_alerts(tools, aws)
    
    assert any(a["severity"] == "critical" and "FullEnrich" in a["affected"] for a in alerts)
    assert any(a["severity"] == "warning" and "Tavily" in a["affected"] for a in alerts)

def test_generate_alerts_exhaustion_thresholds():
    today = date.today()
    tools = [
        {
            "name": "Anthropic", 
            "percent_remaining": 50, 
            "predicted_exhaustion": (today + timedelta(days=3)).isoformat()
        },
        {
            "name": "Tavily", 
            "percent_remaining": 50, 
            "predicted_exhaustion": (today + timedelta(days=5)).isoformat()
        },
        {
            "name": "FullEnrich", 
            "percent_remaining": 50, 
            "predicted_exhaustion": (today + timedelta(days=6)).isoformat()
        }
    ]
    aws = {"budget_pct": 50}
    alerts = generate_alerts(tools, aws)
    
    # Exhaustion in 3 and 5 days triggers alert, 6 days NO alert
    assert len([a for a in alerts if "exhaust in" in a["message"]]) == 2
    assert any("Anthropic" in a["affected"] and "3 days" in a["message"] for a in alerts)
    assert any("Tavily" in a["affected"] and "5 days" in a["message"] for a in alerts)

def test_generate_alerts_spike_detection():
    tools = [
        {"name": "Spiky", "percent_remaining": 50, "daily_avg_usage": 100, "current_24h_usage": 200},
        {"name": "Normal", "percent_remaining": 50, "daily_avg_usage": 100, "current_24h_usage": 150},
        {"name": "LowUsage", "percent_remaining": 50, "daily_avg_usage": 0.4, "current_24h_usage": 1.0}
    ]
    aws = {"budget_pct": 50}
    alerts = generate_alerts(tools, aws)
    
    assert any("Spiky" in a["affected"] and "spike" in a["message"].lower() for a in alerts)
    assert not any("Normal" in a["affected"] and "spike" in a["message"].lower() for a in alerts)
    assert not any("LowUsage" in a["affected"] and "spike" in a["message"].lower() for a in alerts)

def test_generate_alerts_aws():
    tools = []
    # Budget alert > 90
    aws_high = {"budget_pct": 91}
    alerts_high = generate_alerts(tools, aws_high)
    assert any("AWS" in a["affected"] and "budget" in a["message"].lower() for a in alerts_high)
    
    aws_90 = {"budget_pct": 90}
    assert generate_alerts(tools, aws_90) == []
    
    # Spike alert >= 100% change
    aws_spike = {"budget_pct": 50, "weekly_change": 100.0}
    alerts_spike = generate_alerts(tools, aws_spike)
    assert any("AWS" in a["affected"] and "spike" in a["message"].lower() for a in alerts_spike)

def test_generate_alerts_sorting():
    tools = [
        {"name": "WarningTool", "percent_remaining": 15},
        {"name": "CriticalTool", "percent_remaining": 5},
        {"name": "AlertTool", "percent_remaining": 50, "predicted_exhaustion": date.today().isoformat()}
    ]
    aws = {"budget_pct": 50}
    alerts = generate_alerts(tools, aws)
    
    # Sort order: critical (0), alert (1), warning (2)
    assert alerts[0]["severity"] == "critical"
    assert alerts[1]["severity"] == "alert"
    assert alerts[2]["severity"] == "warning"

def test_event_credit_mapping():
    # FR3 coverage
    assert EVENT_CREDIT_MAPPING["search_performed"] == ("Tavily", 1)
    assert EVENT_CREDIT_MAPPING["lead_enriched"] == ("FullEnrich", 2)
    assert EVENT_CREDIT_MAPPING["ai_workflow_run"] == ("Anthropic", 5)
    assert EVENT_CREDIT_MAPPING["data_fetched"] == ("Buyercaddy", 1)
    assert len(EVENT_CREDIT_MAPPING) == 4

def test_posthog_invisibility():
    # AC-05: PostHog is NOT visible anywhere
    tools = [{"name": "Anthropic", "percent_remaining": 5}]
    aws = {"budget_pct": 95}
    alerts = generate_alerts(tools, aws)
    import json
    content = json.dumps(alerts).lower()
    assert "posthog" not in content

@pytest.mark.parametrize("credits, usage", [(i*10, 1) for i in range(1, 31)])
def test_calculate_exhaustion_date_bulk(credits, usage):
    assert calculate_exhaustion_date(credits, usage) is not None

@pytest.mark.parametrize("percent, expected", [
    (0, "Critical"), (5, "Critical"), (9.9, "Critical"),
    (10.0, "Warning"), (15, "Warning"), (30.0, "Warning"),
    (30.1, "Safe"), (50, "Safe"), (100, "Safe"),
    (9.99, "Critical"), (10.01, "Warning"), (29.99, "Warning"),
    (30.01, "Safe"), (11, "Warning"), (25, "Warning"),
    (8, "Critical"), (40, "Safe"), (90, "Safe")
])
def test_calculate_risk_status_parametrized(percent, expected):
    assert calculate_risk_status(percent) == expected

@pytest.mark.parametrize("name", ["Anthropic", "Tavily", "FullEnrich", "Buyercaddy", "AWS", "Worker", "Optimizer", "Assistant"])
def test_generate_alerts_per_tool(name):
    tools = [{"name": name, "credits_remaining": 50, "total_credits": 1000, "percent_remaining": 5, "daily_avg_usage": 1}]
    alerts = generate_alerts(tools, {"budget_pct": 0})
    assert len(alerts) > 0
    assert alerts[0]["affected"] == name

@pytest.mark.parametrize("budget_pct", [96, 100, 105, 110, 120, 150, 200])
def test_generate_alerts_aws_parametrized(budget_pct):
    alerts = generate_alerts([], {"budget_pct": budget_pct})
    assert len(alerts) == 1
    assert "AWS" in alerts[0]["affected"]

def test_generate_alerts_sorting_extended():
    tools = [
        {"name": "C", "percent_remaining": 5, "daily_avg_usage": 1},
        {"name": "A", "percent_remaining": 5, "daily_avg_usage": 1},
        {"name": "B", "percent_remaining": 5, "daily_avg_usage": 1}
    ]
    alerts = generate_alerts(tools, {"budget_pct": 0})
    # The logic in calculations.py sorts ONLY by severity.
    # So the order for same severity is preserved from the input list.
    assert alerts[0]["affected"] == "C"
    assert alerts[1]["affected"] == "A"
    assert alerts[2]["affected"] == "B"

def test_generate_alerts_no_data_graceful():
    assert generate_alerts([], {}) == []
