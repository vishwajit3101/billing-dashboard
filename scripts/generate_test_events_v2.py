import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta

dotenv_path = Path("c:/Users/vishw/billing-dashboard/backend/.env")
load_dotenv(dotenv_path=dotenv_path)

# Use the Project API Key (phc_...) for ingestion
api_key = os.getenv('POSTHOG_API_KEY')
host = "https://us.i.posthog.com"

def send_event(event_name, days_ago):
    url = f"{host}/capture/"
    ts = (datetime.utcnow() - timedelta(days=days_ago)).isoformat()
    
    payload = {
        "api_key": api_key,
        "event": event_name,
        "properties": {
            "distinct_id": "test_user_dashboard",
            "$timestamp": ts
        }
    }
    
    resp = requests.post(url, json=payload)
    return resp.status_code, resp.text

print(f"Generating test events for {api_key[:10]}...")

# Send a variety of events for the last 7 days
for d in range(7, -1, -1):
    # FullEnrich events
    for _ in range(d + 1):
        status, text = send_event("lead_enriched", d)
    # BuyerCaddy events
    for _ in range(d + 2):
        status, text = send_event("data_fetched", d)

print("Test events sent. Status of last call:", status)
