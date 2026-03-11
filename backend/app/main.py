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
from app.buyercaddy import get_buyercaddy_remaining_credits, get_buyercaddy_history, get_buyercaddy_usage_metrics
import io
import csv
import boto3
import os
import requests
from dotenv import load_dotenv
from app.notifications import send_alert_email

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_MONTHLY_BUDGET = float(os.getenv("AWS_MONTHLY_BUDGET", "174.56"))

# Load API keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
FULLENRICH_API_KEY = os.getenv("FULLENRICH_API_KEY")
FULLENRICH_USAGE_URL = os.getenv("FULLENRICH_USAGE_URL", "https://api.fullenrich.com/v1/usage")

# Startup log (no secrets)
print("[INFO] Billing backend starting...")
print(f"[INFO] TAVILY_API_KEY: {'set' if TAVILY_API_KEY else 'missing'}")
print(f"[INFO] FULLENRICH_API_KEY: {'set' if FULLENRICH_API_KEY else 'missing'}")
print(f"[INFO] ANTHROPIC_ADMIN_KEY: {'set' if os.getenv('ANTHROPIC_ADMIN_KEY') else 'missing'}")




app = FastAPI(title="Operator.ai Billing Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/dashboard")
async def get_dashboard(days: int = Query(30, ge=1, le=90)):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        start_date = date.today() - timedelta(days=days - 1)

        cur.execute("""
            SELECT name, credits_remaining, percent_remaining, daily_avg_usage, total_credits
            FROM tools
            ORDER BY name
        """)
        tools_rows = cur.fetchall()

        # 1. Fetch tool history from usage_history table
        cur.execute("""
            SELECT tool_name, date, credits_consumed, events_count
            FROM usage_history
            WHERE date >= %s
            ORDER BY date ASC
        """, (start_date,))
        history_rows = cur.fetchall()
        
        db_history_data = {}
        for h_row in history_rows:
            tool_name, h_date, h_credits, h_count = h_row
            if tool_name not in db_history_data:
                db_history_data[tool_name] = []
            
            # Format history for frontend
            days_ago = (date.today() - h_date).days
            if days_ago == 0:
                label = "Today"
            elif days_ago == 1:
                label = "Yesterday"
            else:
                label = f"{days_ago}d ago"
                
            db_history_data[tool_name].append({
                "day": h_date.strftime("%Y-%m-%d"),
                "label": label,
                "credits": float(h_credits or 0),
                "count": int(h_count or 0)
            })

        tools = []
        for row in tools_rows:
            name, credits_db, percent_db, daily_db, total_db = row
            
            # Read from DB - no real-time API calls in dashboard
            credits = float(credits_db or 0)
            total = float(total_db or 100)
            percent = float(percent_db or 0)
            daily = float(daily_db or 0)
            if name == "Buyercaddy" and daily <= 0:
                try:
                    bc_metrics = get_buyercaddy_usage_metrics(total)
                    daily = float(bc_metrics["avg_daily_usage"])
                except Exception as exc:
                    print(f"[BuyerCaddy] Dashboard metrics fallback error: {exc}")
            
            # Fetch history from our compiled DB data
            history = db_history_data.get(name, [])
            if name == "Buyercaddy" and not history:
                history = get_buyercaddy_history(days)
            
            # Extract last 24h usage from history if today's entry exists
            curr_24h = 0.0
            today_entry = next((h for h in history if h["label"] == "Today"), None)
            if today_entry:
                curr_24h = today_entry["credits"]

            # Predict exhaustion based on DB-stored daily average
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

        from app.aws_cost import get_aws_data
        aws_data = get_aws_data(days=days)

        aws = {
            "current_spend": aws_data["current_spend"],
            "budget": aws_data["budget"],
            "budget_pct": aws_data["budget_pct"],
            "monthly_trend": aws_data["monthly_trend"],
            "cost_by_service": aws_data["cost_by_service"],
            "status": aws_data["status"],
            "weekly_change": aws_data.get("weekly_change", 0.0),
            "filtered_days": days
        }

        alerts = generate_alerts(tools, aws)

        return {
            "tools": tools,
            "aws": aws,
            "alerts": alerts,
            "alert_count": len(alerts),
            "last_updated": datetime.utcnow().isoformat(),
            "filtered_days": days,
            "date_range": {
                "from": start_date.isoformat(),
                "to": date.today().isoformat()
            }
        }
    finally:
        cur.close()
        conn.close()


@app.get("/alerts")
async def get_alerts(critical_only: bool = False):
    data = await get_dashboard(30)
    alerts = data["alerts"]

    if critical_only:
        alerts = [a for a in alerts if a["severity"] == "critical"]

    if alerts:
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

    for service in data["aws"]["cost_by_service"]:
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
    writer.writerow(["Summary", "", "", f"AWS: {data['aws']['budget_pct']}%", "", "", ""])
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
