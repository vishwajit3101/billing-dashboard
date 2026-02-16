# Billing Fetcher Lambda

Fetches credit/billing data from AI tool APIs (Anthropic, Tavily, FullEnrich, Buyercaddy) and stores results in the RDS `credit_snapshots` table.

## Environment variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `TAVILY_API_KEY` | Tavily API key |
| `FULLENRICH_API_KEY` | FullEnrich API key |
| `BUYERCADDY_API_KEY` | Buyercaddy API key |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | RDS connection (or use `DB_SECRET_ARN`) |
| `DB_SECRET_ARN` | Optional: Secrets Manager secret ARN for DB credentials |
| `BILLING_FETCHER_RETRY_ATTEMPTS` | Max HTTP retries (default 3) |
| `BILLING_FETCHER_RETRY_BACKOFF` | Backoff seconds (default 2) |

## Handler

- **Handler:** `handler.handler`
- **Runtime:** Python 3.11+

## Response summary

The handler returns a JSON body with:

- `success_count`, `failed_count`, `failed_tools`
- `results`: list of `{ slug, status, credits_remaining?, credits_total?, cost_usd? }`
- `snapshot_at`: ISO timestamp

## Local run

```bash
cd backend/lambda_functions/billing_fetcher
pip install -r requirements.txt
export DB_HOST=localhost DB_NAME=billing_watch DB_USER=postgres DB_PASSWORD=...
# Optional: set API keys to hit real APIs
python -c "from handler import handler; print(handler({}, None))"
```

## Package for Lambda

```bash
pip install -r requirements.txt -t package/
cp handler.py config.py api_clients.py __init__.py package/
cd package && zip -r ../billing_fetcher.zip . && cd ..
# Upload billing_fetcher.zip to Lambda; set handler to handler.handler
```
