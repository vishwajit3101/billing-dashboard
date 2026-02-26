import requests
import json

def test_dashboard_api():
    url = "http://localhost:8000/dashboard"
    try:
        resp = requests.get(url, params={"days": 30})
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            aws = data.get("aws", {})
            print("AWS Data:")
            print(json.dumps(aws, indent=2))
        else:
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dashboard_api()
