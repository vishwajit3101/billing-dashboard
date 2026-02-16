"""
Lambda handler: check alert thresholds and send email alerts via AWS SES.
- Credits <20% → Warning; <10% → Critical
- Exhaustion <5 days → Urgent
- AWS budget >90% → Budget alert; over 100% → Over budget
- Usage spike (2× 7-day average) → Anomaly
- Store in alerts table; avoid duplicate alerts (same tool+type within 24h).
"""
import json
import logging
import os
from datetime import date, datetime, timezone, timedelta
from typing import Any

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

from email_templates import get_subject_and_html

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)

TOOL_SLUGS = ("anthropic", "tavily", "fullenrich", "buyercaddy")
DEDUPE_HOURS = 24  # do not re-send same alert type for same tool within this many hours


def _get_db_params() -> dict:
    arn = os.environ.get("DB_SECRET_ARN")
    if arn:
        try:
            import boto3 as _boto3
            import json as _json
            client = _boto3.client("secretsmanager")
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


def get_tools_with_snapshots(cursor) -> list[dict]:
    """Tools (id, slug, name) with latest credit_snapshot (credits_remaining, credits_total)."""
    cursor.execute("""
        SELECT t.id, t.slug, t.name,
               s.credits_remaining, s.credits_total
        FROM ai_tools t
        JOIN LATERAL (
            SELECT credits_remaining, credits_total
            FROM credit_snapshots
            WHERE tool_id = t.id
            ORDER BY snapshot_at DESC
            LIMIT 1
        ) s ON true
        WHERE t.is_active AND t.slug = ANY(%s)
    """, (list(TOOL_SLUGS),))
    return [dict(r) for r in cursor.fetchall()]


def get_7d_avg_and_recent_usage(cursor, today: date) -> tuple[dict[int, float], dict[int, float]]:
    """Returns (tool_id -> 7-day avg credits_consumed, tool_id -> most recent day usage)."""
    start_7 = today - timedelta(days=6)
    cursor.execute("""
        SELECT tool_id, avg(credits_consumed) AS avg_usage
        FROM usage_logs
        WHERE usage_date >= %s AND usage_date <= %s
        GROUP BY tool_id
    """, (start_7, today))
    avg_7d = {r["tool_id"]: float(r["avg_usage"]) for r in cursor.fetchall()}

    cursor.execute("""
        SELECT DISTINCT ON (tool_id) tool_id, credits_consumed
        FROM usage_logs
        WHERE usage_date <= %s
        ORDER BY tool_id, usage_date DESC
    """, (today,))
    recent = {r["tool_id"]: float(r["credits_consumed"]) for r in cursor.fetchall()}
    return avg_7d, recent


def get_days_left_per_tool(cursor) -> dict[int, float]:
    """Latest exhaustion_predictions days_until_exhaustion per tool, or from usage if table missing."""
    try:
        cursor.execute("""
            SELECT DISTINCT ON (tool_id) tool_id, days_until_exhaustion
            FROM exhaustion_predictions
            WHERE days_until_exhaustion IS NOT NULL
            ORDER BY tool_id, computed_at DESC
        """)
        return {r["tool_id"]: float(r["days_until_exhaustion"]) for r in cursor.fetchall()}
    except psycopg2.ProgrammingError:
        pass
    return {}


def get_days_left_from_snapshots(cursor, snapshots: list[dict], avg_7d: dict[int, float]) -> dict[int, float]:
    """Compute days_left = credits_remaining / avg_daily_usage for each tool."""
    out = {}
    for row in snapshots:
        tid = row["id"]
        rem = float(row["credits_remaining"])
        avg = avg_7d.get(tid, 0) or 0
        if avg > 0:
            out[tid] = rem / avg
    return out


