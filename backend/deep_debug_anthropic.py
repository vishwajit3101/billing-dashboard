
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def deep_debug():
    key = os.getenv("ANTHROPIC_ADMIN_KEY")
    org_id = os.getenv("ANTHROPIC_ORG_ID")
    
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    print("--- Verifying Org Status ---")
    resp_me = requests.get("https://api.anthropic.com/v1/organizations/me", headers=headers)
    print(f"Me Status: {resp_me.status_code}")
    print(f"Me Body: {resp_me.text}")

    endpoints = [
        "https://api.anthropic.com/v1/billing/balance",
        "https://api.anthropic.com/v1/billing/credits",
        f"https://api.anthropic.com/v1/organizations/{org_id}/billing/balance",
        f"https://api.anthropic.com/v1/organizations/{org_id}/billing",
        "https://api.anthropic.com/v1/stats/usage",
    ]
    
    for url in endpoints:
        print(f"\n--- Testing Endpoint: {url} ---")
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {resp.status_code}")
            print(f"Text: {resp.text[:500]}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    deep_debug()
