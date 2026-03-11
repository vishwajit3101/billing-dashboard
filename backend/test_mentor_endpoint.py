import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def test_mentor_endpoint():
    key = os.getenv("ANTHROPIC_ADMIN_KEY")
    
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    start_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = f"https://api.anthropic.com/v1/organizations/usage_report/messages?starting_at={start_str}&ending_at={end_str}"
    
    print(f"Testing URL: {url}")
    
    try:
        resp = requests.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mentor_endpoint()
