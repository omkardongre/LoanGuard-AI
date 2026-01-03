"""
Visualization Agent - Creates charts and dashboards.
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from alert_service.alert_service.config import MODEL
from alert_service.alert_service.prompts import VISUALIZATION_PROMPT
from alert_service.alert_service.tools.visualization_tools import (
    create_status_chart,
    create_trend_chart,
    create_portfolio_heatmap,
)

status_tool = FunctionTool(func=create_status_chart)
trend_tool = FunctionTool(func=create_trend_chart)
heatmap_tool = FunctionTool(func=create_portfolio_heatmap)

visualization_agent = Agent(
    name="VisualizationAgent",
    model=MODEL,
    description="Creates charts and visual dashboards",
    instruction=VISUALIZATION_PROMPT,
    tools=[status_tool, trend_tool, heatmap_tool],
)
