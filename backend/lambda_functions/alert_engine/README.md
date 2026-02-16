# Alert Engine Lambda

Checks billing thresholds and sends HTML email alerts via AWS SES. Writes to the `alerts` table and avoids duplicate alerts within 24 hours (same tool + alert type).

## Alert conditions

| Condition | Alert type | Email |
|-----------|------------|--------|
| Credits &lt; 20% | credits_warning | Warning |
| Credits &lt; 10% | credits_critical | Critical |
| Exhaustion &lt; 5 days | exhaustion_soon | Urgent |
| AWS budget &gt; 90% | aws_budget_warning | Budget alert |
| AWS over budget | aws_over_budget | Critical |
| Usage 2× 7-day average | usage_spike | Anomaly |

## Env vars

- **ALERT_TO_EMAIL** — Recipient for all alerts (required for sending).
- **ALERT_FROM_EMAIL** or **SES_FROM_EMAIL** — Verified SES sender.
- **DB_*** / DB_SECRET_ARN** — RDS connection.
- **AWS_MONTHLY_BUDGET_USD** — Default budget if `aws_budgets` is empty (default 12000).

## Handler

`handler.handler`. Returns `sent`, `skipped_duplicate`, `skipped_no_recipient`, `errors`.

## SES

- From address must be verified in SES (or use a verified domain).
- Lambda execution role needs `ses:SendEmail` (and optionally `ses:SendRawEmail`).
