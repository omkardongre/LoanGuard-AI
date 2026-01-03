"""
Risk Velocity Indicator - V6 P0 Feature

Measures rate of change (velocity) and acceleration of covenant metrics.
Shows not just WHERE a loan is, but WHERE it's GOING and how FAST.

This is a UNIQUE feature - no competitor has trajectory-based early warning.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TrajectoryDirection(Enum):
    """Trajectory direction."""
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    WORSENING = "WORSENING"


@dataclass
class VelocityResult:
    """Result of velocity calculation."""
    current_velocity: float
    average_velocity: float
    acceleration: float
    trajectory: TrajectoryDirection
    periods_to_breach: Optional[float]
    risk_level: RiskLevel


def calculate_metric_velocity(
    historical_values: List[Dict[str, Any]],
    threshold: float,
    covenant_type: str = "max",
) -> Dict[str, Any]:
    """
    Calculate velocity (rate of change) for a covenant metric.
    
    Args:
        historical_values: List of {value, period_date} dicts, ordered oldest to newest
        threshold: Covenant threshold value
        covenant_type: "max" (like Debt/EBITDA) or "min" (like Interest Coverage)
    
    Returns:
        Velocity analysis with trajectory and breach prediction
    """
    if len(historical_values) < 2:
        return {
            "success": False,
            "error": "Insufficient historical data (need at least 2 periods)",
        }
    
    try:
        # Extract values in chronological order
        values = [h["value"] for h in historical_values]
        
        # Calculate period-over-period velocities
        velocities = []
        for i in range(1, len(values)):
            velocity = values[i] - values[i-1]
            velocities.append(velocity)
        
        current_velocity = velocities[-1]
        avg_velocity = sum(velocities) / len(velocities)
        
        # Calculate acceleration (change in velocity)
        if len(velocities) >= 2:
            acceleration = velocities[-1] - velocities[-2]
        else:
            acceleration = 0.0
        
        # Current value and headroom
        current_value = values[-1]
        
        # Determine if higher or lower is bad based on covenant type
        is_max_covenant = covenant_type.lower() == "max"  # e.g., Debt/EBITDA (lower is better)
        
        if is_max_covenant:
            headroom = threshold - current_value
            is_worsening = current_velocity > 0  # Increasing toward max threshold
        else:  # min covenant (e.g., Interest Coverage - higher is better)
            headroom = current_value - threshold
            is_worsening = current_velocity < 0  # Decreasing toward min threshold
        
        headroom_percent = (headroom / threshold * 100) if threshold != 0 else 0
        
        # Determine trajectory
        if abs(current_velocity) < 0.01:  # Effectively stable
            trajectory = TrajectoryDirection.STABLE
        elif is_worsening:
            trajectory = TrajectoryDirection.WORSENING
        else:
            trajectory = TrajectoryDirection.IMPROVING
        
        # Calculate periods to breach
        if is_worsening and abs(current_velocity) > 0.001:
            periods_to_breach = abs(headroom / current_velocity)
        else:
            periods_to_breach = None  # Not heading toward breach
        
        # Assess risk level
        risk_level = _assess_velocity_risk(
            current_velocity=current_velocity,
            acceleration=acceleration,
            headroom=headroom,
            headroom_percent=headroom_percent,
            is_worsening=is_worsening,
            is_max_covenant=is_max_covenant,
        )
        
        # Generate summary
        summary = _generate_velocity_summary(
            trajectory=trajectory,
            periods_to_breach=periods_to_breach,
            risk_level=risk_level,
            current_velocity=current_velocity,
        )
        
        return {
            "success": True,
            "current_value": round(current_value, 4),
            "threshold": threshold,
            "covenant_type": covenant_type,
            "headroom": round(headroom, 4),
            "headroom_percent": round(headroom_percent, 2),
            "velocity": {
                "current": round(current_velocity, 4),
                "average": round(avg_velocity, 4),
                "unit": "per_period",
            },
            "acceleration": round(acceleration, 4),
            "trajectory": trajectory.value,
            "is_accelerating": (acceleration > 0 and is_worsening) or (acceleration < 0 and not is_worsening),
            "periods_to_breach": round(periods_to_breach, 1) if periods_to_breach else None,
            "risk_level": risk_level.value,
            "summary": summary,
            "analysis_periods": len(historical_values),
        }
        
    except Exception as e:
        logger.error(f"Velocity calculation error: {e}")
        return {"success": False, "error": str(e)}


def calculate_loan_velocity(
    loan_id: str,
    metrics_history: Dict[str, List[Dict[str, Any]]],
    covenant_thresholds: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate velocity for all covenants of a loan.
    
    Args:
        loan_id: Loan identifier
        metrics_history: Dict of metric_name -> list of historical values
        covenant_thresholds: Dict of metric_name -> {threshold, type}
    
    Returns:
        Comprehensive velocity analysis for the loan
    """
    results = []
    highest_risk = RiskLevel.LOW
    critical_metrics = []
    
    for metric_name, history in metrics_history.items():
        if metric_name not in covenant_thresholds:
            continue
            
        threshold_info = covenant_thresholds[metric_name]
        
        velocity_result = calculate_metric_velocity(
            historical_values=history,
            threshold=threshold_info["threshold"],
            covenant_type=threshold_info.get("type", "max"),
        )
        
        if velocity_result.get("success"):
            velocity_result["metric_name"] = metric_name
            results.append(velocity_result)
            
            # Track highest risk
            metric_risk = RiskLevel[velocity_result["risk_level"]]
            if _risk_level_value(metric_risk) > _risk_level_value(highest_risk):
                highest_risk = metric_risk
            
            # Track critical metrics
            if velocity_result["risk_level"] in ["CRITICAL", "HIGH"]:
                critical_metrics.append({
                    "metric": metric_name,
                    "risk_level": velocity_result["risk_level"],
                    "periods_to_breach": velocity_result.get("periods_to_breach"),
                    "trajectory": velocity_result["trajectory"],
                })
    
    # Sort by risk level
    results.sort(key=lambda x: _risk_level_value(RiskLevel[x["risk_level"]]), reverse=True)
    
    return {
        "success": True,
        "loan_id": loan_id,
        "overall_risk": highest_risk.value,
        "metrics_analyzed": len(results),
        "critical_metrics": critical_metrics,
        "critical_count": len(critical_metrics),
        "metric_velocities": results,
        "recommendation": _get_loan_recommendation(highest_risk, critical_metrics),
    }


