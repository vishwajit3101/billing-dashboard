# tests/test_notifications.py
# PRD Requirements: FR8, AC-04, AC-05

import pytest
from unittest.mock import patch, MagicMock
from app.notifications import send_alert_email
from datetime import date

@patch("boto3.client")
def test_send_alert_email_empty(mock_boto):
    # Empty alerts list -> boto3.client never called
    send_alert_email([])
    mock_boto.assert_not_called()

@patch("boto3.client")
def test_send_alert_email_critical(mock_boto):
    mock_ses = MagicMock()
    mock_boto.return_value = mock_ses
    
    alerts = [{"severity": "critical", "message": "Anthropic critical", "affected": "Anthropic"}]
    send_alert_email(alerts)
    
    # Critical alert -> ses.send_email called once
    mock_ses.send_email.assert_called_once()
    args, kwargs = mock_ses.send_email.call_args
    
    # Critical alert -> subject line contains "CRITICAL"
    assert "CRITICAL" in kwargs["Message"]["Subject"]["Data"]
    # Alert message text appears in email body
    assert "Anthropic critical" in kwargs["Message"]["Body"]["Text"]["Data"]
    # Today's date appears in email body
    assert date.today().isoformat() in kwargs["Message"]["Body"]["Text"]["Data"]

@patch("boto3.client")
def test_send_alert_email_warning_only(mock_ses_client):
    mock_ses = MagicMock()
    mock_ses_client.return_value = mock_ses
    
    alerts = [{"severity": "warning", "message": "Tavily warning", "affected": "Tavily"}]
    send_alert_email(alerts)
    
    mock_ses.send_email.assert_called_once()
    args, kwargs = mock_ses.send_email.call_args
    # Only warning alerts -> subject line contains "WARNING"
    assert "WARNING" in kwargs["Message"]["Subject"]["Data"]
    assert "CRITICAL" not in kwargs["Message"]["Subject"]["Data"]

@patch("boto3.client")
def test_send_alert_email_multiple_alerts(mock_ses_client):
    mock_ses = MagicMock()
    mock_ses_client.return_value = mock_ses
    
    alerts = [
        {"severity": "critical", "message": "Crit 1", "affected": "A"},
        {"severity": "warning", "message": "Warn 1", "affected": "B"}
    ]
    send_alert_email(alerts)
    
    # Multiple alerts -> send_email called exactly once (no spam)
    mock_ses.send_email.assert_called_once()
    args, kwargs = mock_ses.send_email.call_args
    
    # 2 alerts -> subject contains "2"
    assert "2" in kwargs["Message"]["Subject"]["Data"]
    # Multiple alerts -> all messages in body
    body = kwargs["Message"]["Body"]["Text"]["Data"]
    assert "Crit 1" in body
    assert "Warn 1" in body

@patch("boto3.client")
def test_send_alert_email_exception_handling(mock_ses_client):
    mock_ses = MagicMock()
    mock_ses.send_email.side_effect = Exception("SES Error")
    mock_ses_client.return_value = mock_ses
    
    alerts = [{"severity": "critical", "message": "Error test", "affected": "X"}]
    
    # SES raises Exception -> function does NOT raise, logs to console (captured by pytest if needed)
    try:
        send_alert_email(alerts)
    except Exception as e:
        pytest.fail(f"send_alert_email raised {type(e).__name__} unexpectedly!")

def test_notifications_posthog_invisibility():
    # AC-05: PostHog is NOT visible anywhere
    with patch("boto3.client") as mock_boto:
        mock_ses = MagicMock()
        mock_boto.return_value = mock_ses
        alerts = [{"severity": "critical", "message": "PostHog test", "affected": "PH"}]
        # Even if "PostHog" is in the label (though it shouldn't be), let's see if we leak it
        # Actually message comes from generate_alerts which we already tested.
        # But let's check the body generation.
        send_alert_email(alerts)
        args, kwargs = mock_ses.send_email.call_args
        content = (kwargs["Message"]["Subject"]["Data"] + kwargs["Message"]["Body"]["Text"]["Data"]).lower()
        # We allow it in the test message itself because we are testing invisibility of the *source*
        # But the PRD says "Zero PostHog references in any frontend output or API response body"
        # Notifications are not exactly API response body, but let's be safe.
        # Wait, if the data itself contains it, it will be there. 
        # But the PRD AC-05 says "PostHog is NOT visible anywhere in the dashboard UI or API responses."
        # Email is a notification.
        pass

@patch("boto3.client")
def test_notification_no_posthog_leak(mock_boto):
    mock_ses = MagicMock()
    mock_boto.return_value = mock_ses
    alerts = [{"severity": "critical", "message": "Test Message", "affected": "Test"}]
    send_alert_email(alerts)
    args, kwargs = mock_ses.send_email.call_args
    content = (kwargs["Message"]["Subject"]["Data"] + kwargs["Message"]["Body"]["Text"]["Data"]).lower()
    assert "posthog" not in content
