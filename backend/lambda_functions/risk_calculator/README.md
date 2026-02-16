# Risk Calculator Lambda

Calculates credit exhaustion predictions and risk levels for all AI tools (Anthropic, Tavily, FullEnrich, Buyercaddy).

## Logic

- **Inputs:** Latest `credit_snapshots` (credits_remaining, credits_total), 7-day average from `usage_logs`.
- **days_left** = credits_remaining / avg_daily_usage (None if avg_daily_usage ≤ 0).
- **exhaustion_date** = current_date + timedelta(days=days_left).
- **risk_level** from % remaining: **>30% = Safe**, **20–30% = Warning**, **<20% = Critical**.

## Updates

- **ai_tools:** `risk_level`, `current_credits` (from latest snapshot).
- **exhaustion_predictions** (optional): one row per run per tool if the table exists. Create it with `schema/002_exhaustion_predictions.sql` if desired.

## Env

`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` or `DB_SECRET_ARN`.

## Handler

`handler.handler`. Returns `tools` (per-tool risk, exhaustion_date, days_left) and `risk_summary` (counts by safe/warning/critical).
