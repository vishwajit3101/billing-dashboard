"""
Lambda: Fetch PostHog event counts (FR2).
Trigger: EventBridge hourly.
Writes: posthog_event_counts, posthog_quota_snapshots, posthog_top_events.
"""
from datetime import datetime, date, timedelta
from src.shared.db import get_cursor
from src.integrations import posthog_client


def handler(event: dict, context: object) -> dict:
    now = datetime.utcnow()
    to_d = date.today()
    from_d = to_d - timedelta(days=30)
    counts = posthog_client.fetch_posthog_event_counts(from_date=from_d, to_date=to_d)
    with get_cursor() as cur:
        for row in counts:
            cur.execute(
                """INSERT INTO posthog_event_counts (event_name, date, count, snapshot_at)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (event_name, date) DO UPDATE SET count = EXCLUDED.count, snapshot_at = EXCLUDED.snapshot_at""",
                (row["event_name"], row["date"], row["count"], now),
            )
        quota = posthog_client.fetch_posthog_quota()
        cur.execute(
            """INSERT INTO posthog_quota_snapshots (events_today, events_this_month, monthly_limit, snapshot_at)
               VALUES (%s, %s, %s, %s)""",
            (quota["events_today"], quota["events_this_month"], quota["monthly_limit"], now),
        )
        for ev in posthog_client.fetch_posthog_top_events():
            cur.execute(
                """INSERT INTO posthog_top_events (snapshot_at, event_name, count) VALUES (%s, %s, %s)""",
                (now, ev["name"], ev["count"]),
            )
    return {"status": "ok", "snapshot_at": now.isoformat()}
