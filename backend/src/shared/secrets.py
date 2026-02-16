"""
Secrets Manager client for DB credentials and API keys.
"""
import os
import json
from typing import Any

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception


def get_secret(secret_id: str) -> dict[str, Any]:
    """Fetch secret from AWS Secrets Manager. Fallback: env vars or empty dict."""
    if not boto3:
        return {}
    client = boto3.client("secretsmanager")
    try:
        resp = client.get_secret_value(SecretId=secret_id)
        if "SecretString" in resp:
            return json.loads(resp["SecretString"])
        return {}
    except ClientError:
        return {}


def get_db_credentials(secret_id: str | None = None) -> dict[str, str]:
    """Return dict with host, port, dbname, user, password for psycopg2."""
    sid = secret_id or os.environ.get("DB_SECRET_ARN")
    if sid:
        s = get_secret(sid)
        return {
            "host": s.get("host", os.environ.get("DB_HOST", "localhost")),
            "port": str(s.get("port", os.environ.get("DB_PORT", "5432"))),
            "dbname": s.get("dbname", os.environ.get("DB_NAME", "billing_watch")),
            "user": s.get("username", os.environ.get("DB_USER", "postgres")),
            "password": s.get("password", os.environ.get("DB_PASSWORD", "")),
        }
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "dbname": os.environ.get("DB_NAME", "billing_watch"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", ""),
    }
