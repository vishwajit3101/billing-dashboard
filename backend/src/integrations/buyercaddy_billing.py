"""
Buyercaddy billing/credits API client.
"""
import os
from typing import Any

def fetch_buyercaddy_billing(api_key: str | None = None) -> dict[str, Any]:
    key = api_key or os.environ.get("BUYERCADDY_API_KEY", "")
    # TODO: integrate Buyercaddy billing API
    return {
        "credits_remaining": 6_800,
        "credits_total": 8_000,
    }
