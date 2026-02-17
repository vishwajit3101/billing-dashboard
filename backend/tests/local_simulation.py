#!/usr/bin/env python3
"""
Local simulation of the hourly billing pipeline.
Runs: billing_fetcher -> posthog_processor -> risk_calculator (compute_usage) -> alert_engine (check_alerts)
in sequence, using .env (or environment) for DB and API keys.

Usage (from backend/):
  python tests/local_simulation.py
  python tests/local_simulation.py --dry-run   # print steps only, do not call DB/APIs

Requires: .env configured (copy from .env.example) and PostgreSQL reachable, or use --dry-run.
"""
import argparse
import os
import sys

# Ensure backend root is on path
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# Load .env when running as script
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND_ROOT, ".env"))
except ImportError:
    pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Run billing pipeline locally")
    parser.add_argument("--dry-run", action="store_true", help="Only print steps, do not invoke handlers")
    args = parser.parse_args()

    steps = [
        ("billing_fetcher", "src.jobs.fetch_billing", "handler"),
        ("posthog_processor", "src.jobs.fetch_posthog", "handler"),
        ("risk_calculator (compute_usage)", "src.jobs.compute_usage", "handler"),
        ("alert_engine", "src.jobs.check_alerts", "handler"),
    ]

    if args.dry_run:
        print("Dry run — would execute:")
        for name, mod_path, attr in steps:
            print(f"  1. {name}: {mod_path}.{attr}()")
        return 0

    print("Running local pipeline simulation...")
    event = {}
    context = None

    for name, mod_path, attr in steps:
        try:
            mod = __import__(mod_path, fromlist=[attr])
            handler = getattr(mod, attr)
            result = handler(event, context)
            status = result.get("status", result.get("statusCode", "?"))
            print(f"  {name}: {status}")
        except Exception as e:
            print(f"  {name}: ERROR — {e}")
            return 1

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
