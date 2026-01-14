"""
Stress Testing Engine for Basel III/IFRS 9 Compliance.
V9 NEW - Stress scenarios with economic and climate risk factors.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
import numpy as np
from datetime import datetime


class ScenarioType(str, Enum):
    """Types of stress scenarios."""
    ECONOMIC = "economic"
    CLIMATE_TRANSITION = "climate_transition"
    CLIMATE_PHYSICAL = "climate_physical"
    COMBINED = "combined"


@dataclass
class StressScenario:
    """
    Definition of a stress scenario with economic and climate parameters.
    Based on NGFS and Basel III standards.
    """
    id: str
    name: str
    description: str
    scenario_type: ScenarioType
    
    # Economic shocks (% change)
    gdp_shock: float = 0.0
    unemployment_shock: float = 0.0
    interest_rate_shock: float = 0.0
    inflation_shock: float = 0.0
    property_price_shock: float = 0.0
    
    # PD/LGD multipliers
    pd_multiplier: float = 1.0
    lgd_multiplier: float = 1.0
    
    # Climate-specific factors (for NGFS scenarios)
    carbon_price_2030: Optional[float] = None  # $/tCO2
    temperature_increase_2050: Optional[float] = None  # °C
    transition_risk_factor: float = 1.0
    physical_risk_factor: float = 1.0
    
    # Sector-specific PD adjustments
    sector_adjustments: Dict[str, float] = field(default_factory=dict)
    
    # Time horizon
    horizon_years: int = 1
    
    def get_adjusted_pd(self, base_pd: float, sector: str = None) -> float:
        """Calculate stressed PD with sector adjustment."""
        adjusted = min(1.0, base_pd * self.pd_multiplier * self.transition_risk_factor)
        if sector and sector in self.sector_adjustments:
            adjusted = min(1.0, adjusted * self.sector_adjustments[sector])
        return adjusted
    
    def get_adjusted_lgd(self, base_lgd: float, has_physical_exposure: bool = False) -> float:
        """Calculate stressed LGD with physical risk adjustment."""
        adjusted = min(1.0, base_lgd * self.lgd_multiplier)
        if has_physical_exposure:
            adjusted = min(1.0, adjusted * self.physical_risk_factor)
        return adjusted


# ============================================
# PREDEFINED SCENARIOS (Basel III + NGFS)
# ============================================

ECONOMIC_SCENARIOS = {
    "mild_recession": StressScenario(
        id="eco_mild",
        name="Mild Recession",
        description="Mild economic downturn with moderate credit deterioration",
        scenario_type=ScenarioType.ECONOMIC,
        gdp_shock=-0.01,  # -1%
        unemployment_shock=0.02,  # +2%
        interest_rate_shock=0.005,  # +0.5%
        inflation_shock=0.01,  # +1%
        property_price_shock=-0.05,  # -5%
        pd_multiplier=1.3,
        lgd_multiplier=1.1,
        sector_adjustments={
            "real_estate": 1.2,
            "retail": 1.15,
            "manufacturing": 1.1,
        },
        horizon_years=1
    ),
    
    "moderate_recession": StressScenario(
        id="eco_moderate",
        name="Moderate Recession",
        description="Significant economic contraction with credit stress",
        scenario_type=ScenarioType.ECONOMIC,
        gdp_shock=-0.03,  # -3%
        unemployment_shock=0.05,  # +5%
        interest_rate_shock=0.01,  # +1%
        inflation_shock=0.02,  # +2%
        property_price_shock=-0.15,  # -15%
        pd_multiplier=1.8,
        lgd_multiplier=1.2,
        sector_adjustments={
            "real_estate": 1.5,
            "retail": 1.4,
            "hospitality": 1.6,
            "manufacturing": 1.3,
        },
        horizon_years=2
    ),
    
    "severe_recession": StressScenario(
        id="eco_severe",
        name="Severe Recession",
        description="Deep recession with severe credit deterioration",
        scenario_type=ScenarioType.ECONOMIC,
        gdp_shock=-0.06,  # -6%
        unemployment_shock=0.10,  # +10%
        interest_rate_shock=0.02,  # +2%
        inflation_shock=0.03,  # +3%
        property_price_shock=-0.30,  # -30%
        pd_multiplier=2.5,
        lgd_multiplier=1.4,
        sector_adjustments={
            "real_estate": 2.0,
            "retail": 1.8,
            "hospitality": 2.2,
            "manufacturing": 1.6,
            "construction": 2.0,
        },
        horizon_years=3
    ),
    
    "crisis_2008": StressScenario(
        id="eco_2008",
        name="2008 Financial Crisis",
        description="Scenario calibrated to 2008-2009 financial crisis severity",
        scenario_type=ScenarioType.ECONOMIC,
        gdp_shock=-0.08,  # -8%
        unemployment_shock=0.12,  # +12%
        interest_rate_shock=0.03,  # +3%
        inflation_shock=0.04,  # +4%
        property_price_shock=-0.40,  # -40%
        pd_multiplier=3.0,
        lgd_multiplier=1.5,
        sector_adjustments={
            "real_estate": 2.5,
            "financial_services": 2.5,
            "retail": 2.0,
            "hospitality": 2.5,
            "manufacturing": 1.8,
            "construction": 2.5,
        },
        horizon_years=3
    ),
}


# NGFS Climate Scenarios (v5, November 2024)
# Source: https://www.ngfs.net/ngfs-scenarios-portal/
CLIMATE_SCENARIOS = {
    "ngfs_disorderly": StressScenario(
        id="climate_disorderly",
        name="NGFS Disorderly Transition",
        description="Delayed policy action leads to abrupt, disorderly transition. High transition risk.",
        scenario_type=ScenarioType.CLIMATE_TRANSITION,
        gdp_shock=-0.02,  # Transition costs
        unemployment_shock=0.03,
        interest_rate_shock=0.01,
        pd_multiplier=1.5,
        lgd_multiplier=1.15,
        carbon_price_2030=250,  # $/tCO2
        temperature_increase_2050=1.8,  # °C
        transition_risk_factor=1.4,
        physical_risk_factor=1.1,
        sector_adjustments={
            # High carbon intensity sectors face higher PD
            "oil_gas": 2.5,
            "utilities": 1.8,
            "mining": 2.0,
            "transportation": 1.6,
            "manufacturing": 1.4,
            "agriculture": 1.3,
            # Green sectors benefit
            "technology": 0.9,
            "renewable_energy": 0.8,
        },
        horizon_years=5
    ),
    
    "ngfs_hot_house": StressScenario(
        id="climate_hot_house",
        name="NGFS Hot House World",
        description="No climate policy, severe physical risks from unmitigated climate change.",
        scenario_type=ScenarioType.CLIMATE_PHYSICAL,
        gdp_shock=-0.04,  # Physical climate impacts
        unemployment_shock=0.04,
        property_price_shock=-0.20,  # Coastal/flood-prone areas
        pd_multiplier=1.6,
        lgd_multiplier=1.3,
        carbon_price_2030=0,  # No carbon pricing
        temperature_increase_2050=3.5,  # °C - severe warming
        transition_risk_factor=1.0,  # No transition
        physical_risk_factor=1.8,  # High physical risk
        sector_adjustments={
            # Physical risk exposure
            "agriculture": 2.0,
            "real_estate": 1.8,  # Coastal/flood exposure
            "insurance": 1.6,
            "tourism": 1.8,
            "infrastructure": 1.5,
            # Less affected
            "technology": 1.1,
            "healthcare": 1.1,
        },
        horizon_years=10
    ),
    
    "ngfs_net_zero_2050": StressScenario(
        id="climate_nz50",
        name="NGFS Net Zero 2050",
        description="Orderly transition to net zero by 2050. Moderate transition costs, limited physical risk.",
        scenario_type=ScenarioType.CLIMATE_TRANSITION,
        gdp_shock=-0.005,  # Manageable transition cost
        unemployment_shock=0.01,
        pd_multiplier=1.1,
        lgd_multiplier=1.05,
        carbon_price_2030=140,  # $/tCO2
        temperature_increase_2050=1.5,  # °C - Paris aligned
        transition_risk_factor=1.15,
        physical_risk_factor=1.05,
        sector_adjustments={
            "oil_gas": 1.8,
            "utilities": 1.3,
            "manufacturing": 1.1,
            "renewable_energy": 0.85,
            "technology": 0.95,
        },
        horizon_years=5
    ),
}


# NGFS Short-Term Scenarios (May 2025)
# Source: NGFS.net - First short-term climate scenarios released May 7, 2025
# 5-year horizon (2025-2030), designed for near-term financial stability assessment
NGFS_SHORT_TERM_SCENARIOS = {
    "ngfs_st_disasters": StressScenario(
        id="st_disasters_stagnation",
        name="Disasters & Policy Stagnation",
        description="Extreme weather events with no climate policy response. Physical risks dominate: droughts, floods, wildfires. Up to 12.5% GDP loss in Africa, 6% in Asia.",
        scenario_type=ScenarioType.CLIMATE_PHYSICAL,
        gdp_shock=-0.06,  # Regional up to -12.5%, global avg ~-6%
        unemployment_shock=0.04,
        property_price_shock=-0.15,  # Physical damage to assets
        pd_multiplier=1.8,
        lgd_multiplier=1.4,
        carbon_price_2030=0,  # No policy = no carbon price
        temperature_increase_2050=3.0,  # Continued warming
        transition_risk_factor=1.0,  # No transition
        physical_risk_factor=2.0,  # High physical risk from disasters
        sector_adjustments={
            "agriculture": 2.5,  # Extreme weather impact
            "real_estate": 2.0,  # Flood/fire damage
            "insurance": 1.8,
            "tourism": 2.0,
            "utilities": 1.5,  # Grid disruptions
            "transportation": 1.6,  # Supply chain disruptions
        },
        horizon_years=5  # 2025-2030
    ),
    
    "ngfs_st_highway_paris": StressScenario(
        id="st_highway_paris",
        name="Highway to Paris (Orderly)",
        description="Early, gradual introduction of ambitious climate policies. Minimal economic disruption: only 0.4% GDP loss by 2030. Orderly energy transition.",
        scenario_type=ScenarioType.CLIMATE_TRANSITION,
        gdp_shock=-0.004,  # Only -0.4% - orderly transition
        unemployment_shock=0.005,  # Minimal
        pd_multiplier=1.1,
        lgd_multiplier=1.05,
        carbon_price_2030=150,  # Gradual carbon pricing
        temperature_increase_2050=1.5,  # Paris-aligned
        transition_risk_factor=1.1,  # Manageable transition
        physical_risk_factor=1.05,  # Limited physical risk
        sector_adjustments={
            "oil_gas": 1.5,  # Managed decline
            "utilities": 1.2,
            "renewable_energy": 0.8,  # Benefits from policy
            "technology": 0.9,
            "manufacturing": 1.1,
        },
        horizon_years=5
    ),
    
    "ngfs_st_sudden_wakeup": StressScenario(
        id="st_sudden_wakeup",
        name="Sudden Wake-Up Call",
        description="3-year policy delay then abrupt pivot in 2027. Sharp carbon price spike, 1.3% GDP loss by 2030, +1.3pp unemployment. High transition stress.",
        scenario_type=ScenarioType.CLIMATE_TRANSITION,
        gdp_shock=-0.013,  # -1.3% by 2030
        unemployment_shock=0.013,  # +1.3pp
        inflation_shock=0.03,  # Carbon price spike causes inflation
        pd_multiplier=1.6,
        lgd_multiplier=1.25,
        carbon_price_2030=300,  # Sharp spike from policy pivot
        temperature_increase_2050=1.8,
        transition_risk_factor=1.5,  # High transition stress
        physical_risk_factor=1.1,
        sector_adjustments={
            "oil_gas": 2.8,  # Abrupt policy hits hardest
            "utilities": 2.0,
            "mining": 2.2,
            "transportation": 1.8,
            "manufacturing": 1.5,
            "agriculture": 1.3,
            "renewable_energy": 0.75,  # Strong benefit
        },
        horizon_years=5
    ),
    
    "ngfs_st_diverging": StressScenario(
        id="st_diverging_realities",
        name="Diverging Realities",
        description="Mixed global response: advanced economies push net-zero while others lag. Regional weather events + supply chain disruptions. Europe -1.7% GDP, N.America -0.8%.",
        scenario_type=ScenarioType.COMBINED,
        gdp_shock=-0.012,  # Regional variation: EU -1.7%, NA -0.8%
        unemployment_shock=0.02,
        interest_rate_shock=0.01,
        property_price_shock=-0.10,  # Regional physical impacts
        pd_multiplier=1.7,
        lgd_multiplier=1.3,
        carbon_price_2030=200,  # Only in advanced economies
        temperature_increase_2050=2.2,
        transition_risk_factor=1.35,  # Uneven transition
        physical_risk_factor=1.5,  # Regional disasters
        sector_adjustments={
            "oil_gas": 2.2,
            "agriculture": 2.0,  # Supply chain + weather
            "real_estate": 1.6,
            "utilities": 1.5,
            "mining": 2.0,  # Critical raw materials disruption
            "transportation": 1.7,
            "manufacturing": 1.4,
        },
        horizon_years=5
    ),
}


# Combined scenarios
COMBINED_SCENARIOS = {
    "climate_recession": StressScenario(
        id="combined_climate_recession",
        name="Climate-Triggered Recession",
        description="Economic recession triggered by climate policy shock combined with physical events.",
        scenario_type=ScenarioType.COMBINED,
        gdp_shock=-0.05,
        unemployment_shock=0.08,
        interest_rate_shock=0.015,
        property_price_shock=-0.25,
        pd_multiplier=2.2,
        lgd_multiplier=1.35,
        carbon_price_2030=200,
        temperature_increase_2050=2.0,
        transition_risk_factor=1.3,
        physical_risk_factor=1.4,
        sector_adjustments={
            "oil_gas": 3.0,
            "real_estate": 2.0,
            "agriculture": 2.2,
            "utilities": 1.8,
            "transportation": 1.7,
            "manufacturing": 1.5,
        },
        horizon_years=5
    ),
}


# All scenarios combined
ALL_SCENARIOS: Dict[str, StressScenario] = {
    **ECONOMIC_SCENARIOS,
    **CLIMATE_SCENARIOS,
    **NGFS_SHORT_TERM_SCENARIOS,  # NGFS Short-Term Scenarios (May 2025)
    **COMBINED_SCENARIOS,
}


def get_scenario(scenario_id: str) -> Optional[StressScenario]:
    """Get a scenario by ID."""
    return ALL_SCENARIOS.get(scenario_id)


def get_scenarios_by_type(scenario_type: ScenarioType) -> List[StressScenario]:
    """Get all scenarios of a specific type."""
    return [s for s in ALL_SCENARIOS.values() if s.scenario_type == scenario_type]


def list_all_scenarios() -> List[Dict[str, Any]]:
    """List all available scenarios with summary info."""
    return [
        {
            "id": s.id,
            "name": s.name,
            "type": s.scenario_type.value,
            "description": s.description,
            "pd_multiplier": s.pd_multiplier,
            "lgd_multiplier": s.lgd_multiplier,
            "horizon_years": s.horizon_years,
        }
        for s in ALL_SCENARIOS.values()
    ]


@dataclass
class StressTestResult:
    """Result of a stress test on a single loan."""
    loan_id: str
    scenario_id: str
    scenario_name: str
    
    # Original values
    base_pd: float
    base_lgd: float
    ead: float
    
    # Stressed values
    stressed_pd: float
    stressed_lgd: float
    
    # ECL calculations
    base_ecl: float
    stressed_ecl: float
    ecl_increase: float
    ecl_increase_pct: float
    
    # Additional info
    sector: Optional[str] = None
    has_physical_exposure: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "loan_id": self.loan_id,
            "scenario": {"id": self.scenario_id, "name": self.scenario_name},
            "base": {"pd": self.base_pd, "lgd": self.base_lgd, "ead": self.ead},
            "stressed": {"pd": self.stressed_pd, "lgd": self.stressed_lgd},
            "ecl": {
                "base": round(self.base_ecl, 2),
                "stressed": round(self.stressed_ecl, 2),
                "increase": round(self.ecl_increase, 2),
                "increase_pct": round(self.ecl_increase_pct, 2),
            },
        }


@dataclass
class PortfolioStressTestResult:
    """Aggregated stress test results for a portfolio."""
    scenario_id: str
    scenario_name: str
    scenario_type: str
    run_timestamp: str
    
    # Portfolio summary
    loan_count: int
    total_ead: float
    
    # ECL summary
    base_ecl_total: float
    stressed_ecl_total: float
    ecl_increase_total: float
    ecl_increase_pct: float
    
    # Breakdown
    loans_with_increased_risk: int
    avg_pd_increase_pct: float
    max_ecl_increase_pct: float
    
    # Sector breakdown
    sector_impacts: Dict[str, Dict[str, float]]
    
    # Individual results
    loan_results: List[StressTestResult]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario": {
                "id": self.scenario_id,
                "name": self.scenario_name,
                "type": self.scenario_type,
            },
            "run_timestamp": self.run_timestamp,
            "portfolio_summary": {
                "loan_count": self.loan_count,
                "total_ead": round(self.total_ead, 2),
            },
            "ecl_summary": {
                "base_ecl_total": round(self.base_ecl_total, 2),
                "stressed_ecl_total": round(self.stressed_ecl_total, 2),
                "ecl_increase_total": round(self.ecl_increase_total, 2),
                "ecl_increase_pct": round(self.ecl_increase_pct, 2),
            },
            "risk_metrics": {
                "loans_with_increased_risk": self.loans_with_increased_risk,
                "avg_pd_increase_pct": round(self.avg_pd_increase_pct, 2),
                "max_ecl_increase_pct": round(self.max_ecl_increase_pct, 2),
            },
            "sector_impacts": self.sector_impacts,
            "loan_results": [r.to_dict() for r in self.loan_results[:50]],  # Limit for API
        }


class StressTester:
    """
    Production-level stress testing engine for loan portfolios.
    Implements Basel III and NGFS climate scenarios.
    """
    
    def __init__(self):
        # Create lookup by both dict key and scenario.id
        self.scenarios = {}
        for key, scenario in ALL_SCENARIOS.items():
            self.scenarios[key] = scenario
            self.scenarios[scenario.id] = scenario  # Also index by ID
    
    def stress_test_loan(
        self,
        loan: Dict[str, Any],
        scenario: StressScenario,
    ) -> StressTestResult:
        """
        Run stress test on a single loan.
        
        Args:
            loan: Loan data with breach_probability, lgd, facility_amount, etc.
            scenario: Stress scenario to apply
            
        Returns:
            StressTestResult with base and stressed values
        """
        # Extract loan data
        loan_id = loan.get("loan_id", "unknown")
        base_pd = loan.get("breach_probability", loan.get("pd", 0.1))
        base_lgd = loan.get("lgd", 0.45)
        ead = loan.get("facility_amount", loan.get("ead", 0))
        sector = loan.get("sector", loan.get("industry", None))
        has_physical_exposure = loan.get("has_physical_exposure", False)
        
        # Apply stress multipliers
        stressed_pd = scenario.get_adjusted_pd(base_pd, sector)
        stressed_lgd = scenario.get_adjusted_lgd(base_lgd, has_physical_exposure)
        
        # Calculate ECL
        base_ecl = base_pd * base_lgd * ead
        stressed_ecl = stressed_pd * stressed_lgd * ead
        ecl_increase = stressed_ecl - base_ecl
        ecl_increase_pct = (ecl_increase / base_ecl * 100) if base_ecl > 0 else 0
        
        return StressTestResult(
            loan_id=loan_id,
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            base_pd=base_pd,
            base_lgd=base_lgd,
            ead=ead,
            stressed_pd=stressed_pd,
            stressed_lgd=stressed_lgd,
            base_ecl=base_ecl,
            stressed_ecl=stressed_ecl,
            ecl_increase=ecl_increase,
            ecl_increase_pct=ecl_increase_pct,
            sector=sector,
            has_physical_exposure=has_physical_exposure,
        )
    
    def stress_test_portfolio(
        self,
        loans: List[Dict[str, Any]],
        scenario_id: str,
    ) -> PortfolioStressTestResult:
        """
        Run stress test on entire loan portfolio.
        
        Args:
            loans: List of loan dictionaries
            scenario_id: ID of scenario to apply
            
        Returns:
            PortfolioStressTestResult with aggregated results
        """
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")
        
        # Run individual loan tests
        loan_results = [self.stress_test_loan(loan, scenario) for loan in loans]
        
        # Aggregate results
        total_ead = sum(r.ead for r in loan_results)
        base_ecl_total = sum(r.base_ecl for r in loan_results)
        stressed_ecl_total = sum(r.stressed_ecl for r in loan_results)
        ecl_increase_total = stressed_ecl_total - base_ecl_total
        ecl_increase_pct = (ecl_increase_total / base_ecl_total * 100) if base_ecl_total > 0 else 0
        
        # Risk metrics
        loans_with_increased_risk = sum(1 for r in loan_results if r.stressed_pd > r.base_pd)
        pd_increases = [(r.stressed_pd - r.base_pd) / r.base_pd * 100 for r in loan_results if r.base_pd > 0]
        avg_pd_increase_pct = np.mean(pd_increases) if pd_increases else 0
        max_ecl_increase_pct = max((r.ecl_increase_pct for r in loan_results), default=0)
        
        # Sector breakdown
        sector_impacts = {}
        for r in loan_results:
            sector = r.sector or "unclassified"
            if sector not in sector_impacts:
                sector_impacts[sector] = {
                    "loan_count": 0,
                    "total_ead": 0,
                    "base_ecl": 0,
                    "stressed_ecl": 0,
                }
            sector_impacts[sector]["loan_count"] += 1
            sector_impacts[sector]["total_ead"] += r.ead
            sector_impacts[sector]["base_ecl"] += r.base_ecl
            sector_impacts[sector]["stressed_ecl"] += r.stressed_ecl
        
        # Calculate sector ECL increase %
        for sector in sector_impacts:
            base = sector_impacts[sector]["base_ecl"]
            stressed = sector_impacts[sector]["stressed_ecl"]
            sector_impacts[sector]["ecl_increase_pct"] = (
                (stressed - base) / base * 100 if base > 0 else 0
            )
        
        return PortfolioStressTestResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            scenario_type=scenario.scenario_type.value,
            run_timestamp=datetime.utcnow().isoformat(),
            loan_count=len(loans),
            total_ead=total_ead,
            base_ecl_total=base_ecl_total,
            stressed_ecl_total=stressed_ecl_total,
            ecl_increase_total=ecl_increase_total,
            ecl_increase_pct=ecl_increase_pct,
            loans_with_increased_risk=loans_with_increased_risk,
            avg_pd_increase_pct=avg_pd_increase_pct,
            max_ecl_increase_pct=max_ecl_increase_pct,
            sector_impacts=sector_impacts,
            loan_results=loan_results,
        )
    
    def run_all_scenarios(
        self,
        loans: List[Dict[str, Any]],
    ) -> Dict[str, PortfolioStressTestResult]:
        """Run all scenarios on the portfolio."""
        return {
            scenario_id: self.stress_test_portfolio(loans, scenario_id)
            for scenario_id in self.scenarios.keys()
        }
    
    def compare_scenarios(
        self,
        loans: List[Dict[str, Any]],
        scenario_ids: List[str] = None,
    ) -> Dict[str, Any]:
        """Compare multiple scenarios side by side."""
        if scenario_ids is None:
            scenario_ids = list(self.scenarios.keys())
        
        results = {}
        for sid in scenario_ids:
            if sid in self.scenarios:
                result = self.stress_test_portfolio(loans, sid)
                results[sid] = {
                    "name": result.scenario_name,
                    "type": result.scenario_type,
                    "ecl_increase_pct": round(result.ecl_increase_pct, 2),
                    "stressed_ecl_total": round(result.stressed_ecl_total, 2),
                    "loans_at_risk": result.loans_with_increased_risk,
                }
        
        # Sort by ECL impact
        sorted_results = dict(
            sorted(results.items(), key=lambda x: x[1]["ecl_increase_pct"], reverse=True)
        )
        
        return {
            "comparison": sorted_results,
            "worst_case": list(sorted_results.keys())[0] if sorted_results else None,
            "total_scenarios": len(sorted_results),
        }


# Singleton instance
_stress_tester: Optional[StressTester] = None


def get_stress_tester() -> StressTester:
    """Get or create StressTester singleton."""
    global _stress_tester
    if _stress_tester is None:
        _stress_tester = StressTester()
    return _stress_tester
