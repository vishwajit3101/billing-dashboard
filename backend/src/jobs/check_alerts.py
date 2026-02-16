"""
Lambda: Evaluate alert rules, write alerts table, send email via SES (FR8).
Trigger: EventBridge hourly.
"""
from datetime import datetime
from src.shared.db import get_cursor
from src.shared.risk import compute_credit_status, compute_aws_status


def handler(event: dict, context: object) -> dict:
    now = datetime.utcnow()
    # TODO: load latest tool_snapshots, exhaustion_predictions, aws_spend_snapshots, aws_budgets;
    # if credits <20% -> warning, <10% -> critical; exhaustion <5 days; AWS >90% or over budget; usage_spike;
    # insert into alerts, send SES to configured email
    return {"status": "ok", "checked_at": now.isoformat()}
