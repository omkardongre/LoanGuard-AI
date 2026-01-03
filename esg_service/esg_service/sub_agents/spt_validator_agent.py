"""
SPT Validator Agent - Validates Sustainability Performance Target achievement.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from esg_service.esg_service.config import MODEL
from esg_service.esg_service.prompts import SPT_VALIDATOR_PROMPT
from esg_service.esg_service.tools.spt_tools import (
    get_spt_definitions,
    validate_spt_achievement,
    calculate_margin_adjustment,
    check_verification_status,
)

logger = logging.getLogger(__name__)

spt_defs_tool = FunctionTool(func=get_spt_definitions)
validate_tool = FunctionTool(func=validate_spt_achievement)
margin_tool = FunctionTool(func=calculate_margin_adjustment)
verification_tool = FunctionTool(func=check_verification_status)

spt_validator_agent = Agent(
    name="SPTValidatorAgent",
    model=MODEL,
    description="Validates SPT achievement and calculates margin adjustments",
    instruction=SPT_VALIDATOR_PROMPT,
    tools=[spt_defs_tool, validate_tool, margin_tool, verification_tool],
)
