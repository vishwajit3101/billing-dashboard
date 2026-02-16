"""
Lambda handler: fetch billing data from AI tool APIs and AWS Cost Explorer;
store in RDS credit_snapshots and aws_spend.
"""
import json
import logging
from calendar import monthrange
from datetime import datetime, timezone, date
from typing import Any

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

from config import get_db_params, TOOL_SLUGS, AWS_MONTHLY_BUDGET_USD
from api_clients import FETCHERS

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)


def get_tool_id_by_slug(cursor, slug: str) -> int | None:
    """Return ai_tools.id for slug, or None if not found."""
    cursor.execute("SELECT id FROM ai_tools WHERE slug = %s AND is_active = true", (slug,))
    row = cursor.fetchone()
    return row["id"] if row else None


def save_snapshot(
    cursor,
    tool_id: int,
    credits_remaining: float,
    credits_total: float | None,
    cost_usd: float | None,
    snapshot_at: datetime,
) -> None:
    """Insert one row into credit_snapshots."""
    cursor.execute(
        """
        INSERT INTO credit_snapshots (tool_id, credits_remaining, credits_total, cost_usd, snapshot_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (tool_id, credits_remaining, credits_total, cost_usd, snapshot_at),
    )
    logger.info("Saved snapshot tool_id=%s credits_remaining=%s", tool_id, credits_remaining)


def get_aws_spend() -> dict[str, Any]:
    """
    Fetch current month's AWS spend and breakdown by service using Cost Explorer.
    Returns dict with total_spend_usd, by_service (list of { service_name, amount_usd }),
    period_start, period_end (YYYY-MM-DD).
    """
    today = date.today()
    period_start = today.replace(day=1)
    _, last_day = monthrange(today.year, today.month)
    period_end = today.replace(day=last_day)
    start_str = period_start.strftime("%Y-%m-%d")
    end_str = period_end.strftime("%Y-%m-%d")

    try:
        ce = boto3.client("ce")
        logger.info("Fetching AWS Cost Explorer data for %s to %s", start_str, end_str)

        # Get cost and usage grouped by service
        response = ce.get_cost_and_usage(
            TimePeriod={"Start": start_str, "End": end_str},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
    except Exception as e:
        logger.exception("Cost Explorer request failed: %s", e)
        return {
            "total_spend_usd": 0.0,
            "by_service": [],
            "period_start": start_str,
            "period_end": end_str,
            "error": str(e),
        }

    by_service: list[dict[str, Any]] = []
    total = 0.0

    for result in response.get("ResultsByTime", []):
        for group in result.get("Groups", []):
            # Keys[0] is the service name (e.g. "Amazon Elastic Compute Cloud - Compute")
            name = (group.get("Keys") or [""])[0]
            if not name or name == "NoService":
                continue
            amount_str = group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", "0")
            try:
                amount = float(amount_str)
            except (TypeError, ValueError):
                amount = 0.0
            if amount <= 0:
                continue
            # Shorten common names for dashboard (e.g. "Amazon EC2" -> "EC2")
            short_name = name.replace("Amazon ", "").split(" - ")[0].strip() or name
            by_service.append({"service_name": short_name, "amount_usd": round(amount, 2)})
            total += amount

    total = round(total, 2)
    logger.info("AWS spend total=%.2f services=%d", total, len(by_service))
    return {
        "total_spend_usd": total,
        "by_service": by_service,
        "period_start": start_str,
        "period_end": end_str,
    }


def save_aws_spend(
    cursor,
    by_service: list[dict[str, Any]],
    period_start: str,
    period_end: str,
    spend_date: date,
) -> None:
    """Insert AWS spend breakdown into aws_spend table (one row per service)."""
    for item in by_service:
        cursor.execute(
            """
            INSERT INTO aws_spend (service_name, amount_usd, spend_date, period_start, period_end)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                item["service_name"],
                item["amount_usd"],
                spend_date,
                period_start,
                period_end,
            ),
        )
    logger.info("Saved aws_spend: %d service rows for %s", len(by_service), period_start)


def get_budget_from_db(cursor) -> float | None:
    """Return current month's budget (monthly_limit_usd) from aws_budgets, or None."""
    cursor.execute(
        """
        SELECT monthly_limit_usd FROM aws_budgets
        WHERE effective_from <= CURRENT_DATE
        ORDER BY effective_from DESC
        LIMIT 1
        """
    )
    row = cursor.fetchone()
    return float(row["monthly_limit_usd"]) if row else None


