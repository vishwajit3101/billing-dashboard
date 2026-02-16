"""
API clients for AI tool billing/credit endpoints.
Uses requests with retries and graceful error handling.
"""
import logging
import time
from typing import Any, Optional

import requests

from config import (
    ANTHROPIC_API_KEY,
    TAVILY_API_KEY,
    FULLENRICH_API_KEY,
    BUYERCADDY_API_KEY,
    ANTHROPIC_BILLING_URL,
    TAVILY_BILLING_URL,
    FULLENRICH_BILLING_URL,
    BUYERCADDY_BILLING_URL,
    RETRY_MAX_ATTEMPTS,
    RETRY_BACKOFF_SECONDS,
)

logger = logging.getLogger(__name__)


def _request_with_retries(
    method: str,
    url: str,
    headers: Optional[dict] = None,
    timeout: int = 30,
) -> Optional[dict[str, Any]]:
    """
    Execute HTTP request with exponential backoff retries.
    Returns parsed JSON or None on failure.
    """
    session = requests.Session()
    last_error: Optional[Exception] = None
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            logger.info("Request %s %s (attempt %d/%d)", method, url, attempt, RETRY_MAX_ATTEMPTS)
            resp = session.request(
                method,
                url,
                headers=headers or {},
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("Request succeeded: %s", resp.status_code)
            return data
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning("Attempt %d failed: %s", attempt, e)
            if attempt < RETRY_MAX_ATTEMPTS:
                sleep_time = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
                logger.info("Retrying in %.1fs", sleep_time)
                time.sleep(sleep_time)
        except ValueError as e:
            last_error = e
            logger.warning("Invalid JSON response: %s", e)
            break
    if last_error:
        logger.error("All retries exhausted: %s", last_error)
    return None


def _normalize_result(
    credits_remaining: Optional[float] = None,
    credits_total: Optional[float] = None,
    cost_usd: Optional[float] = None,
) -> dict[str, Any]:
    """Build a standard result dict for credit_snapshots."""
    return {
        "credits_remaining": float(credits_remaining) if credits_remaining is not None else 0.0,
        "credits_total": float(credits_total) if credits_total is not None else None,
        "cost_usd": float(cost_usd) if cost_usd is not None else None,
    }


# -----------------------------------------------------------------------------
# Anthropic — Claude API usage/credits
# -----------------------------------------------------------------------------
def fetch_anthropic_credits() -> Optional[dict[str, Any]]:
    """Fetch Anthropic (Claude) credit balance. Returns dict or None on error."""
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set; skipping Anthropic fetch")
        return None
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    data = _request_with_retries("GET", ANTHROPIC_BILLING_URL, headers=headers)
    if data is None:
        logger.warning("Anthropic API request failed after retries")
        return None
    # Map common response shapes; adjust keys to match actual Anthropic usage API
    remaining = data.get("credits_remaining") or data.get("balance") or data.get("remaining")
    total = data.get("credits_total") or data.get("total_credits") or data.get("limit")
    cost = data.get("cost_this_month_usd") or data.get("spend") or data.get("cost_usd")
    return _normalize_result(credits_remaining=remaining, credits_total=total, cost_usd=cost)


# -----------------------------------------------------------------------------
# Tavily — Search API credits
# -----------------------------------------------------------------------------
def fetch_tavily_credits() -> Optional[dict[str, Any]]:
    """Fetch Tavily search credits."""
    if not TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY not set; skipping Tavily fetch")
        return None
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TAVILY_API_KEY}"}
    data = _request_with_retries("GET", TAVILY_BILLING_URL, headers=headers)
    if data is None:
        logger.warning("Tavily API request failed after retries")
        return None
    remaining = data.get("credits_remaining") or data.get("balance") or data.get("remaining")
    total = data.get("credits_total") or data.get("total") or data.get("limit")
    return _normalize_result(credits_remaining=remaining, credits_total=total)


# -----------------------------------------------------------------------------
# FullEnrich — Data enrichment credits
# -----------------------------------------------------------------------------
def fetch_fullenrich_credits() -> Optional[dict[str, Any]]:
    """Fetch FullEnrich enrichment credits."""
    if not FULLENRICH_API_KEY:
        logger.warning("FULLENRICH_API_KEY not set; skipping FullEnrich fetch")
        return None
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {FULLENRICH_API_KEY}"}
    data = _request_with_retries("GET", FULLENRICH_BILLING_URL, headers=headers)
    if data is None:
        logger.warning("FullEnrich API request failed after retries")
        return None
    remaining = data.get("credits_remaining") or data.get("balance") or data.get("remaining")
    total = data.get("credits_total") or data.get("total") or data.get("limit")
    return _normalize_result(credits_remaining=remaining, credits_total=total)


# -----------------------------------------------------------------------------
# Buyercaddy — Sales intelligence credits
# -----------------------------------------------------------------------------
def fetch_buyercaddy_credits() -> Optional[dict[str, Any]]:
    """Fetch Buyercaddy sales intelligence credits."""
    if not BUYERCADDY_API_KEY:
        logger.warning("BUYERCADDY_API_KEY not set; skipping Buyercaddy fetch")
        return None
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BUYERCADDY_API_KEY}"}
    data = _request_with_retries("GET", BUYERCADDY_BILLING_URL, headers=headers)
    if data is None:
        logger.warning("Buyercaddy API request failed after retries")
        return None
    remaining = data.get("credits_remaining") or data.get("balance") or data.get("remaining")
    total = data.get("credits_total") or data.get("total") or data.get("limit")
    return _normalize_result(credits_remaining=remaining, credits_total=total)


# Registry for handler to call by slug
FETCHERS = {
    "anthropic": fetch_anthropic_credits,
    "tavily": fetch_tavily_credits,
    "fullenrich": fetch_fullenrich_credits,
    "buyercaddy": fetch_buyercaddy_credits,
}
