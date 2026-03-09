# app/calculations.py

from datetime import date, timedelta

def calculate_exhaustion_date(credits_left: float, daily_usage: float) -> str | None:
    """
    Predict when credits will run out.
    Returns ISO date string (e.g. '2026-02-21') or None if no usage.
    """
    if daily_usage <= 0:
        return None
    
    days_left = credits_left / daily_usage
    # Round up to the next full day
    exhaustion_date = date.today() + timedelta(days=int(days_left + 0.999))
    return exhaustion_date.isoformat()  # returns string like '2026-02-21'


def calculate_risk_status(percent_remaining: float) -> str:
    """
    PRD risk logic (Section 11):
    >30% → Safe
    20–30% → Warning
    <10% → Critical
    Note: Code also handles 10-20% as 'Warning' to bridge the gap in PRD.
    """
    if percent_remaining > 30:
        return "Safe"
    elif percent_remaining >= 10:
        return "Warning"
    else:
        return "Critical"


# app/calculations.py
# ... keep your existing calculate_exhaustion_date and calculate_risk_status ...

def generate_alerts(tools: list[dict], aws: dict) -> list[dict]:
    """
    Generate list of active alerts based on PRD rules.
    Returns list of alert dicts: {"type": "warning/critical", "message": "...", "affected": "..."}
    """
    alerts = []

    # Tool credit alerts
    for tool in tools:
        percent = tool["percent_remaining"]
        exhaustion_str = tool.get("predicted_exhaustion")

        # <20% warning, <10% critical (already in status, but explicit alert)
        if percent < 10:
            alerts.append({
                "type": "critical",
                "message": f"{tool['name']} credits critically low (<10% remaining)",
                "affected": tool["name"],
                "severity": "critical"
            })
        elif percent < 20:
            alerts.append({
                "type": "warning",
                "message": f"{tool['name']} credits low (<20% remaining)",
                "affected": tool["name"],
                "severity": "warning"
            })

        # Exhaustion <5 days
        if exhaustion_str:
            try:
                exhaustion_date = date.fromisoformat(exhaustion_str)
                days_left = (exhaustion_date - date.today()).days
                if days_left <= 5 and days_left >= 0:
                    alerts.append({
                        "type": "alert",
                        "message": f"{tool['name']} predicted to exhaust in {days_left} days",
                        "affected": tool["name"],
                        "severity": "alert"
                    })
            except:
                pass  # skip invalid dates

        # Spike detection (FR6: 2x avg)
        avg = tool.get("daily_avg_usage", 0.0)
        curr = tool.get("current_24h_usage", 0.0)
        if avg > 0.5 and curr >= 2 * avg:  # Threshold of 0.5 to avoid noise on very low usage
            alerts.append({
                "type": "alert",
                "message": f"Usage spike detected for {tool['name']} ({curr:.1f} vs avg {avg:.1f})",
                "affected": tool["name"],
                "severity": "alert"
            })

    # AWS budget alert
    aws_percent = aws.get("percent_used", 0)
    if aws_percent > 90:
        alerts.append({
            "type": "alert",
            "message": f"AWS budget exceeded 90% ({aws_percent:.1f}%)",
            "affected": "AWS",
            "severity": "alert"
        })

    # AWS Spike (FR6)
    aws_change = aws.get("weekly_change", 0.0)
    if aws_change >= 100.0:
        alerts.append({
            "type": "alert",
            "message": f"AWS usage spike detected: {aws_change}% increase over last week",
            "affected": "AWS",
            "severity": "alert"
        })

    # Sort by severity (critical first)
    severity_order = {"critical": 0, "alert": 1, "warning": 2}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 99))

    return alerts