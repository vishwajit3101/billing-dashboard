# app/posthog.py
import requests
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY")
POSTHOG_PROJECT_ID = os.getenv("POSTHOG_PROJECT_ID")
POSTHOG_PERSONAL_API_KEY = os.getenv("POSTHOG_PERSONAL_API_KEY")


# Exact mapping from your PRD
EVENT_CREDIT_MAPPING = {
    "search_performed": ("Tavily", 1),
    "lead_enriched": ("FullEnrich", 2),
    "ai_workflow_run": ("Anthropic", 5),
    "data_fetched": ("Buyercaddy", 1),
}

def fetch_posthog_event_count(event_name: str, days: int = 7) -> int:
    """Count occurrences of an event in last N days using HogQL."""
    if not POSTHOG_API_KEY or not POSTHOG_PROJECT_ID:
        print(f"[PostHog] Missing config for '{event_name}'")
        return 0

    url = f"{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/query/"
    headers = {
        "Authorization": f"Bearer {POSTHOG_PERSONAL_API_KEY}",
        "Content-Type": "application/json"
    }

    query = f"""
    SELECT count() as cnt
    FROM events
    WHERE event = '{event_name}'
      AND timestamp >= now() - toIntervalDay({days})
    """

    payload = {"query": {"kind": "HogQLQuery", "query": query}}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        count = result.get("results", [[0]])[0][0]
        print(f"[PostHog] {event_name} count (last {days}d): {count}")
        return int(count)
    except Exception as e:
        print(f"[PostHog] Error for {event_name}: {str(e)}")
        return 0


def fetch_posthog_daily_counts(event_name: str, days: int = 7) -> list[dict]:
    """Get daily counts for an event over the last N days using HogQL."""
    if not POSTHOG_API_KEY or not POSTHOG_PROJECT_ID:
        return []

    url = f"{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/query/"
    headers = {
        "Authorization": f"Bearer {POSTHOG_PERSONAL_API_KEY}",
        "Content-Type": "application/json"
    }

    # Query for daily counts
    query = f"""
    SELECT toStartOfDay(timestamp) as day, count() as cnt
    FROM events
    WHERE event = '{event_name}'
      AND timestamp >= now() - toIntervalDay({days})
    GROUP BY day
    ORDER BY day ASC
    """

    payload = {"query": {"kind": "HogQLQuery", "query": query}}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        # PostHog returns results as a list of lists: [[day, count], ...]
        rows = result.get("results", [])
        return [{"day": r[0].split('T')[0], "count": int(r[1])} for r in rows]
    except Exception as e:
        print(f"[PostHog] History error for {event_name}: {str(e)}")
        return []


def get_tool_usage_history(days: int = 7) -> dict[str, list[dict]]:
    """Return 7-day credit usage history per tool."""
    history = {}
    
    tasks = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for event, (tool, credits_per) in EVENT_CREDIT_MAPPING.items():
            tasks.append((tool, credits_per, executor.submit(fetch_posthog_daily_counts, event, days)))

    for tool, credits_per, fut in tasks:
        daily_counts = fut.result()
        # Sort counts by day to ensure correct relative labeling
        sorted_counts = sorted(daily_counts, key=lambda x: x["day"])
        
        tool_history = []
        for i, d in enumerate(sorted_counts):
            # Calculate relative label
            days_ago = len(sorted_counts) - 1 - i
            if days_ago == 0:
                label = "Today"
            elif days_ago == 1:
                label = "Yesterday"
            else:
                label = f"{days_ago}d ago"
                
            tool_history.append({
                "day": d["day"],
                "label": label,
                "credits": d["count"] * credits_per
            })
        
        if tool not in history:
            history[tool] = tool_history
        else:
            history[tool] = tool_history

    return history


def get_tool_usage_stats() -> dict[str, dict]:
    """
    Returns stats for each tool, parallelized for speed.
    """
    stats = {}
    
    tasks = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for event, (tool, credits_per) in EVENT_CREDIT_MAPPING.items():
            tasks.append((tool, credits_per, executor.submit(fetch_posthog_event_count, event, 7), executor.submit(fetch_posthog_event_count, event, 1)))

    for tool, credits_per, fut_7d, fut_1d in tasks:
        count_7d = fut_7d.result()
        count_24h = fut_1d.result()

        avg_7d = (count_7d * credits_per) / 7
        curr_24h = (count_24h * credits_per)

        if tool not in stats:
            stats[tool] = {"avg_7d": 0.0, "current_24h": 0.0}

        stats[tool]["avg_7d"] += avg_7d
        stats[tool]["current_24h"] += curr_24h

    print(f"[PostHog] Tool usage stats (parallelized): {stats}")
    return stats