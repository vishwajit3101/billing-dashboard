# backend/test_spike_detection.py
import sys
import os
from datetime import date

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.calculations import generate_alerts

def test_tool_spike():
    print("--- Testing Tool Usage Spike ---")
    tools = [
        {
            "name": "Tavily",
            "percent_remaining": 50,
            "daily_avg_usage": 10.0,
            "current_24h_usage": 25.0,  # > 2x average
            "predicted_exhaustion": "2026-03-10"
        },
        {
            "name": "FullEnrich",
            "percent_remaining": 80,
            "daily_avg_usage": 5.0,
            "current_24h_usage": 6.0,   # < 2x average
            "predicted_exhaustion": "2026-04-01"
        }
    ]
    aws = {
        "percent_used": 15.0,
        "weekly_change": 10.5
    }
    
    alerts = generate_alerts(tools, aws)
    print(f"Generated {len(alerts)} alerts.")
    for a in alerts:
        print(f"[{a['type'].upper()}] {a['message']}")
    
    spike_detected = any("spike" in a["message"].lower() and "Tavily" in a["message"] for a in alerts)
    assert spike_detected, "Tavily spike alert missing!"
    print("✅ Tool spike detection verified.")

def test_aws_spike():
    print("\n--- Testing AWS Usage Spike ---")
    tools = [
        {
            "name": "Anthropic",
            "percent_remaining": 90,
            "daily_avg_usage": 100.0,
            "current_24h_usage": 120.0,
            "predicted_exhaustion": "2026-05-01"
        }
    ]
    aws = {
        "percent_used": 50.0,
        "weekly_change": 150.0 # > 100% (doubled)
    }
    
    alerts = generate_alerts(tools, aws)
    print(f"Generated {len(alerts)} alerts.")
    for a in alerts:
        print(f"[{a['type'].upper()}] {a['message']}")
        
    aws_spike = any("spike" in a["message"].lower() and "AWS" in a["message"] for a in alerts)
    assert aws_spike, "AWS spike alert missing!"
    print("✅ AWS spike detection verified.")

if __name__ == "__main__":
    try:
        test_tool_spike()
        test_aws_spike()
        print("\n✨ All spike detection tests PASSED!")
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
