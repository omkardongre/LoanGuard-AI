"""
Report Builder Agent - Generates compliance reports.
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from alert_service.alert_service.config import MODEL
from alert_service.alert_service.prompts import REPORT_BUILDER_PROMPT
from alert_service.alert_service.tools.report_tools import (
    generate_compliance_report,
    generate_executive_summary,
    export_report_pdf,
)

report_tool = FunctionTool(func=generate_compliance_report)
summary_tool = FunctionTool(func=generate_executive_summary)
export_tool = FunctionTool(func=export_report_pdf)

report_builder_agent = Agent(
    name="ReportBuilderAgent",
    model=MODEL,
    description="Generates comprehensive compliance reports",
    instruction=REPORT_BUILDER_PROMPT,
    tools=[report_tool, summary_tool, export_tool],
)
