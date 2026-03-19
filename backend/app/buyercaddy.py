import os
from datetime import datetime, timedelta, UTC
from pathlib import Path

import requests
from dotenv import load_dotenv

from app.posthog import fetch_posthog_daily_counts

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEFAULT_BUYERCADDY_BALANCE_URL = "https://api.salescaddy.ai/api/credits/report"
DEFAULT_BUYERCADDY_TOTAL_CREDITS = 10000.0


def _get_buyercaddy_config() -> tuple[str | None, str, float]:
    # Read env at call time so local .env edits are picked up without a restart.
    api_key = (os.getenv("BUYERCADDY_API_KEY") or "").strip() or None
    balance_url = (os.getenv("BUYERCADDY_BALANCE_URL", DEFAULT_BUYERCADDY_BALANCE_URL) or DEFAULT_BUYERCADDY_BALANCE_URL).strip()
    total_default = float(os.getenv("BUYERCADDY_TOTAL_CREDITS", str(DEFAULT_BUYERCADDY_TOTAL_CREDITS)))
    return api_key, balance_url, total_default


def _coerce_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_buyercaddy_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def _buyercaddy_header_variants(api_key: str) -> tuple[dict[str, str], ...]:
    return (
        {"X-API-Key": api_key},
        {"x-api-key": api_key},
        {"Authorization": f"Bearer {api_key}"},
        {"Authorization": api_key},
    )


def fetch_buyercaddy_usage_report() -> dict | None:
    api_key, balance_url, _ = _get_buyercaddy_config()
    if not api_key:
        return None

    session = _build_buyercaddy_session()
    last_error = None

    for headers in _buyercaddy_header_variants(api_key):
        try:
            resp = session.get(balance_url, headers=headers, timeout=8)
            print(f"[BuyerCaddy] Status code: {resp.status_code} with headers {list(headers.keys())}")
            if resp.status_code in (401, 403):
                last_error = requests.HTTPError(f"Auth failed with status {resp.status_code}")
                continue

            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_error = exc

    if last_error:
        raise last_error
    return None


def _extract_credit_values(payload: dict, total_default: float) -> tuple[float | None, float | None]:
    containers = [payload]
    for key in ("data", "account", "result", "credits"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            containers.append(nested)

    remaining_keys = (
        "credits_remaining",
        "remaining_credits",
        "remainingCredits",
        "available_credits",
        "availableCredits",
        "balance",
        "remaining",
        "credits",
    )
    total_keys = (
        "total_credits",
        "totalCredits",
        "credit_limit",
        "creditLimit",
        "limit",
        "total",
        "plan_credits",
        "planCredits",
    )
    used_keys = ("credits_used", "used_credits", "usedCredits", "usage", "consumed")

    remaining = None
    total = None
    used = None

    for container in containers:
        if remaining is None:
            for key in remaining_keys:
                remaining = _coerce_float(container.get(key))
                if remaining is not None:
                    break
        if total is None:
            for key in total_keys:
                total = _coerce_float(container.get(key))
                if total is not None:
                    break
        if used is None:
            for key in used_keys:
                used = _coerce_float(container.get(key))
                if used is not None:
                    break

    if remaining is None and total is not None and used is not None:
        remaining = max(total - used, 0.0)
    if total is None:
        total = total_default
    if remaining is None and used is not None:
        remaining = max(total - used, 0.0)
    if remaining is None:
        report_count = _coerce_float(payload.get("count"))
        if report_count is not None:
            remaining = max(total - report_count, 0.0)

    return remaining, total


def _get_recent_buyercaddy_usage_from_db(days: int = 7) -> float | None:
    try:
        from app.database import get_db_connection

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COALESCE(SUM(credits_consumed), 0)
                FROM usage_history
                WHERE tool_name = %s
                  AND date >= %s
                """,
                ("Buyercaddy", datetime.now(UTC).date() - timedelta(days=days - 1)),
            )
            total_usage = float(cur.fetchone()[0] or 0.0)
        finally:
            cur.close()
            conn.close()

        return total_usage / max(days, 1)
    except Exception as exc:
        print(f"[BuyerCaddy] Recent DB usage fallback error: {exc}")
        return None


def get_buyercaddy_usage_metrics(total_credits: float | None = None) -> dict:
    _, _, total_default = _get_buyercaddy_config()
    total = float(total_credits or total_default)
    report = fetch_buyercaddy_usage_report()
    used_credits = _coerce_float((report or {}).get("count"))

    if used_credits is None:
        raise ValueError("BuyerCaddy usage report did not include a usable count")

    today = datetime.now(UTC).date()
    days_elapsed = max(today.day, 1)
    avg_daily = used_credits / days_elapsed

    recent_avg = _get_recent_buyercaddy_usage_from_db(7)
    if recent_avg is not None and recent_avg > 0:
        avg_daily = recent_avg

    remaining = max(total - used_credits, 0.0)

    return {
        "used_credits": float(used_credits),
        "avg_daily_usage": float(avg_daily),
        "remaining_credits": float(remaining),
        "total_credits": float(total),
        "days_elapsed": days_elapsed,
        "source": "buyercaddy_report",
    }


def _derive_buyercaddy_remaining_from_posthog(total_default: float) -> tuple[float, float, bool] | None:
    posthog_key = (os.getenv("POSTHOG_PERSONAL_API_KEY") or "").strip()
    posthog_project_id = (os.getenv("POSTHOG_PROJECT_ID") or "").strip()
    if not posthog_key or not posthog_project_id:
        return None

    today = datetime.now(UTC).date()
    month_start = today.replace(day=1)
    days_to_fetch = max((today - month_start).days + 1, 1)
    daily_counts = fetch_posthog_daily_counts("data_fetched", days_to_fetch)
    if not daily_counts:
        return None

    used_credits = 0.0
    for row in daily_counts:
        try:
            if datetime.fromisoformat(row["day"]).date() >= month_start:
                used_credits += float(row["count"])
        except (KeyError, TypeError, ValueError):
            continue

    remaining = max(total_default - used_credits, 0.0)
    print(
        f"[BuyerCaddy] Derived remaining from PostHog month-to-date usage: "
        f"used={used_credits}, remaining={remaining}, total={total_default}"
    )
    return remaining, total_default, True


def _derive_buyercaddy_remaining_from_db(total_default: float) -> tuple[float, float, bool] | None:
    try:
        from app.database import get_db_connection

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COALESCE(SUM(credits_consumed), 0)
                FROM usage_history
                WHERE tool_name = %s
                  AND date_trunc('month', date) = date_trunc('month', CURRENT_DATE)
                """,
                ("Buyercaddy",),
            )
            used_credits = float(cur.fetchone()[0] or 0.0)
        finally:
            cur.close()
            conn.close()

        remaining = max(total_default - used_credits, 0.0)
        print(
            f"[BuyerCaddy] Derived remaining from DB month-to-date usage: "
            f"used={used_credits}, remaining={remaining}, total={total_default}"
        )
        return remaining, total_default, True
    except Exception as exc:
        print(f"[BuyerCaddy] DB fallback error: {exc}")
        return None


