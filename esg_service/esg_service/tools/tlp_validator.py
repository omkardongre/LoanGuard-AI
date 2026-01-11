"""
TLP Validator Agent - Validate Transition Loan Principles compliance.

Production-level implementation based on LMA Guide to Transition Loans (October 2025).
Implements the 5 core TLP principles with scoring.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, date

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


@dataclass
class TLPScore:
    """TLP compliance score breakdown."""
    overall_score: float
    entity_strategy: float
    use_of_proceeds: float
    project_evaluation: float
    proceeds_management: float
    reporting: float
    is_compliant: bool


class TLPValidatorAgent:
    """
    Validate Transition Loan Principles compliance.
    
    Based on LMA/APLMA/LSTA Guide to Transition Loans (October 2025):
    - Principle 1: Entity-Level Transition Strategy
    - Principle 2: Use of Proceeds
    - Principle 3: Process for Project Evaluation and Selection
    - Principle 4: Management of Proceeds
    - Principle 5: Reporting
    
    Reference: research2_transition_loans.md
    """
    
    # Principle weights (100 total)
    PRINCIPLE_WEIGHTS = {
        "entity_strategy": 25,       # Has transition plan/indicators
        "use_of_proceeds": 20,       # Proceeds for transition projects
        "project_evaluation": 25,    # Project eligibility + DNSH
        "proceeds_management": 10,   # Tracking/audit trail
        "reporting": 20,             # TLP-compliant reporting
    }
    
    # Compliance threshold
    COMPLIANCE_THRESHOLD = 70  # 70% to be considered TLP compliant
    
    def __init__(self):
        """Initialize TLP Validator Agent."""
        self.bq = BigQueryClient()
    
    def validate_transition_loan(self, loan_id: str) -> Dict[str, Any]:
        """
        Full TLP validation for a transition loan.
        
        Args:
            loan_id: Loan identifier
            
        Returns:
            TLP compliance assessment
        """
        try:
            # Check existing assessment
            existing = self._get_existing_assessment(loan_id)
            if existing:
                return existing
            
            # Get loan and transition plan data
            plan_data = self._get_transition_plan(loan_id)
            indicators = self._get_transition_indicators(loan_id)
            projects = self._get_transition_projects(loan_id)
            
            # Score each principle
            p1_score = self._score_entity_strategy(plan_data, indicators)
            p2_score = self._score_use_of_proceeds(projects)
            p3_score = self._score_project_evaluation(loan_id, projects)
            p4_score = self._score_proceeds_management(projects)
            p5_score = self._score_reporting(loan_id)
            
            # Calculate weighted overall score
            overall = (
                p1_score * self.PRINCIPLE_WEIGHTS["entity_strategy"] +
                p2_score * self.PRINCIPLE_WEIGHTS["use_of_proceeds"] +
                p3_score * self.PRINCIPLE_WEIGHTS["project_evaluation"] +
                p4_score * self.PRINCIPLE_WEIGHTS["proceeds_management"] +
                p5_score * self.PRINCIPLE_WEIGHTS["reporting"]
            ) / 100
            
            is_compliant = overall >= self.COMPLIANCE_THRESHOLD
            
            return {
                "success": True,
                "loan_id": loan_id,
                "tlp_overall_score": round(overall, 1),
                "is_compliant": is_compliant,
                "compliance_status": "COMPLIANT" if is_compliant else "NON_COMPLIANT",
                "principle_scores": {
                    "entity_strategy": round(p1_score, 1),
                    "use_of_proceeds": round(p2_score, 1),
                    "project_evaluation": round(p3_score, 1),
                    "proceeds_management": round(p4_score, 1),
                    "reporting": round(p5_score, 1),
                },
                "has_transition_plan": plan_data.get("has_published_plan", False) if plan_data else False,
                "project_count": len(projects) if projects else 0,
                "assessment_date": str(date.today()),
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"TLP validation error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_existing_assessment(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Check for existing TLP assessment."""
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
                WHERE loan_id = '{loan_id}'
                ORDER BY created_at DESC
                LIMIT 1
            """
            results = self.bq.execute_query(query)
            
            if results:
                row = results[0]
                return {
                    "success": True,
                    "loan_id": loan_id,
                    "tlp_overall_score": row.get("tlp_overall_score", 0),
                    "is_compliant": row.get("tlp_overall_score", 0) >= self.COMPLIANCE_THRESHOLD,
                    "principle_scores": {
                        "entity_strategy": row.get("entity_strategy_score", 0),
                        "use_of_proceeds": row.get("use_of_proceeds_score", 0),
                        "project_evaluation": row.get("project_evaluation_score", 0),
                        "proceeds_management": row.get("proceeds_management_score", 0),
                        "reporting": row.get("reporting_score", 0),
                    },
                    "carbon_lockin_risk": row.get("carbon_lockin_risk"),
                    "dnsh_status": row.get("dnsh_status"),
                    "assessment_date": str(row.get("assessment_date")),
                    "source": "BigQuery",
                }
            return None
        except Exception:
            return None
    
    def _get_transition_plan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get transition plan for loan's borrower."""
        try:
            # First get borrower from loan
            loan_query = f"""
                SELECT borrower_id
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.loans`
                WHERE loan_id = '{loan_id}'
            """
            loan_results = self.bq.execute_query(loan_query)
            
            if not loan_results:
                return None
            
            borrower_id = loan_results[0].get("borrower_id")
            
            # Get transition plan
            plan_query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_plans`
                WHERE borrower_id = '{borrower_id}'
                ORDER BY created_at DESC
                LIMIT 1
            """
            plan_results = self.bq.execute_query(plan_query)
            
            return plan_results[0] if plan_results else None
        except Exception:
            return None
    
    def _get_transition_indicators(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get transition indicators for loan."""
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_indicators`
                WHERE loan_id = '{loan_id}'
                ORDER BY created_at DESC
                LIMIT 1
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
            """
            return self.bq.execute_query(query) or []
        except Exception:
            return []
    
    def _score_entity_strategy(
        self, 
        plan_data: Optional[Dict[str, Any]], 
        indicators: Optional[Dict[str, Any]]
    ) -> float:
        """
        Score Principle 1: Entity-Level Transition Strategy.
        
        Either has published transition plan OR meets indicator thresholds.
        """
        score = 0
        
        if plan_data:
            # Has transition plan
            if plan_data.get("has_published_plan"):
                score += 40
            if plan_data.get("sbti_aligned"):
                score += 20
            if plan_data.get("third_party_verified"):
                score += 15
            if plan_data.get("has_board_oversight"):
                score += 10
            if plan_data.get("has_climate_committee"):
                score += 10
            if plan_data.get("executive_incentives_linked"):
                score += 5
        elif indicators:
            # Use indicator-based assessment (LMA Section 2.2)
            indicator_score = indicators.get("indicator_score", 0)
            score = indicator_score  # Already 0-100
        
        return min(score, 100)
    
    def _score_use_of_proceeds(self, projects: List[Dict[str, Any]]) -> float:
        """
        Score Principle 2: Use of Proceeds.
        
        All proceeds must go to Transition Projects.
        """
        if not projects:
            return 0
        
        eligible_count = sum(1 for p in projects if p.get("eligibility_status") == "ELIGIBLE")
        eligible_pct = (eligible_count / len(projects)) * 100 if projects else 0
        
        return eligible_pct
    
    def _score_project_evaluation(
        self, 
        loan_id: str, 
        projects: List[Dict[str, Any]]
    ) -> float:
        """
        Score Principle 3: Project Evaluation and Selection.
        
        Checks: pathway alignment, no low-carbon alternatives, DNSH, carbon lock-in.
        """
        score = 0
        
        if not projects:
            return 0
        
        # Pathway alignment (25 points)
        pathway_aligned = sum(1 for p in projects if p.get("pathway_aligned") in ["IEA", "IPCC", "SBTi"])
        pathway_pct = (pathway_aligned / len(projects)) * 25
        score += pathway_pct
        
        # No low-carbon alternatives (25 points)
        no_alt = sum(1 for p in projects if not p.get("low_carbon_alternative_exists", True))
        no_alt_pct = (no_alt / len(projects)) * 25
        score += no_alt_pct
        
        # DNSH status (25 points) - from transition_loans table
        try:
            query = f"""
                SELECT dnsh_status
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
                WHERE loan_id = '{loan_id}'
            """
            results = self.bq.execute_query(query)
            if results and results[0].get("dnsh_status") == "PASS":
                score += 25
            elif results and results[0].get("dnsh_status") == "PARTIAL":
                score += 12.5
        except Exception:
            pass
        
        # Carbon lock-in (25 points)
        try:
            query = f"""
                SELECT carbon_lockin_risk
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
                WHERE loan_id = '{loan_id}'
            """
            results = self.bq.execute_query(query)
            if results:
                risk = results[0].get("carbon_lockin_risk", "HIGH")
                if risk == "LOW":
                    score += 25
                elif risk == "MEDIUM":
                    score += 15
                elif risk == "HIGH":
                    score += 5
        except Exception:
            pass
        
        return min(score, 100)
    
    def _score_proceeds_management(self, projects: List[Dict[str, Any]]) -> float:
        """
        Score Principle 4: Management of Proceeds.
        
        Checks: allocation tracking, audit trail.
        """
        if not projects:
            return 0
        
        # Has allocation dates and amounts
        tracked = sum(1 for p in projects if p.get("allocated_amount") and p.get("allocation_date"))
        tracked_pct = (tracked / len(projects)) * 100 if projects else 0
        
        return tracked_pct
    
    def _score_reporting(self, loan_id: str) -> float:
        """
        Score Principle 5: Reporting.
        
        Checks: project list, amounts, impact tracking.
        """
        try:
            # Check if impact metrics are being tracked
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    COUNTIF(expected_ghg_reduction_tco2 IS NOT NULL) as has_expected,
                    COUNTIF(achieved_ghg_reduction_tco2 IS NOT NULL) as has_achieved,
                    COUNTIF(impact_verified = TRUE) as verified
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_projects`
                WHERE loan_id = '{loan_id}'
            """
            results = self.bq.execute_query(query)
            
            if not results or results[0].get("total", 0) == 0:
                return 0
            
            row = results[0]
            total = row.get("total", 1)
            
            # Score components
            expected_pct = (row.get("has_expected", 0) / total) * 40  # Has expected impact
            achieved_pct = (row.get("has_achieved", 0) / total) * 40  # Has achieved impact
            verified_pct = (row.get("verified", 0) / total) * 20     # Impact verified
            
            return expected_pct + achieved_pct + verified_pct
            
        except Exception:
            return 0
    
    def save_assessment(self, loan_id: str, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Save TLP assessment to BigQuery."""
        try:
            scores = assessment.get("principle_scores", {})
            
            query = f"""
                INSERT INTO `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
                (loan_id, tlp_overall_score, entity_strategy_score, use_of_proceeds_score,
                 project_evaluation_score, proceeds_management_score, reporting_score,
                 assessment_date, assessor_agent, created_at)
                VALUES (
                    '{loan_id}',
                    {assessment.get('tlp_overall_score', 0)},
                    {scores.get('entity_strategy', 0)},
                    {scores.get('use_of_proceeds', 0)},
                    {scores.get('project_evaluation', 0)},
                    {scores.get('proceeds_management', 0)},
                    {scores.get('reporting', 0)},
                    CURRENT_DATE(),
                    'TLPValidatorAgent',
                    CURRENT_TIMESTAMP()
                )
            """
            
            self.bq.execute_query(query)
            
            return {"success": True, "message": "TLP assessment saved"}
            
        except Exception as e:
            logger.error(f"Failed to save TLP assessment: {e}")
            return {"success": False, "error": str(e)}
    
    def get_tlp_summary(self) -> Dict[str, Any]:
        """Get portfolio-level TLP summary."""
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total_loans,
                    AVG(tlp_overall_score) as avg_score,
                    COUNTIF(tlp_overall_score >= 70) as compliant_count,
                    COUNTIF(carbon_lockin_risk = 'LOW') as low_lockin,
                    COUNTIF(carbon_lockin_risk = 'HIGH') as high_lockin,
                    COUNTIF(dnsh_status = 'PASS') as dnsh_pass
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.transition_loans`
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": True, "total_loans": 0, "source": "BigQuery"}
            
            row = results[0]
            total = row.get("total_loans", 0) or 0
            compliant = row.get("compliant_count", 0) or 0
            
            return {
                "success": True,
                "total_loans": total,
                "avg_tlp_score": round(row.get("avg_score", 0) or 0, 1),
                "compliant_count": compliant,
                "compliance_rate": round(compliant / total * 100, 1) if total > 0 else 0,
                "carbon_lockin": {
                    "low": row.get("low_lockin", 0),
                    "high": row.get("high_lockin", 0),
                },
                "dnsh_pass_count": row.get("dnsh_pass", 0),
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"TLP summary error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_tlp_validator: Optional[TLPValidatorAgent] = None


def get_tlp_validator() -> TLPValidatorAgent:
    """Get or create TLP Validator singleton."""
    global _tlp_validator
    if _tlp_validator is None:
        _tlp_validator = TLPValidatorAgent()
    return _tlp_validator


# Convenience functions
def validate_transition_loan(loan_id: str) -> Dict[str, Any]:
    """Validate TLP compliance for a loan."""
    return get_tlp_validator().validate_transition_loan(loan_id)


def get_tlp_summary() -> Dict[str, Any]:
    """Get portfolio TLP summary."""
    return get_tlp_validator().get_tlp_summary()


def save_tlp_assessment(loan_id: str, assessment: Dict[str, Any]) -> Dict[str, Any]:
    """Save TLP assessment."""
    return get_tlp_validator().save_assessment(loan_id, assessment)
