#!/usr/bin/env python3
"""
Initialize the Operator.ai Billing Dashboard PostgreSQL database.
Runs schema/init_db.sql to create tables, indexes, and seed data.

Usage:
    python scripts/init_database.py
    python scripts/init_database.py --host localhost --port 5432 --dbname billing_watch --user postgres

Environment variables (optional):
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("Error: psycopg2 is required. Install with: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)


def get_connection_params(args: argparse.Namespace) -> dict:
    """Build connection params from args and env."""
    return {
        "host": args.host or os.environ.get("DB_HOST", "localhost"),
        "port": int(args.port or os.environ.get("DB_PORT", "5432")),
        "dbname": args.dbname or os.environ.get("DB_NAME", "billing_watch"),
        "user": args.user or os.environ.get("DB_USER", "postgres"),
        "password": args.password or os.environ.get("DB_PASSWORD", ""),
    }


def find_schema_file() -> Path:
    """Resolve path to schema/init_db.sql (relative to script or cwd)."""
    script_dir = Path(__file__).resolve().parent
    backend_root = script_dir.parent
    schema_file = backend_root / "schema" / "init_db.sql"
    if not schema_file.exists():
        schema_file = Path("schema/init_db.sql")
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: schema/init_db.sql (checked {backend_root / 'schema'})")
    return schema_file


def run_schema(conn_params: dict, schema_path: Path, verbose: bool = True) -> None:
    """Execute the SQL schema file. Uses autocommit for DDL and separate statements where needed."""
    sql_content = schema_path.read_text(encoding="utf-8")
    # Strip comments that are alone on a line and split by semicolon for statements
    # PostgreSQL doesn't allow running multiple statements with CREATE TYPE in one execute easily in some drivers
    # so we run the whole file as one script - psycopg2 can run multiple statements in one commit
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            if verbose:
                print(f"Running schema from {schema_path}...")
            cur.execute(sql_content)
            if verbose:
                print("Schema executed successfully.")
    except Exception as e:
        if verbose:
            print(f"Error executing schema: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize Billing Dashboard PostgreSQL database")
    parser.add_argument("--host", help="Database host (or DB_HOST)")
    parser.add_argument("--port", help="Database port (or DB_PORT)")
    parser.add_argument("--dbname", help="Database name (or DB_NAME)")
    parser.add_argument("--user", help="Database user (or DB_USER)")
    parser.add_argument("--password", help="Database password (or DB_PASSWORD)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    conn_params = get_connection_params(args)
    verbose = not args.quiet

    try:
        schema_path = find_schema_file()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1

    try:
        run_schema(conn_params, schema_path, verbose=verbose)
        if verbose:
            print("Database initialization complete.")
        return 0
    except Exception as e:
        if verbose:
            print(f"Initialization failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
