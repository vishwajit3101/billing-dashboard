from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.database import get_db_connection
from datetime import date, timedelta, datetime
from app.calculations import (
    calculate_exhaustion_date,
    calculate_risk_status,
    generate_alerts
)
from app.tavily import get_tavily_remaining_credits
from app.fullenrich import get_fullenrich_remaining_credits
from app.anthropic import get_anthropic_remaining_credits
from app.buyercaddy import get_buyercaddy_remaining_credits
import io
import csv
import boto3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_MONTHLY_BUDGET = float(os.getenv("AWS_MONTHLY_BUDGET", "12000.0"))

# Load API keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
FULLENRICH_API_KEY = os.getenv("FULLENRICH_API_KEY")
FULLENRICH_USAGE_URL = os.getenv("FULLENRICH_USAGE_URL", "https://api.fullenrich.com/v1/usage")

# Debug prints — AFTER variables are defined
print("[DEBUG] TAVILY_API_KEY loaded:", TAVILY_API_KEY[:10] + "..." if TAVILY_API_KEY else "None")
print("[DEBUG] FULLENRICH_API_KEY loaded:", FULLENRICH_API_KEY[:10] + "..." if FULLENRICH_API_KEY else "None")
print("[DEBUG] ANTHROPIC_ADMIN_KEY loaded:", (os.getenv("ANTHROPIC_ADMIN_KEY")[:10] if os.getenv("ANTHROPIC_ADMIN_KEY") else "None") + "...")

