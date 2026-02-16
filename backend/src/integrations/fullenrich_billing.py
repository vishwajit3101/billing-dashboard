"""
FullEnrich billing/credits API client.
"""
import os
from typing import Any

def fetch_fullenrich_billing(api_key: str | None = None) -> dict[str, Any]:
    key = api_key or os.environ.get("FULLENRICH_API_KEY", "")
    # TODO: integrate FullEnrich billing API
    return {
        "credits_remaining": 500,
        "credits_total": 5_000,
    }
