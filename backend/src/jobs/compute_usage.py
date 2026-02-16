"""
Lambda: Map PostHog events to credits, compute avg daily, exhaustion, spikes (FR3–FR6).
Trigger: EventBridge hourly (after FetchPostHog).
Writes: tool_daily_usage, exhaustion_predictions, usage_spikes.
"""
from datetime import datetime, date, timedelta
from src.shared.db import get_cursor
from src.shared.event_credit_map import get_event_credit_map


def handler(event: dict, context: object) -> dict:
    now = datetime.utcnow()
    mapping = get_event_credit_map(load_from_db=True)
    with get_cursor() as cur:
        # TODO: read posthog_event_counts by date, aggregate by tool via mapping,
        # insert tool_daily_usage; then compute rolling avg, exhaustion date, insert exhaustion_predictions;
        # detect 2x avg spike and insert usage_spikes
        pass
    return {"status": "ok", "computed_at": now.isoformat()}
