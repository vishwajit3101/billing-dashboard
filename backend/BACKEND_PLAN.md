# Operator.ai Billing Dashboard — Backend Plan

This document defines the backend architecture for the AI billing monitoring dashboard: folder structure, Lambda functions, PostgreSQL schema, and API endpoints aligned with the PRD and frontend.

---

## 1. Folder Structure

```
backend/
├── BACKEND_PLAN.md                 # This document
├── requirements.txt                # Python deps (shared)
├── template.yaml                  # SAM/CloudFormation (Lambda, API Gateway, RDS, etc.)
├── samconfig.toml                 # SAM deploy config
│
├── src/
│   ├── __init__.py
│   ├── shared/                     # Shared code used by Lambdas
│   │   ├── __init__.py
│   │   ├── db.py                   # RDS connection, connection pooling
│   │   ├── secrets.py              # Secrets Manager client
│   │   ├── risk.py                 # Risk logic (safe/warning/critical, exhaustion)
│   │   └── event_credit_map.py     # PostHog event → tool → credits (configurable)
│   │
│   ├── integrations/               # External API clients
│   │   ├── __init__.py
│   │   ├── anthropic_billing.py    # Anthropic credits/cost (or mock)
│   │   ├── tavily_billing.py
│   │   ├── fullenrich_billing.py
│   │   ├── buyercaddy_billing.py
│   │   ├── posthog_client.py        # PostHog events/counts
│   │   └── aws_cost_explorer.py    # AWS Cost Explorer
│   │
│   ├── jobs/                       # Scheduled / event-driven jobs
│   │   ├── __init__.py
│   │   ├── fetch_billing.py        # Lambda: fetch all tool billing + AWS spend
│   │   ├── fetch_posthog.py        # Lambda: fetch PostHog event counts
│   │   ├── compute_usage.py       # Lambda: map events → credits, avg daily, exhaustion
│   │   └── check_alerts.py        # Lambda: evaluate alert rules, send SES
│   │
│   └── api/                        # API Gateway handlers
│       ├── __init__.py
│       ├── dashboard.py            # GET /dashboard — unified dashboard payload
│       ├── export.py               # GET /export — report export (CSV/PDF)
│       ├── tools.py                # GET /tools/{id}, /tools/{id}/risk
│       └── health.py               # GET /health — liveness
│
└── tests/
    ├── unit/
    │   ├── test_risk.py
    │   ├── test_event_credit_map.py
    │   └── test_integrations.py
    └── integration/
        └── test_api_dashboard.py
```

---

## 2. Lambda Functions

| Lambda | Trigger | Purpose |
|--------|---------|--------|
| **FetchBilling** | EventBridge (hourly) | FR1. Call Anthropic, Tavily, FullEnrich, Buyercaddy billing APIs and AWS Cost Explorer; write to `tool_snapshots`, `aws_spend_snapshots`, `aws_service_breakdown`. |
| **FetchPostHog** | EventBridge (hourly) | FR2. Call PostHog API for event counts (by event name, by day); write to `posthog_event_counts`. |
| **ComputeUsage** | EventBridge (hourly, after FetchPostHog) | FR3–FR6. Read event counts + event_credit mapping; compute daily credit usage per tool, rolling avg, exhaustion date, spike detection; write to `tool_daily_usage`, `exhaustion_predictions`, `usage_spikes`. |
| **CheckAlerts** | EventBridge (hourly) | FR8. Read current snapshots + predictions; if credits &lt;20%, &lt;10%, exhaustion &lt;5 days, AWS &gt;90%, or spike → create `alerts` row and send email via SES. |
| **ApiDashboard** | API Gateway GET /dashboard | Serves unified dashboard JSON for frontend (date range query). |
| **ApiExport** | API Gateway GET /export | FR10. Generates report (e.g. CSV) for selected date range. |
| **ApiTools** | API Gateway GET /tools, /tools/{id}, /tools/{id}/risk | Tool detail and risk payload for side panels. |
| **ApiHealth** | API Gateway GET /health | Health check for API and DB connectivity. |

**Optional (can be merged):**

- **ApiAll** — Single Lambda with router (e.g. by path/query) handling `/dashboard`, `/export`, `/tools`, `/health` to reduce number of Lambdas.

