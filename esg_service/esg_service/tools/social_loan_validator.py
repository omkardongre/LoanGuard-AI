"""
Social Loan Validator Agent - Validate Social Loan Principles (SLP) compliance.

Production-level implementation based on LMA/APLMA/LSTA Social Loan Principles (March 2025).
Implements the 4 core SLP components with scoring.

Reference: self-docs/research/SOCIAL_LOANS_RESEARCH.md
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, date
import json

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


# SLP March 2025 - 6 Eligible Social Project Categories
SLP_CATEGORIES = [
    "AFFORDABLE_INFRASTRUCTURE",    # Water, sanitation, telecom, energy, transport
    "ESSENTIAL_SERVICES",           # Healthcare, education, financial services
    "AFFORDABLE_HOUSING",           # Social housing, supported housing, rental
    "EMPLOYMENT_GENERATION",        # SME financing, job creation, re-skilling
    "FOOD_SECURITY",                # Sustainable food systems, agriculture
    "SOCIOECONOMIC_ADVANCEMENT",    # Equity programs, empowerment, wealth building
]

# SLP March 2025 - Target Populations
SLP_TARGET_POPULATIONS = [
    "BELOW_POVERTY_LINE",
    "EXCLUDED_MARGINALIZED",
    "PEOPLE_WITH_DISABILITIES",
    "MIGRANTS_DISPLACED",
    "UNDEREDUCATED",
    "UNDERSERVED",
    "UNEMPLOYED",
    "WOMEN",
    "LGBTQ",
    "AGING_POPULATIONS",
    "VULNERABLE_YOUTH",
    "INDIGENOUS_COMMUNITIES",
    "RURAL_POPULATIONS",
    "VETERANS",
    "FORMERLY_INCARCERATED",
]

# Keywords for category detection from loan text
CATEGORY_KEYWORDS = {
    "AFFORDABLE_INFRASTRUCTURE": [
        "water", "sanitation", "telecommunications", "telecom", "energy access",
        "transport", "electricity", "broadband", "connectivity", "infrastructure",
        "public transport", "clean water", "sewage", "public utility"
    ],
    "ESSENTIAL_SERVICES": [
        "healthcare", "hospital", "clinic", "education", "school", "university",
        "financial services", "banking", "microfinance", "childcare", "eldercare",
        "legal services", "training", "vocational"
    ],
    "AFFORDABLE_HOUSING": [
        "affordable housing", "social housing", "low-income housing", "housing",
        "rental housing", "rent-to-own", "housing development", "shelters",
        "senior living", "supported housing"
    ],
    "EMPLOYMENT_GENERATION": [
        "employment", "job creation", "SME", "small business", "entrepreneurship",
        "re-skilling", "workforce development", "job training", "cooperatives",
        "social enterprise", "hiring", "employment generation"
    ],
    "FOOD_SECURITY": [
        "food security", "agriculture", "farming", "food distribution",
        "nutrition", "sustainable food", "smallholder", "food access",
        "food production", "fisheries"
    ],
    "SOCIOECONOMIC_ADVANCEMENT": [
        "empowerment", "equity", "financial literacy", "wealth building",
        "minority business", "digital inclusion", "social mobility",
        "community development", "gender equity", "advancement"
    ],
}

# Keywords for target population detection
POPULATION_KEYWORDS = {
    "BELOW_POVERTY_LINE": ["poverty", "poor", "low-income", "disadvantaged"],
    "EXCLUDED_MARGINALIZED": ["marginalized", "excluded", "minority", "underrepresented"],
    "PEOPLE_WITH_DISABILITIES": ["disability", "disabled", "handicap", "special needs"],
    "MIGRANTS_DISPLACED": ["refugee", "migrant", "displaced", "asylum"],
    "UNDEREDUCATED": ["illiterate", "uneducated", "low literacy", "undereducated"],
    "UNDERSERVED": ["underserved", "unbanked", "underbanked", "rural", "remote"],
    "UNEMPLOYED": ["unemployed", "jobless", "out of work", "unemployment"],
    "WOMEN": ["women", "female", "gender", "women-owned", "women-led"],
    "LGBTQ": ["lgbtq", "lgbt", "sexual minority", "gender minority"],
    "AGING_POPULATIONS": ["elderly", "senior", "aging", "retired", "pensioner"],
    "VULNERABLE_YOUTH": ["youth", "at-risk youth", "orphan", "homeless youth", "young people"],
    "INDIGENOUS_COMMUNITIES": ["indigenous", "native", "tribal", "aboriginal"],
    "RURAL_POPULATIONS": ["rural", "village", "remote area", "countryside"],
    "VETERANS": ["veteran", "military", "ex-military", "service member"],
    "FORMERLY_INCARCERATED": ["incarcerated", "formerly incarcerated", "prison", "ex-offender"],
}


@dataclass
class SLPScore:
    """SLP compliance score breakdown following 4 core components."""
    overall_score: float
    use_of_proceeds_score: float      # Component 1
    project_evaluation_score: float    # Component 2
    proceeds_management_score: float   # Component 3
    reporting_score: float             # Component 4
    is_compliant: bool
    social_category: str
    target_populations: List[str]


class SocialLoanValidatorAgent:
    """
    Validate Social Loan Principles compliance.
    
    Based on LMA/APLMA/LSTA Social Loan Principles (March 2025):
    - Component 1: Use of Proceeds
    - Component 2: Process for Project Evaluation and Selection
    - Component 3: Management of Proceeds
    - Component 4: Reporting
    
    Reference: self-docs/research/SOCIAL_LOANS_RESEARCH.md
    """
    
    # Component weights (100 total)
    COMPONENT_WEIGHTS = {
        "use_of_proceeds": 35,          # Proceeds for eligible social projects
        "project_evaluation": 25,       # Clear criteria and objectives
        "proceeds_management": 20,      # Tracking/audit trail
        "reporting": 20,                # Annual reporting (mandatory 2025)
    }
    
    # Compliance threshold (70% to be SLP compliant)
    COMPLIANCE_THRESHOLD = 70
    
    def __init__(self):
        """Initialize Social Loan Validator Agent."""
        self.bq = BigQueryClient()
    
    def validate_social_loan(
        self, 
        loan_id: str, 
        loan_purpose: Optional[str] = None,
        borrower_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Full SLP validation for a potential social loan.
        
        Args:
            loan_id: Loan identifier
            loan_purpose: Stated purpose/description of the loan
            borrower_info: Optional borrower information
            
        Returns:
            SLP compliance assessment with scores and recommendations
        """
        try:
            # Check for existing assessment
            existing = self._get_existing_assessment(loan_id)
            if existing:
                return existing
            
            # Get loan data if not provided
            if not loan_purpose:
                loan_data = self._get_loan_data(loan_id)
                if loan_data:
                    loan_purpose = loan_data.get("loan_type", "") or ""
                    borrower_info = loan_data
            
            # Classify social category
            social_category = self._classify_social_category(loan_purpose or "")
            
            # Identify target populations
            target_populations = self._identify_target_populations(loan_purpose or "")
            
            # Score each component
            c1_score = self._score_use_of_proceeds(loan_purpose, social_category)
            c2_score = self._score_project_evaluation(loan_purpose, social_category, target_populations)
            c3_score = self._score_proceeds_management(loan_id)
            c4_score = self._score_reporting(loan_id)
            
            # Calculate weighted overall score
            overall = (
                c1_score * self.COMPONENT_WEIGHTS["use_of_proceeds"] +
                c2_score * self.COMPONENT_WEIGHTS["project_evaluation"] +
                c3_score * self.COMPONENT_WEIGHTS["proceeds_management"] +
                c4_score * self.COMPONENT_WEIGHTS["reporting"]
            ) / 100
            
            is_compliant = overall >= self.COMPLIANCE_THRESHOLD
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                c1_score, c2_score, c3_score, c4_score,
                social_category, target_populations
            )
            
            return {
                "success": True,
                "loan_id": loan_id,
                "is_social_loan": social_category != "UNCLASSIFIED",
                "is_slp_compliant": is_compliant,
                "social_category": social_category,
                "target_populations": target_populations,
                "scores": {
                    "overall": round(overall, 1),
                    "use_of_proceeds": round(c1_score, 1),
                    "project_evaluation": round(c2_score, 1),
                    "proceeds_management": round(c3_score, 1),
                    "reporting": round(c4_score, 1),
                },
                "compliance_threshold": self.COMPLIANCE_THRESHOLD,
                "recommendations": recommendations,
                "assessment_date": datetime.now().isoformat(),
                "assessor_agent": "social_loan_validator",
                "slp_version": "March 2025",
            }
            
        except Exception as e:
            logger.error(f"Error validating social loan {loan_id}: {e}")
            return {
                "success": False,
                "loan_id": loan_id,
                "error": str(e),
            }
    
    def _get_existing_assessment(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Check for existing social loan assessment."""
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.get_full_table_id('social_loans')}`
                WHERE loan_id = @loan_id
                ORDER BY created_at DESC
                LIMIT 1
            """
            from google.cloud import bigquery
            params = [bigquery.ScalarQueryParameter("loan_id", "STRING", loan_id)]
            results = self.bq.execute_query(query, params)
            
            if results:
                row = results[0]
                return {
                    "success": True,
                    "loan_id": loan_id,
                    "is_social_loan": True,
                    "is_slp_compliant": row.get("slp_compliance_score", 0) >= self.COMPLIANCE_THRESHOLD,
                    "social_category": row.get("social_category"),
                    "target_populations": row.get("target_population", "").split(",") if row.get("target_population") else [],
                    "scores": {
                        "overall": row.get("slp_compliance_score", 0),
                        "use_of_proceeds": row.get("use_of_proceeds_score", 0),
                        "project_evaluation": row.get("project_eval_score", 0),
                        "proceeds_management": row.get("proceeds_mgmt_score", 0),
                        "reporting": row.get("reporting_score", 0),
                    },
                    "verification_status": row.get("verification_status"),
                    "assessment_date": str(row.get("assessment_date")),
                    "cached": True,
                }
            return None
        except Exception as e:
            logger.debug(f"No existing assessment for {loan_id}: {e}")
            return None
    
    def _get_loan_data(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get loan data from BigQuery."""
        return self.bq.get_loan_by_id(loan_id)
    
    def _classify_social_category(self, text: str) -> str:
        """
        Classify loan into one of the 6 SLP social categories.
        
        Uses keyword matching against SLP Appendix 1 categories.
        """
        text_lower = text.lower()
        category_scores = {}
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return "UNCLASSIFIED"
        
        # Return category with highest keyword matches
        return max(category_scores, key=category_scores.get)
    
    def _identify_target_populations(self, text: str) -> List[str]:
        """
        Identify target populations from loan text.
        
        Based on SLP Appendix 2 target populations.
        """
        text_lower = text.lower()
        identified = []
        
        for population, keywords in POPULATION_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                identified.append(population)
        
        return identified if identified else ["GENERAL_POPULATION"]
    
    def _score_use_of_proceeds(self, loan_purpose: str, category: str) -> float:
        """
        Score Component 1: Use of Proceeds.
        
        Proceeds must be exclusively for eligible Social Projects.
        """
        score = 0.0
        
        # Category match (40 points)
        if category != "UNCLASSIFIED":
            score += 40.0
        
        # Clear social purpose stated (30 points)
        social_keywords = ["social", "community", "affordable", "access", "inclusion", "equity"]
        if any(kw in (loan_purpose or "").lower() for kw in social_keywords):
            score += 30.0
        
        # Specific project description (30 points)
        if len(loan_purpose or "") > 50 and category != "UNCLASSIFIED":
            score += 30.0
        
        return min(score, 100.0)
    
    def _score_project_evaluation(
        self, 
        loan_purpose: str, 
        category: str, 
        target_populations: List[str]
    ) -> float:
        """
        Score Component 2: Process for Project Evaluation and Selection.
        
        Borrower must communicate social objectives and selection criteria.
        """
        score = 0.0
        
        # Social category identified (30 points)
        if category != "UNCLASSIFIED":
            score += 30.0
        
        # Target population identified (30 points)
        if target_populations and target_populations != ["GENERAL_POPULATION"]:
            score += 30.0
        
        # Clear social objectives (20 points)
        objective_keywords = ["improve", "provide", "increase", "reduce", "support", "enable", "create"]
        if any(kw in (loan_purpose or "").lower() for kw in objective_keywords):
            score += 20.0
        
        # Quantifiable benefits mentioned (20 points)
        quantity_patterns = ["beneficiaries", "households", "people", "jobs", "units", "students", "patients"]
        if any(pat in (loan_purpose or "").lower() for pat in quantity_patterns):
            score += 20.0
        
        return min(score, 100.0)
    
    def _score_proceeds_management(self, loan_id: str) -> float:
        """
        Score Component 3: Management of Proceeds.
        
        Proceeds must be tracked by borrower.
        Based on REAL data from BigQuery - no default scores without data.
        """
        score = 0.0
        
        try:
            # Check if loan exists in system (tracked)
            loan_data = self._get_loan_data(loan_id)
            if not loan_data:
                return 0.0  # No data = no score
            
            # Loan exists in system (40 points)
            score += 40.0
            
            # Has agent bank for audit trail (30 points)
            if loan_data.get("agent_bank"):
                score += 30.0
            
            # Has syndicate structure for tracking (30 points)
            if loan_data.get("syndicate_members"):
                score += 30.0
                
        except Exception as e:
            logger.debug(f"Error scoring proceeds management: {e}")
            return 0.0
        
        return min(score, 100.0)
    
    def _score_reporting(self, loan_id: str) -> float:
        """
        Score Component 4: Reporting.
        
        Annual reporting to lenders is MANDATORY as of SLP 2025.
        Based on REAL data from BigQuery - no default scores without data.
        """
        score = 0.0
        
        try:
            # Check if loan exists
            loan_data = self._get_loan_data(loan_id)
            if not loan_data:
                return 0.0  # No data = no score
            
            # Loan is in system (can generate reports) - 40 points
            score += 40.0
            
            # Check if ESG KPIs exist (reporting capability) - 30 points
            query = f"""
                SELECT COUNT(*) as count
                FROM `{self.bq.get_full_table_id('esg_kpis')}`
                WHERE loan_id = @loan_id
            """
            from google.cloud import bigquery
            params = [bigquery.ScalarQueryParameter("loan_id", "STRING", loan_id)]
            results = self.bq.execute_query(query, params)
            
            if results and results[0].get("count", 0) > 0:
                score += 30.0
            
            # Check for existing social loan assessment (indicates reporting) - 30 points
            existing = self._get_existing_assessment(loan_id)
            if existing:
                score += 30.0
                
        except Exception as e:
            logger.debug(f"Error scoring reporting: {e}")
            return 0.0
        
        return min(score, 100.0)
    
    def _generate_recommendations(
        self,
        c1: float, c2: float, c3: float, c4: float,
        category: str, populations: List[str]
    ) -> List[str]:
        """Generate improvement recommendations based on scores."""
        recommendations = []
        
        if category == "UNCLASSIFIED":
            recommendations.append(
                "CRITICAL: Loan does not match any SLP eligible category. "
                "Review loan purpose against 6 SLP categories: Infrastructure, "
                "Essential Services, Housing, Employment, Food Security, Socioeconomic Advancement."
            )
        
        if c1 < 70:
            recommendations.append(
                "Use of Proceeds: Document specific Social Projects to be financed. "
                "Ensure proceeds are exclusively for eligible social purposes."
            )
        
        if c2 < 70:
            recommendations.append(
                "Project Evaluation: Clearly define social objectives and target populations. "
                "Document selection criteria for eligible projects."
            )
        
        if populations == ["GENERAL_POPULATION"]:
            recommendations.append(
                "Target Population: SLP 2025 recommends identifying specific beneficiary groups. "
                "Document target population and expected number of beneficiaries."
            )
        
        if c3 < 70:
            recommendations.append(
                "Proceeds Management: Establish tracking mechanism for fund allocation. "
                "Consider dedicated account or ring-fenced internal tracking."
            )
        
        if c4 < 70:
            recommendations.append(
                "Reporting: Annual reporting is MANDATORY under SLP 2025. "
                "Prepare to report on use of proceeds and social impact annually."
            )
        
        return recommendations
    
    def save_assessment(self, loan_id: str, assessment: Dict[str, Any]) -> bool:
        """Save SLP assessment to BigQuery social_loans table."""
        try:
            row = {
                "loan_id": loan_id,
                "social_category": assessment.get("social_category", "UNCLASSIFIED"),
                "target_population": ",".join(assessment.get("target_populations", [])),
                "population_size": 0,  # To be updated with actual data
                "geographic_area": "",  # To be updated
                "impact_metrics": json.dumps({}),
                "slp_compliance_score": assessment.get("scores", {}).get("overall", 0),
                "use_of_proceeds_score": assessment.get("scores", {}).get("use_of_proceeds", 0),
                "project_eval_score": assessment.get("scores", {}).get("project_evaluation", 0),
                "proceeds_mgmt_score": assessment.get("scores", {}).get("proceeds_management", 0),
                "reporting_score": assessment.get("scores", {}).get("reporting", 0),
                "social_projects": json.dumps([]),
                "verification_status": "PENDING",
                "verifier_name": None,
                "external_review_type": None,
                "verification_date": None,
                "assessment_date": datetime.now().date().isoformat(),
                "assessor_agent": "social_loan_validator",
                "assessment_rationale": "; ".join(assessment.get("recommendations", [])),
            }
            
            errors = self.bq.insert_rows("social_loans", [row])
            if errors:
                logger.error(f"Error saving assessment: {errors}")
                return False
            return True
            
        except Exception as e:
            logger.error(f"Error saving assessment: {e}")
            return False
    
    def get_social_loan_summary(self) -> Dict[str, Any]:
        """Get portfolio-level social loan summary."""
        try:
            query = f"""
                SELECT 
                    social_category,
                    COUNT(*) as loan_count,
                    AVG(slp_compliance_score) as avg_compliance_score,
                    SUM(population_size) as total_beneficiaries
                FROM `{self.bq.get_full_table_id('social_loans')}`
                WHERE social_category IS NOT NULL
                GROUP BY social_category
                ORDER BY loan_count DESC
            """
            results = self.bq.execute_query(query)
            
            total_loans = sum(r.get("loan_count", 0) for r in results)
            
            return {
                "success": True,
                "total_social_loans": total_loans,
                "by_category": [
                    {
                        "category": r["social_category"],
                        "loan_count": r["loan_count"],
                        "avg_score": round(r.get("avg_compliance_score", 0), 1),
                        "beneficiaries": r.get("total_beneficiaries", 0),
                    }
                    for r in results
                ],
                "slp_version": "March 2025",
            }
            
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_social_loan_validator: Optional[SocialLoanValidatorAgent] = None


def get_social_loan_validator() -> SocialLoanValidatorAgent:
    """Get or create Social Loan Validator singleton."""
    global _social_loan_validator
    if _social_loan_validator is None:
        _social_loan_validator = SocialLoanValidatorAgent()
    return _social_loan_validator


# Convenience functions
def validate_social_loan(loan_id: str, loan_purpose: str = None) -> Dict[str, Any]:
    """Validate SLP compliance for a loan."""
    return get_social_loan_validator().validate_social_loan(loan_id, loan_purpose)


def get_social_loan_summary() -> Dict[str, Any]:
    """Get portfolio social loan summary."""
    return get_social_loan_validator().get_social_loan_summary()


def save_social_loan_assessment(loan_id: str, assessment: Dict[str, Any]) -> bool:
    """Save social loan assessment."""
    return get_social_loan_validator().save_assessment(loan_id, assessment)
