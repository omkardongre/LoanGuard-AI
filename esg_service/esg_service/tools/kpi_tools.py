"""
KPI tracking tools for ESG monitoring - PRODUCTION VERSION.

All data fetched from BigQuery - NO MOCK DATA.
"""

import logging
from typing import Any, Dict, List, Optional

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


def get_kpi_definitions(loan_id: str) -> Dict[str, Any]:
    """
    Get KPI definitions for a sustainability-linked loan from BigQuery.

    Args:
        loan_id: Loan identifier

    Returns:
        Dictionary with KPI definitions
    """
    try:
        bq = BigQueryClient()
        
        # First try SLL KPIs table (new module)
        query = f"""
            SELECT 
                kpi_id,
                kpi_name,
                kpi_type,
                baseline_value,
                target_value,
                unit,
                measurement_frequency,
                verification_required,
                target_year
            FROM `{bq.project_id}.{bq.dataset_id}.sll_kpis`
            WHERE loan_id = '{loan_id}'
            ORDER BY created_at DESC
        """
        
        results = bq.execute_query(query)
        
        # If no SLL KPIs, try legacy esg_kpis table
        if not results:
            legacy_query = f"""
                SELECT 
                    kpi_id,
                    kpi_name,
                    kpi_type,
                    baseline_value,
                    target_value,
                    current_value,
                    unit,
                    measurement_date,
                    verification_status
                FROM `{bq.project_id}.{bq.dataset_id}.esg_kpis`
                WHERE loan_id = '{loan_id}'
                ORDER BY measurement_date DESC
            """
            results = bq.execute_query(legacy_query)
        
        return {
            "success": True,
            "loan_id": loan_id,
            "kpi_count": len(results),
            "kpis": results,
            "source": "BigQuery"
        }
        
    except Exception as e:
        logger.error(f"Failed to get KPI definitions: {e}")
        return {"success": False, "error": str(e), "kpis": []}


def get_current_kpi_values(loan_id: str) -> Dict[str, Any]:
    """
    Get current KPI values for a loan from BigQuery.

    Args:
        loan_id: Loan identifier

    Returns:
        Dictionary with current KPI values
    """
    try:
        bq = BigQueryClient()
        
        query = f"""
            SELECT 
                kpi_id,
                kpi_name,
                current_value,
                last_measurement_date as measurement_date,
                verification_status as verified
            FROM `{bq.project_id}.{bq.dataset_id}.sll_kpis`
            WHERE loan_id = '{loan_id}'
            AND current_value IS NOT NULL
            ORDER BY last_measurement_date DESC
        """
        
        results = bq.execute_query(query)
        
        # If no SLL KPIs, try legacy table
        if not results:
            legacy_query = f"""
                SELECT 
                    kpi_id,
                    kpi_name,
                    current_value,
                    measurement_date,
                    CASE WHEN verification_status = 'VERIFIED' THEN TRUE ELSE FALSE END as verified
                FROM `{bq.project_id}.{bq.dataset_id}.esg_kpis`
                WHERE loan_id = '{loan_id}'
                ORDER BY measurement_date DESC
            """
            results = bq.execute_query(legacy_query)
        
        # Convert to dict keyed by kpi_id
        values = {r.get("kpi_id"): r for r in results}
        
        return {
            "success": True,
            "loan_id": loan_id,
            "values": values,
            "source": "BigQuery"
        }
        
    except Exception as e:
        logger.error(f"Failed to get current KPI values: {e}")
        return {"success": False, "error": str(e), "values": {}}


def calculate_kpi_progress(
    baseline: float = None,
    target: float = None,
    current: float = None,
    kpi_name: str = None,
    current_value: float = None,
    target_value: float = None,
) -> Dict[str, Any]:
    """
    Calculate progress towards KPI target.

    Args:
        baseline: Baseline value (optional, defaults to 0)
        target: Target value
        current: Current value
        kpi_name: Name of the KPI
        current_value: Alternative param name for current
        target_value: Alternative param name for target

    Returns:
        Progress calculation result
    """
    try:
        # Handle alternative parameter names
        _current = current if current is not None else current_value
        _target = target if target is not None else target_value
        _baseline = baseline if baseline is not None else 0
        
        if _current is None or _target is None:
            return {
                "success": False,
                "error": "current and target values required",
                "progress_pct": 0,
                "on_track": False
            }
        
        # Calculate total required change
        required_change = _target - _baseline
        
        if required_change == 0:
            return {
                "success": True,
                "kpi_name": kpi_name,
                "progress_pct": 100.0,
                "on_track": True,
                "status": "TARGET_MET",
            }
        
        # Calculate actual change
        actual_change = _current - _baseline
        
        # Calculate progress percentage
        progress = (actual_change / required_change) * 100
        
        # Determine status
        if progress >= 100:
            status = "TARGET_MET"
            on_track = True
        elif progress >= 75:
            status = "ON_TRACK"
            on_track = True
        elif progress >= 50:
            status = "NEEDS_ATTENTION"
            on_track = False
        else:
            status = "AT_RISK"
            on_track = False

        return {
            "success": True,
            "kpi_name": kpi_name,
            "baseline": _baseline,
            "target": _target,
            "current": _current,
            "required_change": required_change,
            "actual_change": actual_change,
            "progress_pct": round(progress, 1),
            "remaining_gap": _target - _current,
            "status": status,
            "on_track": on_track,
        }
    except Exception as e:
        logger.error(f"KPI progress calculation error: {e}")
        return {"success": False, "error": str(e), "progress_pct": 0, "on_track": False}


def get_kpi_trend(
    loan_id: str = None,
    kpi_id: str = None,
    periods: int = 4,
) -> Dict[str, Any]:
    """
    Get historical trend for a KPI from BigQuery covenant_measurements table.

    Args:
        loan_id: Loan identifier (alternative)
        kpi_id: KPI identifier
        periods: Number of periods to analyze

    Returns:
        Trend analysis result
    """
    try:
        bq = BigQueryClient()
        
        # Query historical data from covenant_measurements
        # This table stores periodic measurements
        query = f"""
            SELECT 
                FORMAT_DATE('%Y-%m', measurement_date) as period,
                measured_value as value,
                measurement_date
            FROM `{bq.project_id}.{bq.dataset_id}.covenant_measurements`
            WHERE covenant_id LIKE '%{kpi_id or loan_id}%'
            ORDER BY measurement_date DESC
            LIMIT {periods}
        """
        
        results = bq.execute_query(query)
        
        if not results or len(results) < 2:
            return {
                "success": True,
                "kpi_id": kpi_id,
                "history": results or [],
                "trend": "INSUFFICIENT_DATA",
                "change_percentage": None,
                "source": "BigQuery"
            }
        
        # Calculate trend
        first_value = results[-1].get("value", 0)
        last_value = results[0].get("value", 0)
        
        if first_value == 0:
            change = 0
        else:
            change = ((last_value - first_value) / first_value) * 100
        
        if change < -5:
            trend = "IMPROVING"
        elif change > 5:
            trend = "DETERIORATING"
        else:
            trend = "STABLE"
        
        return {
            "success": True,
            "kpi_id": kpi_id,
            "history": list(reversed(results)),
            "trend": trend,
            "change_percentage": round(change, 1),
            "source": "BigQuery"
        }
        
    except Exception as e:
        logger.error(f"KPI trend error: {e}")
        return {
            "success": False, 
            "error": str(e), 
            "history": [],
            "trend": "ERROR"
        }
