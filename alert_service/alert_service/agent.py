"""
Main agent definition for Alert Service.
"""

import logging
from google.adk.agents import SequentialAgent

from alert_service.alert_service.config import MODEL
from alert_service.alert_service.sub_agents.alert_generator_agent import alert_generator_agent
from alert_service.alert_service.sub_agents.report_builder_agent import report_builder_agent
from alert_service.alert_service.sub_agents.notification_agent import notification_agent
from alert_service.alert_service.sub_agents.visualization_agent import visualization_agent
from alert_service.alert_service.callbacks import post_alert_callback

logger = logging.getLogger(__name__)

alert_agent = SequentialAgent(
    name="AlertAgent",
    description="Sequential agent for generating alerts, reports, and notifications",
    sub_agents=[
        alert_generator_agent,
        report_builder_agent,
        visualization_agent,
        notification_agent,
    ],
    after_agent_callback=post_alert_callback,
)

root_agent = alert_agent
