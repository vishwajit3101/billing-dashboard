"""
Configurable PostHog event → tool slug → credits per event.
Loaded from DB (event_credit_mapping + tools) or default in-memory map.
"""
from typing import Optional

# Default mapping per PRD (used if DB not available)
DEFAULT_EVENT_CREDIT_MAP = {
    "search_performed": ("tavily", 1),
    "lead_enriched": ("fullenrich", 2),
    "ai_workflow_run": ("anthropic", 5),
    "data_fetched": ("buyercaddy", 1),
}


def get_event_credit_map(load_from_db: bool = False) -> dict[str, tuple[str, int]]:
    """
    Return dict: event_name -> (tool_slug, credits_per_event).
    If load_from_db=True, use event_credit_mapping + tools; else return DEFAULT_EVENT_CREDIT_MAP.
    """
    if not load_from_db:
        return dict(DEFAULT_EVENT_CREDIT_MAP)
    try:
        from .db import get_cursor
        with get_cursor() as cur:
            cur.execute("""
                SELECT e.posthog_event_name, t.slug, e.credits_per_event
                FROM event_credit_mapping e
                JOIN tools t ON t.id = e.tool_id
            """)
            return {row["posthog_event_name"]: (row["slug"], row["credits_per_event"]) for row in cur.fetchall()}
    except Exception:
        return dict(DEFAULT_EVENT_CREDIT_MAP)


def credits_for_events(event_counts: dict[str, int], tool_slug: str, mapping: Optional[dict] = None) -> float:
    """Sum credits for a given tool from event name -> count dict."""
    if mapping is None:
        mapping = get_event_credit_map()
    total = 0
    for event_name, count in event_counts.items():
        t = mapping.get(event_name)
        if t and t[0] == tool_slug:
            total += t[1] * count
    return float(total)
