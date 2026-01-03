"""
ESG Rating Agent - Analyzes ESG ratings from external providers.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from esg_service.esg_service.config import MODEL
from esg_service.esg_service.prompts import ESG_RATING_PROMPT
from esg_service.esg_service.tools.rating_tools import (
    get_esg_rating,
    get_rating_history,
    compare_peer_ratings,
    get_rating_breakdown,
)

logger = logging.getLogger(__name__)

rating_tool = FunctionTool(func=get_esg_rating)
history_tool = FunctionTool(func=get_rating_history)
peer_tool = FunctionTool(func=compare_peer_ratings)
breakdown_tool = FunctionTool(func=get_rating_breakdown)

esg_rating_agent = Agent(
    name="ESGRatingAgent",
    model=MODEL,
    description="Analyzes ESG ratings and provides peer comparisons",
    instruction=ESG_RATING_PROMPT,
    tools=[rating_tool, history_tool, peer_tool, breakdown_tool],
)
