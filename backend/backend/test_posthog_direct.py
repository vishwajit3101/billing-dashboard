import os
import requests
from dotenv import load_dotenv

load_dotenv()

POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
POSTHOG_PROJECT_ID = os.getenv("POSTHOG_PROJECT_ID")
POSTHOG_PERSONAL_API_KEY = os.getenv("POSTHOG_PERSONAL_API_KEY")

EVENT_CREDIT_MAPPING = {
    "search_performed": ("Tavily", 1),
    "lead_enriched": ("FullEnrich", 2),
    "ai_workflow_run": ("Anthropic", 5),
    "data_fetched": ("Buyercaddy", 1),
}

def check_posthog():
    print(f"Checking PostHog for Project ID: {POSTHOG_PROJECT_ID}")
    if not POSTHOG_PROJECT_ID or not POSTHOG_PERSONAL_API_KEY:
        print("Missing PostHog configuration")
        return

    url = f"{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/query/"
    headers = {
        "Authorization": f"Bearer {POSTHOG_PERSONAL_API_KEY}",
        "Content-Type": "application/json"
    }

    for event_name in EVENT_CREDIT_MAPPING.keys():
        query = f"""
        SELECT count() as cnt
        FROM events
        WHERE event = '{event_name}'
          AND timestamp >= now() - toIntervalDay(7)
        """
        payload = {"query": {"kind": "HogQLQuery", "query": query}}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                count = resp.json().get("results", [[0]])[0][0]
                print(f"Event '{event_name}': {count} occurrences (last 7 days)")
            else:
                print(f"Error for '{event_name}': {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Exception for '{event_name}': {e}")

if __name__ == "__main__":
    check_posthog()
