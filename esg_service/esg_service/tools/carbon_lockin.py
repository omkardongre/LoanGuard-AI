"""
Carbon Lock-in Risk Agent - Assess carbon lock-in risk for transition projects.

Production-level implementation based on LMA TLP Section 3.2.1 iv (October 2025).
Assesses 8 criteria for carbon lock-in risk.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class CarbonLockinAgent:
    """
    Assess Carbon Lock-in Risk for transition projects.
    
    Based on LMA Definition (Section 3.2.1 iv):
    "Carbon lock-in occurs when fossil fuel infrastructure or assets continue 
    to be used, despite the possibility of substituting them with low-emission 
    alternatives"
    
    8 Assessment Criteria:
    1. Project lifetime
    2. Utilization rates
    3. Emissions trajectory
    4. Cumulative emissions
    5. Displaceability
    6. Reversibility
    7. Best-available technology
    8. End-use emissions
    """
    
    # Risk thresholds
    RISK_THRESHOLDS = {
        "project_lifetime": {"low": 10, "medium": 20, "high": 30},  # years
        "utilization_rate": {"low": 0.5, "medium": 0.7, "high": 0.9},
        "cumulative_emissions": {"low": 10000, "medium": 50000, "high": 100000},  # tCO2
    }
    
    # Criteria weights (100 total)
    CRITERIA_WEIGHTS = {
        "project_lifetime": 15,
        "utilization_rate": 10,
        "emissions_trajectory": 20,
        "cumulative_emissions": 15,
        "displaceability": 15,
        "reversibility": 10,
        "best_available_tech": 10,
        "end_use_emissions": 5,
    }
    
    def __init__(self):
        """Initialize Carbon Lock-in Agent."""
        self.bq = BigQueryClient()
    
    def assess_carbon_lockin(
        self,
        loan_id: str = None,
        asset_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Assess carbon lock-in risk for a loan or asset.
        
        Args:
            loan_id: Loan identifier (fetches from DB)
            asset_data: Direct asset data for assessment
            
        Returns:
            Carbon lock-in risk assessment
        """
        try:
            if loan_id and not asset_data:
                asset_data = self._get_asset_data(loan_id)
            
            if not asset_data:
                return {"success": False, "error": "No asset data provided or found"}
            
            # Assess each criterion
            criteria_scores = {
                "project_lifetime": self._score_project_lifetime(asset_data),
                "utilization_rate": self._score_utilization(asset_data),
                "emissions_trajectory": self._score_trajectory(asset_data),
                "cumulative_emissions": self._score_cumulative(asset_data),
                "displaceability": self._score_displaceability(asset_data),
                "reversibility": self._score_reversibility(asset_data),
                "best_available_tech": self._score_best_tech(asset_data),
                "end_use_emissions": self._score_end_use(asset_data),
            }
            
            # Calculate weighted risk score (0-100, higher = more risk)
            total_score = sum(
                score * self.CRITERIA_WEIGHTS[criterion]
                for criterion, score in criteria_scores.items()
            ) / 100
            
            # Determine risk level
            if total_score >= 70:
                risk_level = "VERY_HIGH"
            elif total_score >= 50:
                risk_level = "HIGH"
            elif total_score >= 30:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            # Generate recommendations
            recommendations = self._generate_recommendations(criteria_scores, risk_level)
            
            return {
                "success": True,
                "loan_id": loan_id,
                "carbon_lockin_score": round(total_score, 1),
                "risk_level": risk_level,
                "criteria_scores": {k: round(v, 1) for k, v in criteria_scores.items()},
                "highest_risk_criteria": max(criteria_scores, key=criteria_scores.get),
                "recommendations": recommendations,
                "assessment_date": str(date.today()),
                "source": "BigQuery" if loan_id else "Calculated",
            }
            
        except Exception as e:
            logger.error(f"Carbon lock-in assessment error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_asset_data(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get asset data from transition_loans table."""
        try:
            query = f"""
                SELECT 
                    project_lifetime_years,
                    utilization_rate,
                    emissions_trajectory,
                    cumulative_emissions_tco2,
                    displaceability,
                    reversibility,
                    best_available_tech
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
                WHERE loan_id = '{loan_id}'
            """
            results = self.bq.execute_query(query)
            return results[0] if results else None
        except Exception:
            return None
    
    def _score_project_lifetime(self, data: Dict[str, Any]) -> float:
        """Score based on project lifetime (longer = higher risk)."""
        years = data.get("project_lifetime_years", 0) or 0
        
        if years <= self.RISK_THRESHOLDS["project_lifetime"]["low"]:
            return 20
        elif years <= self.RISK_THRESHOLDS["project_lifetime"]["medium"]:
            return 50
        elif years <= self.RISK_THRESHOLDS["project_lifetime"]["high"]:
            return 75
        else:
            return 100
    
    def _score_utilization(self, data: Dict[str, Any]) -> float:
        """Score based on utilization rate (higher = more locked in)."""
        rate = data.get("utilization_rate", 0) or 0
        
        if rate <= self.RISK_THRESHOLDS["utilization_rate"]["low"]:
            return 20
        elif rate <= self.RISK_THRESHOLDS["utilization_rate"]["medium"]:
            return 50
        elif rate <= self.RISK_THRESHOLDS["utilization_rate"]["high"]:
            return 75
        else:
            return 100
    
    def _score_trajectory(self, data: Dict[str, Any]) -> float:
        """Score based on emissions trajectory."""
        trajectory = (data.get("emissions_trajectory") or "STABLE").upper()
        
        if trajectory == "DECREASING":
            return 10
        elif trajectory == "STABLE":
            return 50
        elif trajectory == "INCREASING":
            return 100
        else:
            return 50  # Unknown = medium risk
    
    def _score_cumulative(self, data: Dict[str, Any]) -> float:
        """Score based on cumulative lifetime emissions."""
        emissions = data.get("cumulative_emissions_tco2", 0) or 0
        
        if emissions <= self.RISK_THRESHOLDS["cumulative_emissions"]["low"]:
            return 20
        elif emissions <= self.RISK_THRESHOLDS["cumulative_emissions"]["medium"]:
            return 50
        elif emissions <= self.RISK_THRESHOLDS["cumulative_emissions"]["high"]:
            return 75
        else:
            return 100
    
    def _score_displaceability(self, data: Dict[str, Any]) -> float:
        """Score based on displaceability (harder = higher risk)."""
        displaceable = (data.get("displaceability") or "NO").upper()
        
        if displaceable == "YES":
            return 10
        elif displaceable == "PARTIAL":
            return 50
        elif displaceable == "NO":
            return 100
        else:
            return 75  # Unknown = high-ish risk
    
    def _score_reversibility(self, data: Dict[str, Any]) -> float:
        """Score based on reversibility/repurposing potential."""
        reversible = (data.get("reversibility") or "NO").upper()
        
        if reversible == "YES":
            return 10
        elif reversible == "PARTIAL":
            return 50
        elif reversible == "NO":
            return 100
        else:
            return 75
    
    def _score_best_tech(self, data: Dict[str, Any]) -> float:
        """Score based on best-available technology usage."""
        best_tech = data.get("best_available_tech", False)
        
        return 10 if best_tech else 80
    
    def _score_end_use(self, data: Dict[str, Any]) -> float:
        """Score based on end-use emissions (from output)."""
        # This would typically require more data about what the asset produces
        # For now, use a moderate default
        return 50
    
    def _generate_recommendations(
        self, 
        scores: Dict[str, float], 
        risk_level: str
    ) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []
        
        if risk_level in ["HIGH", "VERY_HIGH"]:
            recommendations.append("Consider phased asset retirement plan")
            recommendations.append("Implement emissions reduction targets")
        
        if scores.get("project_lifetime", 0) >= 75:
            recommendations.append("Shorten asset lifetime or plan early phase-out")
        
        if scores.get("emissions_trajectory", 0) >= 75:
            recommendations.append("Set declining emissions trajectory targets")
        
        if scores.get("displaceability", 0) >= 75:
            recommendations.append("Evaluate retrofit options for low-carbon alternatives")
        
        if scores.get("best_available_tech", 0) >= 75:
            recommendations.append("Upgrade to best-available technology")
        
        if not recommendations:
            recommendations.append("Continue monitoring emissions trajectory")
        
        return recommendations
    
    def save_assessment(self, loan_id: str, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Save carbon lock-in assessment to BigQuery."""
        try:
            scores = assessment.get("criteria_scores", {})
            
            query = f"""
                UPDATE `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
                SET 
                    carbon_lockin_risk = '{assessment.get("risk_level", "MEDIUM")}',
                    carbon_lockin_score = {assessment.get("carbon_lockin_score", 0)},
                    updated_at = CURRENT_TIMESTAMP()
                WHERE loan_id = '{loan_id}'
            """
            
            self.bq.execute_query(query)
            
            return {"success": True, "message": "Carbon lock-in assessment saved"}
            
        except Exception as e:
            logger.error(f"Failed to save carbon lock-in assessment: {e}")
            return {"success": False, "error": str(e)}
    
    def get_portfolio_lockin_summary(self) -> Dict[str, Any]:
        """Get portfolio-level carbon lock-in summary."""
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    AVG(carbon_lockin_score) as avg_score,
                    COUNTIF(carbon_lockin_risk = 'LOW') as low_risk,
                    COUNTIF(carbon_lockin_risk = 'MEDIUM') as medium_risk,
                    COUNTIF(carbon_lockin_risk = 'HIGH') as high_risk,
                    COUNTIF(carbon_lockin_risk = 'VERY_HIGH') as very_high_risk,
                    SUM(cumulative_emissions_tco2) as total_emissions
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
                WHERE carbon_lockin_risk IS NOT NULL
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": True, "total": 0, "source": "BigQuery"}
            
            row = results[0]
            
            return {
                "success": True,
                "total_assessed": row.get("total", 0),
                "avg_lockin_score": round(row.get("avg_score", 0) or 0, 1),
                "by_risk_level": {
                    "low": row.get("low_risk", 0),
                    "medium": row.get("medium_risk", 0),
                    "high": row.get("high_risk", 0),
                    "very_high": row.get("very_high_risk", 0),
                },
                "total_emissions_tco2": row.get("total_emissions", 0),
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Portfolio lock-in summary error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_carbon_lockin: Optional[CarbonLockinAgent] = None


def get_carbon_lockin_agent() -> CarbonLockinAgent:
    """Get or create Carbon Lock-in Agent singleton."""
    global _carbon_lockin
    if _carbon_lockin is None:
        _carbon_lockin = CarbonLockinAgent()
    return _carbon_lockin


# Convenience functions
def assess_carbon_lockin(loan_id: str = None, asset_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Assess carbon lock-in risk."""
    return get_carbon_lockin_agent().assess_carbon_lockin(loan_id, asset_data)


def get_portfolio_lockin_summary() -> Dict[str, Any]:
    """Get portfolio carbon lock-in summary."""
    return get_carbon_lockin_agent().get_portfolio_lockin_summary()
