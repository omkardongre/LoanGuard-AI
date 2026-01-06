"""
Recovery Rate Agent - Predicts loan recovery rates and LGD with SHAP explanations.
Trained on 98,125 Lending Club charged-off loans.

Part of LoanGuard V9 - Basel III compliance suite.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from covenant_service.covenant_service.config import MODEL
from covenant_service.covenant_service.prompts import RECOVERY_RATE_PROMPT
from covenant_service.covenant_service.tools.recovery_rate_tools import (
    predict_recovery_rate,
    explain_recovery_prediction,
    get_recovery_feature_importance,
    get_lgd,
)

logger = logging.getLogger(__name__)

predict_recovery_tool = FunctionTool(func=predict_recovery_rate)
explain_recovery_tool = FunctionTool(func=explain_recovery_prediction)
importance_tool = FunctionTool(func=get_recovery_feature_importance)
lgd_tool = FunctionTool(func=get_lgd)

recovery_rate_agent = Agent(
    name="RecoveryRateAgent",
    model=MODEL,
    description="Predicts loan recovery rates and LGD for Basel III compliance",
    instruction=RECOVERY_RATE_PROMPT,
    tools=[predict_recovery_tool, explain_recovery_tool, importance_tool, lgd_tool],
)
