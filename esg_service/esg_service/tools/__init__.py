"""
Tools for ESG Service agents.
"""

from esg_service.esg_service.tools.kpi_tools import (
    get_kpi_definitions,
    get_current_kpi_values,
    calculate_kpi_progress,
    get_kpi_trend,
)
from esg_service.esg_service.tools.spt_tools import (
    get_spt_definitions,
    validate_spt_achievement,
    calculate_margin_adjustment,
    check_verification_status,
)
from esg_service.esg_service.tools.rating_tools import (
    get_esg_rating,
    get_rating_history,
    compare_peer_ratings,
    get_rating_breakdown,
)
from esg_service.esg_service.tools.greenwashing_tools import (
    analyze_esg_claims,
    check_verification_gaps,
    compare_claims_vs_actions,
    calculate_greenwashing_score,
)
from esg_service.esg_service.tools.greenwashing_search_tools import (
    GreenwashingDetector,
    get_greenwashing_detector,
    detect_greenwashing_sync,
    detect_greenwashing_async,
    analyze_greenwashing,
    GreenwashingRisk,
    ClaimVerdict,
)
from esg_service.esg_service.tools.carbon_tools import (
    CarbonEmissionsTracker,
    get_carbon_tracker,
    calculate_carbon_emissions,
    calculate_loan_carbon_footprint,
    EmissionScope,
)
from esg_service.esg_service.tools.news_tools import (
    NewsValidator,
    get_news_validator,
    validate_company_claim,
    get_company_controversies,
    ClaimCredibility,
)

__all__ = [
    # KPI tools
    "get_kpi_definitions",
    "get_current_kpi_values",
    "calculate_kpi_progress",
    "get_kpi_trend",
    # SPT tools
    "get_spt_definitions",
    "validate_spt_achievement",
    "calculate_margin_adjustment",
    "check_verification_status",
    # Rating tools
    "get_esg_rating",
    "get_rating_history",
    "compare_peer_ratings",
    "get_rating_breakdown",
    # Greenwashing tools (basic)
    "analyze_esg_claims",
    "check_verification_gaps",
    "compare_claims_vs_actions",
    "calculate_greenwashing_score",
    # Greenwashing Detection (V8 HERO)
    "GreenwashingDetector",
    "get_greenwashing_detector",
    "detect_greenwashing_sync",
    "detect_greenwashing_async",
    "analyze_greenwashing",
    "GreenwashingRisk",
    "ClaimVerdict",
    # Carbon Tracking (P2)
    "CarbonEmissionsTracker",
    "get_carbon_tracker",
    "calculate_carbon_emissions",
    "calculate_loan_carbon_footprint",
    "EmissionScope",
    # News API Validation (P2)
    "NewsValidator",
    "get_news_validator",
    "validate_company_claim",
    "get_company_controversies",
    "ClaimCredibility",
]
