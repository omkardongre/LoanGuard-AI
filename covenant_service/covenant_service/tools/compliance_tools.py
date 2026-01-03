"""
Compliance checking tools for covenant monitoring.
"""

import logging
from typing import Any, Dict, List, Optional

from covenant_service.covenant_service.config import DEFAULT_WARNING_THRESHOLD

logger = logging.getLogger(__name__)


def check_covenant_compliance(
    actual_value: float,
    threshold_value: float,
    threshold_operator: str,
    covenant_name: str,
) -> Dict[str, Any]:
    """
    Check if a covenant is compliant.

    Args:
        actual_value: Calculated actual value
        threshold_value: Covenant threshold
        threshold_operator: Comparison operator (<, >, <=, >=)
        covenant_name: Name of the covenant

    Returns:
        Compliance check result
    """
    try:
        is_compliant = False
        
        if threshold_operator == "<":
            is_compliant = actual_value < threshold_value
        elif threshold_operator == "<=":
            is_compliant = actual_value <= threshold_value
        elif threshold_operator == ">":
            is_compliant = actual_value > threshold_value
        elif threshold_operator == ">=":
            is_compliant = actual_value >= threshold_value
        elif threshold_operator == "=":
            is_compliant = abs(actual_value - threshold_value) < 0.0001
        else:
            return {
                "success": False,
                "error": f"Unknown operator: {threshold_operator}",
            }

        # Calculate buffer
        buffer_result = calculate_buffer_percentage(
            actual_value, threshold_value, threshold_operator
        )
        buffer_pct = buffer_result.get("buffer_percentage", 0)

        # Determine status
        status_result = determine_status_color(is_compliant, buffer_pct)

        return {
            "success": True,
            "covenant_name": covenant_name,
            "actual_value": actual_value,
            "threshold_value": threshold_value,
            "threshold_operator": threshold_operator,
            "is_compliant": is_compliant,
            "buffer_percentage": buffer_pct,
            "status": status_result.get("status"),
            "status_description": status_result.get("description"),
        }
    except Exception as e:
        logger.error(f"Compliance check error: {e}")
        return {"success": False, "error": str(e)}


def determine_status_color(
    is_compliant: bool,
    buffer_percentage: float,
    warning_threshold: float = DEFAULT_WARNING_THRESHOLD,
) -> Dict[str, Any]:
    """
    Determine traffic light status color.

    Args:
        is_compliant: Whether covenant is currently compliant
        buffer_percentage: Buffer to threshold (as decimal, e.g., 0.15 for 15%)
        warning_threshold: Threshold for warning status

    Returns:
        Status color and description
    """
    if not is_compliant:
        return {
            "success": True,
            "status": "RED",
            "description": "Covenant breach - immediate attention required",
            "priority": 1,
        }
    elif buffer_percentage < warning_threshold:
        return {
            "success": True,
            "status": "AMBER",
            "description": f"Warning - only {buffer_percentage:.1%} buffer remaining",
            "priority": 2,
        }
    else:
        return {
            "success": True,
            "status": "GREEN",
            "description": f"Compliant with {buffer_percentage:.1%} buffer",
            "priority": 3,
        }


def check_cross_default(
    loan_id: str,
    covenant_breaches: List[Dict[str, Any]],
    cross_default_threshold: float = 0,
) -> Dict[str, Any]:
    """
    Check for cross-default triggers.

    Args:
        loan_id: Loan identifier
        covenant_breaches: List of current breaches
        cross_default_threshold: Materiality threshold for cross-default

    Returns:
        Cross-default analysis result
    """
    try:
        if not covenant_breaches:
            return {
                "success": True,
                "loan_id": loan_id,
                "cross_default_triggered": False,
                "message": "No covenant breaches - no cross-default risk",
            }

        # Count breaches by type
        financial_breaches = [
            b for b in covenant_breaches 
            if b.get("covenant_type") == "financial"
        ]
        
        # Typically cross-default triggers on any financial covenant breach
        cross_default_triggered = len(financial_breaches) > 0

        return {
            "success": True,
            "loan_id": loan_id,
            "cross_default_triggered": cross_default_triggered,
            "breach_count": len(covenant_breaches),
            "financial_breach_count": len(financial_breaches),
            "message": (
                "Cross-default may be triggered - review other facilities"
                if cross_default_triggered
                else "No cross-default trigger"
            ),
            "breaches": covenant_breaches,
        }
    except Exception as e:
        logger.error(f"Cross-default check error: {e}")
        return {"success": False, "error": str(e)}


def calculate_buffer_percentage(
    actual_value: float,
    threshold_value: float,
    threshold_operator: str,
) -> Dict[str, Any]:
    """
    Calculate buffer percentage to covenant threshold.

    Args:
        actual_value: Current calculated value
        threshold_value: Covenant threshold
        threshold_operator: Comparison operator

    Returns:
        Buffer percentage result
    """
    try:
        if threshold_value == 0:
            return {
                "success": True,
                "buffer_percentage": 1.0 if actual_value != 0 else 0,
                "note": "Threshold is zero",
            }

        # Calculate absolute difference
        difference = abs(actual_value - threshold_value)
        
        # Buffer as percentage of threshold
        buffer_pct = difference / abs(threshold_value)

        # Adjust sign based on operator direction
        if threshold_operator in ["<", "<="]:
            # Lower is better, so actual < threshold means positive buffer
            if actual_value < threshold_value:
                buffer_pct = buffer_pct
            else:
                buffer_pct = -buffer_pct
        elif threshold_operator in [">", ">="]:
            # Higher is better, so actual > threshold means positive buffer
            if actual_value > threshold_value:
                buffer_pct = buffer_pct
            else:
                buffer_pct = -buffer_pct

        return {
            "success": True,
            "buffer_percentage": buffer_pct,
            "actual_value": actual_value,
            "threshold_value": threshold_value,
            "difference": difference,
            "direction": "above" if actual_value > threshold_value else "below",
        }
    except Exception as e:
        logger.error(f"Buffer calculation error: {e}")
        return {"success": False, "error": str(e), "buffer_percentage": 0}
