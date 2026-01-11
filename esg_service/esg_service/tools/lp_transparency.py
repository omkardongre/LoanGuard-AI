"""
LP Transparency Agent - LP Position Tracking and Transparency Reporting.

Production-level implementation for Fund Finance LP transparency.
Based on ILPA July 2024 Guidance: "Transparency is more important than ever"
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class LPTransparencyAgent:
    """
    LP Transparency Agent for Fund Finance.
    
    Based on Research 6 Quote:
    "Complexity is manageable; opacity isn't" - Kathryn Robinson, Genera Capital
    
    Features:
    - Individual LP exposure tracking
    - Aggregate fund-level leverage visibility
    - LPAC member identification
    - Concentration risk analysis
    """
    
    def __init__(self):
        """Initialize LP Transparency Agent."""
        self.bq = BigQueryClient()
    
    def get_lp_position(self, fund_id: str, lp_name: str = None) -> Dict[str, Any]:
        """
        Get LP position details for a fund.
        
        Args:
            fund_id: Fund identifier
            lp_name: Optional specific LP name
            
        Returns:
            LP position data
        """
        try:
            if lp_name:
                query = f"""
                    SELECT *
                    FROM `{self.bq.project_id}.{self.bq.dataset_id}.lp_positions`
                    WHERE fund_id = '{fund_id}' AND lp_name = '{lp_name}'
                """
            else:
                query = f"""
                    SELECT *
                    FROM `{self.bq.project_id}.{self.bq.dataset_id}.lp_positions`
                    WHERE fund_id = '{fund_id}'
                    ORDER BY commitment_amount DESC
                """
            
            results = self.bq.execute_query(query)
            
            return {
                "success": True,
                "fund_id": fund_id,
                "lp_count": len(results),
                "positions": results,
                "source": "BigQuery"
            }
            
        except Exception as e:
            logger.error(f"Failed to get LP positions: {e}")
            return {"success": False, "error": str(e), "positions": []}
    
    def get_aggregate_leverage_exposure(self, fund_id: str) -> Dict[str, Any]:
        """
        Calculate aggregate fund-level leverage exposure for all LPs.
        
        ILPA Guidance: "LPs calling for greater visibility on fund-level leverage"
        
        Args:
            fund_id: Fund identifier
            
        Returns:
            Aggregate leverage exposure data
        """
        try:
            # Get NAV facility exposure
            nav_query = f"""
                SELECT 
                    SUM(drawn_amount) as total_nav_drawn,
                    SUM(facility_amount) as total_nav_facility,
                    AVG(ltv_ratio) as avg_ltv
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.nav_facilities`
                WHERE fund_id = '{fund_id}' AND status = 'ACTIVE'
            """
            nav_results = self.bq.execute_query(nav_query)
            
            # Get subscription facility exposure
            sub_query = f"""
                SELECT 
                    SUM(drawn_amount) as total_sub_drawn,
                    SUM(facility_amount) as total_sub_facility
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.subscription_facilities`
                WHERE fund_id = '{fund_id}' AND status = 'ACTIVE'
            """
            sub_results = self.bq.execute_query(sub_query)
            
            # Get LP commitments
            lp_query = f"""
                SELECT 
                    SUM(commitment_amount) as total_commitments,
                    COUNT(*) as lp_count
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.lp_positions`
                WHERE fund_id = '{fund_id}'
            """
            lp_results = self.bq.execute_query(lp_query)
            
            nav_row = nav_results[0] if nav_results else {}
            sub_row = sub_results[0] if sub_results else {}
            lp_row = lp_results[0] if lp_results else {}
            
            total_nav_drawn = nav_row.get("total_nav_drawn", 0) or 0
            total_sub_drawn = sub_row.get("total_sub_drawn", 0) or 0
            total_commitments = lp_row.get("total_commitments", 0) or 0
            
            total_leverage = total_nav_drawn + total_sub_drawn
            leverage_to_commitment = (total_leverage / total_commitments * 100) if total_commitments > 0 else 0
            
            return {
                "success": True,
                "fund_id": fund_id,
                "nav_facility_exposure": {
                    "drawn": total_nav_drawn,
                    "facility_size": nav_row.get("total_nav_facility", 0) or 0,
                    "avg_ltv_pct": round((nav_row.get("avg_ltv", 0) or 0) * 100, 2),
                },
                "subscription_facility_exposure": {
                    "drawn": total_sub_drawn,
                    "facility_size": sub_row.get("total_sub_facility", 0) or 0,
                },
                "total_leverage": total_leverage,
                "total_commitments": total_commitments,
                "leverage_to_commitment_pct": round(leverage_to_commitment, 2),
                "lp_count": lp_row.get("lp_count", 0),
                "source": "BigQuery"
            }
            
        except Exception as e:
            logger.error(f"Aggregate leverage calculation error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_lp_leverage_share(self, fund_id: str, lp_name: str) -> Dict[str, Any]:
        """
        Calculate individual LP's share of fund-level leverage.
        
        Args:
            fund_id: Fund identifier
            lp_name: LP name
            
        Returns:
            LP's leverage exposure
        """
        try:
            # Get LP's position
            lp_query = f"""
                SELECT 
                    commitment_amount,
                    concentration_percentage
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.lp_positions`
                WHERE fund_id = '{fund_id}' AND lp_name = '{lp_name}'
            """
            lp_results = self.bq.execute_query(lp_query)
            
            if not lp_results:
                return {"success": False, "error": f"LP {lp_name} not found in fund {fund_id}"}
            
            lp_row = lp_results[0]
            concentration = lp_row.get("concentration_percentage", 0) or 0
            
            # Get aggregate leverage
            aggregate = self.get_aggregate_leverage_exposure(fund_id)
            
            if not aggregate.get("success"):
                return aggregate
            
            total_leverage = aggregate.get("total_leverage", 0)
            
            # LP's share of leverage
            lp_leverage_share = total_leverage * (concentration / 100)
            
            return {
                "success": True,
                "fund_id": fund_id,
                "lp_name": lp_name,
                "commitment_amount": lp_row.get("commitment_amount", 0),
                "concentration_pct": round(concentration, 2),
                "fund_total_leverage": total_leverage,
                "lp_leverage_share": round(lp_leverage_share, 2),
                "lp_leverage_to_commitment": round(
                    lp_leverage_share / lp_row.get("commitment_amount", 1) * 100, 2
                ) if lp_row.get("commitment_amount", 0) > 0 else 0,
            }
            
        except Exception as e:
            logger.error(f"LP leverage share calculation error: {e}")
            return {"success": False, "error": str(e)}
    
    def create_lp_position(self, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new LP position in BigQuery.
        
        Args:
            position_data: LP position data
            
        Returns:
            Creation result
        """
        try:
            position_id = position_data.get("position_id") or f"LP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            fund_id = position_data.get("fund_id", "")
            lp_name = position_data.get("lp_name", "")
            lp_type = position_data.get("lp_type", "Institutional")
            commitment = position_data.get("commitment_amount", 0)
            called = position_data.get("called_amount", 0)
            is_lpac = position_data.get("is_lpac_member", False)
            
            query = f"""
                INSERT INTO `{self.bq.project_id}.{self.bq.dataset_id}.lp_positions`
                (position_id, fund_id, lp_name, lp_type, commitment_amount, called_amount,
                 uncalled_commitment, is_lpac_member, created_at)
                VALUES (
                    '{position_id}',
                    '{fund_id}',
                    '{lp_name.replace("'", "''")}',
                    '{lp_type}',
                    {commitment},
                    {called},
                    {commitment - called},
                    {str(is_lpac).upper()},
                    CURRENT_TIMESTAMP()
                )
            """
            
            self.bq.execute_query(query)
            
            return {
                "success": True,
                "position_id": position_id,
                "message": f"LP position created for {lp_name}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create LP position: {e}")
            return {"success": False, "error": str(e)}
    
    def get_lpac_members(self, fund_id: str) -> Dict[str, Any]:
        """
        Get LPAC members for a fund.
        
        ILPA: "LPAC consent required for NAV facilities"
        
        Args:
            fund_id: Fund identifier
            
        Returns:
            LPAC member list
        """
        try:
            query = f"""
                SELECT 
                    lp_name,
                    lp_type,
                    commitment_amount,
                    concentration_percentage
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.lp_positions`
                WHERE fund_id = '{fund_id}' AND is_lpac_member = TRUE
                ORDER BY commitment_amount DESC
            """
            
            results = self.bq.execute_query(query)
            
            return {
                "success": True,
                "fund_id": fund_id,
                "lpac_member_count": len(results),
                "lpac_members": results,
                "source": "BigQuery"
            }
            
        except Exception as e:
            logger.error(f"Failed to get LPAC members: {e}")
            return {"success": False, "error": str(e), "lpac_members": []}
    
    def get_concentration_analysis(self, fund_id: str) -> Dict[str, Any]:
        """
        Analyze LP concentration risk.
        
        Args:
            fund_id: Fund identifier
            
        Returns:
            Concentration risk analysis
        """
        try:
            query = f"""
                SELECT 
                    lp_name,
                    commitment_amount,
                    lp_type
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.lp_positions`
                WHERE fund_id = '{fund_id}'
                ORDER BY commitment_amount DESC
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": True, "fund_id": fund_id, "message": "No LP positions found"}
            
            total_commitments = sum(r.get("commitment_amount", 0) for r in results)
            
            # Calculate concentration percentages
            for r in results:
                r["concentration_pct"] = round(
                    r.get("commitment_amount", 0) / total_commitments * 100, 2
                ) if total_commitments > 0 else 0
            
            # Top 5 concentration
            top_5_commitment = sum(r.get("commitment_amount", 0) for r in results[:5])
            top_5_concentration = top_5_commitment / total_commitments * 100 if total_commitments > 0 else 0
            
            # HHI (Herfindahl-Hirschman Index)
            hhi = sum((r.get("concentration_pct", 0) ** 2) for r in results)
            
            return {
                "success": True,
                "fund_id": fund_id,
                "total_lps": len(results),
                "total_commitments": total_commitments,
                "top_5_concentration_pct": round(top_5_concentration, 1),
                "hhi_index": round(hhi, 0),
                "concentration_risk": "HIGH" if top_5_concentration > 70 else "MODERATE" if top_5_concentration > 50 else "LOW",
                "lp_breakdown": results[:10],  # Top 10 LPs
                "source": "BigQuery"
            }
            
        except Exception as e:
            logger.error(f"Concentration analysis error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_lp_transparency: Optional[LPTransparencyAgent] = None


def get_lp_transparency_agent() -> LPTransparencyAgent:
    """Get or create LP Transparency singleton."""
    global _lp_transparency
    if _lp_transparency is None:
        _lp_transparency = LPTransparencyAgent()
    return _lp_transparency


# Convenience functions
def get_lp_positions(fund_id: str) -> Dict[str, Any]:
    """Get LP positions for a fund."""
    return get_lp_transparency_agent().get_lp_position(fund_id)


def get_fund_leverage_exposure(fund_id: str) -> Dict[str, Any]:
    """Get aggregate leverage exposure for fund."""
    return get_lp_transparency_agent().get_aggregate_leverage_exposure(fund_id)


def get_lp_leverage(fund_id: str, lp_name: str) -> Dict[str, Any]:
    """Get individual LP's leverage share."""
    return get_lp_transparency_agent().get_lp_leverage_share(fund_id, lp_name)


def create_lp_position(position_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create new LP position."""
    return get_lp_transparency_agent().create_lp_position(position_data)
