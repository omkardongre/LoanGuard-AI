"""
Compliance Checker Agent - Determines covenant compliance status.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from covenant_service.covenant_service.config import MODEL
from covenant_service.covenant_service.prompts import COMPLIANCE_CHECKER_PROMPT
from covenant_service.covenant_service.tools.compliance_tools import (
    check_covenant_compliance,
    determine_status_color,
    check_cross_default,
    calculate_buffer_percentage,
)

logger = logging.getLogger(__name__)

compliance_tool = FunctionTool(func=check_covenant_compliance)
status_color_tool = FunctionTool(func=determine_status_color)
cross_default_tool = FunctionTool(func=check_cross_default)
buffer_tool = FunctionTool(func=calculate_buffer_percentage)

compliance_checker_agent = Agent(
    name="ComplianceCheckerAgent",
    model=MODEL,
    description="Checks covenant compliance and assigns status colors",
    instruction=COMPLIANCE_CHECKER_PROMPT,
    tools=[compliance_tool, status_color_tool, cross_default_tool, buffer_tool],
)