def get_aws_spend_and_budget(cursor) -> tuple[float, float]:
    """Current month total spend and monthly budget. Returns (spend, budget)."""
    today = date.today()
    start = today.replace(day=1)
    cursor.execute("""
        SELECT coalesce(sum(amount_usd), 0) AS total
        FROM aws_spend
        WHERE spend_date >= %s AND spend_date <= %s
    """, (start, today))
    row = cursor.fetchone()
    spend = float(row["total"]) if row else 0.0
    cursor.execute("""
        SELECT monthly_limit_usd FROM aws_budgets
        WHERE effective_from <= %s
        ORDER BY effective_from DESC LIMIT 1
    """, (today,))
    row = cursor.fetchone()
    budget = float(row["monthly_limit_usd"]) if row else float(os.environ.get("AWS_MONTHLY_BUDGET_USD", "12000"))
    return spend, budget


def already_sent_recently(cursor, tool_id: int | None, alert_type: str, within_hours: int = DEDUPE_HOURS) -> bool:
    """True if we already sent this (tool_id, alert_type) within the last within_hours."""
    since = datetime.now(timezone.utc) - timedelta(hours=within_hours)
    if tool_id is None:
        cursor.execute("""
            SELECT 1 FROM alerts
            WHERE tool_id IS NULL AND alert_type = %s AND triggered_at >= %s
            LIMIT 1
        """, (alert_type, since))
    else:
        cursor.execute("""
            SELECT 1 FROM alerts
            WHERE tool_id = %s AND alert_type = %s AND triggered_at >= %s
            LIMIT 1
        """, (tool_id, alert_type, since))
    return cursor.fetchone() is not None


