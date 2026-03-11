
import os
import requests
import traceback
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

ANTHROPIC_ADMIN_KEY = os.getenv("ANTHROPIC_ADMIN_KEY")
ANTHROPIC_ORG_ID = os.getenv("ANTHROPIC_ORG_ID")

def debug_to_file():
    with open("anthropic_debug.log", "w") as f:
        f.write("--- Debugging Anthropic Credits ---\n")
        f.write(f"Org ID: {ANTHROPIC_ORG_ID}\n")
        
        headers = {
            "x-api-key": ANTHROPIC_ADMIN_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/billing/credits"
        f.write(f"URL: {url}\n")
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            f.write(f"Status: {resp.status_code}\n")
            f.write(f"Response: {resp.text}\n")
            
            if resp.status_code == 404:
                url_pp = f"https://api.anthropic.com/v1/organizations/{ANTHROPIC_ORG_ID}/prepaid/credits"
                f.write(f"\nRetrying with {url_pp}...\n")
                resp = requests.get(url_pp, headers=headers, timeout=10)
                f.write(f"Status: {resp.status_code}\n")
                f.write(f"Response: {resp.text}\n")
                
        except Exception as e:
            f.write(f"\nException: {str(e)}\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    debug_to_file()
