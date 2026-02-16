-- Operator.ai Billing Dashboard — PostgreSQL Schema
-- Run with: psql -h <host> -U <user> -d <dbname> -f schema/init_db.sql

-- =============================================================================
-- ENUMS
-- =============================================================================

DO $$ BEGIN
    CREATE TYPE risk_level AS ENUM ('safe', 'warning', 'critical');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_type AS ENUM (
    'credits_warning',
    'credits_critical',
    'exhaustion_soon',
    'aws_over_budget',
    'aws_budget_warning',
    'usage_spike'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- 1. AI TOOLS CONFIGURATION
-- =============================================================================
-- name, API endpoint, current credits, risk level

CREATE TABLE IF NOT EXISTS ai_tools (
    id              SERIAL PRIMARY KEY,
    slug            VARCHAR(64) NOT NULL UNIQUE,
    name            VARCHAR(128) NOT NULL,
    description     VARCHAR(256),
    api_endpoint    VARCHAR(512),
    api_key_secret  VARCHAR(128),
    current_credits  NUMERIC(18, 2) NOT NULL DEFAULT 0,
    credits_total   NUMERIC(18, 2),
    risk_level      risk_level NOT NULL DEFAULT 'safe',
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE ai_tools IS 'AI tool configuration: name, API endpoint, current credits, risk level';

CREATE INDEX idx_ai_tools_slug ON ai_tools(slug);
CREATE INDEX idx_ai_tools_risk_level ON ai_tools(risk_level);
CREATE INDEX idx_ai_tools_is_active ON ai_tools(is_active) WHERE is_active = true;

-- =============================================================================
-- 2. POSTHOG EVENT-TO-CREDIT MAPPING
-- =============================================================================
-- event name, tool, credits per event

CREATE TABLE IF NOT EXISTS posthog_event_credit_mapping (
    id                  SERIAL PRIMARY KEY,
    event_name          VARCHAR(128) NOT NULL,
    tool_id             INTEGER NOT NULL REFERENCES ai_tools(id) ON DELETE CASCADE,
    credits_per_event   INTEGER NOT NULL CHECK (credits_per_event >= 0),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(event_name)
);

COMMENT ON TABLE posthog_event_credit_mapping IS 'Maps PostHog event names to AI tool and credits consumed per event';

CREATE INDEX idx_event_mapping_tool_id ON posthog_event_credit_mapping(tool_id);
CREATE INDEX idx_event_mapping_event_name ON posthog_event_credit_mapping(event_name);

-- =============================================================================
-- 3. CREDIT SNAPSHOTS (historical credit data with timestamps)
-- =============================================================================

CREATE TABLE IF NOT EXISTS credit_snapshots (
    id                   SERIAL PRIMARY KEY,
    tool_id              INTEGER NOT NULL REFERENCES ai_tools(id) ON DELETE CASCADE,
    credits_remaining    NUMERIC(18, 2) NOT NULL,
    credits_total        NUMERIC(18, 2),
    cost_usd             NUMERIC(12, 2),
    snapshot_at          TIMESTAMPTZ NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE credit_snapshots IS 'Historical credit balance snapshots per tool';

CREATE INDEX idx_credit_snapshots_tool_id ON credit_snapshots(tool_id);
CREATE INDEX idx_credit_snapshots_snapshot_at ON credit_snapshots(snapshot_at DESC);
CREATE INDEX idx_credit_snapshots_tool_snapshot ON credit_snapshots(tool_id, snapshot_at DESC);

-- =============================================================================
-- 4. USAGE LOGS (daily credit consumption)
-- =============================================================================

CREATE TABLE IF NOT EXISTS usage_logs (
    id               SERIAL PRIMARY KEY,
    tool_id          INTEGER NOT NULL REFERENCES ai_tools(id) ON DELETE CASCADE,
    usage_date       DATE NOT NULL,
    credits_consumed NUMERIC(18, 2) NOT NULL DEFAULT 0,
    events_count     INTEGER,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tool_id, usage_date)
);

COMMENT ON TABLE usage_logs IS 'Daily credit consumption per tool (from PostHog-derived usage)';

CREATE INDEX idx_usage_logs_tool_id ON usage_logs(tool_id);
CREATE INDEX idx_usage_logs_usage_date ON usage_logs(usage_date DESC);
CREATE INDEX idx_usage_logs_tool_date ON usage_logs(tool_id, usage_date DESC);

-- =============================================================================
-- 5. AWS SPEND (service name, amount, date)
-- =============================================================================

CREATE TABLE IF NOT EXISTS aws_spend (
    id           SERIAL PRIMARY KEY,
    service_name VARCHAR(128) NOT NULL,
    amount_usd   NUMERIC(12, 2) NOT NULL,
    spend_date   DATE NOT NULL,
    period_start DATE,
    period_end   DATE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE aws_spend IS 'AWS cost by service and date (from Cost Explorer)';

CREATE INDEX idx_aws_spend_service ON aws_spend(service_name);
CREATE INDEX idx_aws_spend_date ON aws_spend(spend_date DESC);
CREATE INDEX idx_aws_spend_service_date ON aws_spend(service_name, spend_date DESC);

-- Optional: monthly budget for comparison
CREATE TABLE IF NOT EXISTS aws_budgets (
    id               SERIAL PRIMARY KEY,
    budget_name      VARCHAR(128) NOT NULL,
    monthly_limit_usd NUMERIC(12, 2) NOT NULL,
    effective_from   DATE NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 6. ALERTS (tool, alert type, threshold, timestamp)
-- =============================================================================

CREATE TABLE IF NOT EXISTS alerts (
    id          SERIAL PRIMARY KEY,
    tool_id     INTEGER REFERENCES ai_tools(id) ON DELETE SET NULL,
    alert_type  alert_type NOT NULL,
    threshold   NUMERIC(18, 2),
    message     TEXT,
    payload     JSONB,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE alerts IS 'Triggered alerts: tool, type, threshold, and timestamp';

CREATE INDEX idx_alerts_tool_id ON alerts(tool_id);
CREATE INDEX idx_alerts_alert_type ON alerts(alert_type);
CREATE INDEX idx_alerts_triggered_at ON alerts(triggered_at DESC);
CREATE INDEX idx_alerts_tool_triggered ON alerts(tool_id, triggered_at DESC);

-- =============================================================================
-- TRIGGER: update updated_at on ai_tools and posthog_event_credit_mapping
-- =============================================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS ai_tools_updated_at ON ai_tools;
CREATE TRIGGER ai_tools_updated_at
    BEFORE UPDATE ON ai_tools
    FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

DROP TRIGGER IF EXISTS event_mapping_updated_at ON posthog_event_credit_mapping;
CREATE TRIGGER event_mapping_updated_at
    BEFORE UPDATE ON posthog_event_credit_mapping
    FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

-- =============================================================================
-- SAMPLE INSERT STATEMENTS (initial data)
-- =============================================================================

-- AI tools
INSERT INTO ai_tools (slug, name, description, api_endpoint, current_credits, credits_total, risk_level) VALUES
    ('anthropic', 'Anthropic', 'Claude API Credits', 'https://api.anthropic.com', 42350, 500000, 'critical'),
    ('tavily', 'Tavily', 'Search API', 'https://api.tavily.com', 2800, 10000, 'warning'),
    ('fullenrich', 'FullEnrich', 'Data Enrichment', 'https://api.fullenrich.com', 500, 5000, 'critical'),
    ('buyercaddy', 'Buyercaddy', 'Sales Intelligence', 'https://api.buyercaddy.com', 6800, 8000, 'safe')
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    api_endpoint = EXCLUDED.api_endpoint,
    current_credits = EXCLUDED.current_credits,
    credits_total = EXCLUDED.credits_total,
    risk_level = EXCLUDED.risk_level,
    updated_at = NOW();

-- PostHog event-to-credit mapping
INSERT INTO posthog_event_credit_mapping (event_name, tool_id, credits_per_event)
SELECT 'search_performed', id, 1 FROM ai_tools WHERE slug = 'tavily'
ON CONFLICT (event_name) DO UPDATE SET tool_id = EXCLUDED.tool_id, credits_per_event = EXCLUDED.credits_per_event, updated_at = NOW();

INSERT INTO posthog_event_credit_mapping (event_name, tool_id, credits_per_event)
SELECT 'lead_enriched', id, 2 FROM ai_tools WHERE slug = 'fullenrich'
ON CONFLICT (event_name) DO UPDATE SET tool_id = EXCLUDED.tool_id, credits_per_event = EXCLUDED.credits_per_event, updated_at = NOW();

INSERT INTO posthog_event_credit_mapping (event_name, tool_id, credits_per_event)
SELECT 'ai_workflow_run', id, 5 FROM ai_tools WHERE slug = 'anthropic'
ON CONFLICT (event_name) DO UPDATE SET tool_id = EXCLUDED.tool_id, credits_per_event = EXCLUDED.credits_per_event, updated_at = NOW();

INSERT INTO posthog_event_credit_mapping (event_name, tool_id, credits_per_event)
SELECT 'data_fetched', id, 1 FROM ai_tools WHERE slug = 'buyercaddy'
ON CONFLICT (event_name) DO UPDATE SET tool_id = EXCLUDED.tool_id, credits_per_event = EXCLUDED.credits_per_event, updated_at = NOW();

-- Sample credit snapshots (last 7 days for Anthropic)
INSERT INTO credit_snapshots (tool_id, credits_remaining, credits_total, cost_usd, snapshot_at)
SELECT id, 42350 - (n * 15420), 500000, 4280, (CURRENT_DATE - (n || ' days')::INTERVAL)::DATE + TIME '12:00:00'
FROM ai_tools, generate_series(0, 6) AS n
WHERE slug = 'anthropic';

-- Sample usage logs (last 7 days)
INSERT INTO usage_logs (tool_id, usage_date, credits_consumed, events_count)
SELECT t.id, (CURRENT_DATE - (n || ' days')::INTERVAL)::DATE,
       (ARRAY[15420, 14800, 16200, 15100, 17800, 16500, 18200])[n + 1],
       (ARRAY[3084, 2960, 3240, 3020, 3560, 3300, 3640])[n + 1]
FROM ai_tools t, generate_series(0, 6) AS n
WHERE t.slug = 'anthropic'
ON CONFLICT (tool_id, usage_date) DO UPDATE SET credits_consumed = EXCLUDED.credits_consumed, events_count = EXCLUDED.events_count;

-- Sample AWS spend (current month by service)
INSERT INTO aws_spend (service_name, amount_usd, spend_date) VALUES
    ('EC2', 5200.00, CURRENT_DATE),
    ('RDS', 3800.00, CURRENT_DATE),
    ('S3', 2100.00, CURRENT_DATE),
    ('Lambda', 1800.00, CURRENT_DATE),
    ('Other', 1200.00, CURRENT_DATE);

-- AWS budget
INSERT INTO aws_budgets (budget_name, monthly_limit_usd, effective_from) VALUES
    ('Monthly Infrastructure', 12000.00, DATE_TRUNC('month', CURRENT_DATE)::DATE);

-- Sample alerts
INSERT INTO alerts (tool_id, alert_type, threshold, message, triggered_at)
SELECT id, 'credits_critical', 10, 'Credits below 10%', NOW() - INTERVAL '2 hours'
FROM ai_tools WHERE slug = 'anthropic';

INSERT INTO alerts (tool_id, alert_type, threshold, message, triggered_at)
SELECT id, 'credits_warning', 20, 'Credits below 20%', NOW() - INTERVAL '5 hours'
FROM ai_tools WHERE slug = 'fullenrich';
