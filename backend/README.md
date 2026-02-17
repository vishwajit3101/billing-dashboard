# Operator.ai Billing Dashboard — Backend

Python backend for the AI billing monitoring dashboard. Uses **AWS Lambda**, **PostgreSQL (RDS)**, **API Gateway**, **EventBridge**, **Secrets Manager**, and **SES**.

---

## Quick setup

1. **Clone and enter backend**
   ```bash
   cd backend
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your values (see "Environment variables" below).
   ```

4. **Database**
   - Create a PostgreSQL database (e.g. `billing_watch`).
   - Run schema: `psql -h <host> -U <user> -d billing_watch -f schema/init_db.sql`
   - Optional: `schema/002_exhaustion_predictions.sql`

5. **Run tests**
   ```bash
   python -m pytest tests/ -v
   ```

6. **Deploy (Terraform)**
   - From repo root: `./scripts/deploy.sh plan` then `./scripts/deploy.sh apply`
   - Or SAM: `sam build && sam deploy --guided`

---

## Environment variables

Copy `.env.example` to `.env` and set values. Never commit `.env`.

| Variable | Description | Example |
|----------|-------------|---------|
| **Database** | | |
| `RDS_HOST` | PostgreSQL host | `localhost` or RDS endpoint |
| `RDS_PORT` | Port | `5432` |
| `RDS_DB` | Database name | `billing_watch` |
| `RDS_USER` | DB user | `postgres` |
| `RDS_PASSWORD` | DB password | *(required for local)* |
| `DB_SECRET_ARN` | (Lambda) Secrets Manager ARN for DB | Overrides RDS_* when set |
| **API keys** | | |
| `ANTHROPIC_API_KEY` | Anthropic billing API | |
| `TAVILY_API_KEY` | Tavily credits API | |
| `FULLENRICH_API_KEY` | FullEnrich API | |
| `BUYERCADDY_API_KEY` | Buyercaddy API | |
| `POSTHOG_API_KEY` | PostHog (personal API key) | |
| `POSTHOG_PROJECT_ID` | PostHog project ID | |
| `POSTHOG_HOST` | PostHog host | `https://us.posthog.com` |
| **AWS** | | |
| `AWS_REGION` | AWS region | `us-east-1` |
| `AWS_ACCOUNT_ID` | Account ID (optional) | |
| `SES_EMAIL_FROM` | From address for alert emails | `alerts@operator.ai` |
| **Config** | | |
| `MONTHLY_AWS_BUDGET` | AWS budget limit (USD) | `12000` |
| `ALERT_EMAIL` | Recipient for billing alerts | `admin@operator.ai` |

Alternative names supported: `DB_HOST`/`DB_PORT`/`DB_NAME`/`DB_USER`/`DB_PASSWORD`, `ALERT_FROM_EMAIL`, `ALERT_TO_EMAIL`, `AWS_MONTHLY_BUDGET_USD`.

---

## Centralized config

Use the shared config object so all code reads from one place:

```python
from config import settings

# Database (for psycopg2)
params = settings.get_db_connection_params()
# Or individual: settings.rds_host, settings.rds_port, settings.rds_db, settings.rds_user, settings.rds_password

# API keys
settings.anthropic_api_key
settings.posthog_api_key
settings.posthog_project_id

# AWS
settings.aws_region
settings.ses_email_from

# Config
settings.monthly_aws_budget   # float
settings.alert_email
```

Config loads `.env` from the backend directory when `python-dotenv` is installed. In Lambda, set env vars (or use Secrets Manager); `DB_SECRET_ARN` overrides direct DB env vars when present.

---

## Project layout

- **config.py** — Centralized configuration (env + .env).
- **.env.example** — Template for required env vars; copy to `.env`.
- **src/shared/** — DB, secrets, risk, event_credit_map.
- **src/jobs/** — Lambdas: fetch_billing, fetch_posthog, compute_usage, check_alerts.
- **src/integrations/** — API clients (Anthropic, Tavily, PostHog, AWS Cost Explorer).
- **src/api/** — API handlers (dashboard, tools, export, health).
- **lambda_functions/dashboard_api/** — REST API Lambda (tools, trend, aws/spend, alerts, export).
- **schema/** — PostgreSQL init and migrations.
- **tests/** — Pytest suite (mocked DB and APIs).

---

## API (after deploy)

- `GET /api/tools` — List tools with credits, risk, exhaustion.
- `GET /api/tools/{tool_id}/trend?days=7` — Usage trend.
- `GET /api/aws/spend` — AWS spend and budget.
- `GET /api/alerts` — Active alerts.
- `GET /api/export?range=30d&format=csv` — Export report.
- `GET /api/health` — Health check.

---

## Jobs (hourly pipeline)

- **FetchBilling** — Tool credits + AWS Cost Explorer → DB.
- **FetchPostHog** — Event counts and quota → DB.
- **ComputeUsage** — Events → credits, exhaustion, spikes.
- **CheckAlerts** — Threshold checks → alerts table + SES email.

See **BACKEND_PLAN.md** for architecture and **infrastructure/README.md** for Terraform deploy.
