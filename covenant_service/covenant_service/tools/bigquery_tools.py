"""
BigQuery tools for retrieving loan and covenant data.
"""

import logging
from typing import Any, Dict, List, Optional

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])

from common.bigquery_client import bq_client

logger = logging.getLogger(__name__)


def get_loan_data(loan_id: str) -> Dict[str, Any]:
    """
    Retrieve loan details from BigQuery.

    Args:
        loan_id: Unique identifier for the loan

    Returns:
        Dictionary containing loan information
    """
    try:
        loan = bq_client.get_loan_by_id(loan_id)
        if loan:
            return {
                "success": True,
                "loan": loan,
            }
        return {
            "success": False,
            "error": f"Loan {loan_id} not found",
        }
    except Exception as e:
        logger.error(f"Error retrieving loan {loan_id}: {e}")
        return {"success": False, "error": str(e)}


def get_covenant_definitions(loan_id: str) -> Dict[str, Any]:
    """
    Retrieve covenant definitions for a loan.

    Args:
        loan_id: Unique identifier for the loan

    Returns:
        Dictionary containing covenant definitions
    """
    try:
        covenants = bq_client.get_covenants_by_loan(loan_id)
        return {
            "success": True,
            "loan_id": loan_id,
            "covenant_count": len(covenants),
            "covenants": covenants,
        }
    except Exception as e:
        logger.error(f"Error retrieving covenants for {loan_id}: {e}")
        return {"success": False, "error": str(e)}


def get_latest_financials(
    loan_id: str,
    periods: int = 4,
) -> Dict[str, Any]:
    """
    Retrieve latest financial data for a borrower.

    Args:
        loan_id: Unique identifier for the loan
        periods: Number of reporting periods to retrieve

    Returns:
        Dictionary containing financial data
    """
    try:
        # Get covenants first to know what to measure
        covenants = bq_client.get_covenants_by_loan(loan_id)
        
        financials = {
            "loan_id": loan_id,
            "periods_requested": periods,
            "measurements": [],
        }

        for covenant in covenants:
            covenant_id = covenant.get("covenant_id")
            if covenant_id:
                measurements = bq_client.get_latest_measurements(covenant_id, periods)
                financials["measurements"].extend(measurements)

        return {
            "success": True,
            "financials": financials,
        }
    except Exception as e:
        logger.error(f"Error retrieving financials for {loan_id}: {e}")
        return {"success": False, "error": str(e)}


def get_historical_measurements(
    covenant_id: str,
    limit: int = 12,
) -> Dict[str, Any]:
    """
    Retrieve historical measurements for trend analysis.

    Args:
        covenant_id: Unique identifier for the covenant
        limit: Maximum number of measurements to retrieve

    Returns:
        Dictionary containing historical measurements
    """
    try:
        measurements = bq_client.get_latest_measurements(covenant_id, limit)
        
        # Calculate trend if enough data points
        trend = None
        if len(measurements) >= 3:
            values = [m.get("actual_value", 0) for m in measurements if m.get("actual_value")]
            if len(values) >= 3:
                # Simple trend: compare first half average to second half average
                mid = len(values) // 2
                first_half_avg = sum(values[:mid]) / mid if mid > 0 else 0
                second_half_avg = sum(values[mid:]) / (len(values) - mid) if (len(values) - mid) > 0 else 0
                
                if first_half_avg > 0:
                    trend_pct = (second_half_avg - first_half_avg) / first_half_avg * 100
                    if trend_pct > 5:
                        trend = "improving"
                    elif trend_pct < -5:
                        trend = "deteriorating"
                    else:
                        trend = "stable"

        return {
            "success": True,
            "covenant_id": covenant_id,
            "measurement_count": len(measurements),
            "measurements": measurements,
            "trend": trend,
        }
    except Exception as e:
        logger.error(f"Error retrieving history for {covenant_id}: {e}")
        return {"success": False, "error": str(e)}
