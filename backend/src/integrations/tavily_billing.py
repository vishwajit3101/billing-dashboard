"""
Tavily billing/credits API client.
"""
import os
from typing import Any

def fetch_tavily_billing(api_key: str | None = None) -> dict[str, Any]:
    key = api_key or os.environ.get("TAVILY_API_KEY", "")
    # TODO: integrate Tavily billing API
    return {
        "credits_remaining": 2_800,
        "credits_total": 10_000,
    }
