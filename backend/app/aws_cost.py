# app/aws_cost.py
import boto3
from botocore.config import Config
from datetime import datetime, timedelta, UTC
import os
import json
import time
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
CACHE_FILE = Path(
    os.getenv(
        "AWS_COST_CACHE_FILE",
        str(Path(tempfile.gettempdir()) / "aws_cost_cache.json"),
    )
)
CACHE_TTL = 86400  # 24 hours

def get_aws_data(days: int = 30) -> dict:
    """
    Fetch comprehensive AWS cost data with 24-hour caching.
    Each API call to Cost Explorer costs $0.01.
    This function makes 5 calls, so caching saves $0.05 per refresh.
    """
    # 1. Check Cache
    try:
        if CACHE_FILE.exists():
            file_age = time.time() - CACHE_FILE.stat().st_mtime
            if file_age < CACHE_TTL:
                with open(CACHE_FILE, "r") as f:
                    cache_data = json.load(f)
                    # Verify cache is for the same 'days' parameter
                    if cache_data.get("days_param") == days:
                        print(f"[AWS] Using cached data (age: {int(file_age)}s)")
                        return cache_data["data"]
    except Exception as e:
        print(f"[AWS] Cache read error: {e}")

    # 2. Fetch Fresh Data (5 expensive API calls)
    print("[AWS] Fetching fresh data from Cost Explorer API...")
    client = boto3.client(
        'ce',
        region_name=AWS_REGION,
        config=Config(proxies={}),
    )
    today = datetime.now(UTC).date()
    first_of_month = today.replace(day=1)
    
    # AWS CE requires Start < End; on 1st of month they'd be equal
    end_date = today if today > first_of_month else today + timedelta(days=1)
    
    try:
        # A. Current Month Spend
        resp_current = client.get_cost_and_usage(
            TimePeriod={"Start": first_of_month.isoformat(), "End": end_date.isoformat()},
            Granularity="MONTHLY", Metrics=["UnblendedCost"]
        )
        current_spend = 0.0
        if resp_current["ResultsByTime"]:
            current_spend = float(resp_current["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])

        # B. Monthly Spend Trend (last 6 months)
        six_months_ago = (first_of_month - timedelta(days=180)).replace(day=1)
        resp_trend = client.get_cost_and_usage(
            TimePeriod={"Start": six_months_ago.isoformat(), "End": end_date.isoformat()},
            Granularity="MONTHLY", Metrics=["UnblendedCost"]
        )
        monthly_trend = [
            {
                "month": r["TimePeriod"]["Start"][:7],
                "label": datetime.strptime(r["TimePeriod"]["Start"], "%Y-%m-%d").strftime("%b"),
                "spend": max(0.0, round(float(r["Total"]["UnblendedCost"]["Amount"]), 2))
            }
            for r in resp_trend["ResultsByTime"]
        ]

        # C. Cost Breakdown by Service (current month)
        resp_services = client.get_cost_and_usage(
            TimePeriod={"Start": first_of_month.isoformat(), "End": end_date.isoformat()},
            Granularity="MONTHLY", Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
        )
        
        raw_services = []
        if resp_services["ResultsByTime"]:
            raw_services = [
                {"service": g["Keys"][0], "amount": max(0.0, round(float(g["Metrics"]["UnblendedCost"]["Amount"]), 2))}
                for g in resp_services["ResultsByTime"][0]["Groups"]
                if float(g["Metrics"]["UnblendedCost"]["Amount"]) != 0
            ]

        service_totals = {"Lambda": 0.0, "EC2": 0.0, "RDS": 0.0, "S3": 0.0, "Other": 0.0}
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
        
        for s in raw_services:
            name = SERVICE_MAP.get(s["service"], "Other")
            service_totals[name] = max(0.0, round(service_totals[name] + s["amount"], 2))
        
        final_services = [{"service": k, "amount": v} for k, v in service_totals.items()]
        
        # D. Weekly Change (Last 7d vs Previous 7d)
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
        
        curr_week_val = curr_week_total if curr_week_total > 0.01 else 0.0
        prev_week_val = prev_week_total if prev_week_total > 0.01 else 0.0

        weekly_change = 0.0
        if prev_week_val > 0.01:
            weekly_change = round(max(-100.0, ((curr_week_val - prev_week_val) / prev_week_val) * 100), 1)
        else:
            weekly_change = 100.0 if curr_week_val > 0.01 else 0.0

        budget = float(os.getenv("AWS_MONTHLY_BUDGET", "174.56"))
        
        data = {
            "current_spend": max(0.0, round(current_spend, 2)),
            "budget": budget,
            "budget_pct": max(0.0, round((current_spend / budget * 100), 1)) if budget > 0 else 0.0,
            "monthly_trend": monthly_trend,
            "cost_by_service": final_services,
            "weekly_change": weekly_change,
            "status": "on_track" if current_spend < budget * 0.7 else "warning" if current_spend < budget * 0.9 else "critical"
        }

        # 3. Write Cache
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w") as f:
                json.dump({"data": data, "days_param": days, "timestamp": time.time()}, f)
            print(f"[AWS] Cache updated successfully at {CACHE_FILE}")
        except Exception as e:
            print(f"[AWS] Cache write error: {e}")

        return data

    except Exception as e:
        print(f"[AWS] API error: {e}")
        # Fallback to expired cache if available
        if CACHE_FILE.exists():
            print("[AWS] Falling back to stale cache data during API error.")
            with open(CACHE_FILE, "r") as f:
                return json.load(f)["data"]
        raise e
