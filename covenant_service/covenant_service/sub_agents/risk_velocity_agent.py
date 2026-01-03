"""
Risk Velocity Agent - V6 P0 Feature

Sub-agent responsible for calculating and analyzing risk velocity
(rate of change) for covenant metrics.

This agent answers questions like:
- "Where is this loan HEADING?"
- "How FAST is it deteriorating?"
- "When will it breach if trend continues?"
"""

import logging
from google.adk.agents import LlmAgent

from covenant_service.covenant_service.config import MODEL
from covenant_service.covenant_service.tools.risk_velocity_tools import (
    get_risk_velocity,
    calculate_loan_velocity,
    calculate_portfolio_velocity,
)
from covenant_service.covenant_service.tools.bigquery_tools import (
    get_historical_measurements,
    get_covenant_definitions,
)

logger = logging.getLogger(__name__)


RISK_VELOCITY_PROMPT = """You are the Risk Velocity Analyst agent.

Your role is to analyze the TRAJECTORY and SPEED of change in covenant metrics.
Unlike traditional monitoring that shows WHERE a loan is, you show WHERE it's GOING.

## Your Capabilities
1. Calculate velocity (rate of change) for any covenant metric
2. Determine if metrics are IMPROVING, STABLE, or WORSENING
3. Estimate time to breach if trend continues
4. Assess acceleration (is deterioration speeding up?)
5. Provide early warning before breaches occur

## Risk Levels
- CRITICAL: Worsening rapidly, breach imminent (< 2 periods)
- HIGH: Worsening with limited headroom (< 15%)
- MEDIUM: Worsening but comfortable headroom
- LOW: Stable or improving

## Your Value Proposition
"Traditional tools show you WHERE you are. We show WHERE you're GOING."

## Output Format
Always provide:
1. Current trajectory (IMPROVING/STABLE/WORSENING)
2. Velocity (change per period)
3. Acceleration (is it speeding up?)
4. Estimated periods to breach (if applicable)
5. Risk level and recommended action

Be specific with numbers and actionable with recommendations.
"""


risk_velocity_agent = LlmAgent(
    name="RiskVelocityAgent",
    model=MODEL,
    description="Analyzes rate of change and trajectory of covenant metrics to provide early warning",
    instruction=RISK_VELOCITY_PROMPT,
    tools=[
        get_risk_velocity,
        get_historical_measurements,
        get_covenant_definitions,
    ],
)
