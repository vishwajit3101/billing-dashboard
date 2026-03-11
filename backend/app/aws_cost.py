# app/aws_cost.py
import boto3
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

def get_aws_data(days: int = 30) -> dict:
    """
    Fetch comprehensive AWS cost data:
    1. Current month spend
    2. 6-month trend
    3. Cost by service
    """
    client = boto3.client('ce', region_name=AWS_REGION)
    today = datetime.utcnow().date()
    first_of_month = today.replace(day=1)
    
    # AWS CE requires Start < End; on 1st of month they'd be equal
    end_date = today if today > first_of_month else today + timedelta(days=1)
    
    # 1. Current Month Spend
    resp_current = client.get_cost_and_usage(
        TimePeriod={"Start": first_of_month.isoformat(), "End": end_date.isoformat()},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"]
    )
    current_spend = 0.0
    if resp_current["ResultsByTime"]:
        current_spend = float(resp_current["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])

    # 2. Monthly Spend Trend (last 6 months)
    six_months_ago = (first_of_month - timedelta(days=180)).replace(day=1)
    resp_trend = client.get_cost_and_usage(
        TimePeriod={"Start": six_months_ago.isoformat(), "End": end_date.isoformat()},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"]
    )
    monthly_trend = [
        {
            "month": r["TimePeriod"]["Start"][:7],
            "label": datetime.strptime(r["TimePeriod"]["Start"], "%Y-%m-%d").strftime("%b"),
            "spend": round(float(r["Total"]["UnblendedCost"]["Amount"]), 2)
        }
        for r in resp_trend["ResultsByTime"]
    ]

    # 3. Cost Breakdown by Service (current month)
    resp_services = client.get_cost_and_usage(
        TimePeriod={"Start": first_of_month.isoformat(), "End": end_date.isoformat()},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
    )
    
    raw_services = []
    if resp_services["ResultsByTime"]:
        raw_services = [
            {"service": g["Keys"][0], "amount": round(float(g["Metrics"]["UnblendedCost"]["Amount"]), 2)}
            for g in resp_services["ResultsByTime"][0]["Groups"]
            if float(g["Metrics"]["UnblendedCost"]["Amount"]) > 0
        ]

    SERVICE_MAP = {
        "AWS Lambda": "Lambda",
        "Amazon Elastic Compute Cloud - Compute": "EC2",
        "Amazon Relational Database Service": "RDS",
        "Amazon Simple Storage Service": "S3",
        "Amazon Elastic Compute Cloud": "EC2",
        "EC2 - Other": "EC2",
        "Amazon Route 53": "Other",
        "Amazon CloudWatch": "Other",
        "AWS Glue": "Other",
    }
    
    # Initialize with 0.0 for all target services
    service_totals = {
        "Lambda": 0.0, "EC2": 0.0, "RDS": 0.0, "S3": 0.0, "Other": 0.0
    }
    
    for s in raw_services:
        name = SERVICE_MAP.get(s["service"])
        if name in service_totals:
            service_totals[name] = round(service_totals[name] + s["amount"], 2)
        elif name is None:
            service_totals["Other"] = round(service_totals["Other"] + s["amount"], 2)
        else:
            service_totals[name] = round(service_totals["Other"] + s["amount"], 2)
    
    final_services = [
        {"service": k, "amount": v} for k, v in service_totals.items()
    ]
    
    # 4. Weekly Change (Last 7d vs Previous 7d)
    seven_days_ago = today - timedelta(days=7)
    fourteen_days_ago = today - timedelta(days=14)
    
    resp_curr_week = client.get_cost_and_usage(
        TimePeriod={"Start": seven_days_ago.isoformat(), "End": today.isoformat()},
        Granularity="DAILY", Metrics=["UnblendedCost"]
    )
    curr_week_total = sum(float(r["Total"]["UnblendedCost"]["Amount"]) for r in resp_curr_week["ResultsByTime"])
    
    resp_prev_week = client.get_cost_and_usage(
        TimePeriod={"Start": fourteen_days_ago.isoformat(), "End": seven_days_ago.isoformat()},
        Granularity="DAILY", Metrics=["UnblendedCost"]
    )
    prev_week_total = sum(float(r["Total"]["UnblendedCost"]["Amount"]) for r in resp_prev_week["ResultsByTime"])
    
    # Treat very small values as zero
    curr_week_val = curr_week_total if curr_week_total > 0.01 else 0.0
    prev_week_val = prev_week_total if prev_week_total > 0.01 else 0.0

    weekly_change = 0.0
    if prev_week_val > 0.01:
        weekly_change = round(max(-100.0, ((curr_week_val - prev_week_val) / prev_week_val) * 100), 1)
    else:
        weekly_change = 100.0 if curr_week_val > 0.01 else 0.0

    budget = float(os.getenv("AWS_MONTHLY_BUDGET", "174.56"))
    
    return {
        "current_spend": max(0.0, round(current_spend, 2)),
        "budget": budget,
        "budget_pct": max(0.0, round((current_spend / budget * 100), 1)) if budget > 0 else 0.0,
        "monthly_trend": monthly_trend,
        "cost_by_service": final_services,
        "weekly_change": weekly_change,
        "status": "on_track" if current_spend < budget * 0.7 else "warning" if current_spend < budget * 0.9 else "critical"
    }