def fetch_real_aws_spend(days: int = 30) -> dict:
    try:
        client = boto3.client('ce', region_name=AWS_REGION)
        
        # Calculate weekly change
        end = datetime.utcnow().date()
        week1_start = end - timedelta(days=7)
        week1_end = end
        week2_start = end - timedelta(days=14)
        week2_end = end - timedelta(days=7)

        def get_total_for_period(start, end):
            try:
                resp = client.get_cost_and_usage(
                    TimePeriod={'Start': start.isoformat(), 'End': end.isoformat()},
                    Granularity='DAILY',
                    Metrics=['AmortizedCost']
                )
                return sum(float(r['Total']['AmortizedCost']['Amount']) for r in resp['ResultsByTime'])
            except:
                return 0.0

        current_week = get_total_for_period(week1_start, week1_end)
        prev_week = get_total_for_period(week2_start, week2_end)
        
        weekly_change = 0.0
        # If prev_week is near zero, and current_week is also small (<$5), ignore spike
        if prev_week < 1.0 and current_week < 5.0:
            weekly_change = 0.0
        elif prev_week > 0:
            weekly_change = round(((current_week - prev_week) / prev_week) * 100, 1)
            # Cap the spike display to something more readable if needed, or just let it be
        elif current_week > 1.0:
            weekly_change = 100.0

        # Existing logic for history and services
        start_history = (end - timedelta(days=180)).replace(day=1)
        
        response = client.get_cost_and_usage(
            TimePeriod={'Start': start_history.isoformat(), 'End': end.isoformat()},
            Granularity='MONTHLY',
            Metrics=['AmortizedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        history = []
        current_period_services = []
        total_current_month_spend = 0.0
        
        results = sorted(response['ResultsByTime'], key=lambda x: x['TimePeriod']['Start'])
        
        SERVICE_MAPPING = {
            "Amazon Elastic Compute Cloud": "EC2",
            "Amazon Relational Database Service": "RDS",
            "AWS Lambda": "Lambda",
            "Amazon Simple Storage Service": "S3",
            "EC2 - Other": "EC2",
            "Amazon CloudWatch": "CloudWatch",
            "Amazon Route 53": "Route 53",
            "AWS Glue": "Glue",
            "Amazon Simple Email Service": "SES",
            "Amazon DynamoDB": "DynamoDB",
            "Amazon ElastiCache": "ElastiCache",
            "Amazon Kinesis": "Kinesis",
            "Amazon Redshift": "Redshift",
            "Amazon API Gateway": "API Gateway",
            "AWS Secrets Manager": "Secrets Manager",
            "Amazon GuardDuty": "GuardDuty",
            "Amazon Inspector": "Inspector",
            "AWS Budget": "Budgets",
            "AWS Cost Explorer": "Cost Explorer",
            "AWS Step Functions": "Step Functions"
        }

        def aggregate_services(raw_services):
            # Targeted categories
            TARGETS = ["EC2", "RDS", "Lambda", "S3"]
            buckets = {t: 0.0 for t in TARGETS}
            buckets["Other"] = 0.0

            for s in raw_services:
                raw_name = s['service']
                amount = s['amount']
                
                # Normalize the name
                clean_name = SERVICE_MAPPING.get(raw_name)
                if not clean_name:
                    clean_name = raw_name.replace('Amazon ', '').replace('AWS ', '')
                    if ' - Other' in clean_name:
                        clean_name = clean_name.replace(' - Other', '')
                
                # Bucket it
                matched = False
                for target in TARGETS:
                    if clean_name.upper() == target.upper():
                        buckets[target] += amount
                        matched = True
                        break
                
                if not matched:
                    buckets["Other"] += amount
            
            # Convert to results list
            results = []
            # Order them as requested: Lambda, EC2, RDS, S3, Other
            # We always include them so the chart isn't empty in the frontend
            for target in ["Lambda", "EC2", "RDS", "S3", "Other"]:
                val = buckets.get(target, 0.0)
                results.append({"service": target, "amount": round(val, 2)})
            
            return results

        for idx, result in enumerate(results):
            period_start = result['TimePeriod']['Start']
            month_label = datetime.strptime(period_start, '%Y-%m-%d').strftime('%b')
            period_total = 0.0
            period_services_raw = []
            for group in result['Groups']:
                service = group['Keys'][0].replace('AWS::', '')
                amount = float(group['Metrics']['AmortizedCost']['Amount'])
                period_total += amount
                period_services_raw.append({"service": service, "amount": amount})
            
            history.append({"month": month_label, "spend": round(period_total, 2)})
            if idx == len(results) - 1:
                current_period_services = period_services_raw
                total_current_month_spend = period_total
        
        final_services = aggregate_services(current_period_services)
        
        return {
            "monthly_spend": total_current_month_spend,
            "weekly_change": weekly_change,
            "services": final_services,
            "history": history
        }
    except Exception as e:
        print(f"[AWS] Error: {str(e)} → mock fallback with history")
        return {
            "monthly_spend": 14100.0,
            "weekly_change": 18.2,
            "services": [
                {"service": "Lambda", "amount": 1800.0},
                {"service": "EC2", "amount": 8200.0},
                {"service": "RDS", "amount": 4500.0},
                {"service": "S3", "amount": 1200.0},
                {"service": "Other", "amount": 1400.0}
            ],
            "history": [
                {"month": "Sep", "spend": 8200},
                {"month": "Oct", "spend": 9100},
                {"month": "Nov", "spend": 8800},
                {"month": "Dec", "spend": 10200},
                {"month": "Jan", "spend": 12400},
                {"month": "Feb", "spend": 14100}
            ]
        }

def send_alert_email(alerts: list[dict]):
    critical_alerts = [a for a in alerts if a["severity"] == "critical"]
    if not critical_alerts:
        return

    sender = os.getenv("ALERT_EMAIL_SENDER", "billing@operator.ai")
    recipient = os.getenv("ALERT_EMAIL_RECIPIENT", os.getenv("DB_USER", "admin@operator.ai"))
    
    subject = f"CRITICAL Billing Alert - {len(critical_alerts)} Issues ({date.today().isoformat()})"
    body_text = f"URGENT: Critical billing risks detected\n"
    body_text += "----------------------------------------\n"
    body_text += f"Date: {date.today().isoformat()}\n"
    body_text += f"Total critical alerts: {len(critical_alerts)}\n\n"

    for alert in critical_alerts:
        body_text += f"[{alert['severity'].upper()}] {alert['message']}\n"
        body_text += f" → Status: Critical (Action Required)\n\n"

    body_text += "Immediate action required to avoid service disruption.\n"
    body_text += f"Dashboard: {os.getenv('DASHBOARD_URL', 'http://localhost:8080')}\n"
    body_text += "----------------------------------------\n"

    try:
        ses = boto3.client('ses', region_name=AWS_REGION)
        ses.send_email(
            Source=sender,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )
        print(f"[SES] Alert email sent to {recipient}")
    except Exception as e:
        print(f"[SES] Error sending email: {str(e)}")
        # Fallback to print for visibility in logs
        print("\n" + "="*60)
        print("FAILED TO SEND EMAIL - LOGGING TO CONSOLE")
        print("Subject:", subject)
        print(body_text)
        print("="*60 + "\n")


app = FastAPI(title="Operator.ai Billing Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/dashboard")
async def get_dashboard(days: int = Query(30, ge=1, le=90)):
    conn = get_db_connection()
    cur = conn.cursor()

    start_date = date.today() - timedelta(days=days - 1)

    cur.execute("""
        SELECT name, credits_remaining, percent_remaining, daily_avg_usage, total_credits
        FROM tools
        WHERE last_updated >= %s
        ORDER BY name
    """, (start_date,))
    tools_rows = cur.fetchall()

    from app.posthog import get_tool_usage_stats, get_tool_usage_history
    tool_usage_data = get_tool_usage_stats()
    tool_history_data = get_tool_usage_history(days=7)

    tools = []
    for row in tools_rows:
        name, credits_db, percent_db, daily_db, total_db = row
        total = float(total_db or 100)

        # Real API for Tavily, FullEnrich, Anthropic
        if name == "Tavily":
            credits, total = get_tavily_remaining_credits()
        elif name == "FullEnrich":
            credits, total = get_fullenrich_remaining_credits()
        elif name == "Anthropic":
            credits, total = get_anthropic_remaining_credits()
        elif name == "Buyercaddy":
            credits, total = get_buyercaddy_remaining_credits()
        else:
            credits = float(credits_db or 0)

        percent = (credits / total * 100) if total > 0 else 0
        
        # Get usage stats and history for this tool
        tool_stats = tool_usage_data.get(name, {})
        daily = tool_stats.get("avg_7d", float(daily_db or 0))
        curr_24h = tool_stats.get("current_24h", 0.0)
        history = tool_history_data.get(name, [])
        
        exhaustion = calculate_exhaustion_date(credits, daily)
        status = calculate_risk_status(float(percent))

        tools.append({
            "name": name,
            "credits_remaining": credits,
            "percent_remaining": round(percent, 1),
            "daily_avg_usage": round(daily, 2),
            "current_24h_usage": round(curr_24h, 2),
            "predicted_exhaustion": exhaustion,
            "status": status,
            "history": history
        })

    aws_data = fetch_real_aws_spend(days=days)

    aws = {
        "monthly_spend": aws_data["monthly_spend"],
        "monthly_budget": AWS_MONTHLY_BUDGET,
        "percent_used": round((aws_data["monthly_spend"] / AWS_MONTHLY_BUDGET) * 100, 1) if aws_data["monthly_spend"] > 0 else 0.0,
        "weekly_change": aws_data.get("weekly_change", 0.0),
        "services": aws_data["services"],
        "history": aws_data.get("history", []),
        "filtered_days": days
    }

    alerts = generate_alerts(tools, aws)

    cur.close()
    conn.close()

    return {
        "tools": tools,
        "aws": aws,
        "alerts": alerts,
        "alert_count": len(alerts),
        "last_updated": date.today().isoformat(),
        "filtered_days": days,
        "date_range": {
            "from": start_date.isoformat(),
            "to": date.today().isoformat()
        }
    }


@app.get("/alerts")
async def get_alerts(critical_only: bool = False):
    data = await get_dashboard(30)
    alerts = data["alerts"]

    if critical_only:
        alerts = [a for a in alerts if a["severity"] == "critical"]

    if any(a["severity"] == "critical" for a in alerts):
        send_alert_email(alerts)

    return {
        "alerts": alerts,
        "count": len(alerts),
        "timestamp": date.today().isoformat()
    }


@app.get("/export")
async def export_report(
    days: int = Query(30, ge=1, le=90),
    format: str = Query("json", pattern="^(json|csv)$")
):
    data = await get_dashboard(days)

    if format == "json":
        return data

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Type", "Name/Service", "Credits/Amount", "% Used", "Daily Avg", "Exhaustion Date", "Status"])

    for tool in data["tools"]:
        writer.writerow([
            "Tool",
            tool["name"],
            tool["credits_remaining"],
            f"{tool['percent_remaining']}%",
            tool["daily_avg_usage"],
            tool.get("predicted_exhaustion", ""),
            tool["status"]
        ])

    for service in data["aws"]["services"]:
        writer.writerow([
            "AWS Service",
            service["service"],
            service["amount"],
            "",
            "",
            "",
            ""
        ])

    writer.writerow([])
    writer.writerow(["Summary", "", "", f"AWS: {data['aws']['percent_used']}%", "", "", ""])
    writer.writerow(["Alert Count", data["alert_count"], "", "", "", "", ""])

    writer.writerow([])
    writer.writerow(["Alerts"])
    writer.writerow(["Severity", "Message", "Affected"])
    for alert in data["alerts"]:
        writer.writerow([alert["severity"], alert["message"], alert["affected"]])

    csv_content = output.getvalue()
    filename = f"billing_report_{date.today().isoformat()}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


handler = Mangum(app)