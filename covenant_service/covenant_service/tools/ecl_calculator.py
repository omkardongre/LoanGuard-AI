"""
ECL (Expected Credit Loss) Calculator for IFRS 9 Compliance.
V9 NEW - Calculates ECL with proper staging logic.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import IntEnum
from datetime import datetime
import numpy as np


class IFRS9Stage(IntEnum):
    """IFRS 9 credit staging classification."""
    STAGE_1 = 1  # Performing - 12-month ECL
    STAGE_2 = 2  # Underperforming - Lifetime ECL
    STAGE_3 = 3  # Non-performing/Credit impaired - Lifetime ECL


@dataclass
class StagingCriteria:
    """Criteria for IFRS 9 stage classification."""
    # Stage 2 triggers
    days_past_due_stage2: int = 30
    pd_increase_threshold: float = 0.5  # 50% increase = significant
    rating_downgrade_notches: int = 2
    
    # Stage 3 triggers
    days_past_due_stage3: int = 90
    is_default_indicator: bool = True


@dataclass
class ECLResult:
    """Result of ECL calculation for a single loan."""
    loan_id: str
    stage: int
    stage_name: str
    
    # Input parameters
    pd_12m: float
    pd_lifetime: float
    lgd: float
    ead: float
    
    # ECL calculation
    ecl_amount: float
    ecl_pct_of_ead: float
    
    # Staging factors
    days_past_due: int = 0
    pd_increase_since_origination: float = 0.0
    is_defaulted: bool = False
    
    # Discount factor (present value)
    discount_rate: float = 0.0
    discount_factor: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "loan_id": self.loan_id,
            "stage": self.stage,
            "stage_name": self.stage_name,
            "parameters": {
                "pd_12m": round(self.pd_12m, 4),
                "pd_lifetime": round(self.pd_lifetime, 4),
                "lgd": round(self.lgd, 4),
                "ead": round(self.ead, 2),
            },
            "ecl": {
                "amount": round(self.ecl_amount, 2),
                "pct_of_ead": round(self.ecl_pct_of_ead, 2),
            },
            "staging_factors": {
                "days_past_due": self.days_past_due,
                "pd_increase_pct": round(self.pd_increase_since_origination * 100, 2),
                "is_defaulted": self.is_defaulted,
            },
        }


@dataclass
class PortfolioECLResult:
    """Aggregated ECL results for a portfolio."""
    calculation_date: str
    loan_count: int
    total_ead: float
    total_ecl: float
    ecl_coverage_ratio: float  # ECL as % of EAD
    
    # Stage breakdown
    stage_summary: Dict[int, Dict[str, Any]]
    
    # Sector breakdown
    sector_summary: Dict[str, Dict[str, Any]]
    
    # Individual results
    loan_results: List[ECLResult]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "calculation_date": self.calculation_date,
            "portfolio_summary": {
                "loan_count": self.loan_count,
                "total_ead": round(self.total_ead, 2),
                "total_ecl": round(self.total_ecl, 2),
                "ecl_coverage_ratio_pct": round(self.ecl_coverage_ratio, 2),
            },
            "stage_breakdown": self.stage_summary,
            "sector_breakdown": self.sector_summary,
            "loan_results": [r.to_dict() for r in self.loan_results[:100]],
        }


class ECLCalculator:
    """
    Production-level ECL calculator implementing IFRS 9 requirements.
    
    Key features:
    - Proper 3-stage classification
    - 12-month vs lifetime ECL based on stage
    - Sector and scenario adjustments
    - Portfolio aggregation
    """
    
    # Default parameters (can be overridden)
    DEFAULT_LGD = 0.45
    DEFAULT_DISCOUNT_RATE = 0.05
    LIFETIME_MULTIPLIER = 3.0  # Simplified: lifetime PD ≈ 3x 12-month PD
    
    def __init__(self, criteria: StagingCriteria = None):
        self.criteria = criteria or StagingCriteria()
        self.stage_names = {
            IFRS9Stage.STAGE_1: "Stage 1 (12-month ECL)",
            IFRS9Stage.STAGE_2: "Stage 2 (Lifetime ECL)",
            IFRS9Stage.STAGE_3: "Stage 3 (Credit Impaired)",
        }
    
    def determine_stage(self, loan: Dict[str, Any]) -> IFRS9Stage:
        """
        Determine IFRS 9 stage for a loan based on credit quality indicators.
        
        Stage 1: No significant increase in credit risk since origination
        Stage 2: Significant increase in credit risk (30+ DPD, rating downgrade, PD increase)
        Stage 3: Credit impaired (90+ DPD, default, or specific impairment)
        """
        days_past_due = loan.get("days_past_due", 0)
        is_defaulted = loan.get("is_defaulted", False)
        pd_increase = loan.get("pd_increase_since_origination", 0.0)
        rating_downgrade = loan.get("rating_downgrade_notches", 0)
        has_specific_impairment = loan.get("has_specific_impairment", False)
        
        # Stage 3 criteria (credit impaired)
        if (
            days_past_due >= self.criteria.days_past_due_stage3 or
            is_defaulted or
            has_specific_impairment
        ):
            return IFRS9Stage.STAGE_3
        
        # Stage 2 criteria (significant increase in credit risk)
        if (
            days_past_due >= self.criteria.days_past_due_stage2 or
            pd_increase >= self.criteria.pd_increase_threshold or
            rating_downgrade >= self.criteria.rating_downgrade_notches
        ):
            return IFRS9Stage.STAGE_2
        
        # Otherwise Stage 1 (performing)
        return IFRS9Stage.STAGE_1
    
    def estimate_lifetime_pd(self, pd_12m: float, remaining_term_years: float = 3.0) -> float:
        """
        Estimate lifetime PD from 12-month PD.
        
        Uses simplified approach: lifetime PD = 1 - (1 - pd_12m)^years
        Capped at 1.0
        """
        if pd_12m >= 1.0:
            return 1.0
        
        # Survival probability over remaining term
        survival_prob = (1 - pd_12m) ** remaining_term_years
        lifetime_pd = 1 - survival_prob
        
        return min(1.0, lifetime_pd)
    
    def calculate_discount_factor(
        self,
        discount_rate: float,
        years: float = 1.0
    ) -> float:
        """Calculate present value discount factor."""
        return 1 / ((1 + discount_rate) ** years)
    
    def calculate_ecl(self, loan: Dict[str, Any]) -> ECLResult:
        """
        Calculate Expected Credit Loss for a single loan.
        
        ECL = PD x LGD x EAD x Discount Factor
        
        Where PD is:
        - 12-month PD for Stage 1
        - Lifetime PD for Stage 2 and 3
        """
        loan_id = loan.get("loan_id", "unknown")
        
        # Get credit risk parameters
        pd_12m = loan.get("breach_probability", loan.get("pd_12m", loan.get("pd", 0.1)))
        lgd = loan.get("lgd", self.DEFAULT_LGD)
        ead = loan.get("facility_amount", loan.get("ead", 0))
        remaining_term_years = loan.get("remaining_term_years", 3.0)
        discount_rate = loan.get("discount_rate", self.DEFAULT_DISCOUNT_RATE)
        
        # Staging factors
        days_past_due = loan.get("days_past_due", 0)
        pd_increase = loan.get("pd_increase_since_origination", 0.0)
        is_defaulted = loan.get("is_defaulted", False)
        
        # Determine stage
        stage = self.determine_stage(loan)
        
        # Calculate lifetime PD
        pd_lifetime = self.estimate_lifetime_pd(pd_12m, remaining_term_years)
        
        # Select appropriate PD based on stage
        if stage == IFRS9Stage.STAGE_1:
            ecl_pd = pd_12m
        else:
            ecl_pd = pd_lifetime
        
        # Apply discount factor for long-term ECL
        if stage in (IFRS9Stage.STAGE_2, IFRS9Stage.STAGE_3):
            avg_time_to_default = remaining_term_years / 2  # Simplified
            discount_factor = self.calculate_discount_factor(discount_rate, avg_time_to_default)
        else:
            discount_factor = self.calculate_discount_factor(discount_rate, 0.5)  # 6-month avg
        
        # Calculate ECL
        ecl_amount = ecl_pd * lgd * ead * discount_factor
        ecl_pct_of_ead = (ecl_amount / ead * 100) if ead > 0 else 0
        
        return ECLResult(
            loan_id=loan_id,
            stage=int(stage),
            stage_name=self.stage_names[stage],
            pd_12m=pd_12m,
            pd_lifetime=pd_lifetime,
            lgd=lgd,
            ead=ead,
            ecl_amount=ecl_amount,
            ecl_pct_of_ead=ecl_pct_of_ead,
            days_past_due=days_past_due,
            pd_increase_since_origination=pd_increase,
            is_defaulted=is_defaulted,
            discount_rate=discount_rate,
            discount_factor=discount_factor,
        )
    
    def calculate_portfolio_ecl(
        self,
        loans: List[Dict[str, Any]],
    ) -> PortfolioECLResult:
        """
        Calculate ECL for entire loan portfolio with aggregations.
        """
        # Calculate individual ECLs
        loan_results = [self.calculate_ecl(loan) for loan in loans]
        
        # Aggregate totals
        total_ead = sum(r.ead for r in loan_results)
        total_ecl = sum(r.ecl_amount for r in loan_results)
        ecl_coverage_ratio = (total_ecl / total_ead * 100) if total_ead > 0 else 0
        
        # Stage breakdown
        stage_summary = {}
        for stage in IFRS9Stage:
            stage_loans = [r for r in loan_results if r.stage == stage]
            stage_ead = sum(r.ead for r in stage_loans)
            stage_ecl = sum(r.ecl_amount for r in stage_loans)
            stage_summary[int(stage)] = {
                "name": self.stage_names[stage],
                "loan_count": len(stage_loans),
                "total_ead": round(stage_ead, 2),
                "total_ecl": round(stage_ecl, 2),
                "ecl_coverage_pct": round(
                    (stage_ecl / stage_ead * 100) if stage_ead > 0 else 0, 2
                ),
                "pct_of_portfolio_ead": round(
                    (stage_ead / total_ead * 100) if total_ead > 0 else 0, 2
                ),
            }
        
        # Sector breakdown
        sector_summary = {}
        for r in loan_results:
            # Get sector from original loan data
            sector = loans[loan_results.index(r)].get("sector", "unclassified")
            if sector not in sector_summary:
                sector_summary[sector] = {
                    "loan_count": 0,
                    "total_ead": 0,
                    "total_ecl": 0,
                    "avg_pd": 0,
                    "pd_sum": 0,
                }
            sector_summary[sector]["loan_count"] += 1
            sector_summary[sector]["total_ead"] += r.ead
            sector_summary[sector]["total_ecl"] += r.ecl_amount
            sector_summary[sector]["pd_sum"] += r.pd_12m
        
        # Calculate sector averages
        for sector in sector_summary:
            count = sector_summary[sector]["loan_count"]
            ead = sector_summary[sector]["total_ead"]
            ecl = sector_summary[sector]["total_ecl"]
            sector_summary[sector]["avg_pd"] = round(
                sector_summary[sector]["pd_sum"] / count if count > 0 else 0, 4
            )
            sector_summary[sector]["ecl_coverage_pct"] = round(
                (ecl / ead * 100) if ead > 0 else 0, 2
            )
            sector_summary[sector]["total_ead"] = round(ead, 2)
            sector_summary[sector]["total_ecl"] = round(ecl, 2)
            del sector_summary[sector]["pd_sum"]
        
        return PortfolioECLResult(
            calculation_date=datetime.utcnow().isoformat(),
            loan_count=len(loans),
            total_ead=total_ead,
            total_ecl=total_ecl,
            ecl_coverage_ratio=ecl_coverage_ratio,
            stage_summary=stage_summary,
            sector_summary=sector_summary,
            loan_results=loan_results,
        )
    
    def calculate_stressed_ecl(
        self,
        loans: List[Dict[str, Any]],
        pd_multiplier: float = 1.0,
        lgd_multiplier: float = 1.0,
    ) -> PortfolioECLResult:
        """
        Calculate ECL under stressed conditions.
        
        Args:
            loans: Loan portfolio
            pd_multiplier: Stress multiplier for PD
            lgd_multiplier: Stress multiplier for LGD
        """
        # Apply stress to loans
        stressed_loans = []
        for loan in loans:
            stressed_loan = loan.copy()
            base_pd = loan.get("breach_probability", loan.get("pd_12m", loan.get("pd", 0.1)))
            base_lgd = loan.get("lgd", self.DEFAULT_LGD)
            
            stressed_loan["breach_probability"] = min(1.0, base_pd * pd_multiplier)
            stressed_loan["lgd"] = min(1.0, base_lgd * lgd_multiplier)
            
            # Stress may cause stage migration
            if pd_multiplier > 1.5:
                # Significant stress increases DPD proxy
                current_dpd = loan.get("days_past_due", 0)
                stressed_loan["days_past_due"] = max(current_dpd, 15)
            
            stressed_loans.append(stressed_loan)
        
        return self.calculate_portfolio_ecl(stressed_loans)


# Singleton instance
_ecl_calculator: Optional[ECLCalculator] = None


def get_ecl_calculator() -> ECLCalculator:
    """Get or create ECLCalculator singleton."""
    global _ecl_calculator
    if _ecl_calculator is None:
        _ecl_calculator = ECLCalculator()
    return _ecl_calculator
