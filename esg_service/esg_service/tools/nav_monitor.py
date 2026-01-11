"""
NAV Monitor Agent - NAV Facility Monitoring with LTV Buffer Analysis.

Production-level implementation for Fund Finance NAV monitoring.
Based on ILPA July 2024 NAV-Based Facilities Guidance.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, date

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


@dataclass
class NAVFacility:
    """NAV Facility data structure."""
    facility_id: str
    fund_id: str
    fund_name: str
    fund_type: str
    nav_value: float
    facility_amount: float
    drawn_amount: float
    ltv_ratio: float
    ltv_covenant_threshold: float
    buffer_percentage: float
    status: str


class NAVMonitorAgent:
    """
    Monitor NAV Facilities with LTV buffer analysis.
    
    Based on ILPA July 2024 Guidance:
    - Senior secured lending typically features LTV ratios of 5-12%
    - Built-in buffers to prevent covenant breach
    - NAV valuation tracking
    """
    
    # Industry standard LTV thresholds (from ILPA guidance)
    LTV_THRESHOLDS = {
        "senior_secured": {"min": 0.05, "max": 0.12, "typical": 0.10},
        "mezzanine": {"min": 0.15, "max": 0.25, "typical": 0.20},
        "unitranche": {"min": 0.10, "max": 0.20, "typical": 0.15},
    }
    
    def __init__(self):
        """Initialize NAV Monitor Agent."""
        self.bq = BigQueryClient()
    
    def get_facility(self, facility_id: str) -> Dict[str, Any]:
        """
        Get NAV facility details from BigQuery.
        
        Args:
            facility_id: NAV facility identifier
            
        Returns:
            Facility details
        """
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.nav_facilities`
                WHERE facility_id = '{facility_id}'
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": False, "error": f"Facility {facility_id} not found"}
            
            return {
                "success": True,
                "facility": results[0],
                "source": "BigQuery"
            }
            
        except Exception as e:
            logger.error(f"Failed to get NAV facility: {e}")
            return {"success": False, "error": str(e)}
    
    def calculate_ltv(
        self,
        facility_id: str = None,
        drawn_amount: float = None,
        nav_value: float = None,
    ) -> Dict[str, Any]:
        """
        Calculate current LTV ratio for a NAV facility.
        
        Args:
            facility_id: NAV facility ID (fetches from DB if provided)
            drawn_amount: Current drawn amount (optional)
            nav_value: Current NAV value (optional)
            
        Returns:
            LTV calculation with buffer analysis
        """
        try:
            # Fetch from BigQuery if facility_id provided
            if facility_id and (drawn_amount is None or nav_value is None):
                query = f"""
                    SELECT drawn_amount, nav_value, ltv_covenant_threshold, facility_amount
                    FROM `{self.bq.project_id}.{self.bq.dataset_id}.nav_facilities`
                    WHERE facility_id = '{facility_id}'
                """
                results = self.bq.execute_query(query)
                
                if not results:
                    return {"success": False, "error": f"Facility {facility_id} not found"}
                
                row = results[0]
                drawn_amount = row.get("drawn_amount", 0)
                nav_value = row.get("nav_value", 0)
                covenant_threshold = row.get("ltv_covenant_threshold", 0.15)
                facility_amount = row.get("facility_amount", 0)
            else:
                covenant_threshold = 0.15  # Default 15%
                facility_amount = drawn_amount  # Assume fully drawn
            
            if nav_value == 0:
                return {"success": False, "error": "NAV value cannot be zero"}
            
            # Calculate LTV
            ltv_ratio = drawn_amount / nav_value
            
            # Buffer analysis
            ltv_headroom = covenant_threshold - ltv_ratio
            buffer_percentage = (ltv_headroom / covenant_threshold) * 100 if covenant_threshold > 0 else 0
            
            # Calculate NAV decline to breach
            if covenant_threshold > 0 and ltv_ratio > 0:
                # At what NAV would we breach?
                # drawn_amount / breach_nav = covenant_threshold
                # breach_nav = drawn_amount / covenant_threshold
                breach_nav = drawn_amount / covenant_threshold
                nav_decline_to_breach = ((nav_value - breach_nav) / nav_value) * 100
            else:
                nav_decline_to_breach = 100.0
            
            # Determine status
            if ltv_ratio >= covenant_threshold:
                ltv_status = "BREACH"
            elif ltv_ratio >= covenant_threshold * 0.85:
                ltv_status = "WARNING"
            else:
                ltv_status = "OK"
            
            return {
                "success": True,
                "facility_id": facility_id,
                "drawn_amount": drawn_amount,
                "nav_value": nav_value,
                "ltv_ratio": round(ltv_ratio, 4),
                "ltv_percentage": round(ltv_ratio * 100, 2),
                "covenant_threshold": covenant_threshold,
                "covenant_percentage": round(covenant_threshold * 100, 2),
                "ltv_headroom": round(ltv_headroom, 4),
                "buffer_percentage": round(buffer_percentage, 1),
                "nav_decline_to_breach": round(nav_decline_to_breach, 1),
                "ltv_status": ltv_status,
                "facility_amount": facility_amount,
                "utilization": round((drawn_amount / facility_amount) * 100, 1) if facility_amount > 0 else 0,
            }
            
        except Exception as e:
            logger.error(f"LTV calculation error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_buffer_analysis(self, facility_id: str) -> Dict[str, Any]:
        """
        Detailed buffer analysis for NAV facility.
        
        Calculates headroom and stress scenarios based on NAV movements.
        
        Args:
            facility_id: NAV facility identifier
            
        Returns:
            Buffer analysis with stress scenarios
        """
        try:
            # Get current LTV
            ltv_result = self.calculate_ltv(facility_id=facility_id)
            
            if not ltv_result.get("success"):
                return ltv_result
            
            nav_value = ltv_result.get("nav_value", 0)
            drawn_amount = ltv_result.get("drawn_amount", 0)
            covenant = ltv_result.get("covenant_threshold", 0.15)
            
            # Stress scenarios: What if NAV drops?
            stress_scenarios = []
            for decline_pct in [5, 10, 15, 20, 25, 30]:
                stressed_nav = nav_value * (1 - decline_pct / 100)
                stressed_ltv = drawn_amount / stressed_nav if stressed_nav > 0 else 0
                
                stress_scenarios.append({
                    "nav_decline_pct": decline_pct,
                    "stressed_nav": round(stressed_nav, 2),
                    "stressed_ltv": round(stressed_ltv * 100, 2),
                    "breach": stressed_ltv >= covenant,
                    "headroom_bps": round((covenant - stressed_ltv) * 10000) if stressed_ltv < covenant else 0,
                })
            
            # Find breakeven NAV decline
            current_ltv = ltv_result.get("ltv_ratio", 0)
            nav_decline_to_breach = ltv_result.get("nav_decline_to_breach", 0)
            
            return {
                "success": True,
                "facility_id": facility_id,
                "current_analysis": {
                    "nav_value": nav_value,
                    "drawn_amount": drawn_amount,
                    "current_ltv_pct": round(current_ltv * 100, 2),
                    "covenant_ltv_pct": round(covenant * 100, 2),
                    "buffer_pct": ltv_result.get("buffer_percentage"),
                    "status": ltv_result.get("ltv_status"),
                },
                "stress_scenarios": stress_scenarios,
                "nav_decline_to_breach_pct": nav_decline_to_breach,
                "risk_assessment": self._assess_buffer_risk(nav_decline_to_breach),
            }
            
        except Exception as e:
            logger.error(f"Buffer analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    def _assess_buffer_risk(self, nav_decline_to_breach: float) -> Dict[str, Any]:
        """Assess risk level based on buffer."""
        if nav_decline_to_breach >= 30:
            return {"level": "LOW", "description": "Strong buffer - NAV can decline 30%+ before breach"}
        elif nav_decline_to_breach >= 20:
            return {"level": "MODERATE", "description": "Adequate buffer - NAV can decline 20-30% before breach"}
        elif nav_decline_to_breach >= 10:
            return {"level": "ELEVATED", "description": "Limited buffer - NAV decline of 10-20% would breach covenant"}
        else:
            return {"level": "HIGH", "description": "Minimal buffer - At risk of covenant breach"}
    
    def create_facility(self, facility_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new NAV facility in BigQuery.
        
        Args:
            facility_data: NAV facility data
            
        Returns:
            Creation result
        """
        try:
            facility_id = facility_data.get("facility_id") or f"NAV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            fund_id = facility_data.get("fund_id", "")
            fund_name = facility_data.get("fund_name", "")
            fund_type = facility_data.get("fund_type", "PE")
            nav_value = facility_data.get("nav_value", 0)
            facility_amount = facility_data.get("facility_amount", 0)
            drawn_amount = facility_data.get("drawn_amount", 0)
            ltv_covenant = facility_data.get("ltv_covenant_threshold", 0.15)
            
            # Calculate LTV
            ltv_ratio = drawn_amount / nav_value if nav_value > 0 else 0
            initial_ltv = ltv_ratio
            buffer_pct = ((ltv_covenant - ltv_ratio) / ltv_covenant * 100) if ltv_covenant > 0 else 0
            
            query = f"""
                INSERT INTO `{self.bq.project_id}.{self.bq.dataset_id}.nav_facilities`
                (facility_id, fund_id, fund_name, fund_type, nav_value, nav_valuation_date,
                 facility_amount, drawn_amount, ltv_ratio, initial_ltv, ltv_covenant_threshold,
                 buffer_percentage, ilpa_compliant, status, created_at)
                VALUES (
                    '{facility_id}',
                    '{fund_id}',
                    '{fund_name.replace("'", "''")}',
                    '{fund_type}',
                    {nav_value},
                    CURRENT_DATE(),
                    {facility_amount},
                    {drawn_amount},
                    {ltv_ratio},
                    {initial_ltv},
                    {ltv_covenant},
                    {buffer_pct},
                    FALSE,
                    'ACTIVE',
                    CURRENT_TIMESTAMP()
                )
            """
            
            self.bq.execute_query(query)
            
            return {
                "success": True,
                "facility_id": facility_id,
                "ltv_ratio": round(ltv_ratio, 4),
                "buffer_percentage": round(buffer_pct, 1),
                "message": "NAV facility created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to create NAV facility: {e}")
            return {"success": False, "error": str(e)}
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get portfolio-level NAV facility summary.
        
        Returns:
            Aggregated portfolio metrics
        """
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total_facilities,
                    SUM(facility_amount) as total_facility_amount,
                    SUM(drawn_amount) as total_drawn,
                    SUM(nav_value) as total_nav,
                    AVG(ltv_ratio) as avg_ltv,
                    AVG(buffer_percentage) as avg_buffer,
                    COUNTIF(ltv_ratio >= ltv_covenant_threshold) as facilities_in_breach,
                    COUNTIF(ltv_ratio >= ltv_covenant_threshold * 0.85) as facilities_warning
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.nav_facilities`
                WHERE status = 'ACTIVE'
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": True, "total_facilities": 0, "message": "No NAV facilities found"}
            
            row = results[0]
            total_drawn = row.get("total_drawn", 0) or 0
            total_nav = row.get("total_nav", 0) or 0
            
            return {
                "success": True,
                "total_facilities": row.get("total_facilities", 0),
                "total_facility_amount": row.get("total_facility_amount", 0),
                "total_drawn": total_drawn,
                "total_nav": total_nav,
                "portfolio_ltv": round(total_drawn / total_nav * 100, 2) if total_nav > 0 else 0,
                "avg_ltv_pct": round((row.get("avg_ltv", 0) or 0) * 100, 2),
                "avg_buffer_pct": round(row.get("avg_buffer", 0) or 0, 1),
                "facilities_in_breach": row.get("facilities_in_breach", 0),
                "facilities_warning": row.get("facilities_warning", 0),
                "source": "BigQuery"
            }
            
        except Exception as e:
            logger.error(f"Portfolio summary error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_nav_monitor: Optional[NAVMonitorAgent] = None


def get_nav_monitor() -> NAVMonitorAgent:
    """Get or create NAV Monitor singleton."""
    global _nav_monitor
    if _nav_monitor is None:
        _nav_monitor = NAVMonitorAgent()
    return _nav_monitor


# Convenience functions
def get_nav_facility(facility_id: str) -> Dict[str, Any]:
    """Get NAV facility details."""
    return get_nav_monitor().get_facility(facility_id)


def calculate_nav_ltv(facility_id: str) -> Dict[str, Any]:
    """Calculate LTV for NAV facility."""
    return get_nav_monitor().calculate_ltv(facility_id=facility_id)


def get_nav_buffer_analysis(facility_id: str) -> Dict[str, Any]:
    """Get buffer analysis for NAV facility."""
    return get_nav_monitor().get_buffer_analysis(facility_id)


def create_nav_facility(facility_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create new NAV facility."""
    return get_nav_monitor().create_facility(facility_data)


def get_nav_portfolio_summary() -> Dict[str, Any]:
    """Get NAV portfolio summary."""
    return get_nav_monitor().get_portfolio_summary()
