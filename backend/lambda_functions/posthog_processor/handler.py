"""
Lambda handler: process PostHog events to calculate credit usage per tool.
- Query PostHog for event counts (last 24h or for a given date)
- Read posthog_event_credit_mapping (event_name -> tool_id, credits_per_event)
- Compute credits_consumed = sum(event_count × credits_per_event) per tool
- Store daily totals in usage_logs
- Compute 7-day average consumption
"""
import json
import logging
import os
from datetime import date, timedelta
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from posthog_client import get_event_counts_last_24h

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)

# DB connection: env or Secrets Manager (same pattern as billing_fetcher)
def _get_db_params() -> dict:
    import os
    arn = os.environ.get("DB_SECRET_ARN")
    if arn:
        try:
            import boto3
            import json as _json
            client = boto3.client("secretsmanager")
            resp = client.get_secret_value(SecretId=arn)
            s = _json.loads(resp["SecretString"])
            return {
                "host": s.get("host", s.get("hostname", os.environ.get("DB_HOST", "localhost"))),
                "port": int(s.get("port", os.environ.get("DB_PORT", "5432"))),
                "dbname": s.get("dbname", s.get("database", os.environ.get("DB_NAME", "billing_watch"))),
                "user": s.get("username", s.get("user", os.environ.get("DB_USER", "postgres"))),
                "password": s.get("password", os.environ.get("DB_PASSWORD", "")),
            }
        except Exception as e:
            logger.warning("Secrets Manager failed, using env: %s", e)
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "dbname": os.environ.get("DB_NAME", "billing_watch"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", ""),
    }


def get_event_mappings(cursor) -> list[dict]:
    """Read posthog_event_credit_mapping: event_name, tool_id, credits_per_event."""
    cursor.execute("""
        SELECT event_name, tool_id, credits_per_event
        FROM posthog_event_credit_mapping
    """)
    return [dict(row) for row in cursor.fetchall()]


def compute_credits_by_tool(
    event_counts: dict[str, int],
    mappings: list[dict],
) -> dict[int, tuple[float, int]]:
    """
    For each tool_id, compute (credits_consumed, events_count).
    credits_consumed = sum(event_count × credits_per_event) for events mapping to that tool.
    events_count = sum of raw event counts for that tool's events.
    """
    by_tool: dict[int, tuple[float, int]] = {}
    for m in mappings:
        tool_id = m["tool_id"]
        event_name = m["event_name"]
        credits_per = m["credits_per_event"]
        count = event_counts.get(event_name, 0)
        credits = count * credits_per
        events_sum = count
        if tool_id in by_tool:
            prev_c, prev_e = by_tool[tool_id]
            by_tool[tool_id] = (prev_c + credits, prev_e + events_sum)
        else:
            by_tool[tool_id] = (float(credits), events_sum)
    return by_tool


def save_usage_logs(
    cursor,
    by_tool: dict[int, tuple[float, int]],
    usage_date: date,
) -> None:
    """Upsert usage_logs: one row per tool for usage_date."""
    for tool_id, (credits_consumed, events_count) in by_tool.items():
        cursor.execute("""
            INSERT INTO usage_logs (tool_id, usage_date, credits_consumed, events_count)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (tool_id, usage_date)
            DO UPDATE SET credits_consumed = EXCLUDED.credits_consumed, events_count = EXCLUDED.events_count
        """, (tool_id, usage_date, credits_consumed, events_count))
    logger.info("Saved usage_logs for %s: %d tools", usage_date, len(by_tool))


def get_7day_average_by_tool(cursor, through_date: date) -> dict[int, float]:
    """Return tool_id -> average credits_consumed over the last 7 days (including through_date)."""
    start = through_date - timedelta(days=6)
    cursor.execute("""
        SELECT tool_id, avg(credits_consumed) AS avg_credits
        FROM usage_logs
        WHERE usage_date >= %s AND usage_date <= %s
        GROUP BY tool_id
    """, (start, through_date))
    return {row["tool_id"]: float(row["avg_credits"]) for row in cursor.fetchall()}


def handler(event: dict, context: Any) -> dict:
    """
    Main Lambda entrypoint.
    - Fetches PostHog event counts for last 24 hours.
    - Attributes them to today's usage_date (one row per day; overwrites today's row on each run).
    - Reads event_mappings from DB, computes credits per tool, writes usage_logs.
    - Computes 7-day average consumption and returns in summary.
    """
    # Use today as usage_date for "last 24h" so we have a rolling daily total for the current day
    usage_date = date.today()
    summary = {
        "usage_date": usage_date.isoformat(),
        "event_counts": {},
        "credits_by_tool": [],
        "usage_logs_saved": 0,
        "avg_7day_by_tool": [],
        "error": None,
    }

    # 1) PostHog: event counts last 24h
    event_counts = get_event_counts_last_24h()
    summary["event_counts"] = event_counts
    if not event_counts and (os.environ.get("POSTHOG_PROJECT_ID") and os.environ.get("POSTHOG_API_KEY")):
        summary["error"] = "PostHog returned no event counts"
        logger.warning("PostHog returned no events")
    elif not event_counts:
        logger.info("No PostHog config or no events; skipping usage_logs write")
        return {"statusCode": 200, "body": json.dumps(summary, default=str)}

    db_params = _get_db_params()
    try:
        conn = psycopg2.connect(**db_params)
    except Exception as e:
        logger.exception("DB connection failed: %s", e)
        summary["error"] = str(e)
        return {"statusCode": 500, "body": json.dumps(summary, default=str)}

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 2) Read event mappings (event_name -> tool_id, credits_per_event)
            mappings = get_event_mappings(cur)
            if not mappings:
                logger.warning("No rows in posthog_event_credit_mapping")
                conn.close()
                return {"statusCode": 200, "body": json.dumps(summary, default=str)}

            # 3) Calculate credits per tool: event_count × credits_per_event
            by_tool = compute_credits_by_tool(event_counts, mappings)
            for tool_id, (credits, events) in by_tool.items():
                summary["credits_by_tool"].append({
                    "tool_id": tool_id,
                    "credits_consumed": round(credits, 2),
                    "events_count": events,
                })

            # 4) Store daily totals in usage_logs
            save_usage_logs(cur, by_tool, usage_date)
            conn.commit()
            summary["usage_logs_saved"] = len(by_tool)
            logger.info("Wrote %d usage_logs rows for %s", len(by_tool), usage_date)

            # 5) 7-day average consumption
            avg_7d = get_7day_average_by_tool(cur, usage_date)
            summary["avg_7day_by_tool"] = [
                {"tool_id": tid, "avg_credits_consumed_7d": round(avg, 2)}
                for tid, avg in avg_7d.items()
            ]
            logger.info("7-day averages: %s", avg_7d)
    finally:
        conn.close()

    return {"statusCode": 200, "body": json.dumps(summary, default=str)}
