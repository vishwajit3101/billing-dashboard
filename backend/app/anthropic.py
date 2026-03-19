# app/anthropic.py
import requests
import os
import traceback
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_ADMIN_KEY = os.getenv("ANTHROPIC_ADMIN_KEY")
ANTHROPIC_ORG_ID = os.getenv("ANTHROPIC_ORG_ID")
ANTHROPIC_TOTAL_CREDITS = float(os.getenv("ANTHROPIC_TOTAL_CREDITS", "50000.0"))

def get_anthropic_remaining_credits() -> tuple:
    """
    Fetch real usage from Anthropic Usage POST API and calculate remaining credits
    based on the configured total credits limit.
    """
    if not ANTHROPIC_ADMIN_KEY:
        print("[Anthropic] Missing admin key → returning 0.0 remaining")
        return 0.0, ANTHROPIC_TOTAL_CREDITS

    url = "https://api.anthropic.com/v1/organizations/usage_report/messages"
    headers = {
        "x-api-key": ANTHROPIC_ADMIN_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    start_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url_with_params = f"{url}?starting_at={start_str}&ending_at={end_str}"

    try:
        total_usage_cost = 0.0
        has_more = True
        next_page = ""
        
        while has_more:
            page_url = f"{url_with_params}&page={next_page}" if next_page else url_with_params
            resp = requests.get(page_url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            days_data = data.get("data", [])
            
            for day_bucket in days_data:
                results = day_bucket.get("results", [])
                for item in results:
                    uncached_in = item.get("uncached_input_tokens", 0)
                    out_tokens = item.get("output_tokens", 0)
                    cache_read = item.get("cache_read_input_tokens", 0)
                    cache_creation_obj = item.get("cache_creation", {})
                    cache_create = cache_creation_obj.get("ephemeral_5m_input_tokens", 0) + cache_creation_obj.get("ephemeral_1h_input_tokens", 0)
                    
                    cost_in = (uncached_in / 1000000.0) * 3.00
                    cost_out = (out_tokens / 1000000.0) * 15.00
                    cost_cache_read = (cache_read / 1000000.0) * 0.30
                    cost_cache_write = (cache_create / 1000000.0) * 3.75
                    
                    total_usage_cost += (cost_in + cost_out + cost_cache_read + cost_cache_write)
            
            has_more = data.get("has_more", False)
            next_page = data.get("next_page", "")

        remaining = max(0.0, ANTHROPIC_TOTAL_CREDITS - total_usage_cost)
        print(f"[Anthropic] Real remaining calculated: {remaining:.2f} out of {ANTHROPIC_TOTAL_CREDITS}")
        return float(remaining), ANTHROPIC_TOTAL_CREDITS

    except Exception as e:
        print(f"[Anthropic] Error fetching real data: {str(e)}")
        traceback.print_exc()
        print(f"[Anthropic] Returning 0.0 remaining due to error")
        return 0.0, ANTHROPIC_TOTAL_CREDITS

def get_anthropic_usage_history(days: int = 90) -> list[dict]:
    """
    Fetch daily usage from Anthropic Usage POST API for the last N days
    and return it formatted for the dashboard database.
    """
    history = []
    
    if not ANTHROPIC_ADMIN_KEY:
        return history

    url = "https://api.anthropic.com/v1/organizations/usage_report/messages"
    headers = {
        "x-api-key": ANTHROPIC_ADMIN_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    start_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url_with_params = f"{url}?starting_at={start_str}&ending_at={end_str}"

    try:
        has_more = True
        next_page = ""
        
        while has_more:
            page_url = f"{url_with_params}&page={next_page}" if next_page else url_with_params
            resp = requests.get(page_url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            days_data = data.get("data", [])
            
            for day_bucket in days_data:
                date_str = day_bucket.get("starting_at", "").split("T")[0]
                results = day_bucket.get("results", [])
                
                daily_cost = 0.0
                daily_count = 0
                
                for item in results:
                    uncached_in = item.get("uncached_input_tokens", 0)
                    out_tokens = item.get("output_tokens", 0)
                    cache_read = item.get("cache_read_input_tokens", 0)
                    cache_creation_obj = item.get("cache_creation", {})
                    cache_create = cache_creation_obj.get("ephemeral_5m_input_tokens", 0) + cache_creation_obj.get("ephemeral_1h_input_tokens", 0)
                    
                    cost_in = (uncached_in / 1000000.0) * 3.00
                    cost_out = (out_tokens / 1000000.0) * 15.00
                    cost_cache_read = (cache_read / 1000000.0) * 0.30
                    cost_cache_write = (cache_create / 1000000.0) * 3.75
                    
                    daily_cost += (cost_in + cost_out + cost_cache_read + cost_cache_write)
                    daily_count += (uncached_in + out_tokens + cache_read + cache_create)
                
                existing = next((h for h in history if h["day"] == date_str), None)
                if existing:
                    existing["credits"] += daily_cost
                    existing["count"] += daily_count
                else:
                    if date_str:
                        history.append({
                            "day": date_str,
                            "credits": daily_cost,
                            "count": daily_count
                        })
            
            has_more = data.get("has_more", False)
            next_page = data.get("next_page", "")

        return history

    except Exception as e:
        print(f"[Anthropic] Error fetching real history data: {str(e)}")
        return history