def calculate_portfolio_velocity(
    loan_velocities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Aggregate velocity analysis across portfolio.
    
    Args:
        loan_velocities: List of loan velocity results
    
    Returns:
        Portfolio-level velocity summary
    """
    if not loan_velocities:
        return {"success": False, "error": "No loan data provided"}
    
    risk_distribution = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }
    
    worsening_loans = []
    
    for loan in loan_velocities:
        if not loan.get("success"):
            continue
            
        risk_level = loan.get("overall_risk", "LOW")
        risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        # Track worsening loans
        critical = loan.get("critical_metrics", [])
        if critical:
            worsening_loans.append({
                "loan_id": loan["loan_id"],
                "risk_level": risk_level,
                "critical_count": len(critical),
                "nearest_breach": min(
                    (m.get("periods_to_breach") for m in critical if m.get("periods_to_breach")),
                    default=None
                ),
            })
    
    # Sort by nearest breach
    worsening_loans.sort(
        key=lambda x: x.get("nearest_breach") or float('inf')
    )
    
    total_loans = sum(risk_distribution.values())
    
    return {
        "success": True,
        "total_loans_analyzed": total_loans,
        "risk_distribution": risk_distribution,
        "risk_percentages": {
            k: round(v / total_loans * 100, 1) if total_loans > 0 else 0
            for k, v in risk_distribution.items()
        },
        "worsening_loans": worsening_loans[:10],  # Top 10 most at-risk
        "worsening_count": len(worsening_loans),
        "summary": f"{risk_distribution['CRITICAL'] + risk_distribution['HIGH']} loans require immediate attention",
    }


def _assess_velocity_risk(
    current_velocity: float,
    acceleration: float,
    headroom: float,
    headroom_percent: float,
    is_worsening: bool,
    is_max_covenant: bool,
) -> RiskLevel:
    """Assess risk level based on velocity analysis."""
    
    # Critical: Worsening, accelerating, and close to threshold
    if is_worsening and headroom_percent < 5:
        if acceleration > 0 if is_max_covenant else acceleration < 0:
            return RiskLevel.CRITICAL
        return RiskLevel.HIGH
    
    # High: Worsening with limited headroom
    if is_worsening and headroom_percent < 15:
        return RiskLevel.HIGH
    
    # Medium: Worsening but with comfortable headroom
    if is_worsening:
        return RiskLevel.MEDIUM
    
    # Low: Stable or improving
    return RiskLevel.LOW


def _risk_level_value(risk: RiskLevel) -> int:
    """Convert risk level to numeric value for comparison."""
    values = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }
    return values.get(risk, 0)


def _generate_velocity_summary(
    trajectory: TrajectoryDirection,
    periods_to_breach: Optional[float],
    risk_level: RiskLevel,
    current_velocity: float,
) -> str:
    """Generate human-readable velocity summary."""
    
    if periods_to_breach is not None and periods_to_breach < 2:
        return f"⚠️ URGENT: Breach expected within {periods_to_breach:.0f} period(s). Immediate action required."
    
    if periods_to_breach is not None and periods_to_breach < 4:
        return f"⚠️ WARNING: Breach possible in {periods_to_breach:.0f} periods if trend continues."
    
    if risk_level == RiskLevel.CRITICAL:
        return "🚨 CRITICAL: Deteriorating rapidly. Recommend immediate lender engagement."
    
    if risk_level == RiskLevel.HIGH:
        return "⚠️ HIGH RISK: Negative trend detected. Enhanced monitoring recommended."
    
    if trajectory == TrajectoryDirection.IMPROVING:
        return "✅ IMPROVING: Positive trend. Continue standard monitoring."
    
    if trajectory == TrajectoryDirection.STABLE:
        return "✅ STABLE: No significant change. Continue standard monitoring."
    
    return "Monitor for changes in trajectory."


def _get_loan_recommendation(
    risk_level: RiskLevel,
    critical_metrics: List[Dict],
) -> str:
    """Get recommendation based on loan velocity analysis."""
    
    if risk_level == RiskLevel.CRITICAL:
        metrics = ", ".join(m["metric"] for m in critical_metrics[:3])
        return f"IMMEDIATE ACTION: Critical deterioration in {metrics}. Engage borrower immediately."
    
    if risk_level == RiskLevel.HIGH:
        return "ENHANCED MONITORING: Schedule borrower call within 2 weeks. Review remediation options."
    
    if risk_level == RiskLevel.MEDIUM:
        return "WATCHLIST: Add to enhanced monitoring. Review at next quarterly review."
    
    return "STANDARD: Continue normal monitoring schedule."


# Tool function for ADK agent
def get_risk_velocity(
    loan_id: str,
    metric_name: str,
    historical_values: List[Dict[str, Any]],
    threshold: float,
    covenant_type: str = "max",
) -> Dict[str, Any]:
    """
    ADK Tool: Calculate risk velocity for a specific metric.
    
    Args:
        loan_id: Loan identifier
        metric_name: Name of the metric (e.g., "debt_to_ebitda")
        historical_values: List of {value, period_date} dicts
        threshold: Covenant threshold
        covenant_type: "max" or "min"
    
    Returns:
        Velocity analysis result
    """
    result = calculate_metric_velocity(
        historical_values=historical_values,
        threshold=threshold,
        covenant_type=covenant_type,
    )
    
    if result.get("success"):
        result["loan_id"] = loan_id
        result["metric_name"] = metric_name
    
    return result
