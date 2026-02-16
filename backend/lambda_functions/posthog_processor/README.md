# PostHog Processor Lambda

Processes PostHog events to compute credit usage per AI tool and stores daily totals in `usage_logs`.

## Event-to-credit mapping (from DB `posthog_event_credit_mapping`)

| Event             | Tool       | Credits per event |
|-------------------|------------|--------------------|
| search_performed  | Tavily     | 1                  |
| lead_enriched     | FullEnrich | 2                  |
| ai_workflow_run   | Anthropic  | 5                  |
| data_fetched      | Buyercaddy | 1                  |

## Environment variables

| Variable           | Description                                |
|--------------------|--------------------------------------------|
| `POSTHOG_HOST`     | PostHog host (e.g. `https://us.posthog.com`) |
| `POSTHOG_PROJECT_ID` | Project ID                               |
| `POSTHOG_API_KEY`  | Personal API key with Query read permission |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | RDS connection |
| `DB_SECRET_ARN`    | Optional: Secrets Manager secret for DB   |

## Flow

1. Query PostHog (HogQL) for event counts in the **last 24 hours**.
2. Read **posthog_event_credit_mapping** from RDS.
3. For each tool: **credits_consumed = Σ (event_count × credits_per_event)**.
4. Upsert **usage_logs** (tool_id, usage_date, credits_consumed, events_count); usage_date = today.
5. Compute **7-day average** consumption from usage_logs and return in summary.

## Handler

- **Handler:** `handler.handler`
- **Runtime:** Python 3.11+

## Response

- `usage_date`, `event_counts`, `credits_by_tool`, `usage_logs_saved`, `avg_7day_by_tool`, `error` (if any).
