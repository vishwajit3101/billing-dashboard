-- Optional: run if you want the risk_calculator Lambda to persist predictions.
-- Table is referenced by lambda_functions/risk_calculator/handler.py

CREATE TABLE IF NOT EXISTS exhaustion_predictions (
    id                          SERIAL PRIMARY KEY,
    tool_id                      INTEGER NOT NULL REFERENCES ai_tools(id) ON DELETE CASCADE,
    predicted_date               DATE,
    avg_daily_usage              NUMERIC(18, 2) NOT NULL,
    credits_remaining_at_compute NUMERIC(18, 2) NOT NULL,
    days_until_exhaustion        INTEGER,
    computed_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exhaustion_predictions_tool ON exhaustion_predictions(tool_id);
CREATE INDEX IF NOT EXISTS idx_exhaustion_predictions_computed ON exhaustion_predictions(computed_at DESC);
