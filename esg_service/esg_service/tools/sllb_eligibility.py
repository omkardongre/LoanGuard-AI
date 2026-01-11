"""
SLLB Eligibility Engine - Evaluate SLL eligibility for SLLB inclusion.

Production-level implementation based on ICMA SLLBG Component 2.
Evaluates SLLs against SLLP alignment and SLLBG criteria.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class SLLBEligibilityEngine:
    """
    Evaluate SLL eligibility for SLLB inclusion.
    
    Based on ICMA SLLBG Component 2 - Process for SLL Evaluation & Selection:
    - Governance structure
    - Decision-making process
    - Sectoral exclusions
    - ESG risk mitigation
    - Disqualification criteria
    - Re-qualification criteria
    
    Reference: research4_sllb_guidelines.md
    """
    
    # SLLP 5 Components for alignment check
    SLLP_COMPONENTS = [
        "selection_of_kpis",
        "calibration_of_spts",
        "loan_characteristics",
        "reporting",
        "verification",
    ]
    
    # Sector exclusions (example - configurable)
    DEFAULT_SECTOR_EXCLUSIONS = [
        "TOBACCO",
        "CONTROVERSIAL_WEAPONS",
        "THERMAL_COAL",
        "OIL_SANDS",
    ]
    
    # Eligibility criteria weights
    ELIGIBILITY_WEIGHTS = {
        "sllp_alignment": 30,
        "kpi_materiality": 20,
        "spt_ambition": 20,
        "verification_status": 15,
        "no_sector_exclusion": 15,
    }
    
    # Eligibility threshold
    ELIGIBILITY_THRESHOLD = 70
    
    def __init__(self):
        """Initialize SLLB Eligibility Engine."""
        self.bq = BigQueryClient()
    
    def evaluate_sll(self, loan_id: str) -> Dict[str, Any]:
        """
        Evaluate an SLL for SLLB eligibility.
        
        Args:
            loan_id: Loan identifier
            
        Returns:
            Eligibility assessment
        """
        try:
            # Get SLL data
            sll_data = self._get_sll_data(loan_id)
            
            if not sll_data:
                return {
                    "success": False, 
                    "error": f"SLL {loan_id} not found",
                    "source": "BigQuery",
                }
            
            # Evaluate each criterion
            criteria_scores = {
                "sllp_alignment": self._score_sllp_alignment(sll_data),
                "kpi_materiality": self._score_kpi_materiality(sll_data),
                "spt_ambition": self._score_spt_ambition(sll_data),
                "verification_status": self._score_verification(sll_data),
                "no_sector_exclusion": self._score_sector_exclusion(sll_data),
            }
            
            # Calculate weighted score
            total_score = sum(
                score * self.ELIGIBILITY_WEIGHTS[criterion]
                for criterion, score in criteria_scores.items()
            ) / 100
            
            is_eligible = total_score >= self.ELIGIBILITY_THRESHOLD
            
            # Check for automatic disqualification
            disqualification_reason = self._check_disqualification(sll_data, criteria_scores)
            if disqualification_reason:
                is_eligible = False
            
            return {
                "success": True,
                "loan_id": loan_id,
                "eligibility_score": round(total_score, 1),
                "is_eligible": is_eligible,
                "eligibility_status": "ELIGIBLE" if is_eligible else "INELIGIBLE",
                "criteria_scores": {k: round(v, 1) for k, v in criteria_scores.items()},
                "disqualification_reason": disqualification_reason,
                "recommendations": self._generate_recommendations(criteria_scores, is_eligible),
                "evaluation_date": str(date.today()),
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"SLL eligibility evaluation error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_sll_data(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get SLL data from BigQuery."""
        try:
            # Check if we have SLL KPIs for this loan
            kpi_query = f"""
                SELECT 
                    k.loan_id,
                    k.kpi_type,
                    k.baseline_value,
                    k.target_value,
                    k.current_value,
                    k.verification_status
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.sll_kpis` k
                WHERE k.loan_id = '{loan_id}'
                ORDER BY k.created_at DESC
                LIMIT 1
            """
            kpi_results = self.bq.execute_query(kpi_query)
            
            # Get loan details
            loan_query = f"""
                SELECT 
                    loan_id,
                    borrower_id,
                    facility_amount,
                    status
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.loans`
                WHERE loan_id = '{loan_id}'
            """
            loan_results = self.bq.execute_query(loan_query)
            
            if not loan_results:
                return None
            
            loan = loan_results[0]
            kpi = kpi_results[0] if kpi_results else {}
            
            # Get SPT data
            spt_query = f"""
                SELECT 
                    target_description,
                    target_value,
                    current_progress,
                    achievement_probability
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.sll_spts`
                WHERE loan_id = '{loan_id}'
                ORDER BY created_at DESC
                LIMIT 1
            """
            spt_results = self.bq.execute_query(spt_query)
            spt = spt_results[0] if spt_results else {}
            
            return {
                **loan,
                **kpi,
                **spt,
            }
            
        except Exception:
            return None
    
    def _score_sllp_alignment(self, data: Dict[str, Any]) -> float:
        """Score SLLP alignment (all 5 components)."""
        score = 0
        
        # Has KPI defined
        if data.get("kpi_type"):
            score += 20
        
        # Has SPT defined
        if data.get("target_value"):
            score += 20
        
        # Has baseline
        if data.get("baseline_value"):
            score += 20
        
        # Has verification
        if data.get("verification_status") in ["VERIFIED", "PENDING"]:
            score += 20
        
        # Active loan
        if data.get("status") == "ACTIVE":
            score += 20
        
        return score
    
    def _score_kpi_materiality(self, data: Dict[str, Any]) -> float:
        """Score KPI materiality."""
        kpi_type = data.get("kpi_type", "")
        
        # Most material KPIs
        high_materiality = ["GHG_SCOPE_1", "GHG_SCOPE_2", "GHG_SCOPE_3", "ENERGY_INTENSITY"]
        medium_materiality = ["WATER_INTENSITY", "WASTE_REDUCTION", "RENEWABLE_ENERGY"]
        
        if kpi_type in high_materiality:
            return 100
        elif kpi_type in medium_materiality:
            return 70
        elif kpi_type:
            return 50
        else:
            return 0
    
    def _score_spt_ambition(self, data: Dict[str, Any]) -> float:
        """Score SPT ambition level."""
        target = data.get("target_value", 0)
        baseline = data.get("baseline_value", 0)
        
        if baseline == 0:
            return 50  # Can't calculate ambition
        
        # Calculate reduction percentage
        reduction_pct = abs(target - baseline) / abs(baseline) * 100
        
        # Score based on ambition
        if reduction_pct >= 30:
            return 100  # Highly ambitious
        elif reduction_pct >= 20:
            return 80
        elif reduction_pct >= 10:
            return 60
        elif reduction_pct >= 5:
            return 40
        else:
            return 20  # Not ambitious enough
    
    def _score_verification(self, data: Dict[str, Any]) -> float:
        """Score verification status."""
        status = data.get("verification_status", "")
        
        if status == "VERIFIED":
            return 100
        elif status == "PENDING":
            return 60
        elif status == "FAILED":
            return 0
        else:
            return 30  # No verification
    
    def _score_sector_exclusion(self, data: Dict[str, Any]) -> float:
        """Score based on sector exclusions."""
        # Would typically check borrower sector
        # For now, assume no exclusion if data is present
        return 100
    
    def _check_disqualification(
        self, 
        data: Dict[str, Any], 
        scores: Dict[str, float]
    ) -> Optional[str]:
        """Check for automatic disqualification reasons."""
        # Verification failed
        if data.get("verification_status") == "FAILED":
            return "Verification failed"
        
        # No SLLP alignment
        if scores.get("sllp_alignment", 0) < 40:
            return "Insufficient SLLP alignment"
        
        # Sector exclusion (would check actual sector)
        if scores.get("no_sector_exclusion", 100) == 0:
            return "Sector exclusion applies"
        
        return None
    
    def _generate_recommendations(
        self, 
        scores: Dict[str, float], 
        is_eligible: bool
    ) -> List[str]:
        """Generate recommendations for eligibility improvement."""
        recommendations = []
        
        if not is_eligible:
            if scores.get("sllp_alignment", 0) < 70:
                recommendations.append("Improve SLLP alignment - ensure all 5 components are addressed")
            
            if scores.get("kpi_materiality", 0) < 70:
                recommendations.append("Select more material KPIs (e.g., GHG emissions)")
            
            if scores.get("spt_ambition", 0) < 70:
                recommendations.append("Set more ambitious SPTs (target 20%+ improvement)")
            
            if scores.get("verification_status", 0) < 70:
                recommendations.append("Obtain third-party verification of SPTs")
        else:
            recommendations.append("SLL is eligible for SLLB inclusion")
            recommendations.append("Maintain verification and reporting standards")
        
        return recommendations
    
    def batch_evaluate(self, loan_ids: List[str]) -> Dict[str, Any]:
        """Batch evaluate multiple SLLs."""
        try:
            results = []
            eligible_count = 0
            
            for loan_id in loan_ids:
                evaluation = self.evaluate_sll(loan_id)
                results.append(evaluation)
                if evaluation.get("is_eligible"):
                    eligible_count += 1
            
            return {
                "success": True,
                "total_evaluated": len(loan_ids),
                "eligible_count": eligible_count,
                "eligibility_rate": round(eligible_count / len(loan_ids) * 100, 1) if loan_ids else 0,
                "evaluations": results,
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Batch evaluation error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_eligibility_engine: Optional[SLLBEligibilityEngine] = None


def get_eligibility_engine() -> SLLBEligibilityEngine:
    """Get or create SLLB Eligibility Engine singleton."""
    global _eligibility_engine
    if _eligibility_engine is None:
        _eligibility_engine = SLLBEligibilityEngine()
    return _eligibility_engine


# Convenience functions
def evaluate_sll_eligibility(loan_id: str) -> Dict[str, Any]:
    """Evaluate SLL eligibility for SLLB."""
    return get_eligibility_engine().evaluate_sll(loan_id)


def batch_evaluate_sll_eligibility(loan_ids: List[str]) -> Dict[str, Any]:
    """Batch evaluate SLL eligibility."""
    return get_eligibility_engine().batch_evaluate(loan_ids)
