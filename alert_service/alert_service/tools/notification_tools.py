"""
Notification delivery tools.
"""

import logging
from typing import Any, Dict, List, Optional

from alert_service.alert_service.config import (
    SENDGRID_API_KEY,
    SENDGRID_FROM_EMAIL,
    SLACK_WEBHOOK_URL,
)

logger = logging.getLogger(__name__)


def send_email(
    to_emails: List[str],
    subject: str,
    body: str,
    html_body: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send email notification via SendGrid.

    Args:
        to_emails: List of recipient emails
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body

    Returns:
        Send result
    """
    if not SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured")
        return {
            "success": False,
            "error": "SendGrid not configured",
            "mock": True,
            "would_send_to": to_emails,
        }

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        message = Mail(
            from_email=Email(SENDGRID_FROM_EMAIL),
            to_emails=[To(email) for email in to_emails],
            subject=subject,
            plain_text_content=Content("text/plain", body),
        )

        if html_body:
            message.add_content(Content("text/html", html_body))

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        return {
            "success": True,
            "status_code": response.status_code,
            "recipients": to_emails,
        }

    except ImportError:
        logger.warning("sendgrid not installed")
        return {"success": False, "error": "sendgrid not installed", "mock": True}
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return {"success": False, "error": str(e)}


def send_slack_message(
    channel: str,
    message: str,
    severity: str = "info",
) -> Dict[str, Any]:
    """
    Send Slack notification.

    Args:
        channel: Slack channel
        message: Message text
        severity: Severity for formatting

    Returns:
        Send result
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack webhook not configured")
        return {
            "success": False,
            "error": "Slack not configured",
            "mock": True,
            "would_send": {"channel": channel, "message": message},
        }

    try:
        import requests

        # Format message with severity icon
        icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "ℹ️",
        }
        icon = icons.get(severity.lower(), "ℹ️")
        formatted_message = f"{icon} {message}"

        payload = {
            "channel": channel,
            "text": formatted_message,
            "username": "LoanGuard AI",
        }

        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)

        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "channel": channel,
        }

    except Exception as e:
        logger.error(f"Slack send error: {e}")
        return {"success": False, "error": str(e)}


def get_notification_recipients(
    loan_id: str,
    severity: str,
) -> Dict[str, Any]:
    """
    Get notification recipients based on severity.

    Args:
        loan_id: Loan identifier
        severity: Alert severity

    Returns:
        Recipient list
    """
    # Mock recipient configuration
    # In production, fetch from database
    recipients = {
        "CRITICAL": {
            "emails": ["risk-team@bank.com", "credit-head@bank.com", "cro@bank.com"],
            "slack_channels": ["#critical-alerts", "#risk-management"],
        },
        "HIGH": {
            "emails": ["risk-team@bank.com", "loan-officer@bank.com"],
            "slack_channels": ["#loan-alerts"],
        },
        "MEDIUM": {
            "emails": ["loan-officer@bank.com"],
            "slack_channels": ["#loan-monitoring"],
        },
        "LOW": {
            "emails": [],
            "slack_channels": ["#loan-monitoring"],
        },
    }

    config = recipients.get(severity.upper(), recipients["LOW"])

    return {
        "success": True,
        "loan_id": loan_id,
        "severity": severity,
        "email_recipients": config["emails"],
        "slack_channels": config["slack_channels"],
    }
