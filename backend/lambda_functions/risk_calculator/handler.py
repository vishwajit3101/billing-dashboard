"""
Lambda handler: calculate credit exhaustion predictions and risk levels for all tools.
- Read latest credit_snapshots and 7-day avg from usage_logs
- Compute days_left, exhaustion_date, risk_level
- Update ai_tools (risk_level, current_credits)
- Optionally write to exhaustion_predictions table
- Return risk summary
"""
import json
import logging
import os
from datetime import date, timedelta
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from calculator import compute_all

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)

TOOL_SLUGS = ("anthropic", "tavily", "fullenrich", "buyercaddy")


def _get_db_params() -> dict:
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
                "password": s.get("password", os.environ.get("DB_PASSWORD", ""))),
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


def get_latest_snapshots(cursor) -> dict[int, dict]:
    """Latest credit_snapshot per tool_id: { tool_id: { credits_remaining, credits_total } }."""
    cursor.execute("""
        SELECT DISTINCT ON (tool_id) tool_id, credits_remaining, credits_total
        FROM credit_snapshots
        ORDER BY tool_id, snapshot_at DESC
    """)
    return {row["tool_id"]: dict(row) for row in cursor.fetchall()}


def get_avg_daily_usage_7d(cursor, through_date: date) -> dict[int, float]:
    """7-day average credits_consumed per tool. Returns { tool_id: avg }."""
    start = through_date - timedelta(days=6)
    cursor.execute("""
        SELECT tool_id, avg(credits_consumed) AS avg_usage
        FROM usage_logs
        WHERE usage_date >= %s AND usage_date <= %s
        GROUP BY tool_id
    """, (start, through_date))
    return {row["tool_id"]: float(row["avg_usage"]) for row in cursor.fetchall()}


def get_tools_by_slug(cursor) -> dict[str, dict]:
    """Active tools by slug: { slug: { id, name, ... } }."""
    cursor.execute("""
        SELECT id, slug, name, current_credits, credits_total, risk_level
        FROM ai_tools
        WHERE is_active = true AND slug = ANY(%s)
    """, (list(TOOL_SLUGS),))
    return {row["slug"]: dict(row) for row in cursor.fetchall()}


def update_ai_tool_risk(cursor, tool_id: int, risk_level: str, current_credits: float) -> None:
    """Set ai_tools.risk_level and ai_tools.current_credits."""
    cursor.execute("""
        UPDATE ai_tools SET risk_level = %s, current_credits = %s WHERE id = %s
    """, (risk_level, current_credits, tool_id))
    logger.info("Updated ai_tools id=%s risk_level=%s current_credits=%s", tool_id, risk_level, current_credits)


def save_exhaustion_prediction(
    cursor,
    tool_id: int,
    predicted_date: date | None,
    avg_daily_usage: float,
    credits_remaining: float,
    days_left: float | None,
) -> None:
    """Insert into exhaustion_predictions if table exists."""
    try:
        cursor.execute("""
            INSERT INTO exhaustion_predictions
            (tool_id, predicted_date, avg_daily_usage, credits_remaining_at_compute, days_until_exhaustion, computed_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            tool_id,
            predicted_date.isoformat() if predicted_date else None,
            avg_daily_usage,
            credits_remaining,
            int(round(days_left)) if days_left is not None else None,
        ))
    except psycopg2.ProgrammingError as e:
        if "exhaustion_predictions" in str(e) or "does not exist" in str(e).lower():
            logger.debug("Table exhaustion_predictions not present: %s", e)
        else:
            raise


def handler(event: dict, context: Any) -> dict:
    """
    Process all tools: read credit_snapshots + 7-day usage, compute exhaustion and risk,
    update ai_tools, optionally write exhaustion_predictions, return risk summary.
    """
    today = date.today()
    summary = {
        "computed_at": today.isoformat(),
        "tools": [],
        "risk_summary": {"safe": 0, "warning": 0, "critical": 0},
        "error": None,
    }

    db_params = _get_db_params()
    try:
        conn = psycopg2.connect(**db_params)
    except Exception as e:
        logger.exception("DB connection failed: %s", e)
        summary["error"] = str(e)
        return {"statusCode": 500, "body": json.dumps(summary, default=str)}

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            tools = get_tools_by_slug(cur)
            snapshots = get_latest_snapshots(cur)
            avg_usage = get_avg_daily_usage_7d(cur, today)

            for slug in TOOL_SLUGS:
                tool = tools.get(slug)
                if not tool:
                    logger.warning("Tool not found: %s", slug)
                    continue
                tool_id = tool["id"]
                snap = snapshots.get(tool_id)
                if not snap:
                    logger.warning("No credit_snapshot for %s", slug)
                    summary["tools"].append({
                        "slug": slug,
                        "tool_id": tool_id,
                        "status": "no_snapshot",
                        "risk_level": tool.get("risk_level"),
                    })
                    continue

                credits_remaining = float(snap["credits_remaining"])
                credits_total = float(snap["credits_total"]) if snap.get("credits_total") else None
                avg_daily = avg_usage.get(tool_id, 0.0) or 0.0

                result = compute_all(
                    credits_remaining=credits_remaining,
                    credits_total=credits_total,
                    avg_daily_usage=avg_daily,
                    current_date=today,
                )

                summary["risk_summary"][result["risk_level"]] += 1
                summary["tools"].append({
                    "slug": slug,
                    "tool_id": tool_id,
                    "risk_level": result["risk_level"],
                    "percent_remaining": result["percent_remaining"],
                    "credits_remaining": credits_remaining,
                    "avg_daily_usage": result["avg_daily_usage"],
                    "days_left": result["days_left"],
                    "exhaustion_date": result["exhaustion_date"],
                })

                update_ai_tool_risk(cur, tool_id, result["risk_level"], credits_remaining)
                save_exhaustion_prediction(
                    cur,
                    tool_id=tool_id,
                    predicted_date=date.fromisoformat(result["exhaustion_date"]) if result["exhaustion_date"] else None,
                    avg_daily_usage=result["avg_daily_usage"],
                    credits_remaining=credits_remaining,
                    days_left=result["days_left"],
                )
            conn.commit()
    except Exception as e:
        logger.exception("Risk calculation failed: %s", e)
        conn.rollback()
        summary["error"] = str(e)
        return {"statusCode": 500, "body": json.dumps(summary, default=str)}
    finally:
        conn.close()

    logger.info(
        "Risk summary: safe=%s warning=%s critical=%s",
        summary["risk_summary"]["safe"],
        summary["risk_summary"]["warning"],
        summary["risk_summary"]["critical"],
    )
    return {"statusCode": 200, "body": json.dumps(summary, default=str)}
