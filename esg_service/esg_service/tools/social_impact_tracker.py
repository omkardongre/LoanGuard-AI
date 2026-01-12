"""
Social Impact Tracker Agent - Track and measure social impact metrics.

Production-level implementation for monitoring Social Loan impact over lifecycle.
Implements ICMA Handbook 2025 recommended KPIs and reporting requirements.

Reference: self-docs/research/SOCIAL_LOANS_RESEARCH.md
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, date
import json

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


# ICMA Handbook 2025 - Recommended Social KPIs by Category
SOCIAL_KPIS = {
    "AFFORDABLE_INFRASTRUCTURE": [
        {"name": "beneficiaries_reached", "unit": "households", "type": "count"},
        {"name": "access_points_created", "unit": "number", "type": "count"},
        {"name": "coverage_improvement", "unit": "percentage", "type": "percentage"},
        {"name": "service_reliability", "unit": "percentage", "type": "percentage"},
    ],
    "ESSENTIAL_SERVICES": [
        {"name": "patients_treated", "unit": "number", "type": "count"},
        {"name": "students_enrolled", "unit": "number", "type": "count"},
        {"name": "facilities_built", "unit": "number", "type": "count"},
        {"name": "healthcare_workers_trained", "unit": "number", "type": "count"},
        {"name": "teachers_trained", "unit": "number", "type": "count"},
    ],
    "AFFORDABLE_HOUSING": [
        {"name": "housing_units_created", "unit": "units", "type": "count"},
        {"name": "families_housed", "unit": "number", "type": "count"},
        {"name": "rent_reduction_achieved", "unit": "percentage", "type": "percentage"},
        {"name": "sqm_developed", "unit": "sqm", "type": "area"},
    ],
    "EMPLOYMENT_GENERATION": [
        {"name": "jobs_created", "unit": "number", "type": "count"},
        {"name": "people_reskilled", "unit": "number", "type": "count"},
        {"name": "smes_financed", "unit": "number", "type": "count"},
        {"name": "training_hours_delivered", "unit": "hours", "type": "count"},
    ],
    "FOOD_SECURITY": [
        {"name": "smallholders_supported", "unit": "number", "type": "count"},
        {"name": "hectares_sustainably_farmed", "unit": "hectares", "type": "area"},
        {"name": "food_distributed", "unit": "tonnes", "type": "weight"},
        {"name": "meals_provided", "unit": "number", "type": "count"},
    ],
    "SOCIOECONOMIC_ADVANCEMENT": [
        {"name": "people_reached", "unit": "number", "type": "count"},
        {"name": "financial_literacy_participants", "unit": "number", "type": "count"},
        {"name": "loans_disbursed_to_underserved", "unit": "amount", "type": "currency"},
        {"name": "bank_accounts_opened", "unit": "number", "type": "count"},
    ],
}


@dataclass
class ImpactMetric:
    """Single impact metric measurement."""
    metric_name: str
    baseline_value: float
    target_value: float
    current_value: float
    unit: str
    measurement_date: date
    progress_percentage: float


class SocialImpactTrackerAgent:
    """
    Track and measure social impact over loan lifecycle.
    
    Implements ICMA Handbook 2025 recommended KPIs for social impact reporting.
    Supports SLP 2025 Component 4: Reporting (annual reporting mandatory).
    
    Reference: self-docs/research/SOCIAL_LOANS_RESEARCH.md
    """
    
    def __init__(self):
        """Initialize Social Impact Tracker Agent."""
        self.bq = BigQueryClient()
    
    def get_social_loan_impact(self, loan_id: str) -> Dict[str, Any]:
        """
        Get current social impact metrics for a loan.
        
        Args:
            loan_id: Loan identifier
            
        Returns:
            Impact metrics with progress tracking
        """
        try:
            # Get social loan data
            social_loan = self._get_social_loan(loan_id)
            if not social_loan:
                return {
                    "success": False,
                    "loan_id": loan_id,
                    "error": "Social loan not found. Run validation first.",
                }
            
            # Get impact metrics from JSON field
            impact_metrics = self._parse_impact_metrics(social_loan)
            
            # Get recommended KPIs for this category
            category = social_loan.get("social_category", "")
            recommended_kpis = SOCIAL_KPIS.get(category, [])
            
            # Calculate overall impact score
            impact_score = self._calculate_impact_score(impact_metrics)
            
            return {
                "success": True,
                "loan_id": loan_id,
                "social_category": category,
                "target_population": social_loan.get("target_population", ""),
                "expected_beneficiaries": social_loan.get("population_size", 0),
                "actual_beneficiaries": social_loan.get("actual_beneficiaries", 0),
                "impact_score": round(impact_score, 1),
                "metrics": impact_metrics,
                "recommended_kpis": recommended_kpis,
                "reporting_status": self._get_reporting_status(loan_id),
                "last_updated": str(social_loan.get("updated_at", "")),
            }
            
        except Exception as e:
            logger.error(f"Error getting impact for {loan_id}: {e}")
            return {
                "success": False,
                "loan_id": loan_id,
                "error": str(e),
            }
    
    def update_impact_metrics(
        self, 
        loan_id: str, 
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update impact metrics for a social loan.
        
        Args:
            loan_id: Loan identifier
            metrics: Dictionary of metric updates
            
        Returns:
            Update result
        """
        try:
            # Get existing social loan
            social_loan = self._get_social_loan(loan_id)
            if not social_loan:
                return {
                    "success": False,
                    "loan_id": loan_id,
                    "error": "Social loan not found",
                }
            
            # Parse existing metrics
            existing = json.loads(social_loan.get("impact_metrics", "{}") or "{}")
            
            # Merge with new metrics
            existing.update(metrics)
            
            # Update in BigQuery
            query = f"""
                UPDATE `{self.bq.get_full_table_id('social_loans')}`
                SET 
                    impact_metrics = @impact_metrics,
                    actual_beneficiaries = @actual_beneficiaries,
                    updated_at = CURRENT_TIMESTAMP()
                WHERE loan_id = @loan_id
            """
            
            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("loan_id", "STRING", loan_id),
                    bigquery.ScalarQueryParameter("impact_metrics", "STRING", json.dumps(existing)),
                    bigquery.ScalarQueryParameter(
                        "actual_beneficiaries", "INT64", 
                        metrics.get("beneficiaries_reached", 
                                   metrics.get("people_reached", 
                                              social_loan.get("actual_beneficiaries", 0)))
                    ),
                ]
            )
            
            self.bq.client.query(query, job_config=job_config).result()
            
            return {
                "success": True,
                "loan_id": loan_id,
                "updated_metrics": existing,
                "update_date": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error updating impact for {loan_id}: {e}")
            return {
                "success": False,
                "loan_id": loan_id,
                "error": str(e),
            }
    
    def generate_impact_report(self, loan_id: str) -> Dict[str, Any]:
        """
        Generate annual impact report for a social loan.
        
        Required by SLP 2025 Component 4 (mandatory annual reporting).
        
        Args:
            loan_id: Loan identifier
            
        Returns:
            Formatted impact report
        """
        try:
            # Get social loan data
            social_loan = self._get_social_loan(loan_id)
            if not social_loan:
                return {
                    "success": False,
                    "error": "Social loan not found",
                }
            
            # Get loan details
            loan_data = self.bq.get_loan_by_id(loan_id)
            
            # Parse impact metrics
            impact_metrics = self._parse_impact_metrics(social_loan)
            
            # Get projects
            projects = json.loads(social_loan.get("social_projects", "[]") or "[]")
            
            # Build report
            report = {
                "report_type": "SLP_ANNUAL_IMPACT_REPORT",
                "report_date": datetime.now().isoformat(),
                "slp_version": "March 2025",
                "loan_details": {
                    "loan_id": loan_id,
                    "borrower_name": loan_data.get("borrower_name", "") if loan_data else "",
                    "facility_amount": loan_data.get("facility_amount", 0) if loan_data else 0,
                    "currency": loan_data.get("currency", "USD") if loan_data else "USD",
                },
                "social_classification": {
                    "category": social_loan.get("social_category"),
                    "target_population": social_loan.get("target_population"),
                    "geographic_area": social_loan.get("geographic_area", ""),
                },
                "use_of_proceeds": {
                    "description": "Proceeds allocated to eligible Social Projects",
                    "projects": projects if projects else [{"note": "Project details to be updated"}],
                    "allocation_percentage": 100.0,  # SLP requires 100%
                },
                "social_impact": {
                    "expected_beneficiaries": social_loan.get("population_size", 0),
                    "actual_beneficiaries": social_loan.get("actual_beneficiaries", 0),
                    "beneficiary_achievement": self._calc_achievement(
                        social_loan.get("population_size", 0),
                        social_loan.get("actual_beneficiaries", 0)
                    ),
                    "metrics": impact_metrics,
                },
                "slp_compliance": {
                    "overall_score": social_loan.get("slp_compliance_score", 0),
                    "verification_status": social_loan.get("verification_status", "PENDING"),
                    "external_review": social_loan.get("external_review_type"),
                    "verifier": social_loan.get("verifier_name"),
                },
            }
            
            return {
                "success": True,
                "loan_id": loan_id,
                "report": report,
            }
            
        except Exception as e:
            logger.error(f"Error generating report for {loan_id}: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def get_portfolio_impact(self) -> Dict[str, Any]:
        """
        Get portfolio-wide social impact summary.
        
        Returns:
            Aggregated social impact across all social loans
        """
        try:
            query = f"""
                SELECT 
                    social_category,
                    COUNT(*) as loan_count,
                    SUM(population_size) as expected_beneficiaries,
                    SUM(COALESCE(actual_beneficiaries, 0)) as actual_beneficiaries,
                    AVG(slp_compliance_score) as avg_compliance_score,
                    COUNTIF(verification_status = 'VERIFIED') as verified_count
                FROM `{self.bq.get_full_table_id('social_loans')}`
                WHERE social_category IS NOT NULL
                GROUP BY social_category
                ORDER BY loan_count DESC
            """
            results = self.bq.execute_query(query)
            
            total_expected = sum(r.get("expected_beneficiaries", 0) or 0 for r in results)
            total_actual = sum(r.get("actual_beneficiaries", 0) or 0 for r in results)
            
            return {
                "success": True,
                "portfolio_summary": {
                    "total_social_loans": sum(r.get("loan_count", 0) for r in results),
                    "total_expected_beneficiaries": total_expected,
                    "total_actual_beneficiaries": total_actual,
                    "beneficiary_achievement": self._calc_achievement(total_expected, total_actual),
                    "avg_compliance_score": round(
                        sum(r.get("avg_compliance_score", 0) or 0 for r in results) / len(results), 1
                    ) if results else 0,
                },
                "by_category": [
                    {
                        "category": r["social_category"],
                        "loan_count": r["loan_count"],
                        "expected_beneficiaries": r.get("expected_beneficiaries", 0),
                        "actual_beneficiaries": r.get("actual_beneficiaries", 0),
                        "avg_score": round(r.get("avg_compliance_score", 0) or 0, 1),
                        "verified_count": r.get("verified_count", 0),
                    }
                    for r in results
                ],
                "report_date": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio impact: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_social_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get social loan data from BigQuery."""
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.get_full_table_id('social_loans')}`
                WHERE loan_id = @loan_id
                LIMIT 1
            """
            from google.cloud import bigquery
            params = [bigquery.ScalarQueryParameter("loan_id", "STRING", loan_id)]
            results = self.bq.execute_query(query, params)
            return results[0] if results else None
        except Exception:
            return None
    
    def _parse_impact_metrics(self, social_loan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse impact metrics from JSON field."""
        try:
            raw = social_loan.get("impact_metrics", "{}")
            if isinstance(raw, str):
                metrics = json.loads(raw)
            else:
                metrics = raw or {}
            
            return [
                {
                    "name": k,
                    "value": v.get("value") if isinstance(v, dict) else v,
                    "unit": v.get("unit", "") if isinstance(v, dict) else "",
                    "target": v.get("target") if isinstance(v, dict) else None,
                }
                for k, v in metrics.items()
            ]
        except Exception:
            return []
    
    def _calculate_impact_score(self, metrics: List[Dict[str, Any]]) -> float:
        """Calculate overall impact score based on metrics."""
        if not metrics:
            return 0.0
        
        scores = []
        for m in metrics:
            if m.get("target") and m.get("value"):
                try:
                    achievement = (float(m["value"]) / float(m["target"])) * 100
                    scores.append(min(achievement, 100))
                except (ValueError, ZeroDivisionError):
                    pass
        
        return sum(scores) / len(scores) if scores else 50.0  # Default 50 if no targets
    
    def _get_reporting_status(self, loan_id: str) -> str:
        """Check if annual report has been generated."""
        # For now, return status based on verification
        social_loan = self._get_social_loan(loan_id)
        if social_loan:
            if social_loan.get("verification_status") == "VERIFIED":
                return "COMPLIANT"
            elif social_loan.get("impact_metrics") and social_loan["impact_metrics"] != "{}":
                return "PARTIAL"
        return "PENDING"
    
    def _calc_achievement(self, expected: int, actual: int) -> float:
        """Calculate achievement percentage."""
        if not expected or expected == 0:
            return 0.0
        return round((actual / expected) * 100, 1)


# Singleton instance
_social_impact_tracker: Optional[SocialImpactTrackerAgent] = None


def get_social_impact_tracker() -> SocialImpactTrackerAgent:
    """Get or create Social Impact Tracker singleton."""
    global _social_impact_tracker
    if _social_impact_tracker is None:
        _social_impact_tracker = SocialImpactTrackerAgent()
    return _social_impact_tracker


# Convenience functions
def get_social_loan_impact(loan_id: str) -> Dict[str, Any]:
    """Get social impact for a loan."""
    return get_social_impact_tracker().get_social_loan_impact(loan_id)


def update_social_impact(loan_id: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Update social impact metrics."""
    return get_social_impact_tracker().update_impact_metrics(loan_id, metrics)


def generate_social_impact_report(loan_id: str) -> Dict[str, Any]:
    """Generate annual impact report."""
    return get_social_impact_tracker().generate_impact_report(loan_id)


def get_portfolio_social_impact() -> Dict[str, Any]:
    """Get portfolio-wide social impact."""
    return get_social_impact_tracker().get_portfolio_impact()
