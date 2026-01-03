"""
Alert generation tools.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from alert_service.alert_service.config import (
    ALERT_SEVERITY_CRITICAL,
    ALERT_SEVERITY_HIGH,
    ALERT_SEVERITY_MEDIUM,
    ALERT_SEVERITY_LOW,
)

logger = logging.getLogger(__name__)


def create_alert(
    loan_id: str,
    alert_type: str,
    severity: str,
    message: str,
    details: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Create a compliance alert.

    Args:
        loan_id: Loan identifier
        alert_type: Type of alert (covenant_breach, esg_warning, etc.)
        severity: Severity level
        message: Alert message
        details: Additional details

    Returns:
        Created alert
    """
    alert = {
        "alert_id": str(uuid.uuid4())[:8],
        "loan_id": loan_id,
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "details": details or {},
        "created_at": datetime.now().isoformat(),
        "acknowledged": False,
        "acknowledged_by": None,
    }

    # Add recommended action based on severity
    if severity == ALERT_SEVERITY_CRITICAL:
        alert["recommended_action"] = "Immediate escalation required"
        alert["response_deadline"] = "Within 4 hours"
    elif severity == ALERT_SEVERITY_HIGH:
        alert["recommended_action"] = "Review and respond same day"
        alert["response_deadline"] = "Within 24 hours"
    elif severity == ALERT_SEVERITY_MEDIUM:
        alert["recommended_action"] = "Review within 3 business days"
        alert["response_deadline"] = "Within 72 hours"
    else:
        alert["recommended_action"] = "Include in weekly review"
        alert["response_deadline"] = "Within 1 week"

    logger.info(f"Created alert {alert['alert_id']} for loan {loan_id}")
    
    return {"success": True, "alert": alert}


def prioritize_alerts(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Prioritize a list of alerts by severity and age.

    Args:
        alerts: List of alerts to prioritize

    Returns:
        Prioritized alert list
    """
    severity_order = {
        ALERT_SEVERITY_CRITICAL: 0,
        ALERT_SEVERITY_HIGH: 1,
        ALERT_SEVERITY_MEDIUM: 2,
        ALERT_SEVERITY_LOW: 3,
    }

    sorted_alerts = sorted(
        alerts,
        key=lambda x: (
            severity_order.get(x.get("severity", ALERT_SEVERITY_LOW), 4),
            x.get("created_at", ""),
        ),
    )

    return {
        "success": True,
        "prioritized_alerts": sorted_alerts,
        "critical_count": sum(1 for a in alerts if a.get("severity") == ALERT_SEVERITY_CRITICAL),
        "high_count": sum(1 for a in alerts if a.get("severity") == ALERT_SEVERITY_HIGH),
        "medium_count": sum(1 for a in alerts if a.get("severity") == ALERT_SEVERITY_MEDIUM),
        "low_count": sum(1 for a in alerts if a.get("severity") == ALERT_SEVERITY_LOW),
    }


def get_alert_template(alert_type: str) -> Dict[str, Any]:
    """
    Get alert template for a specific type.

    Args:
        alert_type: Type of alert

    Returns:
        Alert template
    """
    templates = {
        "covenant_breach": {
            "title": "Covenant Breach Alert",
            "template": "Loan {loan_id} has breached {covenant_name}. Actual: {actual_value}, Threshold: {threshold_value}",
            "severity_default": ALERT_SEVERITY_HIGH,
        },
        "covenant_warning": {
            "title": "Covenant Warning",
            "template": "Loan {loan_id} is approaching breach of {covenant_name}. Buffer: {buffer_pct}%",
            "severity_default": ALERT_SEVERITY_MEDIUM,
        },
        "esg_spt_miss": {
            "title": "ESG SPT Miss",
            "template": "Loan {loan_id} has missed SPT for {kpi_name}. Target: {target}, Actual: {actual}",
            "severity_default": ALERT_SEVERITY_MEDIUM,
        },
        "greenwashing_risk": {
            "title": "Greenwashing Risk Alert",
            "template": "Loan {loan_id} has {risk_level} greenwashing risk. Score: {score}",
            "severity_default": ALERT_SEVERITY_HIGH,
        },
        "breach_prediction": {
            "title": "Breach Prediction Alert",
            "template": "Loan {loan_id} has {probability}% predicted breach probability in next 90 days",
            "severity_default": ALERT_SEVERITY_MEDIUM,
        },
    }

    template = templates.get(alert_type, {
        "title": "General Alert",
        "template": "Alert for loan {loan_id}: {message}",
        "severity_default": ALERT_SEVERITY_LOW,
    })

    return {"success": True, "template": template}