def handler(event: dict, context: Any) -> dict:
    """
    Main Lambda entrypoint.
    Fetches credits from Anthropic, Tavily, FullEnrich, Buyercaddy → credit_snapshots.
    Fetches AWS spend from Cost Explorer → aws_spend.
    Returns summary with success count, failed tools, AWS summary, and budget %.
    """
    snapshot_at = datetime.now(timezone.utc)
    summary = {
        "success_count": 0,
        "failed_count": 0,
        "failed_tools": [],
        "results": [],
        "snapshot_at": snapshot_at.isoformat(),
        "aws": None,
    }

    logger.info("Starting billing fetch for tools: %s", list(TOOL_SLUGS))

    db_params = get_db_params()
    try:
        conn = psycopg2.connect(**db_params)
    except Exception as e:
        logger.exception("Failed to connect to RDS: %s", e)
        summary["error"] = str(e)
        summary["failed_count"] = len(TOOL_SLUGS)
        summary["failed_tools"] = list(TOOL_SLUGS)
        return {"statusCode": 500, "body": json.dumps(summary)}

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # ---------- AI tool credit fetches ----------
            for slug in TOOL_SLUGS:
                tool_id = get_tool_id_by_slug(cur, slug)
                if not tool_id:
                    logger.warning("Tool not found or inactive: %s", slug)
                    summary["failed_tools"].append(slug)
                    summary["failed_count"] += 1
                    summary["results"].append({"slug": slug, "status": "skipped", "reason": "tool not in ai_tools"})
                    continue

                fetcher = FETCHERS.get(slug)
                if not fetcher:
                    logger.warning("No fetcher for slug: %s", slug)
                    summary["failed_tools"].append(slug)
                    summary["failed_count"] += 1
                    summary["results"].append({"slug": slug, "status": "skipped", "reason": "no fetcher"})
                    continue

                try:
                    data = fetcher()
                except Exception as e:
                    logger.exception("Fetch failed for %s: %s", slug, e)
                    summary["failed_tools"].append(slug)
                    summary["failed_count"] += 1
                    summary["results"].append({"slug": slug, "status": "error", "error": str(e)})
                    continue

                if data is None:
                    logger.warning("Fetcher returned None for %s", slug)
                    summary["failed_tools"].append(slug)
                    summary["failed_count"] += 1
                    summary["results"].append({"slug": slug, "status": "error", "error": "no data"})
                    continue

                try:
                    save_snapshot(
                        cur,
                        tool_id=tool_id,
                        credits_remaining=data["credits_remaining"],
                        credits_total=data.get("credits_total"),
                        cost_usd=data.get("cost_usd"),
                        snapshot_at=snapshot_at,
                    )
                    conn.commit()
                except Exception as e:
                    logger.exception("Failed to save snapshot for %s: %s", slug, e)
                    conn.rollback()
                    summary["failed_tools"].append(slug)
                    summary["failed_count"] += 1
                    summary["results"].append({"slug": slug, "status": "db_error", "error": str(e)})
                    continue

                summary["success_count"] += 1
                summary["results"].append({
                    "slug": slug,
                    "status": "ok",
                    "credits_remaining": data["credits_remaining"],
                    "credits_total": data.get("credits_total"),
                    "cost_usd": data.get("cost_usd"),
                })
                logger.info("Fetched and saved %s: credits_remaining=%s", slug, data["credits_remaining"])

            # ---------- AWS Cost Explorer ----------
            aws_data = get_aws_spend()
            budget_usd = get_budget_from_db(cur) if cur else None
            if budget_usd is None:
                budget_usd = AWS_MONTHLY_BUDGET_USD
                logger.info("Using default AWS budget: %.2f", budget_usd)
            total_spend = aws_data.get("total_spend_usd", 0.0)
            percent_used = (total_spend / budget_usd * 100) if budget_usd else 0.0

            summary["aws"] = {
                "total_spend_usd": total_spend,
                "budget_usd": budget_usd,
                "percent_of_budget_used": round(percent_used, 2),
                "by_service": aws_data.get("by_service", []),
                "period_start": aws_data.get("period_start"),
                "period_end": aws_data.get("period_end"),
            }
            if aws_data.get("error"):
                summary["aws"]["error"] = aws_data["error"]
                logger.warning("AWS Cost Explorer had error: %s", aws_data["error"])
            else:
                try:
                    spend_date = date.today()
                    save_aws_spend(
                        cur,
                        aws_data.get("by_service", []),
                        aws_data.get("period_start", ""),
                        aws_data.get("period_end", ""),
                        spend_date,
                    )
                    conn.commit()
                    logger.info("Saved AWS spend: %.2f USD, %d services", total_spend, len(aws_data.get("by_service", [])))
                except Exception as e:
                    logger.exception("Failed to save aws_spend: %s", e)
                    conn.rollback()
                    summary["aws"]["save_error"] = str(e)

    finally:
        conn.close()

    logger.info(
        "Billing fetch complete: success=%s failed=%s aws_total=%.2f percent=%.1f%%",
        summary["success_count"],
        summary["failed_count"],
        summary.get("aws", {}).get("total_spend_usd", 0),
        summary.get("aws", {}).get("percent_of_budget_used", 0),
    )
    return {
        "statusCode": 200,
        "body": json.dumps(summary, default=str),
    }
