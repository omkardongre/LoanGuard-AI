"""
Main agent definition for Covenant Service.
"""

import logging
from google.adk.agents import SequentialAgent

from covenant_service.covenant_service.config import MODEL
from covenant_service.covenant_service.sub_agents.data_retrieval_agent import data_retrieval_agent
from covenant_service.covenant_service.sub_agents.financial_calculator_agent import financial_calculator_agent
from covenant_service.covenant_service.sub_agents.compliance_checker_agent import compliance_checker_agent
from covenant_service.covenant_service.sub_agents.breach_predictor_agent import breach_predictor_agent
from covenant_service.covenant_service.callbacks import post_compliance_callback

logger = logging.getLogger(__name__)

# Create the root covenant agent as a sequential pipeline
covenant_agent = SequentialAgent(
    name="CovenantAgent",
    description="Sequential agent for monitoring covenant compliance and predicting breaches",
    sub_agents=[
        data_retrieval_agent,
        financial_calculator_agent,
        compliance_checker_agent,
        breach_predictor_agent,
    ],
    after_agent_callback=post_compliance_callback,
)

root_agent = covenant_agent
