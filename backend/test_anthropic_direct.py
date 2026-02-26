import os
import requests
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_ADMIN_KEY = os.getenv("ANTHROPIC_ADMIN_KEY")
ANTHROPIC_ORG_ID = os.getenv("ANTHROPIC_ORG_ID")

def test_anthropic():
    print(f"Testing Anthropic with ORG_ID: {ANTHROPIC_ORG_ID}")
    if not ANTHROPIC_ADMIN_KEY or not ANTHROPIC_ORG_ID:
        print("Missing ANTHROPIC_ADMIN_KEY or ANTHROPIC_ORG_ID")
        return

    url = f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/billing/credits"
    headers = {
        "x-api-key": ANTHROPIC_ADMIN_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    try:
        # Try prepaid credits endpoint (often used in console)
        prepaid_url = f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/prepaid/credits"
        print(f"Trying prepaid/credits: {prepaid_url}")
        resp = requests.get(prepaid_url, headers=headers, timeout=10)
        print(f"Prepaid Status: {resp.status_code}")
        print(f"Prepaid Response: {resp.text}")

        # Try usage report endpoint if prepaid fails
        if resp.status_code == 404:
            usage_url = f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/usage_report/messages"
            print(f"Trying usage_report: {usage_url}")
            resp_usage = requests.get(usage_url, headers=headers, timeout=10)
            print(f"Usage Status: {resp_usage.status_code}")
            print(f"Usage Response: {resp_usage.text[:500]}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_anthropic()
