# app/notifications.py
import boto3
import os
from datetime import date

def send_alert_email(alerts: list[dict]):
    critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
    if not critical_alerts:
        return

    aws_region = os.getenv("AWS_REGION", "ap-south-1")
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
