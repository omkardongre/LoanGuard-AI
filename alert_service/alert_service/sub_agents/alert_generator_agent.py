"""
Alert Generator Agent - Creates compliance alerts.
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from alert_service.alert_service.config import MODEL
from alert_service.alert_service.prompts import ALERT_GENERATOR_PROMPT
from alert_service.alert_service.tools.alert_tools import (
    create_alert,
    prioritize_alerts,
    get_alert_template,
)

create_tool = FunctionTool(func=create_alert)
prioritize_tool = FunctionTool(func=prioritize_alerts)
template_tool = FunctionTool(func=get_alert_template)

alert_generator_agent = Agent(
    name="AlertGeneratorAgent",
    model=MODEL,
    description="Creates and prioritizes compliance alerts",
    instruction=ALERT_GENERATOR_PROMPT,
    tools=[create_tool, prioritize_tool, template_tool],
)