---

## 3. Database Schema (PostgreSQL / RDS)

All monetary amounts in USD; timestamps in UTC.

### 3.1 Tools and configuration

- **tools**  
  - `id` (PK), `slug` (unique: anthropic, tavily, fullenrich, buyercaddy), `name`, `description`, `created_at`, `updated_at`.

- **event_credit_mapping** (configurable per PRD)  
  - `id` (PK), `posthog_event_name`, `tool_id` (FK), `credits_per_event` (int), `created_at`, `updated_at`.  
  - Example rows: search_performed → tavily 1; lead_enriched → fullenrich 2; ai_workflow_run → anthropic 5; data_fetched → buyercaddy 1.

- **aws_budgets**  
  - `id` (PK), `budget_name`, `monthly_limit_usd` (numeric), `effective_from` (date), `created_at`, `updated_at`.  
  - One active row per “default” budget for dashboard.

### 3.2 Billing and spend snapshots

- **tool_snapshots**  
  - `id` (PK), `tool_id` (FK), `credits_remaining`, `credits_total` (nullable), `cost_this_month_usd` (nullable, e.g. Anthropic), `snapshot_at` (timestamptz), `created_at`.  
  - One row per fetch; frontend uses latest per tool (and optionally history for trends).

- **aws_spend_snapshots**  
  - `id` (PK), `period_start` (date), `period_end` (date), `total_spend_usd`, `snapshot_at` (timestamptz), `created_at`.  
  - E.g. one row per month for “current month” spend; can add daily for “weekly change” if needed.

- **aws_service_breakdown**  
  - `id` (PK), `aws_snapshot_id` (FK to aws_spend_snapshots or a logical period), `service_name` (e.g. EC2, RDS, S3, Lambda, Other), `cost_usd`, `created_at`.  
  - One row per service per snapshot/period.

### 3.3 PostHog and derived usage

- **posthog_event_counts**  
  - `id` (PK), `event_name`, `date` (date), `count` (int), `snapshot_at` (timestamptz), `created_at`.  
  - Hourly job writes aggregated counts per event per day.

- **tool_daily_usage** (derived from PostHog + mapping)  
  - `id` (PK), `tool_id` (FK), `date` (date), `credits_used` (numeric), `events_total` (int, optional), `computed_at` (timestamptz), `created_at`.  
  - One row per tool per day; used for 7-day trend and avg daily.

- **exhaustion_predictions**  
  - `id` (PK), `tool_id` (FK), `predicted_date` (date), `avg_daily_usage` (numeric), `credits_remaining_at_compute`, `days_until_exhaustion`, `computed_at` (timestamptz), `created_at`.  
  - Latest row per tool used for dashboard “Exhaustion” and risk.

- **usage_spikes** (FR6)  
  - `id` (PK), `tool_id` (FK), `date` (date), `usage` (numeric), `avg_baseline`, `multiplier`, `detected_at` (timestamptz), `created_at`.  
  - For “usage spike (2× avg)” early alert.

### 3.4 PostHog quota (for PostHog card in UI)

- **posthog_quota_snapshots**  
  - `id` (PK), `events_today` (int), `events_this_month` (int), `monthly_limit` (int), `snapshot_at` (timestamptz), `created_at`.  
  - Optional: **posthog_top_events** — `id`, `snapshot_at`, `event_name`, `count` for “top events” list.

### 3.5 Alerts

- **alerts**  
  - `id` (PK), `tool_id` (FK, nullable), `alert_type` (enum: credits_warning, credits_critical, exhaustion_soon, aws_over_budget, aws_budget_warning, usage_spike), `payload` (jsonb), `sent_at` (timestamptz), `created_at`.  
  - “Last alert sent” in UI = latest `sent_at` for that tool/type.

### 3.6 Indexes (summary)

- `tool_snapshots`: (tool_id, snapshot_at DESC)  
- `aws_spend_snapshots`: (period_start, period_end), (snapshot_at DESC)  
- `posthog_event_counts`: (event_name, date), (date DESC)  
- `tool_daily_usage`: (tool_id, date DESC)  
- `exhaustion_predictions`: (tool_id, computed_at DESC)  
- `alerts`: (tool_id, sent_at DESC)

---

