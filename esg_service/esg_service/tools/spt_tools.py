"""
SPT validation tools for sustainability-linked loans - PRODUCTION VERSION.

All data fetched from BigQuery - NO MOCK DATA.
"""

import logging
from typing import Any, Dict, List, Optional

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


def get_spt_definitions(loan_id: str) -> Dict[str, Any]:
    """
    Get SPT definitions for a loan from BigQuery.

    Args:
        loan_id: Loan identifier

    Returns:
        SPT definitions
    """
    try:
        bq = BigQueryClient()
        
        query = f"""
            SELECT 
                spt_id,
                kpi_id,
                target_description,
                target_value,
                target_year,
                target_type,
                current_progress,
                achievement_probability,
                margin_impact_bps,
                verification_required,
                verifier_name,
                verification_date,
                status,
                created_at
            FROM `{bq.project_id}.{bq.dataset_id}.sll_spts`
            WHERE loan_id = '{loan_id}'
            ORDER BY target_year ASC
        """
        
        results = bq.execute_query(query)
        
        # Calculate total margin impact
        total_margin = sum(r.get("margin_impact_bps", 0) or 0 for r in results)
        
        return {
            "success": True,
            "loan_id": loan_id,
            "spt_count": len(results),
            "spts": results,
            "total_margin_impact_bps": total_margin,
            "source": "BigQuery"
        }
        
    except Exception as e:
        logger.error(f"Failed to get SPT definitions: {e}")
        return {"success": False, "error": str(e), "spts": []}


def validate_spt_achievement(
    loan_id: str = None,
    spt_id: str = None,
    target_value: float = None,
    actual_value: float = None,
    target_type: str = "reduction",
) -> Dict[str, Any]:
    """
    Validate whether an SPT has been achieved.

    If target_value and actual_value not provided, fetches from BigQuery.

    Args:
        loan_id: Loan identifier
        spt_id: SPT identifier
        target_value: Target value (optional, fetched from DB if not provided)
        actual_value: Actual achieved value (optional, fetched from DB if not provided)
        target_type: "reduction" or "increase"

    Returns:
        Validation result
    """
    try:
        # If values not provided, fetch from BigQuery
        if target_value is None or actual_value is None:
            bq = BigQueryClient()
            
            query = f"""
                SELECT 
                    s.spt_id,
                    s.target_value,
                    s.target_type,
                    k.current_value as actual_value
                FROM `{bq.project_id}.{bq.dataset_id}.sll_spts` s
                LEFT JOIN `{bq.project_id}.{bq.dataset_id}.sll_kpis` k ON s.kpi_id = k.kpi_id
                WHERE s.spt_id = '{spt_id}'
                OR (s.loan_id = '{loan_id}' AND s.spt_id = '{spt_id}')
            """
            
            results = bq.execute_query(query)
            
            if not results:
                return {"success": False, "error": f"SPT {spt_id} not found"}
            
            row = results[0]
            target_value = row.get("target_value")
            actual_value = row.get("actual_value")
            target_type = row.get("target_type", "reduction")
        
        if actual_value is None:
            return {
                "success": True,
                "spt_id": spt_id,
                "achieved": False,
                "status": "NO_MEASUREMENT",
                "message": "No current measurement available"
            }
        
        if target_type == "reduction":
            achieved = actual_value <= target_value
            gap = actual_value - target_value
        else:
            achieved = actual_value >= target_value
            gap = target_value - actual_value

        # Calculate achievement percentage
        if target_type == "reduction":
            if target_value > 0:
                achievement_pct = (1 - (actual_value / target_value)) * 100 + 100
            else:
                achievement_pct = 100
        else:
            if target_value > 0:
                achievement_pct = (actual_value / target_value) * 100
            else:
                achievement_pct = 0

        return {
            "success": True,
            "spt_id": spt_id,
            "target_value": target_value,
            "actual_value": actual_value,
            "achieved": achieved,
            "gap": gap,
            "variance_pct": round(achievement_pct - 100, 1),
            "achievement_percentage": round(achievement_pct, 1),
            "status": "ACHIEVED" if achieved else "NOT_ACHIEVED",
        }
    except Exception as e:
        logger.error(f"SPT validation error: {e}")
        return {"success": False, "error": str(e)}


