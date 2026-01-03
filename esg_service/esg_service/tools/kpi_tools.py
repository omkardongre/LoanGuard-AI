"""
KPI tracking tools for ESG monitoring.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_kpi_definitions(loan_id: str) -> Dict[str, Any]:
    """
    Get KPI definitions for a sustainability-linked loan.

    Args:
        loan_id: Loan identifier

    Returns:
        Dictionary with KPI definitions
    """
    # Mock KPI definitions - in production, fetch from BigQuery
    kpis = [
        {
            "kpi_id": f"{loan_id}_carbon",
            "kpi_name": "Carbon Emissions Reduction",
            "kpi_type": "environmental",
            "baseline_value": 100000,
            "target_value": 70000,
            "unit": "tCO2e",
            "measurement_frequency": "annual",
            "verification_required": True,
        },
        {
            "kpi_id": f"{loan_id}_renewable",
            "kpi_name": "Renewable Energy Percentage",
            "kpi_type": "environmental",
            "baseline_value": 20,
            "target_value": 50,
            "unit": "%",
            "measurement_frequency": "annual",
            "verification_required": True,
        },
        {
            "kpi_id": f"{loan_id}_diversity",
            "kpi_name": "Board Gender Diversity",
            "kpi_type": "social",
            "baseline_value": 25,
            "target_value": 40,
            "unit": "%",
            "measurement_frequency": "annual",
            "verification_required": False,
        },
    ]

    return {
        "success": True,
        "loan_id": loan_id,
        "kpi_count": len(kpis),
        "kpis": kpis,
    }


def get_current_kpi_values(loan_id: str) -> Dict[str, Any]:
    """
    Get current KPI values for a loan.

    Args:
        loan_id: Loan identifier

    Returns:
        Dictionary with current KPI values
    """
    # Mock current values
    current_values = {
        f"{loan_id}_carbon": {
            "current_value": 82000,
            "measurement_date": "2025-12-31",
            "verified": True,
        },
        f"{loan_id}_renewable": {
            "current_value": 38,
            "measurement_date": "2025-12-31",
            "verified": True,
        },
        f"{loan_id}_diversity": {
            "current_value": 33,
            "measurement_date": "2025-12-31",
            "verified": False,
        },
    }

    return {
        "success": True,
        "loan_id": loan_id,
        "values": current_values,
    }


def calculate_kpi_progress(
    baseline: float,
    target: float,
    current: float,
    kpi_name: str,
) -> Dict[str, Any]:
    """
    Calculate progress towards KPI target.

    Args:
        baseline: Baseline value
        target: Target value
        current: Current value
        kpi_name: Name of the KPI

    Returns:
        Progress calculation result
    """
    try:
        # Calculate total required change
        required_change = target - baseline
        
        if required_change == 0:
            return {
                "success": True,
                "kpi_name": kpi_name,
                "progress_percentage": 100.0,
                "status": "TARGET_MET",
            }
        
        # Calculate actual change
        actual_change = current - baseline
        
        # Calculate progress percentage
        progress = (actual_change / required_change) * 100
        
        # Determine status
        if progress >= 100:
            status = "TARGET_MET"
        elif progress >= 75:
            status = "ON_TRACK"
        elif progress >= 50:
            status = "NEEDS_ATTENTION"
        else:
            status = "AT_RISK"

        return {
            "success": True,
            "kpi_name": kpi_name,
            "baseline": baseline,
            "target": target,
            "current": current,
            "required_change": required_change,
            "actual_change": actual_change,
            "progress_percentage": round(progress, 1),
            "remaining_gap": target - current,
            "status": status,
        }
    except Exception as e:
        logger.error(f"KPI progress calculation error: {e}")
        return {"success": False, "error": str(e)}


def get_kpi_trend(
    kpi_id: str,
    periods: int = 4,
) -> Dict[str, Any]:
    """
    Get historical trend for a KPI.

    Args:
        kpi_id: KPI identifier
        periods: Number of periods to analyze

    Returns:
        Trend analysis result
    """
    # Mock historical data
    history = [
        {"period": "2023-Q4", "value": 95000},
        {"period": "2024-Q2", "value": 90000},
        {"period": "2024-Q4", "value": 86000},
        {"period": "2025-Q2", "value": 82000},
    ]

    if len(history) >= 2:
        first_value = history[0]["value"]
        last_value = history[-1]["value"]
        change = ((last_value - first_value) / first_value) * 100
        
        if change < -5:
            trend = "IMPROVING"
        elif change > 5:
            trend = "DETERIORATING"
        else:
            trend = "STABLE"
    else:
        trend = "INSUFFICIENT_DATA"

    return {
        "success": True,
        "kpi_id": kpi_id,
        "history": history[-periods:],
        "trend": trend,
        "change_percentage": round(change, 1) if len(history) >= 2 else None,
    }
