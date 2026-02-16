"""
HTML email templates for billing alerts.
Each returns (subject, html_body) for AWS SES.
"""
from typing import Any


def _wrap_html(body: str, title: str = "Billing Alert") -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body style="font-family: system-ui, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px;">
{body}
<hr style="margin-top: 24px; border: none; border-top: 1px solid #eee;">
<p style="color: #888; font-size: 12px;">Operator.ai Billing Dashboard — automated alert</p>
</body>
</html>"""


def credits_warning(tool_name: str, percent_remaining: float, credits_remaining: float, credits_total: float | None) -> tuple[str, str]:
    subject = f"[Warning] {tool_name} — credits below 20%"
    body = f"""
    <h2 style="color: #b45309;">⚠ Credits warning</h2>
    <p><strong>{tool_name}</strong> credit balance is at <strong>{percent_remaining:.1f}%</strong> remaining.</p>
    <ul>
        <li>Credits remaining: <strong>{credits_remaining:,.0f}</strong></li>
        <li>Credits total: <strong>{credits_total:,.0f}</strong> (if set)</li>
    </ul>
    <p><strong>Action needed:</strong> Consider topping up or reducing usage to avoid service disruption.</p>
    """
    return subject, _wrap_html(body.strip(), subject)


def credits_critical(tool_name: str, percent_remaining: float, credits_remaining: float, credits_total: float | None) -> tuple[str, str]:
    subject = f"[Critical] {tool_name} — credits below 10%"
    body = f"""
    <h2 style="color: #b91c1c;">🔴 Credits critical</h2>
    <p><strong>{tool_name}</strong> credit balance is at <strong>{percent_remaining:.1f}%</strong> remaining.</p>
    <ul>
        <li>Credits remaining: <strong>{credits_remaining:,.0f}</strong></li>
        <li>Credits total: <strong>{credits_total:,.0f}</strong> (if set)</li>
    </ul>
    <p><strong>Action needed:</strong> Top up credits immediately to avoid service failure.</p>
    """
    return subject, _wrap_html(body.strip(), subject)


def exhaustion_soon(tool_name: str, days_left: float, exhaustion_date: str, credits_remaining: float) -> tuple[str, str]:
    subject = f"[Urgent] {tool_name} — exhaustion in <5 days"
    body = f"""
    <h2 style="color: #b91c1c;">🚨 Exhaustion imminent</h2>
    <p><strong>{tool_name}</strong> is predicted to run out of credits in <strong>{days_left:.0f} days</strong>.</p>
    <ul>
        <li>Predicted exhaustion date: <strong>{exhaustion_date}</strong></li>
        <li>Credits remaining: <strong>{credits_remaining:,.0f}</strong></li>
    </ul>
    <p><strong>Action needed:</strong> Refill credits or reduce usage before the predicted date.</p>
    """
    return subject, _wrap_html(body.strip(), subject)


def aws_budget_warning(spend: float, budget: float, percent: float) -> tuple[str, str]:
    subject = "[Budget] AWS spend above 90% of monthly budget"
    body = f"""
    <h2 style="color: #b45309;">⚠ AWS budget alert</h2>
    <p>AWS spend is at <strong>{percent:.1f}%</strong> of the monthly budget.</p>
    <ul>
        <li>Current spend: <strong>${spend:,.2f}</strong></li>
        <li>Monthly budget: <strong>${budget:,.2f}</strong></li>
    </ul>
    <p><strong>Action needed:</strong> Review costs or increase budget to avoid overrun.</p>
    """
    return subject, _wrap_html(body.strip(), subject)


def aws_over_budget(spend: float, budget: float, percent: float) -> tuple[str, str]:
    subject = "[Critical] AWS over monthly budget"
    body = f"""
    <h2 style="color: #b91c1c;">🔴 AWS over budget</h2>
    <p>AWS spend has exceeded the monthly budget (<strong>{percent:.1f}%</strong>).</p>
    <ul>
        <li>Current spend: <strong>${spend:,.2f}</strong></li>
        <li>Monthly budget: <strong>${budget:,.2f}</strong></li>
    </ul>
    <p><strong>Action needed:</strong> Review cost breakdown and adjust budget or usage.</p>
    """
    return subject, _wrap_html(body.strip(), subject)


def usage_spike(tool_name: str, usage_today: float, avg_7d: float, multiplier: float) -> tuple[str, str]:
    subject = f"[Anomaly] {tool_name} — usage spike (2× average)"
    body = f"""
    <h2 style="color: #b45309;">📈 Usage spike detected</h2>
    <p><strong>{tool_name}</strong> credit consumption is <strong>{multiplier:.1f}×</strong> the 7-day average.</p>
    <ul>
        <li>Recent usage: <strong>{usage_today:,.0f}</strong> credits</li>
        <li>7-day average: <strong>{avg_7d:,.0f}</strong> credits</li>
    </ul>
    <p><strong>Action needed:</strong> Confirm whether the spike is expected or investigate unusual activity.</p>
    """
    return subject, _wrap_html(body.strip(), subject)


def get_subject_and_html(alert_type: str, **kwargs: Any) -> tuple[str, str]:
    """Dispatch to the right template by alert_type. Returns (subject, html_body)."""
    f = {
        "credits_warning": credits_warning,
        "credits_critical": credits_critical,
        "exhaustion_soon": exhaustion_soon,
        "aws_budget_warning": aws_budget_warning,
        "aws_over_budget": aws_over_budget,
        "usage_spike": usage_spike,
    }.get(alert_type)
    if not f:
        return f"[Alert] {alert_type}", _wrap_html(f"<p>Alert: {alert_type}</p><pre>{kwargs}</pre>")
    return f(**kwargs)