def get_buyercaddy_history(days: int = 7) -> list[dict]:
    """
    Fetch BuyerCaddy daily credit usage from PostHog.
    Falls back to deterministic mock data if PostHog is not configured.
    """
    try:
        daily_counts = fetch_posthog_daily_counts("data_fetched", days)
        if not daily_counts:
            print("[BuyerCaddy] No PostHog history available")
            return []

        sorted_counts = sorted(daily_counts, key=lambda row: row["day"])
        history = []
        total_days = len(sorted_counts)

        for index, row in enumerate(sorted_counts):
            days_ago = total_days - 1 - index
            if days_ago == 0:
                label = "Today"
            elif days_ago == 1:
                label = "Yesterday"
            else:
                label = f"{days_ago}d ago"

            history.append({
                "day": row["day"],
                "label": label,
                "credits": float(row["count"]),
                "count": int(row["count"]),
            })

        return history
    except Exception as e:
        print(f"[BuyerCaddy] History error: {str(e)}")
        return []




def fetch_buyercaddy_credit_snapshot() -> tuple[float, float, bool]:
    """Fetch BuyerCaddy credits and indicate whether the response is real."""
    api_key, balance_url, total_default = _get_buyercaddy_config()

    if not api_key:
        print("[BuyerCaddy] No API key in .env → returning 0.0")
        return 0.0, total_default, False

    try:
        data = fetch_buyercaddy_usage_report()
        remaining, total = _extract_credit_values(data, total_default)
        if remaining is None:
            raise ValueError(f"Could not parse BuyerCaddy credits from response keys: {list((data or {}).keys())}")

        print(f"[BuyerCaddy] Real remaining: {remaining}, total: {total}")
        return float(remaining), float(total), True
    except Exception as e:
        print(f"[BuyerCaddy] API fetch error: {str(e)}")
        derived_snapshot = _derive_buyercaddy_remaining_from_posthog(total_default)
        if derived_snapshot is not None:
            return derived_snapshot

        derived_snapshot = _derive_buyercaddy_remaining_from_db(total_default)
        if derived_snapshot is not None:
            return derived_snapshot

        print("[BuyerCaddy] No real fallback available → returning 0.0")
        return 0.0, total_default, False


def get_buyercaddy_remaining_credits() -> tuple:
    """
    Fetch remaining credits from BuyerCaddy API.
    Falls back to mock values if not configured or on request failure.
    """
    remaining, total, _ = fetch_buyercaddy_credit_snapshot()
    return remaining, total
