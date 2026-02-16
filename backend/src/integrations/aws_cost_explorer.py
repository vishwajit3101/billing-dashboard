"""
AWS Cost Explorer client: current month spend, spend by service (EC2, RDS, S3, etc.).
"""
import os
from datetime import date
from typing import Any

def fetch_aws_current_month_spend() -> dict[str, Any]:
    """Current month total spend and period. Uses Cost Explorer GetCostAndUsage."""
    # TODO: boto3 client('ce').get_cost_and_usage(
    #   TimePeriod={Start, End}, Granularity='MONTHLY', Metrics=['UnblendedCost'], GroupBy=[{'Type':'DIMENSION','Key':'SERVICE'}]
    # )
    return {
        "period_start": date.today().replace(day=1).isoformat(),
        "period_end": date.today().isoformat(),
        "total_spend_usd": 14_100.0,
    }


def fetch_aws_service_breakdown(period_start: date, period_end: date) -> list[dict[str, Any]]:
    """Spend by service. Returns list of { service_name, cost_usd }."""
    # TODO: Cost Explorer with GroupBy SERVICE
    return [
        {"service_name": "EC2", "cost_usd": 5200.0},
        {"service_name": "RDS", "cost_usd": 3800.0},
        {"service_name": "S3", "cost_usd": 2100.0},
        {"service_name": "Lambda", "cost_usd": 1800.0},
        {"service_name": "Other", "cost_usd": 1200.0},
    ]


def fetch_aws_monthly_trend(months: int = 6) -> list[dict[str, Any]]:
    """Last N months total spend. Returns list of { month (e.g. 'Jan'), spend }."""
    # TODO: Cost Explorer monthly aggregation
    return [
        {"month": "Sep", "spend": 8200},
        {"month": "Oct", "spend": 9100},
        {"month": "Nov", "spend": 8800},
        {"month": "Dec", "spend": 10200},
        {"month": "Jan", "spend": 12400},
        {"month": "Feb", "spend": 14100},
    ]
