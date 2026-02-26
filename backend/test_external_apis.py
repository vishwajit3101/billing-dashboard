import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_tavily():
    print("Testing Tavily...")
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("Missing TAVILY_API_KEY")
        return
    url = "https://api.tavily.com/usage"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Tavily Status: {resp.status_code}")
        print(f"Tavily Response: {resp.text}")
    except Exception as e:
        print(f"Tavily Error: {e}")

def test_fullenrich():
    print("\nTesting FullEnrich...")
    api_key = os.getenv("FULLENRICH_API_KEY")
    if not api_key:
        print("Missing FULLENRICH_API_KEY")
        return
    url = "https://api.fullenrich.com/v1/credit_balance"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"FullEnrich Status: {resp.status_code}")
        print(f"FullEnrich Response: {resp.text}")
    except Exception as e:
        print(f"FullEnrich Error: {e}")

if __name__ == "__main__":
    test_tavily()
    test_fullenrich()
