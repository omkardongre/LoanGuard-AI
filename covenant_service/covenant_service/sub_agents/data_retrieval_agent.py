"""
Data Retrieval Agent - Fetches financial data for covenant analysis.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from covenant_service.covenant_service.config import MODEL
from covenant_service.covenant_service.prompts import DATA_RETRIEVAL_PROMPT
from covenant_service.covenant_service.tools.bigquery_tools import (
    get_loan_data,
    get_covenant_definitions,
    get_latest_financials,
    get_historical_measurements,
)

logger = logging.getLogger(__name__)

loan_data_tool = FunctionTool(func=get_loan_data)
covenant_defs_tool = FunctionTool(func=get_covenant_definitions)
financials_tool = FunctionTool(func=get_latest_financials)
history_tool = FunctionTool(func=get_historical_measurements)

data_retrieval_agent = Agent(
    name="DataRetrievalAgent",
    model=MODEL,
    description="Retrieves financial data and covenant definitions from BigQuery",
    instruction=DATA_RETRIEVAL_PROMPT,
    tools=[loan_data_tool, covenant_defs_tool, financials_tool, history_tool],
)
