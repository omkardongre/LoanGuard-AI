"""
Tools for Covenant Service agents.
"""

from covenant_service.covenant_service.tools.bigquery_tools import (
    get_loan_data,
    get_covenant_definitions,
    get_latest_financials,
    get_historical_measurements,
)
from covenant_service.covenant_service.tools.calculation_tools import (
    calculate_debt_to_ebitda,
    calculate_interest_coverage,
    calculate_current_ratio,
    calculate_net_worth,
    calculate_fixed_charge_coverage,
)
from covenant_service.covenant_service.tools.compliance_tools import (
    check_covenant_compliance,
    determine_status_color,
    check_cross_default,
    calculate_buffer_percentage,
)
from covenant_service.covenant_service.tools.ml_tools import (
    predict_breach,
    explain_prediction,
    get_feature_importance,
    get_risk_score,
    get_predictor,
)
from covenant_service.covenant_service.tools.risk_velocity_tools import (
    calculate_metric_velocity,
    calculate_loan_velocity,
    calculate_portfolio_velocity,
    get_risk_velocity,
)
from covenant_service.covenant_service.tools.cure_calculator_tools import (
    calculate_cure_options,
    get_cure_options,
)
from covenant_service.covenant_service.tools.dashboard_tools import (
    get_loan_dashboard,
    get_portfolio_dashboard,
    get_covenant_detail,
    ComplianceStatus,
    TrendDirection,
)
from covenant_service.covenant_service.tools.concentration_tools import (
    get_portfolio_concentration,
    calculate_marginal_concentration_impact,
    calculate_hhi,
    ConcentrationRisk,
)

__all__ = [
    # Data retrieval
    "get_loan_data",
    "get_covenant_definitions",
    "get_latest_financials",
    "get_historical_measurements",
    # Calculations
    "calculate_debt_to_ebitda",
    "calculate_interest_coverage",
    "calculate_current_ratio",
    "calculate_net_worth",
    "calculate_fixed_charge_coverage",
    # Compliance
    "check_covenant_compliance",
    "determine_status_color",
    "check_cross_default",
    "calculate_buffer_percentage",
    # ML/Prediction (v2.0 - Real Lending Club Data)
    "predict_breach",
    "explain_prediction",
    "get_feature_importance",
    "get_risk_score",
    "get_predictor",
    # Risk Velocity
    "calculate_metric_velocity",
    "calculate_loan_velocity",
    "calculate_portfolio_velocity",
    "get_risk_velocity",
    # Cure Calculator
    "calculate_cure_options",
    "get_cure_options",
    # Dashboard (V8)
    "get_loan_dashboard",
    "get_portfolio_dashboard",
    "get_covenant_detail",
    "ComplianceStatus",
    "TrendDirection",
    # Portfolio Concentration (V8 P1)
    "get_portfolio_concentration",
    "calculate_marginal_concentration_impact",
    "calculate_hhi",
    "ConcentrationRisk",
]
