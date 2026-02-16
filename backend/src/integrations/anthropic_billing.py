"""
Anthropic billing/credits API client.
Returns credits_remaining, credits_total (if available), cost_this_month_usd.
MVP: can use mock data until official billing API is available.
"""
import os
from typing import Any

def fetch_anthropic_billing(api_key: str | None = None) -> dict[str, Any]:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    # TODO: call Anthropic billing/usage API when available
    # For now return mock structure for pipeline and dashboard
    return {
        "credits_remaining": 42_350,
        "credits_total": 500_000,
        "cost_this_month_usd": 4280.0,
    }
