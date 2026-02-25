import requests
import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def test_tavily():
    if not TAVILY_API_KEY:
        print("No API key found in .env")
        return

    print(f"Testing with API Key: {TAVILY_API_KEY[:10]}...")
    url = "https://api.tavily.com/usage"
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Headers: {resp.headers}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 200:
            data = resp.json()
            plan_limit = data.get("account", {}).get("plan_limit", "N/A")
            total_usage = data.get("key", {}).get("usage", "N/A")
            print(f"Plan Limit: {plan_limit}")
            print(f"Total Usage: {total_usage}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_tavily()
