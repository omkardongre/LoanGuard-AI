"""
SPT validation tools for sustainability-linked loans.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_spt_definitions(loan_id: str) -> Dict[str, Any]:
    """
    Get SPT definitions for a loan.

    Args:
        loan_id: Loan identifier

    Returns:
        SPT definitions
    """
    spts = [
        {
            "spt_id": f"{loan_id}_spt1",
            "kpi_name": "Carbon Emissions Reduction",
            "target_value": 70000,
            "target_date": "2026-12-31",
            "margin_adjustment_bps": 5,
            "verification_required": True,
            "verifier": "Third-party auditor",
        },
        {
            "spt_id": f"{loan_id}_spt2",
            "kpi_name": "Renewable Energy Percentage",
            "target_value": 50,
            "target_date": "2026-12-31",
            "margin_adjustment_bps": 2.5,
            "verification_required": True,
            "verifier": "Third-party auditor",
        },
    ]

    return {
        "success": True,
        "loan_id": loan_id,
        "spt_count": len(spts),
        "spts": spts,
        "total_margin_impact_bps": sum(s["margin_adjustment_bps"] for s in spts),
    }


def validate_spt_achievement(
    spt_id: str,
    target_value: float,
    actual_value: float,
    target_type: str = "reduction",
) -> Dict[str, Any]:
    """
    Validate whether an SPT has been achieved.

    Args:
        spt_id: SPT identifier
        target_value: Target value
        actual_value: Actual achieved value
        target_type: "reduction" or "increase"

    Returns:
        Validation result
    """
    try:
        if target_type == "reduction":
            achieved = actual_value <= target_value
            gap = actual_value - target_value
        else:
            achieved = actual_value >= target_value
            gap = target_value - actual_value

        # Calculate achievement percentage
        if target_type == "reduction":
            achievement_pct = (1 - (actual_value / target_value)) * 100 + 100
        else:
            achievement_pct = (actual_value / target_value) * 100

        return {
            "success": True,
            "spt_id": spt_id,
            "target_value": target_value,
            "actual_value": actual_value,
            "achieved": achieved,
            "gap": gap,
            "achievement_percentage": round(achievement_pct, 1),
            "status": "ACHIEVED" if achieved else "NOT_ACHIEVED",
        }
    except Exception as e:
        logger.error(f"SPT validation error: {e}")
        return {"success": False, "error": str(e)}


def calculate_margin_adjustment(
    spts_achieved: List[Dict[str, Any]],
    spts_not_achieved: List[Dict[str, Any]],
    two_way_pricing: bool = False,
) -> Dict[str, Any]:
    """
    Calculate margin adjustment based on SPT achievement.

    Args:
        spts_achieved: List of achieved SPTs with margin_adjustment_bps
        spts_not_achieved: List of not achieved SPTs
        two_way_pricing: Whether loan has two-way pricing

    Returns:
        Margin adjustment result
    """
    try:
        achieved_adjustment = sum(
            s.get("margin_adjustment_bps", 0) for s in spts_achieved
        )
        
        if two_way_pricing:
            # Two-way: step-down for achievement, step-up for failure
            not_achieved_adjustment = sum(
                s.get("margin_adjustment_bps", 0) for s in spts_not_achieved
            )
            net_adjustment = achieved_adjustment - not_achieved_adjustment
            direction = "step-down" if net_adjustment > 0 else "step-up"
        else:
            # One-way: only step-down for achievement
            net_adjustment = achieved_adjustment
            direction = "step-down" if net_adjustment > 0 else "no_change"

        return {
            "success": True,
            "spts_achieved_count": len(spts_achieved),
            "spts_not_achieved_count": len(spts_not_achieved),
            "achieved_adjustment_bps": achieved_adjustment,
            "net_adjustment_bps": abs(net_adjustment),
            "adjustment_direction": direction,
            "two_way_pricing": two_way_pricing,
            "effective_margin_change": f"{'-' if direction == 'step-down' else '+'}{abs(net_adjustment)} bps",
        }
    except Exception as e:
        logger.error(f"Margin adjustment calculation error: {e}")
        return {"success": False, "error": str(e)}


def check_verification_status(
    loan_id: str,
    spt_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check third-party verification status for SPTs.

    Args:
        loan_id: Loan identifier
        spt_id: Optional specific SPT to check

    Returns:
        Verification status
    """
    # Mock verification status
    verifications = {
        f"{loan_id}_spt1": {
            "verified": True,
            "verifier": "Deloitte",
            "verification_date": "2025-02-15",
            "verification_type": "Limited assurance",
            "report_available": True,
        },
        f"{loan_id}_spt2": {
            "verified": False,
            "verifier": None,
            "verification_date": None,
            "verification_type": None,
            "report_available": False,
            "reason": "Verification pending - deadline 2025-03-31",
        },
    }

    if spt_id:
        status = verifications.get(spt_id, {"error": "SPT not found"})
        return {
            "success": True,
            "spt_id": spt_id,
            "verification": status,
        }

    return {
        "success": True,
        "loan_id": loan_id,
        "verifications": verifications,
        "all_verified": all(v.get("verified", False) for v in verifications.values()),
    }
