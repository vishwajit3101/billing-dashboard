"""
Centralized configuration for Billing Watch backend.
Reads from environment variables; supports .env via python-dotenv when loaded.

Usage:
    from config import settings
    db_host = settings.rds_host
    api_key = settings.anthropic_api_key
"""
import os
from typing import Optional

# Load .env from backend directory if present (no-op if file missing)
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(_env_path)
except ImportError:
    pass


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _env_int(key: str, default: int = 0) -> int:
    val = os.environ.get(key, "").strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _env_float(key: str, default: float = 0.0) -> float:
    val = os.environ.get(key, "").strip()
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        return default


class Settings:
    """
    Centralized settings from environment.
    Database: RDS_* or DB_* (RDS_* takes precedence).
    """

    # -------------------------------------------------------------------------
    # Database (RDS / PostgreSQL)
    # -------------------------------------------------------------------------
    @property
    def rds_host(self) -> str:
        return _env("RDS_HOST") or _env("DB_HOST", "localhost")

    @property
    def rds_port(self) -> int:
        return _env_int("RDS_PORT") or _env_int("DB_PORT", 5432) or 5432

    @property
    def rds_db(self) -> str:
        return _env("RDS_DB") or _env("DB_NAME", "billing_watch")

    @property
    def rds_user(self) -> str:
        return _env("RDS_USER") or _env("DB_USER", "postgres")

    @property
    def rds_password(self) -> str:
        return _env("RDS_PASSWORD") or _env("DB_PASSWORD", "")

    @property
    def db_secret_arn(self) -> Optional[str]:
        return _env("DB_SECRET_ARN") or None

    def get_db_connection_params(self) -> dict:
        """Dict for psycopg2.connect: host, port, dbname, user, password."""
        return {
            "host": self.rds_host,
            "port": self.rds_port,
            "dbname": self.rds_db,
            "user": self.rds_user,
            "password": self.rds_password,
        }

    # -------------------------------------------------------------------------
    # API keys
    # -------------------------------------------------------------------------
    @property
    def anthropic_api_key(self) -> str:
        return _env("ANTHROPIC_API_KEY")

    @property
    def tavily_api_key(self) -> str:
        return _env("TAVILY_API_KEY")

    @property
    def fullenrich_api_key(self) -> str:
        return _env("FULLENRICH_API_KEY")

    @property
    def buyercaddy_api_key(self) -> str:
        return _env("BUYERCADDY_API_KEY")

    @property
    def posthog_api_key(self) -> str:
        return _env("POSTHOG_API_KEY")

    @property
    def posthog_project_id(self) -> str:
        return _env("POSTHOG_PROJECT_ID")

    @property
    def posthog_host(self) -> str:
        return _env("POSTHOG_HOST", "https://us.posthog.com").rstrip("/")

    # -------------------------------------------------------------------------
    # AWS
    # -------------------------------------------------------------------------
    @property
    def aws_region(self) -> str:
        return _env("AWS_REGION", "us-east-1")

    @property
    def aws_account_id(self) -> str:
        return _env("AWS_ACCOUNT_ID")

    @property
    def ses_email_from(self) -> str:
        return _env("SES_EMAIL_FROM") or _env("ALERT_FROM_EMAIL") or _env("SES_FROM_EMAIL", "")

    # -------------------------------------------------------------------------
    # Config (budget & alerts)
    # -------------------------------------------------------------------------
    @property
    def monthly_aws_budget(self) -> float:
        return _env_float("MONTHLY_AWS_BUDGET", 12000.0) or _env_float("AWS_MONTHLY_BUDGET_USD", 12000.0)

    @property
    def alert_email(self) -> str:
        return _env("ALERT_EMAIL") or _env("ALERT_TO_EMAIL", "")


# Singleton
settings = Settings()
