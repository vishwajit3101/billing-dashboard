# Billing Watch — Test Suite (pytest)

Tests run with **mocked** DB and external APIs so they can run locally without RDS or real API keys.

## Run tests

From `backend/`:

```bash
pip install -r requirements.txt   # pytest, psycopg2-binary, etc.
python -m pytest tests/ -v
python -m pytest tests/ --cov=src --cov=lambda_functions --cov-report=term-missing
```

## Layout

| File | What it tests |
|------|----------------|
| **conftest.py** | Shared fixtures: `mock_cursor`, `mock_get_cursor`, `sample_tools_rows`, `api_gateway_event` |
| **test_billing_fetcher.py** | `src.jobs.fetch_billing` — tool billing APIs + AWS Cost Explorer mocked, DB cursor mocked |
| **test_posthog_processor.py** | `src.jobs.fetch_posthog` — PostHog client and DB mocked |
| **test_risk_calculator.py** | `src.jobs.compute_usage` — event_credit_map and get_cursor mocked |
| **test_alert_engine.py** | `src.jobs.check_alerts` — get_cursor mocked |
| **test_api.py** | Dashboard API: endpoint logic (get_tools, get_tool_trend, get_aws_spend, get_alerts, get_export) and handler routing (GET /api/tools, 404, OPTIONS) with mocked get_cursor |
| **test_integration_flow.py** | Full pipeline: fetch_billing → fetch_posthog → compute_usage → check_alerts in one test with shared mocks |

## Mocks

- **DB:** `get_cursor()` is patched to return a context manager that yields a `MagicMock` cursor; `execute`, `fetchone`, `fetchall` are configured per test.
- **APIs:** `anthropic_billing.fetch_*`, `tavily_billing.fetch_*`, `posthog_client.*`, `aws_cost_explorer.*` are patched to return fixed data.
- No real PostgreSQL or network calls.

## Coverage

To hit more code paths, add tests that assert on `cursor.execute.call_args_list` (e.g. correct SQL or parameters) or that simulate failures (e.g. API raises, DB raises).
