# Billing Watch pipeline orchestrator

Step Functions state machine definition for the hourly billing pipeline.

**Flow:**
1. Every hour at :00 — EventBridge starts the state machine.
2. **Parallel:**
   - Branch 1: Invoke **billing_fetcher** (fetch_billing Lambda).
   - Branch 2: Wait 5 minutes, then invoke **posthog_processor** (fetch_posthog Lambda).
3. After both complete: Invoke **risk_calculator** (compute_usage Lambda).
4. After risk_calculator: Invoke **alert_engine** (check_alerts Lambda).

**Retries:** Each Lambda task has 3 retries with exponential backoff. Failures are caught and the pipeline can fail or continue depending on configuration.

The JSON uses placeholders `${fetch_billing_arn}` etc.; Terraform `templatefile()` injects the real Lambda ARNs from `infrastructure/eventbridge.tf`.
