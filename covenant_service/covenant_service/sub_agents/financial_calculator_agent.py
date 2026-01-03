"""
Financial Calculator Agent - Computes financial ratios for covenant testing.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from covenant_service.covenant_service.config import MODEL
from covenant_service.covenant_service.prompts import FINANCIAL_CALCULATOR_PROMPT
from covenant_service.covenant_service.tools.calculation_tools import (
    calculate_debt_to_ebitda,
    calculate_interest_coverage,
    calculate_current_ratio,
    calculate_net_worth,
    calculate_fixed_charge_coverage,
)

logger = logging.getLogger(__name__)

debt_ebitda_tool = FunctionTool(func=calculate_debt_to_ebitda)
interest_coverage_tool = FunctionTool(func=calculate_interest_coverage)
current_ratio_tool = FunctionTool(func=calculate_current_ratio)
net_worth_tool = FunctionTool(func=calculate_net_worth)
fixed_charge_tool = FunctionTool(func=calculate_fixed_charge_coverage)

financial_calculator_agent = Agent(
    name="FinancialCalculatorAgent",
    model=MODEL,
    description="Calculates financial ratios for covenant compliance testing",
    instruction=FINANCIAL_CALCULATOR_PROMPT,
    tools=[
        debt_ebitda_tool,
        interest_coverage_tool,
        current_ratio_tool,
        net_worth_tool,
        fixed_charge_tool,
    ],
)
