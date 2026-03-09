# app/notifications.py
import boto3
import os
from datetime import date

def send_alert_email(alerts: list[dict]):
    if not alerts:
        return

    critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
    warning_alerts = [a for a in alerts if a.get("severity") in ("warning", "alert")]

    # Only send email if there are critical or warning-level alerts
    if not critical_alerts and not warning_alerts:
        return

    aws_region = os.getenv("AWS_REGION", "ap-south-1")
    sender = os.getenv("ALERT_EMAIL_SENDER", "billing@operator.ai")
    recipient = os.getenv("ALERT_EMAIL_RECIPIENT", os.getenv("DB_USER", "admin@operator.ai"))
    
    severity_label = "CRITICAL" if critical_alerts else "WARNING"
    subject = f"{severity_label} Billing Alert - {len(alerts)} Issues ({date.today().isoformat()})"
    
    body_text = f"Billing risks detected\n"
    body_text += "----------------------------------------\n"
    body_text += f"Date: {date.today().isoformat()}\n"
    body_text += f"Total alerts: {len(alerts)}\n\n"

    if critical_alerts:
        body_text += "=== CRITICAL (Immediate Action Required) ===\n"
        for alert in critical_alerts:
            body_text += f"  [CRITICAL] {alert['message']}\n"
        body_text += "\n"

    if warning_alerts:
        body_text += "=== WARNINGS & ALERTS ===\n"
        for alert in warning_alerts:
            body_text += f"  [{alert['severity'].upper()}] {alert['message']}\n"
        body_text += "\n"

    body_text += "Please review the dashboard for details.\n"
    body_text += f"Dashboard: {os.getenv('DASHBOARD_URL', 'http://localhost:8080')}\n"
    body_text += "----------------------------------------\n"

    try:
        ses = boto3.client('ses', region_name=aws_region)
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
