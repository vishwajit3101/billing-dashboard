
import os
import requests
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

ANTHROPIC_ADMIN_KEY = os.getenv("ANTHROPIC_ADMIN_KEY")
ANTHROPIC_ORG_ID = os.getenv("ANTHROPIC_ORG_ID")

def debug_usage_report():
    headers = {
        "x-api-key": ANTHROPIC_ADMIN_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    # Usage report usually requires daily breakdown
    url = f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/usage_report/messages"
    print(f"Testing: {url}")
    
    try:
        resp = requests.post(url, headers=headers, json={"user_id": None}, timeout=10) # Some version of this exists
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_usage_report()
