"""
Risk Committee Configuration - Production Level.

Centralized configuration for all thresholds, scenarios, and parameters.
No hardcoded values in agent code - all configurable here.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CreditRiskThresholds:
    """Thresholds for credit risk voting decisions."""
    pd_approve_max: float = 0.10      # PD < 10% = APPROVE
    pd_caution_max: float = 0.20      # PD < 20% = CAUTION
    pd_refer_max: float = 0.35        # PD < 35% = REFER
    # PD >= 35% = DECLINE
    
    confidence_approve: float = 0.85
    confidence_caution: float = 0.75
    confidence_refer: float = 0.70
    confidence_decline: float = 0.80


@dataclass
class ESGRiskThresholds:
    """Thresholds for ESG risk voting decisions."""
    esg_caution_high: float = 70      # ESG >= 70 = CAUTION (high confidence)
    esg_caution_medium: float = 50    # ESG >= 50 = CAUTION (lower confidence)
    # ESG < 50 = APPROVE
    
    confidence_caution_high: float = 0.80
    confidence_caution_medium: float = 0.70
    confidence_approve: float = 0.85


@dataclass 
class MarketContextThresholds:
    """Thresholds for market context voting decisions."""
    rate_spread_caution: float = 1.5       # Spread > 1.5% = CAUTION
    fed_funds_high: float = 4.0            # Fed > 4.0% = high rate environment
    transition_risk_sensitive: float = 0.6 # Transition risk > 60% = rate sensitive
    
    # Rate-sensitive sectors (hardcoded is OK here - this IS the config)
    rate_sensitive_sectors: List[str] = None
    
    confidence_caution: float = 0.70
    confidence_caution_sector: float = 0.65
    confidence_approve: float = 0.75
    confidence_refer: float = 0.60
    
    def __post_init__(self):
        if self.rate_sensitive_sectors is None:
            self.rate_sensitive_sectors = ["real_estate", "financial_services"]


@dataclass
class StressScenarios:
    """Stress testing scenarios for Devil's Advocate."""
    # Stress multipliers for PD
    mild_stress: float = 1.25        # 25% stress
    moderate_stress: float = 1.50    # 50% stress (default)
    severe_stress: float = 2.00      # 100% stress
    
    # Default stress level
    default_stress_multiplier: float = 1.50
    
    # Thresholds for challenges
    stress_pd_concern: float = 0.20  # Stress PD > 20% = concern
    esg_concern: float = 60          # ESG > 60 = concern
    large_exposure: float = 5000000  # Amount > $5M = large exposure
    
    confidence_strong: float = 0.70
    confidence_moderate: float = 0.60


@dataclass
class SynthesizerThresholds:
    """Thresholds for final decision synthesis."""
    decline_votes_threshold: int = 2   # 2+ decline = DECLINE
    approve_votes_strong: int = 3      # 3+ approve = APPROVE
    approve_votes_weak: int = 2        # 2+ approve (no decline) = APPROVE
    caution_votes_threshold: int = 2   # 2+ caution = CAUTION


@dataclass
class DebateConfig:
    """Configuration for multi-round agent debate."""
    # Debate rounds
    max_rounds: int = 2               # Maximum debate rounds
    min_rounds: int = 1               # Minimum rounds before convergence
    
    # Convergence thresholds
    consensus_threshold: float = 0.75  # 75% agreement = consensus
    confidence_improvement_min: float = 0.05  # Min confidence gain to continue
    
    # Agent behavior
    allow_vote_changes: bool = True   # Agents can change votes between rounds
    require_justification: bool = True  # Agents must explain vote changes


# Singleton configuration instances
CREDIT_RISK_CONFIG = CreditRiskThresholds()
ESG_RISK_CONFIG = ESGRiskThresholds()
MARKET_CONTEXT_CONFIG = MarketContextThresholds()
STRESS_SCENARIOS = StressScenarios()
SYNTHESIZER_CONFIG = SynthesizerThresholds()
DEBATE_CONFIG = DebateConfig()


# Validation requirements for loan applications
@dataclass
class LoanValidationRequirements:
    """Required fields for production-level loan assessment."""
    # Required fields (cannot be None/empty)
    required_fields: List[str] = None
    
    # Optional fields with documented defaults
    optional_with_defaults: Dict[str, any] = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = [
                "loan_id",
                "borrower_name", 
                "sector",
                "amount",
                "credit_score",
            ]
        if self.optional_with_defaults is None:
            self.optional_with_defaults = {
                "term_months": 60,
                "interest_rate": 0.05,
                "collateral_value": 0.0,
                "existing_debt": 0.0,
                "annual_revenue": 100000,  # Default for individuals
                "location": "United States",
                "employment_length": "5 years",
                "home_ownership": "RENT",
            }


LOAN_VALIDATION = LoanValidationRequirements()


def validate_loan_application(loan_data: dict) -> None:
    """
    Validate loan application has all required fields.
    Raises ValueError if validation fails.
    """
    missing = []
    for field in LOAN_VALIDATION.required_fields:
        if field not in loan_data or loan_data[field] is None:
            missing.append(field)
    
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
