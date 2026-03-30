CREATE TABLE IF NOT EXISTS tools_snapshots (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    credits_remaining NUMERIC NOT NULL,
    percent_remaining NUMERIC NOT NULL,
    daily_avg_usage NUMERIC NOT NULL,
    predicted_exhaustion DATE,
    status TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_credits NUMERIC NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tools_snapshots_name_recorded_at
    ON tools_snapshots (name, recorded_at DESC);
