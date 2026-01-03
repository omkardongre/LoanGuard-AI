"""
Tools for Covenant Service agents.
"""

from covenant_service.covenant_service.tools.bigquery_tools import (
    get_loan_details,
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
    predict_breach_probability,
    get_shap_explanation,
    get_feature_importance,
    generate_risk_score,
)
from covenant_service.covenant_service.tools.gcs_model_loader import (
    get_model_loader,
    predict_breach_probability as predict_breach_with_gcs,
    ModelLoader,
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

__all__ = [
    "get_loan_details",
    "get_covenant_definitions",
    "get_latest_financials",
    "get_historical_measurements",
    "calculate_debt_to_ebitda",
    "calculate_interest_coverage",
    "calculate_current_ratio",
    "calculate_net_worth",
    "calculate_fixed_charge_coverage",
    "check_covenant_compliance",
    "determine_status_color",
    "check_cross_default",
    "calculate_buffer_percentage",
    "predict_breach_probability",
    "get_shap_explanation",
    "get_feature_importance",
    "generate_risk_score",
    "calculate_metric_velocity",
    "calculate_loan_velocity",
    "calculate_portfolio_velocity",
    "get_risk_velocity",
    "calculate_cure_options",
    "get_cure_options",
]
