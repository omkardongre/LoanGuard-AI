"""
Entry point for Document Service.

Runs the document processing agent as an A2A server.
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
    from document_service.document_service.agent import document_agent
    from document_service.agent_executor import DocumentAgentExecutor
    ADK_AVAILABLE = True
except ImportError as e:
    ADK_AVAILABLE = False
    missing_dep = e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the server to.",
)
@click.option(
    "--port",
    default=settings.DOCUMENT_SERVICE_PORT,
    help="Port to bind the server to.",
)
def main(host: str, port: int):
    """Runs the Document Service as an A2A server."""
    if not ADK_AVAILABLE:
        logger.warning(
            f"ADK or A2A SDK dependencies not found ({missing_dep}), "
            "falling back to simple HTTP service."
        )
        return

    logger.info("Configuring Document Service A2A server...")

    try:
        agent_card = AgentCard(
            name=document_agent.name,
            description=document_agent.description,
            url=f"http://{host}:{port}",
            version="1.0.0",
            capabilities=AgentCapabilities(
                streaming=False,
                pushNotifications=False,
            ),
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[
                AgentSkill(
                    id="parse_document",
                    name="Parse Loan Document",
                    description="Parse a loan agreement PDF and extract text content.",
                    examples=[
                        "Parse the credit agreement document",
                        "Extract text from loan document",
                    ],
                    tags=["document", "parse", "pdf"],
                ),
                AgentSkill(
                    id="extract_covenants",
                    name="Extract Covenants",
                    description="Identify and extract covenant definitions from loan documents.",
                    examples=[
                        "Extract all covenants from this credit agreement",
                        "Find financial covenants in the document",
                    ],
                    tags=["covenant", "extract", "nlp"],
                ),
                AgentSkill(
                    id="extract_entities",
                    name="Extract Entities",
                    description="Extract key entities like parties, dates, and amounts.",
                    examples=[
                        "Extract borrower and lender information",
                        "Find loan amount and maturity date",
                    ],
                    tags=["entity", "extract"],
                ),
            ],
        )
    except AttributeError as e:
        logger.error(f"Error accessing agent attributes: {e}")
        raise

    try:
        agent_executor = DocumentAgentExecutor()
        task_store = InMemoryTaskStore()
        request_handler = DefaultRequestHandler(agent_executor, task_store)

        app_builder = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )

        logger.info(f"Starting Document Service A2A server on http://{host}:{port}/")
        uvicorn.run(app_builder.build(), host=host, port=port)

    except Exception as e:
        logger.error(f"Failed to start Document Service: {e}")
        raise


if __name__ == "__main__":
    main()
