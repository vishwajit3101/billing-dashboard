
import os
import requests
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

ANTHROPIC_ADMIN_KEY = os.getenv("ANTHROPIC_ADMIN_KEY")
ANTHROPIC_ORG_ID = os.getenv("ANTHROPIC_ORG_ID")

def test_with_header():
    headers = {
        "x-api-key": ANTHROPIC_ADMIN_KEY,
        "anthropic-version": "2023-06-01",
        "Anthropic-Organization": ANTHROPIC_ORG_ID,
        "Content-Type": "application/json"
    }
    
    endpoints = [
        "https://api.anthropic.com/v1/billing/credits",
        "https://api.anthropic.com/v1/prepaid/credits",
        "https://api.anthropic.com/v1/billing/balance",
    ]
    
    for url in endpoints:
        print(f"\nTesting with header: {url}")
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_with_header()
