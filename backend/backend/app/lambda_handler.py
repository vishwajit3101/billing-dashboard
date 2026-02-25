# lambda_handler.py - hourly job

import json
import os
import psycopg2
import boto3
from datetime import date, timedelta, datetime
from app.tavily import get_tavily_remaining_credits
from app.fullenrich import get_fullenrich_remaining_credits
from app.anthropic import get_anthropic_remaining_credits
from app.buyercaddy import get_buyercaddy_remaining_credits
from app.posthog import get_real_daily_credit_usage
from app.calculations import calculate_exhaustion_date, calculate_risk_status

def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )

def lambda_handler(event, context):
    print("Hourly fetch started...")

    conn = get_db_connection()
    cur = conn.cursor()

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

        # Update aws_spend table
        for s in aws_services:
            cur.execute(
                """
                INSERT INTO aws_spend (date, service, amount)
                VALUES (%s, %s, %s)
                ON CONFLICT (date, service)
                DO UPDATE SET amount = EXCLUDED.amount
                """,
                (today, s["service"], s["amount"]),
            )

        # 2. Tool Fetching (Tavily, FullEnrich, Anthropic, Buyercaddy)
        real_daily_usage = get_real_daily_credit_usage(days=7)
        
        tools_to_fetch = [
            ("Tavily", get_tavily_remaining_credits),
            ("FullEnrich", get_fullenrich_remaining_credits),
            ("Anthropic", get_anthropic_remaining_credits),
            ("Buyercaddy", get_buyercaddy_remaining_credits),
        ]

        for name, fetch_func in tools_to_fetch:
            try:
                credits_rem, total_credits = fetch_func()
                daily_usage = real_daily_usage.get(name, 0.0)
                percent = (credits_rem / total_credits * 100) if total_credits > 0 else 0
                exhaustion = calculate_exhaustion_date(credits_rem, daily_usage)
                status = calculate_risk_status(percent)

                cur.execute("""
                    INSERT INTO tools (
                        name, credits_remaining, percent_remaining, daily_avg_usage,
                        predicted_exhaustion, status, last_updated, total_credits
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        credits_remaining = EXCLUDED.credits_remaining,
                        percent_remaining = EXCLUDED.percent_remaining,
                        daily_avg_usage = EXCLUDED.daily_avg_usage,
                        predicted_exhaustion = EXCLUDED.predicted_exhaustion,
                        status = EXCLUDED.status,
                        last_updated = EXCLUDED.last_updated,
                        total_credits = EXCLUDED.total_credits
                """, (
                    name, credits_rem, round(percent, 1), round(daily_usage, 2),
                    exhaustion, status, today, total_credits
                ))
                print(f"Updated {name}: {credits_rem} credits left")
            except Exception as e:
                print(f"Error updating tool {name}: {e}")

        conn.commit()
        print("RDS updated successfully")

    except Exception as e:
        print(f"Critical error in hourly fetch: {str(e)}")
        conn.rollback()

    finally:
        cur.close()
        conn.close()

    return {"statusCode": 200, "body": json.dumps("Hourly fetch done")}
