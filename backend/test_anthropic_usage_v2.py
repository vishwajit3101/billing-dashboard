
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_usage_cost_api():
    key = os.getenv("ANTHROPIC_ADMIN_KEY")
    org_id = os.getenv("ANTHROPIC_ORG_ID")
    
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        "https://api.anthropic.com/v1/organizations/usage_report/messages",
        "https://api.anthropic.com/v1/organizations/cost_report",
        f"https://api.anthropic.com/v1/organizations/{org_id}/usage_report/messages",
        f"https://api.anthropic.com/v1/organizations/{org_id}/cost_report"
    ]
    
    for url in endpoints:
        print(f"\n--- Testing: {url} ---")
        try:
            # Usage reports often require a POST or specific params, but let's try a GET first to see the error
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_usage_cost_api()