def calculate_margin_adjustment(
    loan_id: str = None,
    spts_achieved: List[Dict[str, Any]] = None,
    spts_not_achieved: List[Dict[str, Any]] = None,
    two_way_pricing: bool = False,
) -> Dict[str, Any]:
    """
    Calculate margin adjustment based on SPT achievement.

    If spts_achieved/spts_not_achieved not provided, calculates from BigQuery data.

    Args:
        loan_id: Loan identifier (to fetch from BigQuery)
        spts_achieved: List of achieved SPTs with margin_adjustment_bps
        spts_not_achieved: List of not achieved SPTs
        two_way_pricing: Whether loan has two-way pricing

    Returns:
        Margin adjustment result
    """
    try:
        # If lists not provided, calculate from BigQuery
        if spts_achieved is None or spts_not_achieved is None:
            if not loan_id:
                return {"success": False, "error": "loan_id required when SPT lists not provided"}
            
            bq = BigQueryClient()
            
            query = f"""
                SELECT 
                    s.spt_id,
                    s.target_value,
                    s.target_type,
                    s.margin_impact_bps,
                    k.current_value
                FROM `{bq.project_id}.{bq.dataset_id}.sll_spts` s
                LEFT JOIN `{bq.project_id}.{bq.dataset_id}.sll_kpis` k ON s.kpi_id = k.kpi_id
                WHERE s.loan_id = '{loan_id}'
            """
            
            results = bq.execute_query(query)
            
            spts_achieved = []
            spts_not_achieved = []
            
            for spt in results:
                target = spt.get("target_value", 0)
                current = spt.get("current_value")
                target_type = spt.get("target_type", "reduction")
                
                if current is None:
                    spts_not_achieved.append(spt)
                elif target_type == "reduction":
                    if current <= target:
                        spts_achieved.append(spt)
                    else:
                        spts_not_achieved.append(spt)
                else:
                    if current >= target:
                        spts_achieved.append(spt)
                    else:
                        spts_not_achieved.append(spt)
        
        achieved_adjustment = sum(
            s.get("margin_impact_bps", 0) or 0 for s in spts_achieved
        )
        
        if two_way_pricing:
            # Two-way: step-down for achievement, step-up for failure
            not_achieved_adjustment = sum(
                s.get("margin_impact_bps", 0) or 0 for s in spts_not_achieved
            )
            net_adjustment = achieved_adjustment - not_achieved_adjustment
            direction = "step-down" if net_adjustment > 0 else "step-up" if net_adjustment < 0 else "no_change"
        else:
            # One-way: only step-down for achievement
            net_adjustment = achieved_adjustment
            direction = "step-down" if net_adjustment > 0 else "no_change"

        return {
            "success": True,
            "loan_id": loan_id,
            "spts_achieved_count": len(spts_achieved),
            "spts_not_achieved_count": len(spts_not_achieved),
            "achieved_adjustment_bps": achieved_adjustment,
            "net_adjustment_bps": abs(net_adjustment),
            "adjustment_bps": abs(net_adjustment),
            "adjustment_direction": direction,
            "two_way_pricing": two_way_pricing,
            "effective_margin_change": f"{'-' if direction == 'step-down' else '+' if direction == 'step-up' else ''}{abs(net_adjustment)} bps",
        }
    except Exception as e:
        logger.error(f"Margin adjustment calculation error: {e}")
        return {"success": False, "error": str(e)}


def check_verification_status(
    loan_id: str,
    spt_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check third-party verification status for SPTs from BigQuery.

    Args:
        loan_id: Loan identifier
        spt_id: Optional specific SPT to check

    Returns:
        Verification status
    """
    try:
        bq = BigQueryClient()
        
        if spt_id:
            query = f"""
                SELECT 
                    spt_id,
                    verification_required,
                    verifier_name,
                    verification_date,
                    status
                FROM `{bq.project_id}.{bq.dataset_id}.sll_spts`
                WHERE spt_id = '{spt_id}'
            """
        else:
            query = f"""
                SELECT 
                    spt_id,
                    verification_required,
                    verifier_name,
                    verification_date,
                    status
                FROM `{bq.project_id}.{bq.dataset_id}.sll_spts`
                WHERE loan_id = '{loan_id}'
            """
        
        results = bq.execute_query(query)
        
        if spt_id:
            if not results:
                return {"success": False, "error": f"SPT {spt_id} not found"}
            
            row = results[0]
            verified = row.get("verification_date") is not None
            
            return {
                "success": True,
                "spt_id": spt_id,
                "verification": {
                    "verified": verified,
                    "verifier": row.get("verifier_name"),
                    "verification_date": str(row.get("verification_date")) if row.get("verification_date") else None,
                    "status": row.get("status"),
                }
            }
        
        # Build verification dict for all SPTs
        verifications = {}
        for row in results:
            verified = row.get("verification_date") is not None
            verifications[row.get("spt_id")] = {
                "verified": verified,
                "verifier": row.get("verifier_name"),
                "verification_date": str(row.get("verification_date")) if row.get("verification_date") else None,
                "status": row.get("status"),
            }
        
        all_verified = all(v.get("verified", False) for v in verifications.values()) if verifications else False
        
        return {
            "success": True,
            "loan_id": loan_id,
            "verifications": verifications,
            "all_verified": all_verified,
            "source": "BigQuery"
        }
        
    except Exception as e:
        logger.error(f"Verification status check error: {e}")
        return {"success": False, "error": str(e)}
