
import os
import requests
import json
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

def test_usage_report_post():
    key = os.getenv("ANTHROPIC_ADMIN_KEY")
    org_id = os.getenv("ANTHROPIC_ORG_ID")
    
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    # Usage reports often require a POST with a date range
    start_date = (date.today() - timedelta(days=7)).isoformat()
    
    data = {
        "start_date": start_date
    }
    
    endpoints = [
        "https://api.anthropic.com/v1/organizations/usage_report/messages",
        f"https://api.anthropic.com/v1/organizations/{org_id}/usage_report/messages"
    ]
    
    for url in endpoints:
        print(f"\n--- Testing POST: {url} ---")
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_usage_report_post()
