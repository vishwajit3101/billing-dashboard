# app/fullenrich.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

FULLENRICH_API_KEY = os.getenv("FULLENRICH_API_KEY")
FULLENRICH_USAGE_URL = os.getenv("FULLENRICH_USAGE_URL", "https://app.fullenrich.com/api/v1/account/credits")
FULLENRICH_TOTAL_CREDITS = float(os.getenv("FULLENRICH_TOTAL_CREDITS", "500"))

def get_fullenrich_remaining_credits() -> tuple:
    # Always refresh from env in case it changed
    total_default = float(os.getenv("FULLENRICH_TOTAL_CREDITS", "500"))
    
    if not FULLENRICH_API_KEY:
        print("[FullEnrich] No API key in .env → using mock 50")
        return 50.0, total_default

    headers = {"Authorization": f"Bearer {FULLENRICH_API_KEY}"}

    try:
        resp = requests.get(FULLENRICH_USAGE_URL, headers=headers, timeout=8)
        print(f"[FullEnrich] Status code: {resp.status_code}")

        resp.raise_for_status()
        data = resp.json()

        remaining = data.get("balance", data.get("credits_remaining", data.get("remaining", 50.0)))
        total = data.get("total_credits", data.get("limit", data.get("total", total_default)))
        print(f"[FullEnrich] Real remaining: {remaining}, total: {total}")
        return float(remaining), float(total)

    except Exception as e:
        print(f"[FullEnrich] Error: {str(e)} → using mock 50")
        return 50.0, total_default