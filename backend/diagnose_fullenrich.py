import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_endpoint(name, url, api_key):
    print(f"Testing {name}: {url}")
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Success! Response: {resp.text}")
        else:
            print(f"Response: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)

def main():
    api_key = os.getenv("FULLENRICH_API_KEY")
    if not api_key:
        print("Missing FULLENRICH_API_KEY")
        return

    endpoints = [
        ("v1 usage", "https://app.fullenrich.com/api/v1/usage"),
        ("v2 usage", "https://app.fullenrich.com/api/v2/usage"),
        ("v1 credit_balance", "https://api.fullenrich.com/v1/credit_balance"), # from previous test attempt
        ("v1 credits balance", "https://api.fullenrich.com/v1/credits/balance"),
        ("v2 credit balance", "https://app.fullenrich.com/api/v2/credit-balance"),
        ("v1 credit balance (app)", "https://app.fullenrich.com/api/v1/credit-balance"),
        ("v1-a usage", "https://api.fullenrich.com/api/v1/usage"),
        ("v2-a usage", "https://api.fullenrich.com/api/v2/usage"),
    ]

    for name, url in endpoints:
        test_endpoint(name, url, api_key)

if __name__ == "__main__":
    main()
