"""
Entry point for ESG Service.

Runs the ESG compliance monitoring agent as an A2A server.
"""

import logging
import click

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from common.config import settings

try:
    import uvicorn
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import AgentCapabilities, AgentCard, AgentSkill
    from esg_service.esg_service.agent import esg_agent
    from esg_service.agent_executor import ESGAgentExecutor
    ADK_AVAILABLE = True
except ImportError as e:
    ADK_AVAILABLE = False
    missing_dep = e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="127.0.0.1", help="Host to bind the server to.")
@click.option("--port", default=settings.ESG_SERVICE_PORT, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the ESG Service as an A2A server."""
    if not ADK_AVAILABLE:
        logger.warning(f"ADK or A2A SDK dependencies not found ({missing_dep})")
        return

    logger.info("Configuring ESG Service A2A server...")

    try:
        agent_card = AgentCard(
            name=esg_agent.name,
            description=esg_agent.description,
            url=f"http://{host}:{port}",
            version="1.0.0",
            capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[
                AgentSkill(
                    id="track_kpis",
                    name="Track ESG KPIs",
                    description="Track sustainability KPIs for sustainability-linked loans.",
                    examples=["Track carbon reduction KPI", "Check ESG performance"],
                    tags=["esg", "kpi", "sustainability"],
                ),
                AgentSkill(
                    id="validate_spt",
                    name="Validate SPT Achievement",
                    description="Validate Sustainability Performance Target achievement.",
                    examples=["Validate SPT for loan ABC", "Check if targets are met"],
                    tags=["spt", "target", "validate"],
                ),
                AgentSkill(
                    id="detect_greenwashing",
                    name="Detect Greenwashing",
                    description="Analyze ESG claims for potential greenwashing risks.",
                    examples=["Check for greenwashing", "Validate ESG claims"],
                    tags=["greenwashing", "risk", "detect"],
                ),
            ],
        )
    except AttributeError as e:
        logger.error(f"Error accessing agent attributes: {e}")
        raise

    try:
        agent_executor = ESGAgentExecutor()
        task_store = InMemoryTaskStore()
        request_handler = DefaultRequestHandler(agent_executor, task_store)
        app_builder = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

        logger.info(f"Starting ESG Service A2A server on http://{host}:{port}/")
        uvicorn.run(app_builder.build(), host=host, port=port)

    except Exception as e:
        logger.error(f"Failed to start ESG Service: {e}")
        raise


if __name__ == "__main__":
    main()
