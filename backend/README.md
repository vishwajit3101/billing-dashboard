# Operator.ai Billing Dashboard — Backend

Python backend for the AI billing monitoring dashboard. Uses **AWS Lambda**, **PostgreSQL (RDS)**, **API Gateway**, **EventBridge**, **Secrets Manager**, and **SES**.

## Docs

- **[BACKEND_PLAN.md](./BACKEND_PLAN.md)** — Architecture: folder structure, Lambda list, DB schema, API contract.

## Setup

1. **Python 3.11+**

   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. **PostgreSQL**

   - Create a DB (e.g. `billing_watch`) and run migrations:
     ```bash
     psql -h <host> -U <user> -d billing_watch -f migrations/001_schema.sql
     ```

3. **Env (local)**

   - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (or `DB_SECRET_ARN` in Lambda).
   - Optional: `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, etc. for real integrations.

4. **Deploy (SAM)**

   - Set `DBSecretArn` and `AlertEmail` in `template.yaml` (or via parameters).
   - Ensure RDS (and VPC) exist; Lambdas that need DB access must run in the same VPC or use RDS Proxy/public access.
   - Build and deploy:
     ```bash
     sam build
     sam deploy --guided
     ```

## API (after deploy)

- `GET /api/dashboard?range=7d|14d|30d|90d` — Full dashboard payload for the frontend.
- `GET /api/export?range=30d&format=csv|json` — Export report.
- `GET /api/tools` — List tools.
- `GET /api/tools/{slug}` — Tool detail (anthropic, aws, tavily, fullenrich, buyercaddy).
- `GET /api/health` — Health check.

## Jobs (hourly)

- **FetchBilling** — Tool credits + AWS spend → `tool_snapshots`, `aws_spend_snapshots`, `aws_service_breakdown`.
- **FetchPostHog** — Event counts + quota → `posthog_event_counts`, `posthog_quota_snapshots`, `posthog_top_events`.
- **ComputeUsage** — Events → credits, avg daily, exhaustion, spikes → `tool_daily_usage`, `exhaustion_predictions`, `usage_spikes`.
- **CheckAlerts** — Evaluate rules, write `alerts`, send email via SES.

## Next steps

Implement each Lambda and integration in order (see BACKEND_PLAN.md §6). Start with DB + shared modules, then integrations (mock or real), then jobs, then API handlers.
