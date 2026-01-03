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
    detect_greenwashing_sync,
    analyze_greenwashing,
)

__all__ = [
    "get_kpi_definitions",
    "get_current_kpi_values",
    "calculate_kpi_progress",
    "get_kpi_trend",
    "get_spt_definitions",
    "validate_spt_achievement",
    "calculate_margin_adjustment",
    "check_verification_status",
    "get_esg_rating",
    "get_rating_history",
    "compare_peer_ratings",
    "get_rating_breakdown",
    "analyze_esg_claims",
    "check_verification_gaps",
    "compare_claims_vs_actions",
    "calculate_greenwashing_score",
    "GreenwashingDetector",
    "detect_greenwashing_sync",
    "analyze_greenwashing",
]
