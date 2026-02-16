"""
Configuration for billing fetcher Lambda.
Uses environment variables for API keys and DB connection.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# API keys (from environment)
# -----------------------------------------------------------------------------
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY: str = os.environ.get("TAVILY_API_KEY", "")
FULLENRICH_API_KEY: str = os.environ.get("FULLENRICH_API_KEY", "")
BUYERCADDY_API_KEY: str = os.environ.get("BUYERCADDY_API_KEY", "")

# -----------------------------------------------------------------------------
# API endpoints (override via env for different environments)
# -----------------------------------------------------------------------------
ANTHROPIC_BILLING_URL: str = os.environ.get(
    "ANTHROPIC_BILLING_URL",
    "https://api.anthropic.com/v1/usage",
)
TAVILY_BILLING_URL: str = os.environ.get(
    "TAVILY_BILLING_URL",
    "https://api.tavily.com/credits",
)
FULLENRICH_BILLING_URL: str = os.environ.get(
    "FULLENRICH_BILLING_URL",
    "https://api.fullenrich.com/v1/credits",
)
BUYERCADDY_BILLING_URL: str = os.environ.get(
    "BUYERCADDY_BILLING_URL",
    "https://api.buyercaddy.com/v1/credits",
)

# -----------------------------------------------------------------------------
# Retry settings
# -----------------------------------------------------------------------------
RETRY_MAX_ATTEMPTS: int = int(os.environ.get("BILLING_FETCHER_RETRY_ATTEMPTS", "3"))
RETRY_BACKOFF_SECONDS: float = float(os.environ.get("BILLING_FETCHER_RETRY_BACKOFF", "2.0"))

# -----------------------------------------------------------------------------
# RDS / Database
# -----------------------------------------------------------------------------
# Option A: Direct env vars
DB_HOST: str = os.environ.get("DB_HOST", "localhost")
DB_PORT: int = int(os.environ.get("DB_PORT", "5432"))
DB_NAME: str = os.environ.get("DB_NAME", "billing_watch")
DB_USER: str = os.environ.get("DB_USER", "postgres")
DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "")

# Option B: Secrets Manager ARN (overrides above when set)
DB_SECRET_ARN: Optional[str] = os.environ.get("DB_SECRET_ARN")

# -----------------------------------------------------------------------------
# AWS Cost Explorer / budget
# -----------------------------------------------------------------------------
AWS_MONTHLY_BUDGET_USD: float = float(os.environ.get("AWS_MONTHLY_BUDGET_USD", "12000"))

# -----------------------------------------------------------------------------
# Tool slugs we fetch (must exist in ai_tools)
# -----------------------------------------------------------------------------
TOOL_SLUGS: tuple[str, ...] = ("anthropic", "tavily", "fullenrich", "buyercaddy")


def get_db_params() -> dict:
    """Return connection params for psycopg2. Uses Secrets Manager if DB_SECRET_ARN is set."""
    if DB_SECRET_ARN:
        try:
            import boto3
            import json
            client = boto3.client("secretsmanager")
            resp = client.get_secret_value(SecretId=DB_SECRET_ARN)
            secret = json.loads(resp["SecretString"])
            return {
                "host": secret.get("host", secret.get("hostname", DB_HOST)),
                "port": int(secret.get("port", DB_PORT)),
                "dbname": secret.get("dbname", secret.get("database", DB_NAME)),
                "user": secret.get("username", secret.get("user", DB_USER)),
                "password": secret.get("password", DB_PASSWORD),
            }
        except Exception as e:
            logger.warning("Secrets Manager fetch failed, using env: %s", e)
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }
