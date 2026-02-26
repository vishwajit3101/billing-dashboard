import requests
import os
from dotenv import load_dotenv

load_dotenv()

FULLENRICH_API_KEY = os.getenv("FULLENRICH_API_KEY")
FULLENRICH_USAGE_URL = "https://app.fullenrich.com/api/v1/account/credits"

def test_fullenrich():
    if not FULLENRICH_API_KEY:
        print("No API key")
        return

    headers = {"Authorization": f"Bearer {FULLENRICH_API_KEY}"}
    try:
        resp = requests.get(FULLENRICH_USAGE_URL, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fullenrich()
