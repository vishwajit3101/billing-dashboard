"""
Dashboard API endpoint logic.
Reads from PostgreSQL (ai_tools, credit_snapshots, usage_logs, aws_spend, aws_budgets, alerts).
"""
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

# Ensure backend root is on path when running as Lambda
import sys
import os
_here = os.path.dirname(os.path.abspath(__file__))
_backend_root = os.path.abspath(os.path.join(_here, "..", ".."))
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from src.shared.db import get_cursor


def _serial(obj: Any) -> Any:
    """Convert Decimal/datetime/date for JSON."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serial(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serial(x) for x in obj]
    return obj


def _json_response(data: Any, status: int = 200) -> dict:
    return {"statusCode": status, "body": json.dumps(_serial(data))}


# ---------------------------------------------------------------------------
# GET /api/tools — all tools with credits, risk level, exhaustion date
# ---------------------------------------------------------------------------
def get_tools() -> dict:
    """Return all tools with current credits, risk level, exhaustion date, avg daily, cost this month."""
    try:
        with get_cursor() as cur:
            # Tools joined with latest credit_snapshot for current credit data and risk level
            cur.execute("""
                SELECT t.id, t.slug, t.name, t.description, t.risk_level,
                       COALESCE(cs.credits_remaining, t.current_credits) AS credits_remaining,
                       COALESCE(cs.credits_total, t.credits_total) AS credits_total,
                       cs.cost_usd
                FROM ai_tools t
                LEFT JOIN LATERAL (
                    SELECT credits_remaining, credits_total, cost_usd
                    FROM credit_snapshots
                    WHERE tool_id = t.id
                    ORDER BY snapshot_at DESC
                    LIMIT 1
                ) cs ON true
                WHERE t.is_active = true
                ORDER BY t.name
            """)
            tools = [dict(row) for row in cur.fetchall()]

            if not tools:
                return _json_response({"tools": [], "meta": {"count": 0}})

            tool_ids = [t["id"] for t in tools]

            # Avg daily usage (last 7 days) from usage_logs
            week_ago = date.today() - timedelta(days=7)
            cur.execute("""
                SELECT tool_id,
                       COALESCE(AVG(credits_consumed), 0) AS avg_daily
                FROM usage_logs
                WHERE tool_id = ANY(%s) AND usage_date >= %s
                GROUP BY tool_id
            """, (tool_ids, week_ago))
            avg_daily = {row["tool_id"]: float(row["avg_daily"]) for row in cur.fetchall()}

            out = []
            for t in tools:
                tid = t["id"]
                credits_total = float(t["credits_total"] or 0)
                credits_remaining = float(t["credits_remaining"] or 0)
                pct_remaining = (credits_remaining / credits_total * 100) if credits_total > 0 else 100
                avg = avg_daily.get(tid, 0)
                # Derive exhaustion_date from avg daily usage and credits remaining (no exhaustion_predictions table)
                exhaustion_date = None
                if avg > 0 and credits_remaining > 0:
                    days_left = credits_remaining / avg
                    try:
                        pred_date = date.today() + timedelta(days=days_left)
                        exhaustion_date = pred_date.strftime("%b %d")
                    except Exception:
                        pass

                out.append({
                    "tool_id": t["slug"],
                    "id": tid,
                    "name": t["name"],
                    "description": t["description"] or "",
                    "credits_remaining": int(credits_remaining),
                    "credits_total": int(credits_total) if credits_total else None,
                    "percent_remaining": round(pct_remaining, 1),
                    "risk_level": str(t["risk_level"]) if t["risk_level"] else "safe",
                    "exhaustion_date": exhaustion_date,
                    "avg_daily_usage": round(avg, 0),
                    "cost_this_month_usd": round(float(t["cost_usd"] or 0), 2),
                })
            return _json_response({"tools": out, "meta": {"count": len(out)}})
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": "tools_failed", "message": str(e)})}


# ---------------------------------------------------------------------------
# GET /api/tools/{tool_id}/trend?days=7 — usage trend data
# ---------------------------------------------------------------------------
def get_tool_trend(tool_id: str, days: int = 7) -> dict:
    """Return daily usage trend for a tool (slug) over the last `days` days."""
    if not tool_id:
        return {"statusCode": 400, "body": json.dumps({"error": "tool_id_required"})}
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM ai_tools WHERE slug = %s AND is_active = true", (tool_id,))
            row = cur.fetchone()
            if not row:
                return {"statusCode": 404, "body": json.dumps({"error": "tool_not_found", "tool_id": tool_id})}
            tid = row["id"]

            start = date.today() - timedelta(days=days)
            cur.execute("""
                SELECT usage_date AS date, credits_consumed AS value
                FROM usage_logs
                WHERE tool_id = %s AND usage_date >= %s
                ORDER BY usage_date ASC
            """, (tid, start))
            rows = cur.fetchall()
            trend = [{"date": r["date"].isoformat(), "value": float(r["value"])} for r in rows]
            return _json_response({
                "tool_id": tool_id,
                "days": days,
                "trend": trend,
                "meta": {"from": start.isoformat(), "to": date.today().isoformat()},
            })
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": "trend_failed", "message": str(e)})}


# ---------------------------------------------------------------------------
# GET /api/aws/spend — AWS monthly spend and service breakdown
# ---------------------------------------------------------------------------
def get_aws_spend() -> dict:
    """Return current month spend, budget, percent of budget, change %, cost by service."""
    try:
        with get_cursor() as cur:
            today = date.today()
            month_start = today.replace(day=1)
            # Current month total spend
            cur.execute("""
                SELECT COALESCE(SUM(amount_usd), 0) AS total
                FROM aws_spend
                WHERE spend_date >= %s AND spend_date <= %s
            """, (month_start, today))
            current_spend = float(cur.fetchone()["total"])

            # Previous month for change %
            prev_month_end = month_start - timedelta(days=1)
            prev_month_start = prev_month_end.replace(day=1)
            cur.execute("""
                SELECT COALESCE(SUM(amount_usd), 0) AS total
                FROM aws_spend
                WHERE spend_date >= %s AND spend_date <= %s
            """, (prev_month_start, prev_month_end))
            prev_spend = float(cur.fetchone()["total"])
            change_pct = ((current_spend - prev_spend) / prev_spend * 100) if prev_spend else 0

            # Budget (active for current month)
            cur.execute("""
                SELECT monthly_limit_usd
                FROM aws_budgets
                WHERE effective_from <= %s
                ORDER BY effective_from DESC
                LIMIT 1
            """, (today,))
            budget_row = cur.fetchone()
            budget = float(budget_row["monthly_limit_usd"]) if budget_row else 0
            percent_of_budget = (current_spend / budget * 100) if budget else 0
            status = "critical" if current_spend > budget else ("warning" if percent_of_budget >= 90 else "healthy")

            # Cost by service (current month)
            cur.execute("""
                SELECT service_name AS service, SUM(amount_usd) AS cost
                FROM aws_spend
                WHERE spend_date >= %s AND spend_date <= %s
                GROUP BY service_name
                ORDER BY cost DESC
            """, (month_start, today))
            cost_by_service = [{"service": r["service"], "cost_usd": float(r["cost"])} for r in cur.fetchall()]

            # Monthly spend trend (last 6 months)
            trend_months = []
            for i in range(6):
                d = today.replace(day=1) - timedelta(days=1)
                for _ in range(i):
                    d = (d.replace(day=1) - timedelta(days=1))
                m_start = d.replace(day=1)
                if m_start.month == 12:
                    m_end = m_start.replace(day=31)
                else:
                    m_end = (m_start.replace(month=m_start.month + 1) - timedelta(days=1))
                cur.execute("""
                    SELECT COALESCE(SUM(amount_usd), 0) AS total
                    FROM aws_spend
                    WHERE spend_date >= %s AND spend_date <= %s
                """, (m_start, m_end))
                trend_months.append({"month": m_start.strftime("%b"), "spend_usd": float(cur.fetchone()["total"])})
            trend_months.reverse()

            return _json_response({
                "current_spend_usd": round(current_spend, 2),
                "budget_usd": round(budget, 2),
                "percent_of_budget": round(percent_of_budget, 1),
                "change_percent": round(change_pct, 1),
                "status": status,
                "cost_by_service": cost_by_service,
                "monthly_trend": trend_months,
                "meta": {"period_start": month_start.isoformat(), "period_end": today.isoformat()},
            })
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": "aws_spend_failed", "message": str(e)})}


# ---------------------------------------------------------------------------
# GET /api/alerts — active alerts
# ---------------------------------------------------------------------------
def get_alerts() -> dict:
    """Return active (recent) alerts with type, message, tool_id, etc."""
    try:
        with get_cursor() as cur:
            # Alerts from last 7 days as "active"
            since = (datetime.utcnow() - timedelta(days=7)).date()
            cur.execute("""
                SELECT a.id, a.tool_id, a.alert_type, a.threshold, a.message, a.triggered_at, a.payload,
                       t.slug AS tool_slug, t.name AS tool_name
                FROM alerts a
                LEFT JOIN ai_tools t ON t.id = a.tool_id
                WHERE a.triggered_at >= %s
                ORDER BY a.triggered_at DESC
            """, (since,))
            rows = cur.fetchall()
            alerts = []
            for r in rows:
                alerts.append({
                    "id": r["id"],
                    "tool_id": r["tool_slug"] or r["tool_id"],
                    "tool_name": r["tool_name"],
                    "alert_type": r["alert_type"],
                    "message": r["message"] or _alert_type_message(r["alert_type"]),
                    "threshold": float(r["threshold"]) if r["threshold"] is not None else None,
                    "triggered_at": r["triggered_at"].isoformat() if r["triggered_at"] else None,
                    "payload": r["payload"],
                })
            return _json_response({"alerts": alerts, "meta": {"count": len(alerts)}})
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": "alerts_failed", "message": str(e)})}


def _alert_type_message(alert_type: str) -> str:
    m = {
        "credits_warning": "Credits below 20%",
        "credits_critical": "Credits Critical",
        "exhaustion_soon": "Exhaustion in less than 5 days",
        "aws_over_budget": "Over Budget",
        "aws_budget_warning": "AWS budget above 90%",
        "usage_spike": "Usage spike detected",
    }
    return m.get(alert_type, str(alert_type))


# ---------------------------------------------------------------------------
# GET /api/export — export report (CSV or JSON)
# ---------------------------------------------------------------------------
def get_export(range_param: str = "30d", fmt: str = "csv") -> dict:
    """Export report data for the given range (7d or 30d) as CSV or JSON."""
    try:
        days = 30 if range_param == "30d" else 7
        start = date.today() - timedelta(days=days)
        with get_cursor() as cur:
            cur.execute("""
                SELECT t.slug, t.name, t.current_credits
                FROM ai_tools t
                WHERE t.is_active = true
            """)
            tools = cur.fetchall()
            cur.execute("""
                SELECT t.slug, ul.usage_date, ul.credits_consumed
                FROM usage_logs ul
                JOIN ai_tools t ON t.id = ul.tool_id
                WHERE ul.usage_date >= %s
                ORDER BY t.slug, ul.usage_date
            """, (start,))
            usage_rows = cur.fetchall()
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": "export_failed", "message": str(e)})}

    # Build report rows
    report = []
    for r in tools:
        report.append({"tool": r["slug"], "name": r["name"], "credits_remaining": float(r["current_credits"] or 0), "date": None, "credits_used": None})
    for r in usage_rows:
        report.append({"tool": r["slug"], "name": None, "credits_remaining": None, "date": r["usage_date"].isoformat(), "credits_used": float(r["credits_consumed"])})

    if fmt == "json":
        body = json.dumps(_serial({"range": range_param, "days": days, "generated_at": datetime.utcnow().isoformat() + "Z", "report": report}))
        content_type = "application/json"
    else:
        lines = ["tool,name,date,credits_remaining,credits_used"]
        for row in report:
            lines.append(",".join(str(x) if x is not None else "" for x in [row["tool"], row["name"], row["date"], row["credits_remaining"], row["credits_used"]]))
        body = "\n".join(lines)
        content_type = "text/csv"

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="billing-report-{range_param}.{fmt}"',
        },
        "body": body,
    }
