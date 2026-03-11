
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def surgical_debug():
    key = os.getenv("ANTHROPIC_ADMIN_KEY")
    org_id = os.getenv("ANTHROPIC_ORG_ID")
    
    print(f"DEBUG: Org ID: {org_id}")
    print(f"DEBUG: Key exists and starts with sk-ant-admin: {key.startswith('sk-ant-admin-') if key else False}")
    
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        f"https://api.anthropic.com/v1/organizations/{org_id}/billing/credits",
        f"https://api.anthropic.com/v1/organizations/{org_id}/prepaid/credits"
    ]
    
    for url in endpoints:
        print(f"\n--- Testing Endpoint: {url} ---")
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {resp.status_code}")
            try:
                print(f"Response Body: {json.dumps(resp.json(), indent=2)}")
            except:
                print(f"Response Text: {resp.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    surgical_debug()
