
import os
import requests
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

ANTHROPIC_ADMIN_KEY = os.getenv("ANTHROPIC_ADMIN_KEY")
ANTHROPIC_ORG_ID = os.getenv("ANTHROPIC_ORG_ID")

def test_endpoints():
    headers = {
        "x-api-key": ANTHROPIC_ADMIN_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/usage_report",
        f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/usage",
        f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/billing",
        "https://api.anthropic.com/v1/organizations/usage_report",
        "https://api.anthropic.com/v1/usage",
    ]
    
    for url in endpoints:
        print(f"\nTesting: {url}")
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_endpoints()
