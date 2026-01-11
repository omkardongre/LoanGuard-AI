"""
TLP Report Agent - Generate TLP-compliant transition loan reports.

Production-level implementation based on LMA TLP Principle 5: Reporting.
Generates standardized reports for transition loans.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import json

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class TLPReportAgent:
    """
    Generate TLP-Compliant Reports for Transition Loans.
    
    Based on LMA TLP Principle 5 (Reporting) - MANDATORY requirements:
    1. List of Transition Projects funded
    2. Amounts allocated to each project
    3. Expected AND achieved impact of each project
    
    Reports are generated per loan and can be exported for regulators.
    """
    
    # Report sections
    REPORT_SECTIONS = [
        "executive_summary",
        "tlp_compliance",
        "project_list",
        "allocation_details",
        "impact_metrics",
        "dnsh_status",
        "carbon_lockin",
        "recommendations",
    ]
    
    def __init__(self):
        """Initialize TLP Report Agent."""
        self.bq = BigQueryClient()
    
    def generate_loan_report(self, loan_id: str) -> Dict[str, Any]:
        """
        Generate full TLP report for a transition loan.
        
        Args:
            loan_id: Loan identifier
            
        Returns:
            Complete TLP report
        """
        try:
            # Get loan data
            loan_data = self._get_transition_loan(loan_id)
            if not loan_data:
                return {"success": False, "error": f"Transition loan {loan_id} not found"}
            
            # Get projects
            projects = self._get_transition_projects(loan_id)
            
            # Get transition plan
            plan = self._get_transition_plan(loan_data)
            
            # Build report sections
            report = {
                "report_id": f"TLP-RPT-{loan_id}-{datetime.now().strftime('%Y%m%d')}",
                "loan_id": loan_id,
                "generation_date": str(date.today()),
                "report_type": "TLP_COMPLIANCE",
                
                "executive_summary": self._generate_executive_summary(loan_data, projects),
                "tlp_compliance": self._generate_compliance_section(loan_data),
                "project_list": self._generate_project_list(projects),
                "allocation_summary": self._generate_allocation_summary(projects),
                "impact_metrics": self._generate_impact_section(projects),
                "dnsh_assessment": self._generate_dnsh_section(loan_data),
                "carbon_lockin_assessment": self._generate_lockin_section(loan_data),
                "recommendations": self._generate_recommendations(loan_data),
                
                "source": "BigQuery",
            }
            
            return {
                "success": True,
                "report": report,
            }
            
        except Exception as e:
            logger.error(f"TLP report generation error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_transition_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get transition loan data."""
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
                WHERE loan_id = '{loan_id}'
            """
            results = self.bq.execute_query(query)
            return results[0] if results else None
        except Exception:
            return None
    
    def _get_transition_projects(self, loan_id: str) -> List[Dict[str, Any]]:
        """Get transition projects for loan."""
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_projects`
                WHERE loan_id = '{loan_id}'
                ORDER BY allocation_date DESC
            """
            return self.bq.execute_query(query) or []
        except Exception:
            return []
    
    def _get_transition_plan(self, loan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get transition plan for borrower."""
        try:
            plan_id = loan_data.get("transition_plan_id")
            if not plan_id:
                return None
            
            query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_plans`
                WHERE plan_id = '{plan_id}'
            """
            results = self.bq.execute_query(query)
            return results[0] if results else None
        except Exception:
            return None
    
    def _generate_executive_summary(
        self, 
        loan_data: Dict[str, Any], 
        projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate executive summary section."""
        total_allocated = sum(p.get("allocated_amount", 0) or 0 for p in projects)
        total_expected_ghg = sum(p.get("expected_ghg_reduction_tco2", 0) or 0 for p in projects)
        total_achieved_ghg = sum(p.get("achieved_ghg_reduction_tco2", 0) or 0 for p in projects)
        
        tlp_score = loan_data.get("tlp_overall_score", 0) or 0
        
        return {
            "tlp_compliance_score": tlp_score,
            "compliance_status": "COMPLIANT" if tlp_score >= 70 else "NON_COMPLIANT",
            "total_projects": len(projects),
            "total_allocated": total_allocated,
            "expected_ghg_reduction_tco2": total_expected_ghg,
            "achieved_ghg_reduction_tco2": total_achieved_ghg,
            "achievement_rate": round(total_achieved_ghg / total_expected_ghg * 100, 1) if total_expected_ghg > 0 else 0,
            "dnsh_status": loan_data.get("dnsh_status", "PENDING"),
            "carbon_lockin_risk": loan_data.get("carbon_lockin_risk", "NOT_ASSESSED"),
        }
    
    def _generate_compliance_section(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate TLP compliance section."""
        return {
            "overall_score": loan_data.get("tlp_overall_score", 0),
            "principle_scores": {
                "entity_strategy": loan_data.get("entity_strategy_score", 0),
                "use_of_proceeds": loan_data.get("use_of_proceeds_score", 0),
                "project_evaluation": loan_data.get("project_evaluation_score", 0),
                "proceeds_management": loan_data.get("proceeds_management_score", 0),
                "reporting": loan_data.get("reporting_score", 0),
            },
            "assessment_date": str(loan_data.get("assessment_date", "")),
        }
    
    def _generate_project_list(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate project list section (LMA Requirement 1)."""
        return [
            {
                "project_id": p.get("project_id"),
                "project_name": p.get("project_name"),
                "category": p.get("project_category"),
                "type": p.get("project_type"),
                "eligibility_status": p.get("eligibility_status"),
                "pathway_aligned": p.get("pathway_aligned"),
            }
            for p in projects
        ]
    
    def _generate_allocation_summary(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate allocation summary (LMA Requirement 2)."""
        total = sum(p.get("allocated_amount", 0) or 0 for p in projects)
        
        by_category = {}
        for p in projects:
            cat = p.get("project_category", "Unknown")
            by_category[cat] = by_category.get(cat, 0) + (p.get("allocated_amount", 0) or 0)
        
        by_type = {}
        for p in projects:
            t = p.get("project_type", "Unknown")
            by_type[t] = by_type.get(t, 0) + (p.get("allocated_amount", 0) or 0)
        
        return {
            "total_allocated": total,
            "by_category": by_category,
            "by_type": by_type,
            "project_allocations": [
                {
                    "project_id": p.get("project_id"),
                    "project_name": p.get("project_name"),
                    "allocated_amount": p.get("allocated_amount", 0),
                    "allocation_date": str(p.get("allocation_date", "")),
                }
                for p in projects
            ],
        }
    
    def _generate_impact_section(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate impact metrics section (LMA Requirement 3)."""
        return {
            "summary": {
                "total_expected_ghg_reduction": sum(p.get("expected_ghg_reduction_tco2", 0) or 0 for p in projects),
                "total_achieved_ghg_reduction": sum(p.get("achieved_ghg_reduction_tco2", 0) or 0 for p in projects),
                "verified_count": sum(1 for p in projects if p.get("impact_verified")),
            },
            "by_project": [
                {
                    "project_id": p.get("project_id"),
                    "project_name": p.get("project_name"),
                    "expected_ghg_reduction_tco2": p.get("expected_ghg_reduction_tco2", 0),
                    "achieved_ghg_reduction_tco2": p.get("achieved_ghg_reduction_tco2", 0),
                    "impact_verified": p.get("impact_verified", False),
                    "achievement_rate": round(
                        (p.get("achieved_ghg_reduction_tco2", 0) or 0) / 
                        (p.get("expected_ghg_reduction_tco2", 0) or 1) * 100, 1
                    ),
                }
                for p in projects
            ],
        }
    
    def _generate_dnsh_section(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate DNSH assessment section."""
        return {
            "overall_status": loan_data.get("dnsh_status", "PENDING"),
            "by_objective": {
                "climate_mitigation": loan_data.get("dnsh_climate_mitigation", "PENDING"),
                "climate_adaptation": loan_data.get("dnsh_climate_adaptation", "PENDING"),
                "water": loan_data.get("dnsh_water", "PENDING"),
                "circular_economy": loan_data.get("dnsh_circular_economy", "PENDING"),
                "pollution": loan_data.get("dnsh_pollution", "PENDING"),
                "biodiversity": loan_data.get("dnsh_biodiversity", "PENDING"),
            },
        }
    
    def _generate_lockin_section(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate carbon lock-in assessment section."""
        return {
            "risk_level": loan_data.get("carbon_lockin_risk", "NOT_ASSESSED"),
            "risk_score": loan_data.get("carbon_lockin_score", 0),
            "project_lifetime_years": loan_data.get("project_lifetime_years"),
            "emissions_trajectory": loan_data.get("emissions_trajectory"),
            "displaceability": loan_data.get("displaceability"),
            "reversibility": loan_data.get("reversibility"),
            "best_available_tech": loan_data.get("best_available_tech"),
        }
    
    def _generate_recommendations(self, loan_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on assessment."""
        recommendations = []
        
        tlp_score = loan_data.get("tlp_overall_score", 0) or 0
        if tlp_score < 70:
            recommendations.append("Improve TLP compliance score to reach 70% threshold")
        
        dnsh = loan_data.get("dnsh_status", "PENDING")
        if dnsh == "FAIL":
            recommendations.append("Address DNSH failures before proceeding")
        elif dnsh == "PENDING":
            recommendations.append("Complete DNSH assessment for all objectives")
        
        lockin = loan_data.get("carbon_lockin_risk", "")
        if lockin in ["HIGH", "VERY_HIGH"]:
            recommendations.append("Develop carbon lock-in mitigation strategy")
        
        if not recommendations:
            recommendations.append("Continue monitoring and reporting as required")
        
        return recommendations
    
    def get_portfolio_report(self) -> Dict[str, Any]:
        """Generate portfolio-level TLP report."""
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total_loans,
                    AVG(tlp_overall_score) as avg_score,
                    COUNTIF(tlp_overall_score >= 70) as compliant_count,
                    COUNTIF(dnsh_status = 'PASS') as dnsh_pass,
                    COUNTIF(carbon_lockin_risk = 'LOW') as low_lockin
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
            """
            
            loan_results = self.bq.execute_query(query)
            
            project_query = f"""
                SELECT 
                    COUNT(*) as total_projects,
                    SUM(allocated_amount) as total_allocated,
                    SUM(expected_ghg_reduction_tco2) as total_expected_ghg,
                    SUM(achieved_ghg_reduction_tco2) as total_achieved_ghg
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_projects`
            """
            
            project_results = self.bq.execute_query(project_query)
            
            loan_row = loan_results[0] if loan_results else {}
            project_row = project_results[0] if project_results else {}
            
            return {
                "success": True,
                "report_date": str(date.today()),
                "loan_summary": {
                    "total_loans": loan_row.get("total_loans", 0),
                    "avg_tlp_score": round(loan_row.get("avg_score", 0) or 0, 1),
                    "compliant_count": loan_row.get("compliant_count", 0),
                    "dnsh_pass_count": loan_row.get("dnsh_pass", 0),
                    "low_lockin_count": loan_row.get("low_lockin", 0),
                },
                "project_summary": {
                    "total_projects": project_row.get("total_projects", 0),
                    "total_allocated": project_row.get("total_allocated", 0),
                    "total_expected_ghg_reduction_tco2": project_row.get("total_expected_ghg", 0),
                    "total_achieved_ghg_reduction_tco2": project_row.get("total_achieved_ghg", 0),
                },
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Portfolio report error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_tlp_report: Optional[TLPReportAgent] = None


def get_tlp_report_agent() -> TLPReportAgent:
    """Get or create TLP Report Agent singleton."""
    global _tlp_report
    if _tlp_report is None:
        _tlp_report = TLPReportAgent()
    return _tlp_report


# Convenience functions
def generate_tlp_report(loan_id: str) -> Dict[str, Any]:
    """Generate TLP report for a loan."""
    return get_tlp_report_agent().generate_loan_report(loan_id)


def get_tlp_portfolio_report() -> Dict[str, Any]:
    """Get portfolio TLP report."""
    return get_tlp_report_agent().get_portfolio_report()
