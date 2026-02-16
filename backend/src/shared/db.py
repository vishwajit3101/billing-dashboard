"""
RDS PostgreSQL connection helpers.
Uses env or Lambda context for host/credentials; supports Secrets Manager.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator, Any

# In Lambda, prefer Secrets Manager (DB_SECRET_ARN); else env: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
def _get_conn_params() -> dict[str, Any]:
    from .secrets import get_db_credentials
    creds = get_db_credentials()
    return {
        "host": creds.get("host", "localhost"),
        "port": int(creds.get("port", "5432")),
        "dbname": creds.get("dbname", "billing_watch"),
        "user": creds.get("user", "postgres"),
        "password": creds.get("password", ""),
    }


def get_connection():
    """Return a new connection. Caller must close it."""
    return psycopg2.connect(**_get_conn_params())


@contextmanager
def get_cursor(dict_cursor: bool = True) -> Generator[Any, None, None]:
    """Context manager: connection + cursor. Yields cursor; closes both on exit."""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor if dict_cursor else None)
        try:
            yield cur
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
