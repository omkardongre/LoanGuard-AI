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
# SLL Module (NEW - P0 Strategy)
from esg_service.esg_service.tools.sll_kpi_extractor import (
    SLLKPIExtractor,
    get_sll_kpi_extractor,
    extract_sll_kpis_from_document,
    get_loan_sll_kpis,
    ExtractedSLLKPI,
)

# Fund Finance Module (P0 Strategy - WINNING_STRATEGY_FINAL.md)
from esg_service.esg_service.tools.nav_monitor import (
    NAVMonitorAgent,
    get_nav_monitor,
    get_nav_facility,
    calculate_nav_ltv,
    get_nav_buffer_analysis,
    create_nav_facility,
    get_nav_portfolio_summary,
)
from esg_service.esg_service.tools.lp_transparency import (
    LPTransparencyAgent,
    get_lp_transparency_agent,
    get_lp_positions,
    get_fund_leverage_exposure,
    get_lp_leverage,
    create_lp_position,
)
from esg_service.esg_service.tools.ilpa_compliance import (
    ILPAComplianceAgent,
    get_ilpa_compliance_agent,
    check_ilpa_compliance,
    validate_ilpa_compliance,
)
from esg_service.esg_service.tools.subscription_tracker import (
    SubscriptionTrackerAgent,
    get_subscription_tracker,
    get_subscription_facility,
    calculate_borrowing_base,
    create_capital_call,
    get_capital_calls,
    get_overdue_calls,
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
    # SLL Module (P0 Strategy)
    "SLLKPIExtractor",
    "get_sll_kpi_extractor",
    "extract_sll_kpis_from_document",
    "get_loan_sll_kpis",
    "ExtractedSLLKPI",
    # Fund Finance Module (P0 Strategy)
    "NAVMonitorAgent",
    "get_nav_monitor",
    "get_nav_facility",
    "calculate_nav_ltv",
    "get_nav_buffer_analysis",
    "create_nav_facility",
    "get_nav_portfolio_summary",
    "LPTransparencyAgent",
    "get_lp_transparency_agent",
    "get_lp_positions",
    "get_fund_leverage_exposure",
    "get_lp_leverage",
    "create_lp_position",
    "ILPAComplianceAgent",
    "get_ilpa_compliance_agent",
    "check_ilpa_compliance",
    "validate_ilpa_compliance",
    "SubscriptionTrackerAgent",
    "get_subscription_tracker",
    "get_subscription_facility",
    "calculate_borrowing_base",
    "create_capital_call",
    "get_capital_calls",
    "get_overdue_calls",
    # Transition Loans Module (P1 Strategy)
    "TLPValidatorAgent",
    "get_tlp_validator",
    "validate_transition_loan",
    "get_tlp_summary",
    "save_tlp_assessment",
    "CarbonLockinAgent",
    "get_carbon_lockin_agent",
    "assess_carbon_lockin",
    "get_portfolio_lockin_summary",
    "DNSHScreeningAgent",
    "get_dnsh_screening_agent",
    "screen_dnsh",
    "get_portfolio_dnsh_summary",
    "TLPReportAgent",
    "get_tlp_report_agent",
    "generate_tlp_report",
    "get_tlp_portfolio_report",
    # SLLB & Regional Module (P1/P2)
    "SLLBPortfolioManager",
    "get_sllb_manager",
    "create_sllb_portfolio",
    "get_sllb_portfolio",
    "add_sll_to_sllb",
    "get_sllb_summary",
    "SLLBEligibilityEngine",
    "get_eligibility_engine",
    "evaluate_sll_eligibility",
    "batch_evaluate_sll_eligibility",
    "ZARONIATransitionAgent",
    "get_zaronia_agent",
    "assess_jibar_transition",
    "initiate_zaronia_transition",
    "get_zaronia_transition_summary",
    "SFDR2Classifier",
    "get_sfdr_classifier",
    "classify_sfdr_product",
    "get_sfdr_portfolio_summary",
    "get_sfdr_migration_analysis",
]


# Transition Loans Module imports
from esg_service.esg_service.tools.tlp_validator import (
    TLPValidatorAgent,
    get_tlp_validator,
    validate_transition_loan,
    get_tlp_summary,
    save_tlp_assessment,
)

from esg_service.esg_service.tools.carbon_lockin import (
    CarbonLockinAgent,
    get_carbon_lockin_agent,
    assess_carbon_lockin,
    get_portfolio_lockin_summary,
)

from esg_service.esg_service.tools.dnsh_screening import (
    DNSHScreeningAgent,
    get_dnsh_screening_agent,
    screen_dnsh,
    get_portfolio_dnsh_summary,
)

from esg_service.esg_service.tools.tlp_report import (
    TLPReportAgent,
    get_tlp_report_agent,
    generate_tlp_report,
    get_tlp_portfolio_report,
)


# SLLB & Regional Module imports
from esg_service.esg_service.tools.sllb_portfolio import (
    SLLBPortfolioManager,
    get_sllb_manager,
    create_sllb_portfolio,
    get_sllb_portfolio,
    add_sll_to_sllb,
    get_sllb_summary,
)

from esg_service.esg_service.tools.sllb_eligibility import (
    SLLBEligibilityEngine,
    get_eligibility_engine,
    evaluate_sll_eligibility,
    batch_evaluate_sll_eligibility,
)

from esg_service.esg_service.tools.zaronia_transition import (
    ZARONIATransitionAgent,
    get_zaronia_agent,
    assess_jibar_transition,
    initiate_zaronia_transition,
    get_zaronia_transition_summary,
)

from esg_service.esg_service.tools.sfdr_classifier import (
    SFDR2Classifier,
    get_sfdr_classifier,
    classify_sfdr_product,
    get_sfdr_portfolio_summary,
    get_sfdr_migration_analysis,
)

