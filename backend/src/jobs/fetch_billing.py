"""
Lambda: Fetch all tool billing + AWS spend (FR1).
Trigger: EventBridge hourly.
Writes: tool_snapshots, aws_spend_snapshots, aws_service_breakdown.
"""
from datetime import datetime, date
from src.shared.db import get_cursor
from src.integrations import anthropic_billing, tavily_billing, fullenrich_billing, buyercaddy_billing
from src.integrations import aws_cost_explorer


def get_tool_id_by_slug(cur, slug: str) -> int | None:
    cur.execute("SELECT id FROM tools WHERE slug = %s", (slug,))
    row = cur.fetchone()
    return row["id"] if row else None


def handler(event: dict, context: object) -> dict:
    now = datetime.utcnow()
    with get_cursor() as cur:
        # Tool snapshots (credits)
        for slug, fetcher in [
            ("anthropic", anthropic_billing.fetch_anthropic_billing),
            ("tavily", tavily_billing.fetch_tavily_billing),
            ("fullenrich", fullenrich_billing.fetch_fullenrich_billing),
            ("buyercaddy", buyercaddy_billing.fetch_buyercaddy_billing),
        ]:
            tid = get_tool_id_by_slug(cur, slug)
            if not tid:
                continue
            data = fetcher()
            cur.execute(
                """INSERT INTO tool_snapshots (tool_id, credits_remaining, credits_total, cost_this_month_usd, snapshot_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    tid,
                    data.get("credits_remaining", 0),
                    data.get("credits_total"),
                    data.get("cost_this_month_usd"),
                    now,
                ),
            )
        # AWS spend
        spend = aws_cost_explorer.fetch_aws_current_month_spend()
        cur.execute(
            """INSERT INTO aws_spend_snapshots (period_start, period_end, total_spend_usd, snapshot_at)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (spend["period_start"], spend["period_end"], spend["total_spend_usd"], now),
        )
        row = cur.fetchone()
        breakdown = aws_cost_explorer.fetch_aws_service_breakdown(
            date.fromisoformat(spend["period_start"]),
            date.fromisoformat(spend["period_end"]),
        )
        for item in breakdown:
            cur.execute(
                """INSERT INTO aws_service_breakdown (period_start, period_end, service_name, cost_usd, snapshot_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (spend["period_start"], spend["period_end"], item["service_name"], item["cost_usd"], now),
            )
    return {"status": "ok", "snapshot_at": now.isoformat()}
