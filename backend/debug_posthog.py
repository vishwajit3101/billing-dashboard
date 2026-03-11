
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load from backend/.env explicitly
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
POSTHOG_PERSONAL_API_KEY = os.getenv("POSTHOG_PERSONAL_API_KEY")
POSTHOG_PROJECT_ID = os.getenv("POSTHOG_PROJECT_ID")

def test_posthog_anthropic():
    print(f"Project ID: {POSTHOG_PROJECT_ID}")
    
    url = f"{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/query/"
    headers = {
        "Authorization": f"Bearer {POSTHOG_PERSONAL_API_KEY}",
        "Content-Type": "application/json"
    }

    # Query for ANY events in the last 30 days to check connection
    print("\n--- Checking any events in last 30d ---")
    query = """
    SELECT event, count() as cnt
    FROM events
    WHERE timestamp >= now() - toIntervalDay(30)
    GROUP BY event
    ORDER BY cnt DESC
    LIMIT 20
    """
    payload = {"query": {"kind": "HogQLQuery", "query": query}}
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        print(f"Events: {result.get('results', [])}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_posthog_anthropic()
