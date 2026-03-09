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

        from app.posthog import get_tool_usage_stats, get_tool_usage_history
        tool_usage_data = get_tool_usage_stats()
        tool_history_data = get_tool_usage_history(days=days)

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
            
            # BuyerCaddy specific mock history (already has labels)
            if name == "Buyercaddy" and not history:
                from app.buyercaddy import get_buyercaddy_history
                history = get_buyercaddy_history(days=7)
                if history:
                    daily = sum(h["credits"] for h in history) / len(history)

            # Ensure history is sorted and has labels
            if name != "Anthropic" and len(history) > 7:
                history = history[-7:]
            elif name == "Anthropic" and len(history) > days:
                 history = history[-days:]

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