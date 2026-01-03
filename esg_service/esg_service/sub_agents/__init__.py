"""
Sub-agents for ESG Service.
"""

from esg_service.esg_service.sub_agents.kpi_tracker_agent import kpi_tracker_agent
from esg_service.esg_service.sub_agents.spt_validator_agent import spt_validator_agent
from esg_service.esg_service.sub_agents.esg_rating_agent import esg_rating_agent
from esg_service.esg_service.sub_agents.greenwashing_detector_agent import greenwashing_detector_agent

__all__ = [
    "kpi_tracker_agent",
    "spt_validator_agent",
    "esg_rating_agent",
    "greenwashing_detector_agent",
]
