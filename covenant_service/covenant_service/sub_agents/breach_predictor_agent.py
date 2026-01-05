"""
Breach Predictor Agent - Predicts covenant breaches using ML with SHAP explanations.
Trained on 720,966 real Lending Club loans.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from covenant_service.covenant_service.config import MODEL
from covenant_service.covenant_service.prompts import BREACH_PREDICTOR_PROMPT
from covenant_service.covenant_service.tools.ml_tools import (
    predict_breach,
    explain_prediction,
    get_feature_importance,
    get_risk_score,
)

logger = logging.getLogger(__name__)

predict_tool = FunctionTool(func=predict_breach)
shap_tool = FunctionTool(func=explain_prediction)
importance_tool = FunctionTool(func=get_feature_importance)
risk_score_tool = FunctionTool(func=get_risk_score)

breach_predictor_agent = Agent(
    name="BreachPredictorAgent",
    model=MODEL,
    description="Predicts breach probability with explainable AI using SHAP",
    instruction=BREACH_PREDICTOR_PROMPT,
    tools=[predict_tool, shap_tool, importance_tool, risk_score_tool],
)
