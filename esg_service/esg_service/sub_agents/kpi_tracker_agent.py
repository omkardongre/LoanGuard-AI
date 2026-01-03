"""
KPI Tracker Agent - Tracks sustainability KPIs for SLLs.
"""

import logging
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from esg_service.esg_service.config import MODEL
from esg_service.esg_service.prompts import KPI_TRACKER_PROMPT
from esg_service.esg_service.tools.kpi_tools import (
    get_kpi_definitions,
    get_current_kpi_values,
    calculate_kpi_progress,
    get_kpi_trend,
)

logger = logging.getLogger(__name__)

kpi_defs_tool = FunctionTool(func=get_kpi_definitions)
current_values_tool = FunctionTool(func=get_current_kpi_values)
progress_tool = FunctionTool(func=calculate_kpi_progress)
trend_tool = FunctionTool(func=get_kpi_trend)

kpi_tracker_agent = Agent(
    name="KPITrackerAgent",
    model=MODEL,
    description="Tracks sustainability KPI progress for sustainability-linked loans",
    instruction=KPI_TRACKER_PROMPT,
    tools=[kpi_defs_tool, current_values_tool, progress_tool, trend_tool],
)