## 4. API Endpoints for Frontend

Base path: `/api` (or stage + resource path). All GET unless noted.

### 4.1 Dashboard (primary)

- **GET /api/dashboard**  
  - Query: `range=7d|14d|30d|90d` (default 30d).  
  - Response: single JSON for the whole dashboard (header, risk banner, all cards).  
  - Includes:
    - **meta**: `last_synced` (ISO timestamp of latest snapshot), `range`.
    - **risk_banner**: `tools_at_risk`, `services_over_budget`, `next_exhaustion` (date string or null).
    - **anthropic**: credits_remaining, credits_total, percent_remaining, status, daily_usage_trend (array of `{ day, credits }`), avg_daily, exhaustion_date, cost_this_month.
    - **aws**: current_spend, budget, percent_of_budget, weekly_change_pct, monthly_spend_trend (array of `{ month, spend }`), cost_by_service (array of `{ service, cost }`), status.
    - **tools**: array for Tavily, FullEnrich, Buyercaddy: slug, name, credits_used, credits_total, credits_remaining, percent_remaining, sparkline_7d (array of values or `{ day, value }`), status.
    - **posthog**: events_today, events_this_month, monthly_limit, percent_used, event_trend_7d (array of `{ day, events }`), top_events (array of `{ name, count }`), status.

### 4.2 Export

- **GET /api/export**  
  - Query: `range=7d|30d`, `format=csv|json`.  
  - Response: file download (CSV or JSON) for the selected range (summary + per-tool + AWS + alerts).

### 4.3 Tool detail (risk panel)

- **GET /api/tools**  
  - Response: list of tools with minimal fields (id, slug, name, current credits, status).

- **GET /api/tools/{slug}**  
  - slug: anthropic | aws | tavily | fullenrich | buyercaddy.  
  - Response: full detail for that card/panel (same shape as the corresponding section in dashboard, plus last_alert_sent if applicable).

- **GET /api/tools/{slug}/risk**  
  - Response: risk-focused payload for side panel (credits remaining, avg daily, exhaustion date, 7-day trend, last alert time).

### 4.4 Health

- **GET /api/health**  
  - Response: `{ "status": "ok", "db": "ok" }` or 503 with error details.

### 4.5 CORS

- Allow frontend origin for GET (and OPTIONS) for `/api/*`.

---

## 5. Risk Logic (Backend)

- **Credits remaining %**  
  - Safe: &gt;30%.  
  - Warning: 20–30%.  
  - Critical: &lt;10%.

- **Exhaustion**  
  - “Exhaustion &lt;5 days” → trigger alert; dashboard shows predicted date.

- **AWS**  
  - Over budget: spend &gt; budget.  
  - Warning: spend ≥ 90% of budget.

- **Usage spike**  
  - Any day &gt; 2× rolling 7-day average → early alert.

Status values returned to frontend: `healthy`, `warning`, `critical` (and optionally `over_budget` for AWS).

---

## 6. Next Steps (Implementation Order)

1. **Project scaffold** — Create `backend/` folder structure, `requirements.txt`, `template.yaml` stubs.  
2. **Database** — SQL migrations for all tables above; run against RDS (or local Postgres for dev).  
3. **Shared** — `db`, `secrets`, `risk`, `event_credit_map`.  
4. **Integrations** — Implement or mock Anthropic, Tavily, FullEnrich, Buyercaddy, PostHog, AWS Cost Explorer.  
5. **FetchBilling** Lambda — Persist tool + AWS snapshots.  
6. **FetchPostHog** Lambda — Persist event counts (and optional PostHog quota/top events).  
7. **ComputeUsage** Lambda — Compute daily usage, exhaustion, spikes.  
8. **CheckAlerts** Lambda — Evaluate rules, write alerts, send SES.  
9. **API** — Implement `/dashboard`, `/export`, `/tools`, `/health` and wire to API Gateway.  
10. **Frontend** — Point dashboard to real `/api/dashboard` and optionally `/api/tools/{slug}` for panels.

This keeps the backend aligned with the PRD (FR1–FR10), the risk rules, and the existing frontend components (AnthropicCard, AWSCard, ToolCard, PostHogCard, RiskBanner, RiskDetailPanel, DashboardHeader).
