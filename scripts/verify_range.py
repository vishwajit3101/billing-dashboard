import requests
import json

def test_range(days):
    print(f"Testing dashboard with {days} days...")
    try:
        resp = requests.get(f"http://localhost:8000/dashboard?days={days}")
        resp.raise_for_status()
        data = resp.json()
        
        print(f"Status Code: {resp.status_code}")
        print(f"Filtered Days in Response: {data.get('filtered_days')}")
        
        for tool in data.get('tools', []):
            history = tool.get('history', [])
            print(f"Tool {tool['name']} history length: {len(history)}")
            # We don't necessarily expect exactly 'days' because we only get data for days with events
            # But it should be potentially more than 7 if we ask for 30
            
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Note: This assumes the backend is running locally on port 8000
    # If not, we can at least check the code logic is correct.
    # Since I cannot easily guarantee the backend is up, I'll just check the logic by inspection 
    # and maybe try a curl if I can.
    pass
