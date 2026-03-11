
import requests
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_ADMIN_KEY = os.getenv("ANTHROPIC_ADMIN_KEY")

def discover_org_id():
    if not ANTHROPIC_ADMIN_KEY:
        print("Missing ANTHROPIC_ADMIN_KEY")
        return

    # Try to get organizations
    url = "https://api.anthropic.com/v1/organizations/me"
    headers = {
        "x-api-key": ANTHROPIC_ADMIN_KEY,
        "anthropic-version": "2023-06-01"
    }
    
    try:
        resp = requests.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    discover_org_id()
