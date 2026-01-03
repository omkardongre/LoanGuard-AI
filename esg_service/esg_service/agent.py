"""
Main agent definition for ESG Service.
"""

import logging
from google.adk.agents import SequentialAgent

from esg_service.esg_service.config import MODEL
from esg_service.esg_service.sub_agents.kpi_tracker_agent import kpi_tracker_agent
from esg_service.esg_service.sub_agents.spt_validator_agent import spt_validator_agent
from esg_service.esg_service.sub_agents.esg_rating_agent import esg_rating_agent
from esg_service.esg_service.sub_agents.greenwashing_detector_agent import greenwashing_detector_agent
from esg_service.esg_service.callbacks import post_esg_callback

logger = logging.getLogger(__name__)

esg_agent = SequentialAgent(
    name="ESGAgent",
    description="Sequential agent for ESG compliance tracking and greenwashing detection",
    sub_agents=[
        kpi_tracker_agent,
        spt_validator_agent,
        esg_rating_agent,
        greenwashing_detector_agent,
    ],
    after_agent_callback=post_esg_callback,
)

root_agent = esg_agent
