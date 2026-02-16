"""
API Gateway: GET /api/dashboard
Returns unified dashboard JSON for frontend (risk banner, Anthropic, AWS, tools, PostHog).
Query: range=7d|14d|30d|90d
"""
from datetime import datetime, date, timedelta
from src.shared.db import get_cursor
from src.shared.risk import compute_credit_status, compute_aws_status, compute_posthog_status


def handler(event: dict, context: object) -> dict:
    # API Gateway passes event with queryStringParameters, etc.
    params = event.get("queryStringParameters") or {}
    range_param = params.get("range", "30d")
    # TODO: query tool_snapshots, tool_daily_usage, exhaustion_predictions, aws_spend_snapshots,
    # aws_service_breakdown, aws_budgets, posthog_quota_snapshots, posthog_top_events;
    # build response matching BACKEND_PLAN.md §4.1
    body = {
        "meta": {"last_synced": datetime.utcnow().isoformat() + "Z", "range": range_param},
        "risk_banner": {"tools_at_risk": 2, "services_over_budget": 1, "next_exhaustion": "Feb 6"},
        "anthropic": {},
        "aws": {},
        "tools": [],
        "posthog": {},
    }
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": __import__("json").dumps(body),
    }
