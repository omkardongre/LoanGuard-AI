"""
ESG Financial Risk Scorer - ESG as Financial Risk Factor.

Implements EBA 2026 requirement to treat ESG as a financial risk factor.
Integrates ESG risk into credit risk assessment and ECL calculation.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .esg_materiality_data import (
    get_sector_materiality,
    calculate_sector_esg_risk_score,
    get_climate_scenario_impact,
    CLIMATE_SCENARIO_IMPACTS,
    ESGPillar,
    RiskSeverity,
)

logger = logging.getLogger(__name__)


class ESGRiskCategory(Enum):
    """ESG risk categories for credit assessment."""
    TRANSITION = "transition"  # Policy, technology, market changes
    PHYSICAL = "physical"       # Acute (events) and chronic (trends)
    REPUTATIONAL = "reputational"  # ESG controversies
    REGULATORY = "regulatory"   # ESG regulation compliance


@dataclass
class ESGFinancialRiskResult:
    """Result of ESG financial risk assessment."""
    loan_id: str
    borrower_name: str
    sector: str
    assessment_date: datetime
    
    # Risk scores (0-100 scale)
    esg_financial_risk_score: float  # Combined ESG → credit risk
    transition_risk_score: float
    physical_risk_score: float
    reputational_risk_score: float
    regulatory_risk_score: float
    
    # Credit impact
    pd_adjustment: float  # Percentage adjustment to base PD
    lgd_adjustment: float  # Percentage adjustment to base LGD
    ecl_impact_percent: float  # Expected ECL increase due to ESG
    
    # Details
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    climate_scenario: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "loan_id": self.loan_id,
            "borrower_name": self.borrower_name,
            "sector": self.sector,
            "assessment_date": self.assessment_date.isoformat(),
            "esg_financial_risk_score": round(self.esg_financial_risk_score, 2),
            "transition_risk_score": round(self.transition_risk_score, 2),
            "physical_risk_score": round(self.physical_risk_score, 2),
            "reputational_risk_score": round(self.reputational_risk_score, 2),
            "regulatory_risk_score": round(self.regulatory_risk_score, 2),
            "pd_adjustment": round(self.pd_adjustment, 4),
            "lgd_adjustment": round(self.lgd_adjustment, 4),
            "ecl_impact_percent": round(self.ecl_impact_percent, 2),
            "risk_factors": self.risk_factors,
            "recommendations": self.recommendations,
            "evidence": self.evidence,
            "climate_scenario": self.climate_scenario,
        }


class ESGFinancialRiskScorer:
    """
    ESG Financial Risk Scorer.
    
    Calculates ESG impact on credit risk per EBA 2026 guidelines:
    - Transition risk (policy, technology, market)
    - Physical risk (acute events, chronic changes)
    - Reputational risk (controversies, greenwashing)
    - Regulatory risk (ESG compliance)
    """
    
    # Risk weight mappings for ESG → PD/LGD adjustments
    ESG_PD_IMPACT_TABLE = {
        # ESG risk score thresholds → PD multiplier
        (0, 20): 0.95,    # Low ESG risk → slight PD reduction
        (20, 40): 1.0,    # Moderate → no change
        (40, 60): 1.10,   # Elevated → 10% PD increase
        (60, 80): 1.25,   # High → 25% PD increase
        (80, 100): 1.50,  # Critical → 50% PD increase
    }
    
    ESG_LGD_IMPACT_TABLE = {
        # ESG risk score thresholds → LGD impact (absolute bps)
        (0, 20): -0.02,   # Low ESG risk → 2% LGD reduction
        (20, 40): 0.0,    # Moderate → no change
        (40, 60): 0.03,   # Elevated → 3% LGD increase
        (60, 80): 0.08,   # High → 8% LGD increase
        (80, 100): 0.15,  # Critical → 15% LGD increase
    }
    
    def __init__(self):
        """Initialize the ESG Financial Risk Scorer."""
        pass
    
    def assess_loan_esg_risk(
        self,
        loan_data: Dict[str, Any],
        borrower_esg_data: Optional[Dict[str, Any]] = None,
        climate_scenario: str = "current_policies",
    ) -> ESGFinancialRiskResult:
        """
        Assess ESG financial risk for a loan.
        
        Args:
            loan_data: Loan information including borrower, sector, amount
            borrower_esg_data: Optional borrower-specific ESG scores
            climate_scenario: NGFS climate scenario ID
            
        Returns:
            ESGFinancialRiskResult with risk scores and credit adjustments
        """
        loan_id = loan_data.get("loan_id", loan_data.get("id", "unknown"))
        borrower_name = loan_data.get("borrower_name", loan_data.get("borrower", "Unknown"))
        sector = self._normalize_sector(loan_data.get("sector", loan_data.get("industry", "manufacturing")))
        
        # Get sector materiality
        sector_risk = calculate_sector_esg_risk_score(sector)
        
        # Get climate scenario impact
        scenario_impact = get_climate_scenario_impact(sector, climate_scenario)
        
        # Calculate component scores
        transition_score = self._calculate_transition_risk(
            sector_risk, 
            scenario_impact, 
            borrower_esg_data
        )
        physical_score = self._calculate_physical_risk(
            sector_risk, 
            scenario_impact, 
            loan_data
        )
        reputational_score = self._calculate_reputational_risk(
            borrower_esg_data,
            loan_data
        )
        regulatory_score = self._calculate_regulatory_risk(
            sector_risk,
            borrower_esg_data
        )
        
        # Combined ESG financial risk score (weighted)
        esg_financial_risk = (
            transition_score * 0.35 +
            physical_score * 0.30 +
            reputational_score * 0.20 +
            regulatory_score * 0.15
        )
        
        # Calculate credit adjustments
        pd_adjustment = self._get_pd_adjustment(esg_financial_risk)
        lgd_adjustment = self._get_lgd_adjustment(esg_financial_risk)
        
        # Estimate ECL impact (simplified)
        ecl_impact = ((pd_adjustment - 1.0) + lgd_adjustment) * 100
        
        # Generate risk factors and recommendations
        risk_factors = self._identify_risk_factors(
            sector_risk, 
            transition_score, 
            physical_score
        )
        recommendations = self._generate_recommendations(
            esg_financial_risk, 
            risk_factors
        )
        evidence = self._compile_evidence(
            sector_risk, 
            scenario_impact, 
            borrower_esg_data
        )
        
        return ESGFinancialRiskResult(
            loan_id=loan_id,
            borrower_name=borrower_name,
            sector=sector,
            assessment_date=datetime.now(timezone.utc),
            esg_financial_risk_score=esg_financial_risk,
            transition_risk_score=transition_score,
            physical_risk_score=physical_score,
            reputational_risk_score=reputational_score,
            regulatory_risk_score=regulatory_score,
            pd_adjustment=pd_adjustment,
            lgd_adjustment=lgd_adjustment,
            ecl_impact_percent=ecl_impact,
            risk_factors=risk_factors,
            recommendations=recommendations,
            evidence=evidence,
            climate_scenario=climate_scenario,
        )
    
    def _normalize_sector(self, sector: str) -> str:
        """Normalize sector name to match materiality data."""
        if not sector:
            return "manufacturing"
        
        sector_lower = sector.lower()
        
        # Common mappings
        mappings = {
            "oil": "energy",
            "gas": "energy",
            "petroleum": "energy",
            "utilities": "energy",
            "construction": "real_estate",
            "property": "real_estate",
            "software": "technology",
            "it": "technology",
            "tech": "technology",
            "pharma": "healthcare",
            "medical": "healthcare",
            "bank": "financial_services",
            "insurance": "financial_services",
            "finance": "financial_services",
            "food": "agriculture",
            "farming": "agriculture",
            "consumer": "retail",
            "industrial": "manufacturing",
        }
        
        for key, value in mappings.items():
            if key in sector_lower:
                return value
        
        return sector_lower.replace(" ", "_").replace("-", "_")
    
    def _calculate_transition_risk(
        self,
        sector_risk: Dict[str, Any],
        scenario_impact: Dict[str, Any],
        borrower_esg_data: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate transition risk score."""
        base_transition = sector_risk.get("transition_risk_exposure", 0.5) * 100
        
        # Adjust for scenario
        if "adjusted_transition_risk" in scenario_impact:
            base_transition = scenario_impact["adjusted_transition_risk"] * 100
        
        # Adjust for borrower-specific data
        if borrower_esg_data:
            env_score = borrower_esg_data.get("environmental_score", 50)
            # Better ESG score reduces transition risk
            adjustment = (50 - env_score) / 100 * 20  # ±20% max adjustment
            base_transition = max(0, min(100, base_transition + adjustment))
        
        return base_transition
    
    def _calculate_physical_risk(
        self,
        sector_risk: Dict[str, Any],
        scenario_impact: Dict[str, Any],
        loan_data: Dict[str, Any]
    ) -> float:
        """Calculate physical climate risk score."""
        base_physical = sector_risk.get("physical_risk_exposure", 0.5) * 100
        
        # Adjust for scenario
        if "adjusted_physical_risk" in scenario_impact:
            base_physical = scenario_impact["adjusted_physical_risk"] * 100
        
        # Adjust for location (if available)
        location = loan_data.get("location", loan_data.get("state", ""))
        high_risk_locations = ["FL", "TX", "LA", "CA", "Miami", "Houston", "New Orleans"]
        
        if any(loc in location for loc in high_risk_locations):
            base_physical = min(100, base_physical * 1.2)
        
        return base_physical
    
    def _calculate_reputational_risk(
        self,
        borrower_esg_data: Optional[Dict[str, Any]],
        loan_data: Dict[str, Any]
    ) -> float:
        """Calculate reputational risk from ESG controversies."""
        base_reputational = 30.0  # Default moderate
        
        if borrower_esg_data:
            # Check for greenwashing flags
            if borrower_esg_data.get("greenwashing_risk", False):
                base_reputational = 80.0
            
            # Check for controversies
            controversies = borrower_esg_data.get("controversies", [])
            if controversies:
                base_reputational = min(100, 30 + len(controversies) * 15)
            
            # Social score impact
            social_score = borrower_esg_data.get("social_score", 50)
            if social_score < 40:
                base_reputational = min(100, base_reputational + 20)
        
        return base_reputational
    
    def _calculate_regulatory_risk(
        self,
        sector_risk: Dict[str, Any],
        borrower_esg_data: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate ESG regulatory compliance risk."""
        base_regulatory = 40.0  # Default moderate
        
        # High emission sectors face more regulatory pressure
        if sector_risk.get("transition_risk_exposure", 0) > 0.7:
            base_regulatory = 60.0
        
        if borrower_esg_data:
            # Governance score impact
            gov_score = borrower_esg_data.get("governance_score", 50)
            if gov_score < 40:
                base_regulatory = min(100, base_regulatory + 25)
            elif gov_score > 70:
                base_regulatory = max(0, base_regulatory - 15)
            
            # ESG disclosure quality
            if borrower_esg_data.get("has_esg_report", False):
                base_regulatory = max(0, base_regulatory - 10)
        
        return base_regulatory
    
    def _get_pd_adjustment(self, esg_risk_score: float) -> float:
        """Get PD multiplier based on ESG risk score."""
        for (low, high), multiplier in self.ESG_PD_IMPACT_TABLE.items():
            if low <= esg_risk_score < high:
                return multiplier
        return 1.50  # Default to highest if score >= 100
    
    def _get_lgd_adjustment(self, esg_risk_score: float) -> float:
        """Get LGD adjustment based on ESG risk score."""
        for (low, high), adjustment in self.ESG_LGD_IMPACT_TABLE.items():
            if low <= esg_risk_score < high:
                return adjustment
        return 0.15  # Default to highest if score >= 100
    
    def _identify_risk_factors(
        self,
        sector_risk: Dict[str, Any],
        transition_score: float,
        physical_score: float
    ) -> List[Dict[str, Any]]:
        """Identify key risk factors for the assessment."""
        factors = []
        
        if transition_score > 60:
            factors.append({
                "factor": "High Transition Risk",
                "severity": "high" if transition_score > 80 else "medium",
                "description": f"Sector exposed to climate transition policies ({transition_score:.0f}/100)",
                "category": "transition"
            })
        
        if physical_score > 60:
            factors.append({
                "factor": "Physical Climate Risk",
                "severity": "high" if physical_score > 80 else "medium",
                "description": f"Exposure to extreme weather and climate events ({physical_score:.0f}/100)",
                "category": "physical"
            })
        
        if sector_risk.get("environmental_score", 0) > 0.7:
            factors.append({
                "factor": "Environmental Materiality",
                "severity": "medium",
                "description": "Sector has significant environmental material issues",
                "category": "environmental"
            })
        
        return factors
    
    def _generate_recommendations(
        self,
        esg_risk_score: float,
        risk_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on risk assessment."""
        recommendations = []
        
        if esg_risk_score > 60:
            recommendations.append("Request detailed ESG disclosure and transition plan")
            recommendations.append("Consider ESG-linked covenant terms")
        
        if esg_risk_score > 80:
            recommendations.append("Require independent ESG verification")
            recommendations.append("Increase monitoring frequency")
        
        for factor in risk_factors:
            if factor["category"] == "transition" and factor["severity"] == "high":
                recommendations.append("Request net-zero transition roadmap")
            if factor["category"] == "physical":
                recommendations.append("Verify climate resilience measures")
        
        if not recommendations:
            recommendations.append("Standard ESG monitoring applies")
        
        return recommendations
    
    def _compile_evidence(
        self,
        sector_risk: Dict[str, Any],
        scenario_impact: Dict[str, Any],
        borrower_esg_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Compile evidence trail for the assessment."""
        evidence = []
        
        evidence.append(f"Sector: {sector_risk.get('sector', 'Unknown')}")
        evidence.append(f"Sector composite ESG risk: {sector_risk.get('composite_risk_score', 0):.2f}")
        
        if "scenario" in scenario_impact:
            evidence.append(f"Climate scenario: {scenario_impact['scenario']}")
        
        if borrower_esg_data:
            evidence.append(f"Borrower E score: {borrower_esg_data.get('environmental_score', 'N/A')}")
            evidence.append(f"Borrower S score: {borrower_esg_data.get('social_score', 'N/A')}")
            evidence.append(f"Borrower G score: {borrower_esg_data.get('governance_score', 'N/A')}")
        
        evidence.append("References: EBA ESG Guidelines 2026, NGFS Scenarios, TNFD Framework")
        
        return evidence


# Singleton instance
_esg_scorer: Optional[ESGFinancialRiskScorer] = None


def get_esg_financial_risk_scorer() -> ESGFinancialRiskScorer:
    """Get or create ESG Financial Risk Scorer instance."""
    global _esg_scorer
    if _esg_scorer is None:
        _esg_scorer = ESGFinancialRiskScorer()
    return _esg_scorer


# ADK-compatible tool functions

def assess_esg_financial_risk(
    loan_data: Dict[str, Any],
    borrower_esg_data: Optional[Dict[str, Any]] = None,
    climate_scenario: str = "current_policies"
) -> Dict[str, Any]:
    """
    Assess ESG financial risk for a loan (ADK tool function).
    
    Args:
        loan_data: Loan information
        borrower_esg_data: Optional borrower ESG scores
        climate_scenario: NGFS climate scenario
        
    Returns:
        ESG financial risk assessment result
    """
    scorer = get_esg_financial_risk_scorer()
    result = scorer.assess_loan_esg_risk(loan_data, borrower_esg_data, climate_scenario)
    return result.to_dict()


def assess_portfolio_esg_risk(
    loans: List[Dict[str, Any]],
    climate_scenario: str = "current_policies"
) -> Dict[str, Any]:
    """
    Assess ESG financial risk for a portfolio of loans.
    
    Args:
        loans: List of loan data dictionaries
        climate_scenario: NGFS climate scenario
        
    Returns:
        Portfolio-level ESG risk summary
    """
    scorer = get_esg_financial_risk_scorer()
    
    results = []
    total_exposure = 0.0
    weighted_esg_risk = 0.0
    total_ecl_impact = 0.0
    
    sector_breakdown = {}
    high_risk_loans = []
    
    for loan in loans:
        amount = float(loan.get("amount", loan.get("loan_amount", 0)))
        total_exposure += amount
        
        result = scorer.assess_loan_esg_risk(loan, None, climate_scenario)
        results.append(result.to_dict())
        
        # Weighted average
        weighted_esg_risk += result.esg_financial_risk_score * amount
        total_ecl_impact += result.ecl_impact_percent * amount
        
        # Sector breakdown
        sector = result.sector
        if sector not in sector_breakdown:
            sector_breakdown[sector] = {"exposure": 0, "avg_risk": 0, "count": 0}
        sector_breakdown[sector]["exposure"] += amount
        sector_breakdown[sector]["avg_risk"] += result.esg_financial_risk_score
        sector_breakdown[sector]["count"] += 1
        
        # Track high risk loans
        if result.esg_financial_risk_score > 60:
            high_risk_loans.append({
                "loan_id": result.loan_id,
                "borrower": result.borrower_name,
                "esg_risk": round(result.esg_financial_risk_score, 1),
                "ecl_impact": round(result.ecl_impact_percent, 2)
            })
    
    # Finalize sector breakdown
    for sector in sector_breakdown:
        sector_breakdown[sector]["avg_risk"] /= sector_breakdown[sector]["count"]
        sector_breakdown[sector]["avg_risk"] = round(sector_breakdown[sector]["avg_risk"], 1)
        sector_breakdown[sector]["exposure_pct"] = round(
            sector_breakdown[sector]["exposure"] / total_exposure * 100, 1
        ) if total_exposure > 0 else 0
    
    return {
        "portfolio_summary": {
            "total_loans": len(loans),
            "total_exposure": round(total_exposure, 2),
            "weighted_avg_esg_risk": round(weighted_esg_risk / total_exposure, 1) if total_exposure > 0 else 0,
            "total_ecl_impact_weighted": round(total_ecl_impact / total_exposure, 2) if total_exposure > 0 else 0,
            "high_risk_loan_count": len(high_risk_loans),
            "climate_scenario": climate_scenario,
        },
        "sector_breakdown": sector_breakdown,
        "high_risk_loans": high_risk_loans[:10],  # Top 10
        "individual_results": results[:20],  # Limit for API response
    }


def get_available_climate_scenarios() -> Dict[str, Any]:
    """Get available NGFS climate scenarios."""
    return {
        "scenarios": [
            {
                "id": k,
                "name": v["name"],
                "description": v["description"],
                "transition_multiplier": v["transition_risk_multiplier"],
                "physical_multiplier": v["physical_risk_multiplier"]
            }
            for k, v in CLIMATE_SCENARIO_IMPACTS.items()
        ]
    }
