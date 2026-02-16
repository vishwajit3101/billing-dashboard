-- Operator.ai Billing Dashboard — Initial Schema
-- PostgreSQL (AWS RDS). Run in order.

-- Tools (AI providers + AWS logical “tool”)
CREATE TABLE IF NOT EXISTS tools (
    id          SERIAL PRIMARY KEY,
    slug        VARCHAR(64) NOT NULL UNIQUE,
    name        VARCHAR(128) NOT NULL,
    description VARCHAR(256),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO tools (slug, name, description) VALUES
    ('anthropic', 'Anthropic', 'Claude API Credits'),
    ('tavily', 'Tavily', 'Search API'),
    ('fullenrich', 'FullEnrich', 'Data Enrichment'),
    ('buyercaddy', 'Buyercaddy', 'Sales Intelligence'),
    ('aws', 'AWS', 'Cloud Infrastructure'),
    ('posthog', 'PostHog', 'Event Analytics')
ON CONFLICT (slug) DO NOTHING;

-- PostHog event → tool → credits per event (configurable)
CREATE TABLE IF NOT EXISTS event_credit_mapping (
    id                  SERIAL PRIMARY KEY,
    posthog_event_name  VARCHAR(128) NOT NULL,
    tool_id             INTEGER NOT NULL REFERENCES tools(id),
    credits_per_event   INTEGER NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(posthog_event_name)
);

INSERT INTO event_credit_mapping (posthog_event_name, tool_id, credits_per_event)
SELECT 'search_performed', t.id, 1 FROM tools t WHERE t.slug = 'tavily'
ON CONFLICT (posthog_event_name) DO NOTHING;
INSERT INTO event_credit_mapping (posthog_event_name, tool_id, credits_per_event)
SELECT 'lead_enriched', t.id, 2 FROM tools t WHERE t.slug = 'fullenrich'
ON CONFLICT (posthog_event_name) DO NOTHING;
INSERT INTO event_credit_mapping (posthog_event_name, tool_id, credits_per_event)
SELECT 'ai_workflow_run', t.id, 5 FROM tools t WHERE t.slug = 'anthropic'
ON CONFLICT (posthog_event_name) DO NOTHING;
INSERT INTO event_credit_mapping (posthog_event_name, tool_id, credits_per_event)
SELECT 'data_fetched', t.id, 1 FROM tools t WHERE t.slug = 'buyercaddy'
ON CONFLICT (posthog_event_name) DO NOTHING;

-- AWS budget (one active row for dashboard)
CREATE TABLE IF NOT EXISTS aws_budgets (
    id               SERIAL PRIMARY KEY,
    budget_name      VARCHAR(128) NOT NULL,
    monthly_limit_usd NUMERIC(12,2) NOT NULL,
    effective_from   DATE NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tool billing snapshots (credits remaining, optional cost)
CREATE TABLE IF NOT EXISTS tool_snapshots (
    id                   SERIAL PRIMARY KEY,
    tool_id              INTEGER NOT NULL REFERENCES tools(id),
    credits_remaining    NUMERIC(18,2) NOT NULL,
    credits_total       NUMERIC(18,2),
    cost_this_month_usd  NUMERIC(12,2),
    snapshot_at          TIMESTAMPTZ NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tool_snapshots_tool_snapshot ON tool_snapshots(tool_id, snapshot_at DESC);

-- AWS spend (e.g. current month total)
CREATE TABLE IF NOT EXISTS aws_spend_snapshots (
    id              SERIAL PRIMARY KEY,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    total_spend_usd NUMERIC(12,2) NOT NULL,
    snapshot_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_aws_spend_period ON aws_spend_snapshots(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_aws_spend_snapshot_at ON aws_spend_snapshots(snapshot_at DESC);

-- AWS cost by service (EC2, RDS, S3, etc.)
CREATE TABLE IF NOT EXISTS aws_service_breakdown (
    id           SERIAL PRIMARY KEY,
    period_start DATE NOT NULL,
    period_end   DATE NOT NULL,
    service_name VARCHAR(64) NOT NULL,
    cost_usd     NUMERIC(12,2) NOT NULL,
    snapshot_at  TIMESTAMPTZ NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_aws_breakdown_period ON aws_service_breakdown(period_start, period_end);

-- PostHog event counts per day (for mapping to credits)
CREATE TABLE IF NOT EXISTS posthog_event_counts (
    id          SERIAL PRIMARY KEY,
    event_name  VARCHAR(128) NOT NULL,
    date        DATE NOT NULL,
    count       INTEGER NOT NULL,
    snapshot_at TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(event_name, date)
);
CREATE INDEX IF NOT EXISTS idx_posthog_event_date ON posthog_event_counts(event_name, date);
CREATE INDEX IF NOT EXISTS idx_posthog_date ON posthog_event_counts(date DESC);

-- Derived: daily credit usage per tool (from PostHog + mapping)
CREATE TABLE IF NOT EXISTS tool_daily_usage (
    id           SERIAL PRIMARY KEY,
    tool_id      INTEGER NOT NULL REFERENCES tools(id),
    date         DATE NOT NULL,
    credits_used NUMERIC(18,2) NOT NULL,
    events_total INTEGER,
    computed_at  TIMESTAMPTZ NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tool_id, date)
);
CREATE INDEX IF NOT EXISTS idx_tool_daily_usage_tool_date ON tool_daily_usage(tool_id, date DESC);

-- Exhaustion predictions (latest per tool)
CREATE TABLE IF NOT EXISTS exhaustion_predictions (
    id                      SERIAL PRIMARY KEY,
    tool_id                 INTEGER NOT NULL REFERENCES tools(id),
    predicted_date          DATE NOT NULL,
    avg_daily_usage         NUMERIC(18,2) NOT NULL,
    credits_remaining_at_compute NUMERIC(18,2) NOT NULL,
    days_until_exhaustion   INTEGER NOT NULL,
    computed_at             TIMESTAMPTZ NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_exhaustion_tool_computed ON exhaustion_predictions(tool_id, computed_at DESC);

-- Usage spikes (2x avg) for alerts
CREATE TABLE IF NOT EXISTS usage_spikes (
    id           SERIAL PRIMARY KEY,
    tool_id      INTEGER NOT NULL REFERENCES tools(id),
    date         DATE NOT NULL,
    usage        NUMERIC(18,2) NOT NULL,
    avg_baseline NUMERIC(18,2) NOT NULL,
    multiplier   NUMERIC(6,2) NOT NULL,
    detected_at  TIMESTAMPTZ NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- PostHog quota (events today, this month, limit) for dashboard card
CREATE TABLE IF NOT EXISTS posthog_quota_snapshots (
    id               SERIAL PRIMARY KEY,
    events_today     INTEGER NOT NULL,
    events_this_month INTEGER NOT NULL,
    monthly_limit    INTEGER NOT NULL,
    snapshot_at      TIMESTAMPTZ NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_posthog_quota_snapshot_at ON posthog_quota_snapshots(snapshot_at DESC);

-- Top PostHog events (for dashboard list)
CREATE TABLE IF NOT EXISTS posthog_top_events (
    id          SERIAL PRIMARY KEY,
    snapshot_at TIMESTAMPTZ NOT NULL,
    event_name  VARCHAR(128) NOT NULL,
    count       INTEGER NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_posthog_top_events_snapshot ON posthog_top_events(snapshot_at DESC);

-- Alerts (sent via SES; “last alert” in UI)
CREATE TYPE alert_type_enum AS ENUM (
    'credits_warning', 'credits_critical', 'exhaustion_soon',
    'aws_over_budget', 'aws_budget_warning', 'usage_spike'
);

CREATE TABLE IF NOT EXISTS alerts (
    id         SERIAL PRIMARY KEY,
    tool_id    INTEGER REFERENCES tools(id),
    alert_type alert_type_enum NOT NULL,
    payload    JSONB,
    sent_at    TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_alerts_tool_sent ON alerts(tool_id, sent_at DESC);
