import json
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
from app.calculations import calculate_exhaustion_date, calculate_risk_status, generate_alerts
from app.notifications import send_alert_email


def _looks_like_update_payload(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    return any(
        key in payload
        for key in ("today_date", "aws_spend", "history_data", "tools_data")
    )


def _extract_payloads(event: dict) -> list[dict]:
    records = event.get("Records", [])
    if records:
        payloads = []
        for record in records:
            body = record.get("body", "{}")
            if isinstance(body, str):
                payloads.append(json.loads(body))
            elif isinstance(body, dict):
                payloads.append(body)
        return payloads

    if _looks_like_update_payload(event):
        print("No SQS records found. Processing direct payload.")
        return [event]

    print("No SQS records or valid direct payload found. Skipping invocation.")
    return []


def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )

def _get_existing_tool_snapshots(cur) -> dict[str, dict]:
    cur.execute("SELECT name, credits_remaining, total_credits FROM tools")
    snapshots = {}
    for name, credits_remaining, total_credits in cur.fetchall():
        snapshots[name] = {
            "credits_remaining": float(credits_remaining or 0.0),
            "total_credits": float(total_credits or 0.0),
        }
    return snapshots

def _upsert_usage_history_row(cur, tool_name: str, usage_date, credits_consumed: float, events_count: int = 0) -> None:
    cur.execute(
        """
        SELECT credits_consumed, events_count
        FROM usage_history
        WHERE tool_name = %s AND date = %s
        """,
        (tool_name, usage_date),
    )
    existing_row = cur.fetchone()

    if existing_row:
        existing_credits = float(existing_row[0] or 0.0)
        existing_count = int(existing_row[1] or 0)
        cur.execute(
            """
            UPDATE usage_history
            SET credits_consumed = %s, events_count = %s
            WHERE tool_name = %s AND date = %s
            """,
            (round(existing_credits + credits_consumed, 2), existing_count + events_count, tool_name, usage_date),
        )
        return

    cur.execute(
        """
        INSERT INTO usage_history (tool_name, date, credits_consumed, events_count)
        VALUES (%s, %s, %s, %s)
        """,
        (tool_name, usage_date, round(credits_consumed, 2), events_count),
    )

def _get_recent_daily_usage(cur, tool_name: str, days: int = 7) -> float:
    cur.execute(
        """
        SELECT COALESCE(SUM(credits_consumed), 0)
        FROM usage_history
        WHERE tool_name = %s
          AND date >= CURRENT_DATE - INTERVAL '%s days'
        """,
        (tool_name, days - 1),
    )
    total_usage = float(cur.fetchone()[0] or 0.0)
    return total_usage / max(days, 1)

def _record_provider_usage_delta(
    cur,
    tool_name: str,
    usage_date,
    current_remaining: float,
    existing_snapshots: dict[str, dict],
) -> None:
    previous_snapshot = existing_snapshots.get(tool_name)
    previous_remaining = previous_snapshot["credits_remaining"] if previous_snapshot else None

    usage_delta = 0.0
    if previous_remaining is not None:
        usage_delta = max(previous_remaining - current_remaining, 0.0)

    _upsert_usage_history_row(cur, tool_name, usage_date, usage_delta, 0)


def lambda_handler(event, context):
    print("DB Update Lambda triggered...")

    payloads = _extract_payloads(event)
    if not payloads:
        return {"statusCode": 200, "body": json.dumps("No update payload to process")}
        
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        existing_tool_snapshots = _get_existing_tool_snapshots(cur)

        for payload in payloads:
            today_date = payload.get("today_date")
            aws_spend = payload.get("aws_spend", {})
            history_data = payload.get("history_data", {})
            tools_data = payload.get("tools_data", [])

            total_aws = aws_spend.get("total_aws", 0.0)
            aws_services = aws_spend.get("services", [])

            # Update aws_spend table
            for s in aws_services:
                cur.execute(
                    """
                    INSERT INTO aws_spend (date, service, amount)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (date, service)
                    DO UPDATE SET amount = EXCLUDED.amount
                    """,
                    (today_date, s["service"], s["amount"]),
                )

            source_history_tools = {tool_name for tool_name, entries in history_data.items() if entries}

            # Update usage_history
            for tool_name, history_list in history_data.items():
                for entry in history_list:
                    cur.execute("""
                        DELETE FROM usage_history WHERE tool_name = %s AND date = %s
                    """, (tool_name, entry["day"]))
                    
                    cur.execute("""
                        INSERT INTO usage_history (tool_name, date, credits_consumed, events_count)
                        VALUES (%s, %s, %s, %s)
                    """, (tool_name, entry["day"], entry["credits"], entry["count"]))

            # Update tools table
            for tool in tools_data:
                name = tool["name"]
                credits_rem = tool["credits_remaining"]
                total_credits = tool["total_credits"]
                daily_usage = tool["daily_avg_usage"]
                percent = tool["percent_remaining"]

                if name != "Anthropic" and name not in source_history_tools:
                    _record_provider_usage_delta(cur, name, today_date, float(credits_rem), existing_tool_snapshots)
                    if daily_usage <= 0:
                        daily_usage = _get_recent_daily_usage(cur, name, 7)

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
                    exhaustion, status, today_date, total_credits
                ))
                print(f"Updated {name} to RDS")

                tool["predicted_exhaustion"] = exhaustion
                tool["status"] = status

            # Generate Alerts
            aws_budget = float(os.environ.get("AWS_MONTHLY_BUDGET", "174.56"))
            aws_summary = {
                "budget_pct": (total_aws / aws_budget * 100) if aws_budget > 0 else 0,
                "monthly_spend": total_aws,
                "weekly_change": 0.0
            }

            alerts = generate_alerts(tools_data, aws_summary)
            if alerts:
                print(f"[Lambda] Detected {len(alerts)} alerts, sending notification...")
                send_alert_email(alerts)

        conn.commit()
        print("DB update committed successfully")

    except Exception as e:
        print(f"Critical error updating DB: {str(e)}")
        conn.rollback()
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    finally:
        cur.close()
        conn.close()

    return {"statusCode": 200, "body": json.dumps("DB Update Lambda success")}
