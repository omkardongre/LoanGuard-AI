"""
Entry point for Covenant Service.

Runs the covenant monitoring agent as an A2A server.
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
    from covenant_service.covenant_service.agent import covenant_agent
    from covenant_service.agent_executor import CovenantAgentExecutor
    ADK_AVAILABLE = True
except ImportError as e:
    ADK_AVAILABLE = False
    missing_dep = e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="127.0.0.1", help="Host to bind the server to.")
@click.option("--port", default=settings.COVENANT_SERVICE_PORT, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the Covenant Service as an A2A server."""
    if not ADK_AVAILABLE:
        logger.warning(f"ADK or A2A SDK dependencies not found ({missing_dep})")
        return

    logger.info("Configuring Covenant Service A2A server...")

    try:
        agent_card = AgentCard(
            name=covenant_agent.name,
            description=covenant_agent.description,
            url=f"http://{host}:{port}",
            version="1.0.0",
            capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[
                AgentSkill(
                    id="check_compliance",
                    name="Check Covenant Compliance",
                    description="Check if a loan is compliant with all its covenants.",
                    examples=["Check compliance for loan ABC123", "Is this loan in breach?"],
                    tags=["compliance", "covenant", "check"],
                ),
                AgentSkill(
                    id="calculate_ratios",
                    name="Calculate Financial Ratios",
                    description="Calculate financial covenant ratios from borrower data.",
                    examples=["Calculate Debt/EBITDA ratio", "Compute interest coverage"],
                    tags=["ratio", "financial", "calculate"],
                ),
                AgentSkill(
                    id="predict_breach",
                    name="Predict Covenant Breach",
                    description="Predict probability of covenant breach with explainable AI.",
                    examples=["What's the breach probability?", "Predict breach risk"],
                    tags=["predict", "breach", "ml"],
                ),
            ],
        )
    except AttributeError as e:
        logger.error(f"Error accessing agent attributes: {e}")
        raise

    try:
        agent_executor = CovenantAgentExecutor()
        task_store = InMemoryTaskStore()
        request_handler = DefaultRequestHandler(agent_executor, task_store)
        app_builder = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

        logger.info(f"Starting Covenant Service A2A server on http://{host}:{port}/")
        uvicorn.run(app_builder.build(), host=host, port=port)

    except Exception as e:
        logger.error(f"Failed to start Covenant Service: {e}")
        raise


if __name__ == "__main__":
    main()
