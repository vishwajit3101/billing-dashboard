
import os
import requests
from dotenv import load_dotenv

# Load from backend/.env explicitly
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

ANTHROPIC_ADMIN_KEY = os.getenv("ANTHROPIC_ADMIN_KEY")
ANTHROPIC_ORG_ID = os.getenv("ANTHROPIC_ORG_ID")

def debug_direct_api():
    print(f"Org ID: {ANTHROPIC_ORG_ID}")
    
    headers = {
        "x-api-key": ANTHROPIC_ADMIN_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    # 1. Try Organizations Me (Verify Key)
    print("\n--- Testing /v1/organizations/me ---")
    resp = requests.get("https://api.anthropic.com/v1/organizations/me", headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    # 2. Try Billing Credits
    print("\n--- Testing /v1/organizations/{org_id}/billing/credits ---")
    url = f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/billing/credits"
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    # 3. Try Prepaid Credits
    print("\n--- Testing /v1/organizations/{org_id}/prepaid/credits ---")
    url = f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/prepaid/credits"
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")

if __name__ == "__main__":
    debug_direct_api()
