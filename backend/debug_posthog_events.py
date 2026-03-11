
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def check_posthog_events():
    api_key = os.getenv("POSTHOG_PERSONAL_API_KEY")
    project_id = os.getenv("POSTHOG_PROJECT_ID")
    host = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
    
    event_name = "ai_workflow_run"
    
    print(f"--- Checking PostHog for '{event_name}' events ---")
    
    url = f"{host}/api/projects/{project_id}/query/"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    query = f"""
    SELECT count() as cnt
    FROM events
    WHERE event = '{event_name}'
      AND timestamp >= now() - toIntervalDay(30)
    """

    payload = {"query": {"kind": "HogQLQuery", "query": query}}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        count = result.get("results", [[0]])[0][0]
        print(f"Result: {count} events found in the last 30 days.")
    except Exception as e:
        print(f"Error checking PostHog: {e}")

if __name__ == "__main__":
    check_posthog_events()
