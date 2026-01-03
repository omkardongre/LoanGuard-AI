"""
Greenwashing Detector Agent - Identifies potential greenwashing risks.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from esg_service.esg_service.config import MODEL
from esg_service.esg_service.prompts import GREENWASHING_DETECTOR_PROMPT
from esg_service.esg_service.tools.greenwashing_tools import (
    analyze_esg_claims,
    check_verification_gaps,
    compare_claims_vs_actions,
    calculate_greenwashing_score,
)

logger = logging.getLogger(__name__)

claims_tool = FunctionTool(func=analyze_esg_claims)
gaps_tool = FunctionTool(func=check_verification_gaps)
compare_tool = FunctionTool(func=compare_claims_vs_actions)
score_tool = FunctionTool(func=calculate_greenwashing_score)

greenwashing_detector_agent = Agent(
    name="GreenwashingDetectorAgent",
    model=MODEL,
    description="Detects potential greenwashing risks in ESG claims",
    instruction=GREENWASHING_DETECTOR_PROMPT,
    tools=[claims_tool, gaps_tool, compare_tool, score_tool],
)
