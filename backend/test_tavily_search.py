import requests
import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def test_tavily_search():
    if not TAVILY_API_KEY:
        print("No API key found in .env")
        return

    print(f"Testing Search with API Key: {TAVILY_API_KEY[:10]}...")
    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": "What is the weather in Delhi?",
        "search_depth": "basic",
        "max_results": 1
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_tavily_search()
