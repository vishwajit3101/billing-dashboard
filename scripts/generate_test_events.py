import os
import time
import requests
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta

dotenv_path = Path("c:/Users/vishw/billing-dashboard/backend/.env")
load_dotenv(dotenv_path=dotenv_path)

api_key = os.getenv('POSTHOG_API_KEY') # phc_...
project_id = os.getenv('POSTHOG_PROJECT_ID')
host = "https://us.i.posthog.com" # Ingestion host

def send_event(event_name, distinct_id="test_user", properties=None):
    url = f"{host}/capture/"
    data = {
        "api_key": api_key,
        "event": event_name,
        "properties": properties or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    resp = requests.post(url, json=data)
    print(f"Sent {event_name}: {resp.status_code}")

print("Sending test events to PostHog to populate graphs...")

# Send events for the last 5 days to create a trend
for i in range(5, 0, -1):
    ts = (datetime.utcnow() - timedelta(days=i)).isoformat()
    # FullEnrich events
    for _ in range(i * 2):
        send_event("lead_enriched", properties={"$timestamp": ts})
    # BuyerCaddy events
    for _ in range(i * 3):
        send_event("data_fetched", properties={"$timestamp": ts})

print("Done. Please wait a minute for PostHog to process these events.")
