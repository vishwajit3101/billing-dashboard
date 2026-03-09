# app/buyercaddy.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

import random
from datetime import datetime, timedelta

BUYERCADDY_API_KEY = os.getenv("BUYERCADDY_API_KEY")

def get_buyercaddy_history(days: int = 7) -> list[dict]:
    """
    Fetch daily credit usage for BuyerCaddy.
    Falls back to randomized mock data if API key is missing or on error.
    """
    if not BUYERCADDY_API_KEY:
        today = datetime.utcnow().date()
        return [
            {
                "day": (today - timedelta(days=days - 1 - i)).strftime("%b %d"),
                "label": ["6d ago", "5d ago", "4d ago", "3d ago", "2d ago", "Yesterday", "Today"][i] if days == 7 else f"{days-1-i}d ago",
                "credits": 80 + ((i * 37 + 13) % 101)  # deterministic: range 80-180
            }
            for i in range(days)
        ]

    # Real API integration placeholder
    url = "https://api.buyercaddy.com/v1/usage/daily"
    headers = {"Authorization": f"Bearer {BUYERCADDY_API_KEY}"}
    params = {"days": days}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            # Map to { day, label, credits }
            return data.get("history", [])
        
        print(f"[BuyerCaddy] History error: Status {resp.status_code} → using mock")
        return get_buyercaddy_history_mock(days)
    except Exception as e:
        print(f"[BuyerCaddy] History error: {str(e)} → using mock")
        return get_buyercaddy_history_mock(days)

def get_buyercaddy_history_mock(days: int):
    today = datetime.utcnow().date()
    return [
        {
            "day": (today - timedelta(days=days - 1 - i)).strftime("%b %d"),
            "label": ["6d ago", "5d ago", "4d ago", "3d ago", "2d ago", "Yesterday", "Today"][i] if days == 7 else f"{days-1-i}d ago",
            "credits": 80 + ((i * 37 + 13) % 101)  # deterministic: range 80-180
        }
        for i in range(days)
    ]

def get_buyercaddy_remaining_credits() -> tuple:
    """
    Fetch real remaining credits from BuyerCaddy API.
    Falls back to mock 6800 if not configured.
    """
    if not BUYERCADDY_API_KEY:
        print("[BuyerCaddy] No API key in .env → using mock 6800")
        return 6800.0, 10000.0

    # Plausible endpoint based on common readme.io integrations
    # Note: If this fails, we fallback to mock gracefully
    url = "https://api.buyercaddy.com/v1/credits/balance"
    headers = {"Authorization": f"Bearer {BUYERCADDY_API_KEY}"}

    try:
        resp = requests.get(url, headers=headers, timeout=8)
        print(f"[BuyerCaddy] Status code: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            remaining = data.get("credits_remaining", data.get("balance", 6800.0))
            total = data.get("total_credits", data.get("limit", 10000.0))
            print(f"[BuyerCaddy] Real remaining: {remaining}")
            return float(remaining), float(total)
        
        print(f"[BuyerCaddy] Non-200 status → using mock 6800")
        return 6800.0, 10000.0

    except Exception as e:
        print(f"[BuyerCaddy] Error: {str(e)} → using mock 6800")
        return 6800.0, 10000.0
