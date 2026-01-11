"""
ILPA Compliance Agent - Validate compliance with ILPA July 2024 NAV Guidance.

Production-level implementation for Fund Finance ILPA compliance checking.
Based on ILPA Guidelines: NAV-Based Facilities Guidance (July 25, 2024)
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class ILPAComplianceAgent:
    """
    ILPA Compliance Agent for NAV Facilities.
    
    Based on ILPA July 2024 NAV-Based Facilities Guidance:
    - LPAC consent requirements
    - Disclosure requirements
    - LPA provisions
    - Use of proceeds tracking
    
    Reference: https://ilpa.org/nav-based-facilities-guidance/
    """
    
    # ILPA Compliance Requirements
    ILPA_REQUIREMENTS = {
        "lpa_addresses_nav": {
            "description": "LPA explicitly addresses NAV-based facilities",
            "weight": 15,
        },
        "leverage_limits_defined": {
            "description": "Fund-level leverage limits clearly defined in LPA",
            "weight": 15,
        },
        "lpac_consent_required": {
            "description": "LPAC consent required for NAV facilities per guidance",
            "weight": 20,
        },
        "lpac_consent_obtained": {
            "description": "LPAC consent actually obtained",
            "weight": 20,
        },
        "rationale_disclosed": {
            "description": "Rationale for NAV facility disclosed to LPs",
            "weight": 5,
        },
        "size_disclosed": {
            "description": "Size of NAV facility disclosed",
            "weight": 5,
        },
        "structure_disclosed": {
            "description": "Structure and terms disclosed",
            "weight": 5,
        },
        "economic_terms_disclosed": {
            "description": "Economic terms (interest rate, fees) disclosed",
            "weight": 5,
        },
        "initial_ltv_disclosed": {
            "description": "Initial LTV ratio disclosed at time of borrowing",
            "weight": 5,
        },
        "distribution_consent": {
            "description": "If proceeds for distribution, specific consent obtained",
            "weight": 5,
        },
    }
    
    def __init__(self):
        """Initialize ILPA Compliance Agent."""
        self.bq = BigQueryClient()
    
    def check_compliance(self, facility_id: str) -> Dict[str, Any]:
        """
        Check ILPA compliance for a NAV facility.
        
        Args:
            facility_id: NAV facility identifier
            
        Returns:
            Compliance assessment result
        """
        try:
            # Get facility details
            query = f"""
                SELECT 
                    facility_id,
                    fund_id,
                    fund_name,
                    ilpa_compliant,
                    lpac_consent_obtained,
                    lpac_consent_date,
                    lpac_consent_purpose,
                    lpa_explicitly_permits,
                    use_of_proceeds,
                    distribution_amount,
                    initial_ltv,
                    ltv_ratio
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.nav_facilities`
                WHERE facility_id = '{facility_id}'
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": False, "error": f"Facility {facility_id} not found"}
            
            facility = results[0]
            
            # Check existing compliance record
            check_query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.ilpa_compliance_checks`
                WHERE facility_id = '{facility_id}'
                ORDER BY check_date DESC
                LIMIT 1
            """
            
            check_results = self.bq.execute_query(check_query)
            
            if check_results:
                # Return existing compliance check
                check = check_results[0]
                return {
                    "success": True,
                    "facility_id": facility_id,
                    "fund_name": facility.get("fund_name"),
                    "compliance_score": check.get("compliance_score", 0),
                    "is_compliant": check.get("compliance_score", 0) >= 80,
                    "check_date": str(check.get("check_date")),
                    "requirements": {
                        "lpa_addresses_nav": check.get("lpa_addresses_nav_facilities", False),
                        "leverage_limits_defined": check.get("leverage_limits_defined", False),
                        "lpac_consent_required": check.get("lpac_consent_required", True),
                        "lpac_consent_obtained": check.get("lpac_consent_obtained", False),
                        "rationale_disclosed": check.get("rationale_disclosed", False),
                        "size_disclosed": check.get("size_disclosed", False),
                        "structure_disclosed": check.get("structure_disclosed", False),
                        "economic_terms_disclosed": check.get("economic_terms_disclosed", False),
                        "initial_ltv_disclosed": check.get("initial_ltv_disclosed", False),
                        "distribution_consent": check.get("distribution_consent_obtained", False),
                    },
                    "issues": check.get("issues_found"),
                    "recommendations": check.get("recommendations"),
                    "source": "BigQuery"
                }
            else:
                # Generate new compliance assessment based on facility data
                return self._assess_facility_compliance(facility)
            
        except Exception as e:
            logger.error(f"ILPA compliance check error: {e}")
            return {"success": False, "error": str(e)}
    
    def _assess_facility_compliance(self, facility: Dict[str, Any]) -> Dict[str, Any]:
        """Assess ILPA compliance based on facility data."""
        requirements = {}
        issues = []
        recommendations = []
        score = 0
        
        # Check LPA provisions
        lpa_permits = facility.get("lpa_explicitly_permits", False)
        requirements["lpa_addresses_nav"] = lpa_permits
        if lpa_permits:
            score += self.ILPA_REQUIREMENTS["lpa_addresses_nav"]["weight"]
        else:
            issues.append("LPA does not explicitly address NAV-based facilities")
            recommendations.append("Consider LPA amendment to explicitly permit NAV facilities")
        
        # Assume leverage limits defined if LPA permits
        requirements["leverage_limits_defined"] = lpa_permits
        if lpa_permits:
            score += self.ILPA_REQUIREMENTS["leverage_limits_defined"]["weight"]
        
        # LPAC consent requirement
        requirements["lpac_consent_required"] = True  # Always required per ILPA
        
        # LPAC consent obtained
        lpac_obtained = facility.get("lpac_consent_obtained", False)
        requirements["lpac_consent_obtained"] = lpac_obtained
        if lpac_obtained:
            score += self.ILPA_REQUIREMENTS["lpac_consent_obtained"]["weight"]
            score += self.ILPA_REQUIREMENTS["lpac_consent_required"]["weight"]
        else:
            issues.append("LPAC consent not obtained")
            recommendations.append("Obtain LPAC consent before drawing on NAV facility")
        
        # Disclosure requirements - assume disclosed if LPAC consent obtained
        for disclosure in ["rationale_disclosed", "size_disclosed", "structure_disclosed", 
                          "economic_terms_disclosed", "initial_ltv_disclosed"]:
            requirements[disclosure] = lpac_obtained
            if lpac_obtained:
                score += self.ILPA_REQUIREMENTS[disclosure]["weight"]
        
        if not lpac_obtained:
            issues.append("Required disclosures may not have been made")
            recommendations.append("Provide standardized NAV facility disclosures to LPs")
        
        # Distribution consent
        use_of_proceeds = facility.get("use_of_proceeds", "")
        is_distribution = "distribution" in (use_of_proceeds or "").lower()
        if is_distribution:
            distribution_consent = lpac_obtained  # Assume same as LPAC consent
            requirements["distribution_consent"] = distribution_consent
            if distribution_consent:
                score += self.ILPA_REQUIREMENTS["distribution_consent"]["weight"]
            else:
                issues.append("NAV facility used for distributions without proper consent")
                recommendations.append("Obtain explicit LPAC consent for distribution-related borrowing")
        else:
            requirements["distribution_consent"] = True  # N/A
            score += self.ILPA_REQUIREMENTS["distribution_consent"]["weight"]
        
        return {
            "success": True,
            "facility_id": facility.get("facility_id"),
            "fund_name": facility.get("fund_name"),
            "compliance_score": score,
            "is_compliant": score >= 80,
            "check_date": str(date.today()),
            "requirements": requirements,
            "issues": "; ".join(issues) if issues else None,
            "recommendations": "; ".join(recommendations) if recommendations else None,
            "use_of_proceeds": use_of_proceeds,
            "source": "Calculated"
        }
    
    def save_compliance_check(
        self, 
        facility_id: str, 
        compliance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save ILPA compliance check to BigQuery.
        
        Args:
            facility_id: NAV facility identifier
            compliance_data: Compliance check results
            
        Returns:
            Save result
        """
        try:
            check_id = f"ILPA-{facility_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Get fund_id from facility
            fac_query = f"""
                SELECT fund_id
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.nav_facilities`
                WHERE facility_id = '{facility_id}'
            """
            fac_results = self.bq.execute_query(fac_query)
            fund_id = fac_results[0].get("fund_id", "") if fac_results else ""
            
            requirements = compliance_data.get("requirements", {})
            
            query = f"""
                INSERT INTO `{self.bq.project_id}.{self.bq.dataset_id}.ilpa_compliance_checks`
                (check_id, facility_id, fund_id, check_date,
                 lpa_addresses_nav_facilities, leverage_limits_defined,
                 lpac_consent_required, lpac_consent_obtained,
                 rationale_disclosed, size_disclosed, structure_disclosed,
                 economic_terms_disclosed, initial_ltv_disclosed,
                 use_for_distributions, distribution_consent_obtained,
                 compliance_score, issues_found, recommendations, created_at)
                VALUES (
                    '{check_id}',
                    '{facility_id}',
                    '{fund_id}',
                    CURRENT_DATE(),
                    {str(requirements.get("lpa_addresses_nav", False)).upper()},
                    {str(requirements.get("leverage_limits_defined", False)).upper()},
                    {str(requirements.get("lpac_consent_required", True)).upper()},
                    {str(requirements.get("lpac_consent_obtained", False)).upper()},
                    {str(requirements.get("rationale_disclosed", False)).upper()},
                    {str(requirements.get("size_disclosed", False)).upper()},
                    {str(requirements.get("structure_disclosed", False)).upper()},
                    {str(requirements.get("economic_terms_disclosed", False)).upper()},
                    {str(requirements.get("initial_ltv_disclosed", False)).upper()},
                    {str(compliance_data.get("use_of_proceeds", "").lower() == "distribution").upper()},
                    {str(requirements.get("distribution_consent", False)).upper()},
                    {compliance_data.get("compliance_score", 0)},
                    {f"'{compliance_data.get('issues', '')[:500]}'" if compliance_data.get("issues") else "NULL"},
                    {f"'{compliance_data.get('recommendations', '')[:500]}'" if compliance_data.get("recommendations") else "NULL"},
                    CURRENT_TIMESTAMP()
                )
            """
            
            self.bq.execute_query(query)
            
            return {
                "success": True,
                "check_id": check_id,
                "message": "ILPA compliance check saved"
            }
            
        except Exception as e:
            logger.error(f"Failed to save compliance check: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_ilpa_compliance(
        self,
        facility_id: str = None,
        facility_data: Dict[str, Any] = None,
        save_result: bool = True,
    ) -> Dict[str, Any]:
        """
        Full ILPA compliance validation workflow.
        
        Args:
            facility_id: NAV facility ID (to fetch from DB)
            facility_data: Or direct facility data
            save_result: Whether to save compliance check to DB
            
        Returns:
            Compliance validation result
        """
        try:
            if facility_id:
                result = self.check_compliance(facility_id)
            elif facility_data:
                result = self._assess_facility_compliance(facility_data)
            else:
                return {"success": False, "error": "facility_id or facility_data required"}
            
            if result.get("success") and save_result and facility_id:
                self.save_compliance_check(facility_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"ILPA validation error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_ilpa_compliance: Optional[ILPAComplianceAgent] = None


def get_ilpa_compliance_agent() -> ILPAComplianceAgent:
    """Get or create ILPA Compliance singleton."""
    global _ilpa_compliance
    if _ilpa_compliance is None:
        _ilpa_compliance = ILPAComplianceAgent()
    return _ilpa_compliance


# Convenience functions
def check_ilpa_compliance(facility_id: str) -> Dict[str, Any]:
    """Check ILPA compliance for a NAV facility."""
    return get_ilpa_compliance_agent().check_compliance(facility_id)


def validate_ilpa_compliance(
    facility_id: str = None,
    facility_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Full ILPA compliance validation."""
    return get_ilpa_compliance_agent().validate_ilpa_compliance(facility_id, facility_data)
