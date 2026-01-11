"""
DNSH Screening Agent - Do No Significant Harm screening for transition projects.

Production-level implementation based on EU Taxonomy DNSH principle.
Screens 6 environmental objectives for compliance.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class DNSHScreeningAgent:
    """
    Do No Significant Harm (DNSH) Screening Agent.
    
    Based on EU Taxonomy 6 Environmental Objectives:
    1. Climate change mitigation
    2. Climate change adaptation
    3. Sustainable use of water and marine resources
    4. Transition to a circular economy
    5. Pollution prevention and control
    6. Protection of biodiversity and ecosystems
    
    Also includes social safeguards (labor rights, community health).
    """
    
    # DNSH Objectives (EU Taxonomy)
    DNSH_OBJECTIVES = [
        "climate_mitigation",
        "climate_adaptation",
        "water",
        "circular_economy",
        "pollution",
        "biodiversity",
    ]
    
    # Screening criteria per objective
    SCREENING_CRITERIA = {
        "climate_mitigation": [
            "Does not increase GHG emissions",
            "Does not lock-in fossil fuel assets",
            "Supports Paris Agreement alignment",
        ],
        "climate_adaptation": [
            "Does not increase vulnerability to climate risks",
            "Has adaptation measures in place",
            "Does not harm other locations' adaptation",
        ],
        "water": [
            "Does not degrade water quality",
            "Does not deplete water resources",
            "Complies with water permits",
        ],
        "circular_economy": [
            "Does not increase waste generation",
            "Supports material efficiency",
            "Has end-of-life plan",
        ],
        "pollution": [
            "Does not increase air pollution",
            "Does not increase soil contamination",
            "Does not increase noise/vibration",
        ],
        "biodiversity": [
            "Does not harm protected areas",
            "Does not harm endangered species",
            "Has biodiversity impact assessment",
        ],
    }
    
    def __init__(self):
        """Initialize DNSH Screening Agent."""
        self.bq = BigQueryClient()
    
    def screen_project(
        self,
        loan_id: str = None,
        project_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Screen a project/loan for DNSH compliance.
        
        Args:
            loan_id: Loan identifier
            project_data: Direct project data for screening
            
        Returns:
            DNSH screening results
        """
        try:
            if loan_id and not project_data:
                project_data = self._get_project_data(loan_id)
            
            if not project_data:
                # If no data, return pending status
                return {
                    "success": True,
                    "loan_id": loan_id,
                    "dnsh_status": "PENDING",
                    "message": "No project data found - manual review required",
                    "source": "BigQuery",
                }
            
            # Screen each objective
            objective_results = {}
            issues_found = []
            
            for objective in self.DNSH_OBJECTIVES:
                result = self._screen_objective(objective, project_data)
                objective_results[objective] = result["status"]
                if result["issues"]:
                    issues_found.extend(result["issues"])
            
            # Determine overall status
            statuses = list(objective_results.values())
            if "FAIL" in statuses:
                overall_status = "FAIL"
            elif "PENDING" in statuses:
                overall_status = "PARTIAL"
            else:
                overall_status = "PASS"
            
            # Calculate compliance score
            pass_count = statuses.count("PASS")
            na_count = statuses.count("N/A")
            applicable_count = len(statuses) - na_count
            compliance_score = (pass_count / applicable_count * 100) if applicable_count > 0 else 0
            
            return {
                "success": True,
                "loan_id": loan_id,
                "dnsh_status": overall_status,
                "compliance_score": round(compliance_score, 1),
                "objective_results": objective_results,
                "issues_found": issues_found,
                "recommendations": self._generate_recommendations(issues_found),
                "screening_date": str(date.today()),
                "source": "BigQuery" if loan_id else "Calculated",
            }
            
        except Exception as e:
            logger.error(f"DNSH screening error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_project_data(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get project data from transition_loans table."""
        try:
            query = f"""
                SELECT 
                    dnsh_climate_mitigation,
                    dnsh_climate_adaptation,
                    dnsh_water,
                    dnsh_circular_economy,
                    dnsh_pollution,
                    dnsh_biodiversity,
                    emissions_trajectory,
                    carbon_lockin_risk,
                    taxonomy_activity_code
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
                WHERE loan_id = '{loan_id}'
            """
            results = self.bq.execute_query(query)
            return results[0] if results else None
        except Exception:
            return None
    
    def _screen_objective(
        self, 
        objective: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Screen a single DNSH objective."""
        # Map to database field
        field_name = f"dnsh_{objective}"
        
        # Check if we have existing assessment
        existing_status = data.get(field_name)
        
        if existing_status:
            return {
                "status": existing_status,
                "issues": [] if existing_status in ["PASS", "N/A"] else [f"{objective}: needs attention"],
            }
        
        # Infer from other data
        issues = []
        
        if objective == "climate_mitigation":
            # Check emissions trajectory and carbon lock-in
            trajectory = data.get("emissions_trajectory", "").upper()
            lockin = data.get("carbon_lockin_risk", "").upper()
            
            if trajectory == "INCREASING":
                issues.append("Emissions trajectory is increasing - may harm mitigation")
            if lockin in ["HIGH", "VERY_HIGH"]:
                issues.append("High carbon lock-in risk - may undermine mitigation")
            
            status = "FAIL" if issues else "PENDING"
            
        elif objective == "climate_adaptation":
            # Would need climate risk data
            status = "PENDING"
            
        else:
            # Default to pending for objectives we can't assess
            status = "PENDING"
        
        return {"status": status, "issues": issues}
    
    def _generate_recommendations(self, issues: List[str]) -> List[str]:
        """Generate recommendations based on issues."""
        recommendations = []
        
        if any("mitigation" in i.lower() for i in issues):
            recommendations.append("Develop emissions reduction plan")
            recommendations.append("Consider carbon offset mechanisms")
        
        if any("lock-in" in i.lower() for i in issues):
            recommendations.append("Conduct technology alternatives assessment")
            recommendations.append("Plan for asset retirement or retrofit")
        
        if any("biodiversity" in i.lower() for i in issues):
            recommendations.append("Complete Environmental Impact Assessment")
            recommendations.append("Implement biodiversity offsetting")
        
        if not recommendations:
            recommendations.append("Complete full DNSH assessment with third-party verification")
        
        return recommendations
    
    def save_assessment(self, loan_id: str, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Save DNSH assessment to BigQuery."""
        try:
            obj_results = assessment.get("objective_results", {})
            
            query = f"""
                UPDATE `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
                SET 
                    dnsh_status = '{assessment.get("dnsh_status", "PENDING")}',
                    dnsh_climate_mitigation = '{obj_results.get("climate_mitigation", "PENDING")}',
                    dnsh_climate_adaptation = '{obj_results.get("climate_adaptation", "PENDING")}',
                    dnsh_water = '{obj_results.get("water", "PENDING")}',
                    dnsh_circular_economy = '{obj_results.get("circular_economy", "PENDING")}',
                    dnsh_pollution = '{obj_results.get("pollution", "PENDING")}',
                    dnsh_biodiversity = '{obj_results.get("biodiversity", "PENDING")}',
                    updated_at = CURRENT_TIMESTAMP()
                WHERE loan_id = '{loan_id}'
            """
            
            self.bq.execute_query(query)
            
            return {"success": True, "message": "DNSH assessment saved"}
            
        except Exception as e:
            logger.error(f"Failed to save DNSH assessment: {e}")
            return {"success": False, "error": str(e)}
    
    def get_portfolio_dnsh_summary(self) -> Dict[str, Any]:
        """Get portfolio-level DNSH summary."""
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    COUNTIF(dnsh_status = 'PASS') as pass_count,
                    COUNTIF(dnsh_status = 'FAIL') as fail_count,
                    COUNTIF(dnsh_status = 'PARTIAL') as partial_count,
                    COUNTIF(dnsh_status = 'PENDING') as pending_count,
                    COUNTIF(dnsh_climate_mitigation = 'PASS') as mitigation_pass,
                    COUNTIF(dnsh_biodiversity = 'PASS') as biodiversity_pass
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": True, "total": 0, "source": "BigQuery"}
            
            row = results[0]
            total = row.get("total", 0) or 0
            
            return {
                "success": True,
                "total_screened": total,
                "by_status": {
                    "pass": row.get("pass_count", 0),
                    "fail": row.get("fail_count", 0),
                    "partial": row.get("partial_count", 0),
                    "pending": row.get("pending_count", 0),
                },
                "compliance_rate": round(row.get("pass_count", 0) / total * 100, 1) if total > 0 else 0,
                "by_objective": {
                    "climate_mitigation_pass": row.get("mitigation_pass", 0),
                    "biodiversity_pass": row.get("biodiversity_pass", 0),
                },
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Portfolio DNSH summary error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_dnsh_screening: Optional[DNSHScreeningAgent] = None


def get_dnsh_screening_agent() -> DNSHScreeningAgent:
    """Get or create DNSH Screening Agent singleton."""
    global _dnsh_screening
    if _dnsh_screening is None:
        _dnsh_screening = DNSHScreeningAgent()
    return _dnsh_screening


# Convenience functions
def screen_dnsh(loan_id: str = None, project_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Screen project for DNSH compliance."""
    return get_dnsh_screening_agent().screen_project(loan_id, project_data)


def get_portfolio_dnsh_summary() -> Dict[str, Any]:
    """Get portfolio DNSH summary."""
    return get_dnsh_screening_agent().get_portfolio_dnsh_summary()
