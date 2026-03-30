import json
import os
import boto3
from dotenv import load_dotenv
from datetime import date, timedelta, datetime

load_dotenv()
from app.tavily import get_tavily_remaining_credits
from app.fullenrich import get_fullenrich_remaining_credits
from app.anthropic import get_anthropic_remaining_credits
from app.buyercaddy import get_buyercaddy_remaining_credits, fetch_buyercaddy_credit_snapshot, get_buyercaddy_usage_metrics
from app.posthog import get_tool_usage_stats, get_tool_usage_history
from app.anthropic import get_anthropic_usage_history

def lambda_handler(event, context):
    print("Hourly fetch started...")

    try:
        today = date.today()

        # 1. AWS Cost Explorer
        ce = boto3.client("ce")
        end = today
        start = end - timedelta(days=30)

        # Basic AWS monthly fetch
        resp = ce.get_cost_and_usage(
            TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
            Granularity="MONTHLY",
            Metrics=["AmortizedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        total_aws = 0.0
        aws_services = []

        for r in resp["ResultsByTime"]:
            for g in r["Groups"]:
                svc = g["Keys"][0].replace("AWS::", "")
                amt = float(g["Metrics"]["AmortizedCost"]["Amount"])
                aws_services.append({"service": svc, "amount": amt})
                total_aws += amt

        print(f"Fetched real AWS spend: ${total_aws:.2f}")

        # 2. Tool Fetching (Tavily, FullEnrich, Anthropic, Buyercaddy)
        real_usage_stats = get_tool_usage_stats()
        real_daily_usage = {tool: data["avg_7d"] for tool, data in real_usage_stats.items()}
        
        # Save usage history (last 90 days) into usage_history table
        history_data = get_tool_usage_history(days=90)
        
        # Override Anthropic with real API data
        anthropic_history = get_anthropic_usage_history(days=90)
        if anthropic_history:
            history_data["Anthropic"] = anthropic_history
            
            # Recalculate the 7-day trailing average and 24h for Anthropic
            recent_7_days = sorted(anthropic_history, key=lambda x: x["day"], reverse=True)[:7]
            if recent_7_days:
                avg_7d = sum(d["credits"] for d in recent_7_days) / len(recent_7_days)
                real_daily_usage["Anthropic"] = avg_7d
                if "Anthropic" not in real_usage_stats:
                    real_usage_stats["Anthropic"] = {}
                real_usage_stats["Anthropic"]["current_24h"] = recent_7_days[0]["credits"]

        tools_to_fetch = [
            ("Tavily", get_tavily_remaining_credits),
            ("FullEnrich", get_fullenrich_remaining_credits),
            ("Anthropic", get_anthropic_remaining_credits),
            ("Buyercaddy", get_buyercaddy_remaining_credits),
        ]

        tools_data = []

        for name, fetch_func in tools_to_fetch:
            try:
                if name == "Buyercaddy":
                    credits_rem, total_credits, is_real = fetch_buyercaddy_credit_snapshot()
                    if not is_real:
                        print("[Lambda] Skipping BuyerCaddy tool update because live credit fetch failed")
                        continue
                    try:
                        # Keep the fetch lambda API/PostHog-only; DB reads belong in the app/update path.
                        bc_metrics = get_buyercaddy_usage_metrics(
                            total_credits,
                            allow_db_fallback=False,
                        )
                        daily_usage = float(bc_metrics["avg_daily_usage"])
                    except Exception as exc:
                        print(f"[Lambda] BuyerCaddy usage metrics fallback error: {exc}")
                        daily_usage = real_daily_usage.get(name, 0.0)
                else:
                    credits_rem, total_credits = fetch_func()
                    daily_usage = real_daily_usage.get(name, 0.0)

                percent = (credits_rem / total_credits * 100) if total_credits > 0 else 0

                tools_data.append({
                    "name": name,
                    "credits_remaining": float(credits_rem),
                    "total_credits": float(total_credits),
                    "daily_avg_usage": float(daily_usage),
                    "percent_remaining": float(percent),
                    "current_24h_usage": real_usage_stats.get(name, {}).get("current_24h", 0.0)
                })
                print(f"Fetched {name}: {credits_rem} credits left")
            except Exception as e:
                print(f"Error updating tool {name}: {e}")

        # Construct payload for SQS
        payload = {
            "today_date": today.isoformat(),
            "aws_spend": {
                "total_aws": total_aws,
                "services": aws_services
            },
            "history_data": history_data,
            "real_usage_stats": real_usage_stats,
            "tools_data": tools_data
        }

        queue_url = os.environ.get("SQS_QUEUE_URL")
        if not queue_url:
            print("[Lambda] SQS_QUEUE_URL not set in environment, returning payload directly.")
            return payload

        sqs = boto3.client('sqs')
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(payload)
        )
        print("Successfully sent payload to SQS")

    except Exception as e:
        print(f"Critical error in fetch lambda: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    return {"statusCode": 200, "body": json.dumps("Hourly fetch done")}