def insert_alert(cursor, tool_id: int | None, alert_type: str, threshold: float | None, message: str, payload: dict | None) -> None:
    cursor.execute("""
        INSERT INTO alerts (tool_id, alert_type, threshold, message, payload, triggered_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (tool_id, alert_type, threshold, message, json.dumps(payload) if payload else None))


def send_ses_email(to_address: str, subject: str, html_body: str, from_address: str | None = None) -> bool:
    from_address = from_address or os.environ.get("ALERT_FROM_EMAIL", os.environ.get("SES_FROM_EMAIL", ""))
    if not from_address or not to_address:
        logger.warning("SES skipped: missing ALERT_TO_EMAIL or ALERT_FROM_EMAIL")
        return False
    try:
        ses = boto3.client("ses")
        ses.send_email(
            Source=from_address,
            Destination={"ToAddresses": [to_address]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Html": {"Data": html_body, "Charset": "UTF-8"}},
            },
        )
        logger.info("SES sent to %s: %s", to_address, subject[:50])
        return True
    except Exception as e:
        logger.exception("SES send failed: %s", e)
        return False


def handler(event: dict, context: Any) -> dict:
    to_email = os.environ.get("ALERT_TO_EMAIL", "")
    summary = {"sent": [], "skipped_duplicate": [], "skipped_no_recipient": [], "errors": []}

    db_params = _get_db_params()
    try:
        conn = psycopg2.connect(**db_params)
    except Exception as e:
        logger.exception("DB connection failed: %s", e)
        summary["errors"].append(str(e))
        return {"statusCode": 500, "body": json.dumps(summary, default=str)}

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            today = date.today()
            tools = get_tools_with_snapshots(cur)
            avg_7d, recent_usage = get_7d_avg_and_recent_usage(cur, today)
            days_left_pred = get_days_left_per_tool(cur)
            if not days_left_pred and tools:
                days_left_pred = get_days_left_from_snapshots(cur, tools, avg_7d)
            aws_spend, aws_budget = get_aws_spend_and_budget(cur)

            # ----- Per-tool: credits %, exhaustion, usage spike -----
            for t in tools:
                tool_id = t["id"]
                name = t["name"]
                rem = float(t["credits_remaining"])
                total = t["credits_total"]
                total_f = float(total) if total is not None else None
                pct = (rem / total_f * 100) if total_f and total_f > 0 else None
                avg_u = avg_7d.get(tool_id, 0) or 0
                days_left = days_left_pred.get(tool_id)
                recent_u = recent_usage.get(tool_id, 0)

                # Credits < 10% → Critical
                if pct is not None and pct < 10:
                    at = "credits_critical"
                    if already_sent_recently(cur, tool_id, at):
                        summary["skipped_duplicate"].append(f"{name}:{at}")
                        continue
                    subj, html = get_subject_and_html("credits_critical", tool_name=name, percent_remaining=pct, credits_remaining=rem, credits_total=total_f)
                    if to_email and send_ses_email(to_email, subj, html):
                        insert_alert(cur, tool_id, at, 10, "Credits below 10%", {"percent_remaining": pct, "credits_remaining": rem})
                        summary["sent"].append(f"{name}:{at}")
                # Credits < 20% → Warning (only if not already critical)
                elif pct is not None and pct < 20:
                    at = "credits_warning"
                    if already_sent_recently(cur, tool_id, at):
                        summary["skipped_duplicate"].append(f"{name}:{at}")
                        continue
                    subj, html = get_subject_and_html("credits_warning", tool_name=name, percent_remaining=pct, credits_remaining=rem, credits_total=total_f)
                    if to_email and send_ses_email(to_email, subj, html):
                        insert_alert(cur, tool_id, at, 20, "Credits below 20%", {"percent_remaining": pct, "credits_remaining": rem})
                        summary["sent"].append(f"{name}:{at}")

                # Exhaustion < 5 days
                if days_left is not None and days_left < 5 and days_left >= 0:
                    at = "exhaustion_soon"
                    if already_sent_recently(cur, tool_id, at):
                        summary["skipped_duplicate"].append(f"{name}:{at}")
                        continue
                    exh_date = (today + timedelta(days=int(round(days_left)))).isoformat()
                    subj, html = get_subject_and_html("exhaustion_soon", tool_name=name, days_left=days_left, exhaustion_date=exh_date, credits_remaining=rem)
                    if to_email and send_ses_email(to_email, subj, html):
                        insert_alert(cur, tool_id, at, 5, "Exhaustion in under 5 days", {"days_left": days_left, "exhaustion_date": exh_date})
                        summary["sent"].append(f"{name}:{at}")

                # Usage spike 2× average
                if avg_u > 0 and recent_u >= 2 * avg_u:
                    at = "usage_spike"
                    if already_sent_recently(cur, tool_id, at):
                        summary["skipped_duplicate"].append(f"{name}:{at}")
                        continue
                    subj, html = get_subject_and_html("usage_spike", tool_name=name, usage_today=recent_u, avg_7d=avg_u, multiplier=recent_u / avg_u)
                    if to_email and send_ses_email(to_email, subj, html):
                        insert_alert(cur, tool_id, at, 2.0, "Usage spike (2× average)", {"recent_usage": recent_u, "avg_7d": avg_u})
                        summary["sent"].append(f"{name}:{at}")

            # ----- AWS budget (tool_id = None) -----
            if aws_budget > 0:
                pct = (aws_spend / aws_budget) * 100
                if pct > 100:
                    at = "aws_over_budget"
                    if not already_sent_recently(cur, None, at):
                        subj, html = get_subject_and_html("aws_over_budget", spend=aws_spend, budget=aws_budget, percent=pct)
                        if to_email and send_ses_email(to_email, subj, html):
                            insert_alert(cur, None, at, 100, "AWS over budget", {"spend": aws_spend, "budget": aws_budget, "percent": pct})
                            summary["sent"].append(f"aws:{at}")
                        else:
                            summary["skipped_no_recipient"].append("aws_over_budget")
                elif pct > 90:
                    at = "aws_budget_warning"
                    if not already_sent_recently(cur, None, at):
                        subj, html = get_subject_and_html("aws_budget_warning", spend=aws_spend, budget=aws_budget, percent=pct)
                        if to_email and send_ses_email(to_email, subj, html):
                            insert_alert(cur, None, at, 90, "AWS budget above 90%", {"spend": aws_spend, "budget": aws_budget, "percent": pct})
                            summary["sent"].append(f"aws:{at}")
                        else:
                            summary["skipped_no_recipient"].append("aws_budget_warning")

            if not to_email:
                summary["skipped_no_recipient"].append("ALERT_TO_EMAIL not set")
            conn.commit()
    except Exception as e:
        logger.exception("Alert run failed: %s", e)
        conn.rollback()
        summary["errors"].append(str(e))
        return {"statusCode": 500, "body": json.dumps(summary, default=str)}
    finally:
        conn.close()

    return {"statusCode": 200, "body": json.dumps(summary, default=str)}
