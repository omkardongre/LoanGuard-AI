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
    Get notification recipients based on severity from BigQuery.
    
    Fetches real email addresses from notification_config table.
    No hardcoded or mock data.
    
    Args:
        loan_id: Loan identifier
        severity: Alert severity (CRITICAL, HIGH, MEDIUM, LOW)

    Returns:
        Recipient configuration with real emails from database
    """
    from common.bigquery_client import get_bigquery_client
    
    try:
        bq_client = get_bigquery_client()
        
        # Query real recipients from BigQuery
        query = f"""
        SELECT 
            role,
            email,
            slack_channel
        FROM `{bq_client.project_id}.{bq_client.dataset_id}.notification_config`
        WHERE severity = '{severity}'
          AND active = true
        ORDER BY role
        """
        
        results = bq_client.execute_query(query)
        
        if not results:
            logger.warning(f"No recipients configured in database for severity: {severity}")
            return {
                "success": False,
                "error": f"No recipients found for severity {severity}",
                "loan_id": loan_id,
                "severity": severity,
                "email_recipients": [],
                "slack_channels": [],
            }
        
        # Extract emails and slack channels from database results
        emails = [row['email'] for row in results]
        slack_channels = list(set([row['slack_channel'] for row in results if row.get('slack_channel')]))
        
        logger.info(f"Found {len(emails)} recipients for {severity} severity from database")
        
        return {
            "success": True,
            "loan_id": loan_id,
            "severity": severity,
            "email_recipients": emails,
            "slack_channels": slack_channels,
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch recipients from database: {e}")
        return {
            "success": False,
            "error": str(e),
            "loan_id": loan_id,
            "severity": severity,
            "email_recipients": [],
            "slack_channels": [],
        }
