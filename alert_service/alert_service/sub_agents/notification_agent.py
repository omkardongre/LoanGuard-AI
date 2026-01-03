"""
Notification Agent - Sends alerts via email and Slack.
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from alert_service.alert_service.config import MODEL
from alert_service.alert_service.prompts import NOTIFICATION_PROMPT
from alert_service.alert_service.tools.notification_tools import (
    send_email,
    send_slack_message,
    get_notification_recipients,
)

email_tool = FunctionTool(func=send_email)
slack_tool = FunctionTool(func=send_slack_message)
recipients_tool = FunctionTool(func=get_notification_recipients)

notification_agent = Agent(
    name="NotificationAgent",
    model=MODEL,
    description="Sends notifications via email and Slack",
    instruction=NOTIFICATION_PROMPT,
    tools=[email_tool, slack_tool, recipients_tool],
)
