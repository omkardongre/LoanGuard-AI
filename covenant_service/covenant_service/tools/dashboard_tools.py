"""
Covenant Dashboard Tools - V8 Production

Provides comprehensive dashboard data for covenant monitoring.
Core value proposition for LoanGuard AI.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import sys
sys.path.insert(0, str(__file__).rsplit("/", 4)[0])

from common.bigquery_client import bq_client

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """Covenant compliance status."""
    IN_COMPLIANCE = "IN_COMPLIANCE"
    WARNING = "WARNING"
    BREACH = "BREACH"
    WAIVED = "WAIVED"
    PENDING = "PENDING"


class TrendDirection(Enum):
    """Trend direction for metrics."""
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DETERIORATING = "DETERIORATING"


@dataclass
class CovenantSummary:
    """Summary data for a single covenant."""
    covenant_id: str
    covenant_name: str
    covenant_type: str
    threshold_value: float
    threshold_operator: str
    current_value: Optional[float]
    headroom_percent: float
    status: str
    trend: str
    last_measured: Optional[str]


@dataclass
class DashboardSummary:
    """Complete dashboard summary for a loan."""
    loan_id: str
    borrower_name: str
    facility_amount: float
    currency: str
    maturity_date: Optional[str]
    total_covenants: int
    in_compliance: int
    warnings: int
    breaches: int
    overall_health: str
    covenants: List[Dict[str, Any]]
    last_updated: str


def get_loan_dashboard(loan_id: str) -> Dict[str, Any]:
    """
    Get complete dashboard data for a single loan.
    
    Args:
        loan_id: Unique loan identifier
        
    Returns:
        Comprehensive dashboard data including all covenants
    """
    try:
        logger.info(f"Fetching dashboard data for loan {loan_id}")
        
        # Get loan details
        loan = bq_client.get_loan_by_id(loan_id)
        if not loan:
            return {
                "success": False,
                "error": f"Loan {loan_id} not found",
            }
        
        # Get all covenants for this loan
        covenants = bq_client.get_covenants_by_loan(loan_id)
        
        covenant_summaries = []
        in_compliance = 0
        warnings = 0
        breaches = 0
        
        for covenant in covenants:
            covenant_id = covenant.get("covenant_id")
            
            # Get latest measurement
            measurements = bq_client.get_latest_measurements(covenant_id, limit=4)
            
            current_value = None
            headroom_percent = 0.0
            status = ComplianceStatus.PENDING.value
            trend = TrendDirection.STABLE.value
            last_measured = None
            
            if measurements:
                latest = measurements[0]
                current_value = latest.get("measured_value")
                headroom_percent = latest.get("headroom_percent", 0.0)
                is_compliant = latest.get("is_in_compliance", True)
                last_measured = str(latest.get("measurement_date", ""))
                
                # Determine status
                if not is_compliant:
                    status = ComplianceStatus.BREACH.value
                    breaches += 1
                elif headroom_percent < 15:
                    status = ComplianceStatus.WARNING.value
                    warnings += 1
                else:
                    status = ComplianceStatus.IN_COMPLIANCE.value
                    in_compliance += 1
                
                # Calculate trend from last 4 measurements
                if len(measurements) >= 2:
                    trend = _calculate_trend(measurements, covenant.get("threshold_type", "max"))
            else:
                # No measurements yet
                status = ComplianceStatus.PENDING.value
            
            summary = CovenantSummary(
                covenant_id=covenant_id,
                covenant_name=covenant.get("metric_name", "Unknown"),
                covenant_type=covenant.get("covenant_type", "financial"),
                threshold_value=covenant.get("threshold_value", 0.0),
                threshold_operator=covenant.get("threshold_type", "<="),
                current_value=current_value,
                headroom_percent=headroom_percent,
                status=status,
                trend=trend,
                last_measured=last_measured,
            )
            
            covenant_summaries.append(asdict(summary))
        
        # Determine overall health
        if breaches > 0:
            overall_health = "CRITICAL"
        elif warnings > 0:
            overall_health = "AT_RISK"
        elif in_compliance == len(covenants) and len(covenants) > 0:
            overall_health = "HEALTHY"
        else:
            overall_health = "UNKNOWN"
        
        dashboard = DashboardSummary(
            loan_id=loan_id,
            borrower_name=loan.get("borrower_name", "Unknown"),
            facility_amount=loan.get("facility_amount", 0.0),
            currency=loan.get("currency", "USD"),
            maturity_date=str(loan.get("maturity_date", "")) if loan.get("maturity_date") else None,
            total_covenants=len(covenants),
            in_compliance=in_compliance,
            warnings=warnings,
            breaches=breaches,
            overall_health=overall_health,
            covenants=covenant_summaries,
            last_updated=datetime.utcnow().isoformat(),
        )
        
        return {
            "success": True,
            "dashboard": asdict(dashboard),
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard for {loan_id}: {e}")
        return {"success": False, "error": str(e)}


def get_portfolio_dashboard() -> Dict[str, Any]:
    """
    Get portfolio-wide covenant dashboard summary.
    
    Returns:
        Aggregated dashboard data across all loans
    """
    try:
        logger.info("Fetching portfolio dashboard")
        
        # Get all active loans
        loans = bq_client.get_all_loans(status="ACTIVE")
        
        if not loans:
            return {
                "success": True,
                "portfolio": {
                    "total_loans": 0,
                    "total_facility": 0,
                    "healthy_loans": 0,
                    "at_risk_loans": 0,
                    "critical_loans": 0,
                    "loans": [],
                    "last_updated": datetime.utcnow().isoformat(),
                }
            }
        
        total_facility = 0.0
        healthy_loans = 0
        at_risk_loans = 0
        critical_loans = 0
        loan_summaries = []
        
        for loan in loans:
            loan_id = loan.get("loan_id")
            dashboard_result = get_loan_dashboard(loan_id)
            
            if dashboard_result.get("success"):
                dashboard = dashboard_result.get("dashboard", {})
                total_facility += dashboard.get("facility_amount", 0.0)
                
                health = dashboard.get("overall_health", "UNKNOWN")
                if health == "HEALTHY":
                    healthy_loans += 1
                elif health == "AT_RISK":
                    at_risk_loans += 1
                elif health == "CRITICAL":
                    critical_loans += 1
                
                loan_summaries.append({
                    "loan_id": loan_id,
                    "borrower_name": dashboard.get("borrower_name"),
                    "facility_amount": dashboard.get("facility_amount"),
                    "overall_health": health,
                    "breaches": dashboard.get("breaches", 0),
                    "warnings": dashboard.get("warnings", 0),
                })
        
        # Sort by health (critical first)
        health_order = {"CRITICAL": 0, "AT_RISK": 1, "UNKNOWN": 2, "HEALTHY": 3}
        loan_summaries.sort(key=lambda x: health_order.get(x.get("overall_health", "UNKNOWN"), 4))
        
        return {
            "success": True,
            "portfolio": {
                "total_loans": len(loans),
                "total_facility": total_facility,
                "currency": "USD",
                "healthy_loans": healthy_loans,
                "at_risk_loans": at_risk_loans,
                "critical_loans": critical_loans,
                "health_distribution": {
                    "healthy_pct": round(healthy_loans / len(loans) * 100, 1) if loans else 0,
                    "at_risk_pct": round(at_risk_loans / len(loans) * 100, 1) if loans else 0,
                    "critical_pct": round(critical_loans / len(loans) * 100, 1) if loans else 0,
                },
                "loans": loan_summaries,
                "last_updated": datetime.utcnow().isoformat(),
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching portfolio dashboard: {e}")
        return {"success": False, "error": str(e)}


def get_covenant_detail(
    loan_id: str,
    covenant_id: str,
) -> Dict[str, Any]:
    """
    Get detailed data for a specific covenant including history.
    
    Args:
        loan_id: Loan identifier
        covenant_id: Covenant identifier
        
    Returns:
        Detailed covenant data with historical measurements
    """
    try:
        # Get covenant definition
        covenants = bq_client.get_covenants_by_loan(loan_id)
        covenant = next((c for c in covenants if c.get("covenant_id") == covenant_id), None)
        
        if not covenant:
            return {
                "success": False,
                "error": f"Covenant {covenant_id} not found for loan {loan_id}",
            }
        
        # Get historical measurements
        measurements = bq_client.get_latest_measurements(covenant_id, limit=12)
        
        # Calculate statistics
        values = [m.get("measured_value") for m in measurements if m.get("measured_value") is not None]
        
        stats = {}
        if values:
            stats = {
                "min_value": min(values),
                "max_value": max(values),
                "avg_value": sum(values) / len(values),
                "current_value": values[0] if values else None,
                "measurement_count": len(values),
            }
        
        # Determine trend
        trend = TrendDirection.STABLE.value
        if len(measurements) >= 2:
            trend = _calculate_trend(measurements, covenant.get("threshold_type", "max"))
        
        return {
            "success": True,
            "covenant": {
                "covenant_id": covenant_id,
                "loan_id": loan_id,
                "name": covenant.get("metric_name"),
                "type": covenant.get("covenant_type"),
                "threshold_value": covenant.get("threshold_value"),
                "threshold_operator": covenant.get("threshold_type"),
                "frequency": covenant.get("frequency", "quarterly"),
                "trend": trend,
                "statistics": stats,
                "history": [
                    {
                        "date": str(m.get("measurement_date", "")),
                        "value": m.get("measured_value"),
                        "headroom": m.get("headroom_percent"),
                        "compliant": m.get("is_in_compliance"),
                    }
                    for m in measurements
                ],
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching covenant detail: {e}")
        return {"success": False, "error": str(e)}


def _calculate_trend(
    measurements: List[Dict[str, Any]],
    threshold_type: str,
) -> str:
    """
    Calculate trend direction from measurements.
    
    Args:
        measurements: List of measurements (newest first)
        threshold_type: max or min threshold
        
    Returns:
        Trend direction string
    """
    if len(measurements) < 2:
        return TrendDirection.STABLE.value
    
    values = [m.get("measured_value") for m in measurements[:4] if m.get("measured_value") is not None]
    
    if len(values) < 2:
        return TrendDirection.STABLE.value
    
    # Compare newest to oldest
    newest = values[0]
    oldest = values[-1]
    
    if oldest == 0:
        return TrendDirection.STABLE.value
    
    change_pct = ((newest - oldest) / abs(oldest)) * 100
    
    # For max covenants (like Debt/EBITDA), lower is better
    # For min covenants (like Interest Coverage), higher is better
    is_max_covenant = threshold_type in ["max", "<=", "<"]
    
    threshold = 5.0  # 5% change threshold
    
    if is_max_covenant:
        # Lower is better
        if change_pct < -threshold:
            return TrendDirection.IMPROVING.value
        elif change_pct > threshold:
            return TrendDirection.DETERIORATING.value
    else:
        # Higher is better
        if change_pct > threshold:
            return TrendDirection.IMPROVING.value
        elif change_pct < -threshold:
            return TrendDirection.DETERIORATING.value
    
    return TrendDirection.STABLE.value


# Export tool functions for ADK agents
__all__ = [
    "get_loan_dashboard",
    "get_portfolio_dashboard",
    "get_covenant_detail",
    "ComplianceStatus",
    "TrendDirection",
]
