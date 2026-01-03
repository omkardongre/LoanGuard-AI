"""
Entry point for Alert Service.
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
    from alert_service.alert_service.agent import alert_agent
    from alert_service.agent_executor import AlertAgentExecutor
    ADK_AVAILABLE = True
except ImportError as e:
    ADK_AVAILABLE = False
    missing_dep = e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=settings.ALERT_SERVICE_PORT)
def main(host: str, port: int):
    """Runs the Alert Service as an A2A server."""
    if not ADK_AVAILABLE:
        logger.warning(f"ADK dependencies not found ({missing_dep})")
        return

    logger.info("Configuring Alert Service A2A server...")

    try:
        agent_card = AgentCard(
            name=alert_agent.name,
            description=alert_agent.description,
            url=f"http://{host}:{port}",
            version="1.0.0",
            capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[
                AgentSkill(
                    id="generate_alert",
                    name="Generate Alert",
                    description="Generate compliance alert for covenant breach or ESG issue.",
                    examples=["Generate alert for loan ABC", "Create breach notification"],
                    tags=["alert", "notification"],
                ),
                AgentSkill(
                    id="create_report",
                    name="Create Compliance Report",
                    description="Generate comprehensive compliance report.",
                    examples=["Create quarterly report", "Generate compliance summary"],
                    tags=["report", "compliance"],
                ),
                AgentSkill(
                    id="send_notification",
                    name="Send Notification",
                    description="Send email or Slack notification.",
                    examples=["Send alert to team", "Email loan officer"],
                    tags=["email", "slack", "notify"],
                ),
            ],
        )

        agent_executor = AlertAgentExecutor()
        task_store = InMemoryTaskStore()
        request_handler = DefaultRequestHandler(agent_executor, task_store)
        app_builder = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

        logger.info(f"Starting Alert Service on http://{host}:{port}/")
        uvicorn.run(app_builder.build(), host=host, port=port)

    except Exception as e:
        logger.error(f"Failed to start Alert Service: {e}")
        raise


if __name__ == "__main__":
    main()
