"""
Agent executor for Covenant Service.

Handles A2A request execution and ADK agent orchestration.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import DataPart, Part

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types as genai_types

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from common.config import settings
from covenant_service.covenant_service.agent import covenant_agent

logger = logging.getLogger(__name__)

log_file = Path.cwd() / "covenant_service" / "covenant_service.log"


def log_to_file(message: str):
    """Write log message to file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n[{timestamp}] {message}\n\n")


class CovenantAgentExecutor(AgentExecutor):
    """Executes the Covenant Agent logic in response to A2A requests."""

    def __init__(self):
        self._adk_agent = covenant_agent
        self._adk_runner = Runner(
            app_name="covenant_service_runner",
            agent=self._adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
        )
        logger.info("CovenantAgentExecutor initialized with ADK Runner.")

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        """Execute covenant monitoring request."""
        task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        logger.info(f"Processing request: {context.task_id}")

        if not context.current_task:
            task_updater.submit(message=context.message)

        task_updater.start_work(
            message=task_updater.new_agent_message(
                parts=[Part(root=DataPart(data={"status": "Analyzing covenant compliance..."}))]
            )
        )

        # Extract input parameters
        loan_id: Optional[str] = None
        action: str = "check_compliance"
        financial_data: Optional[dict] = None

        if context.message and context.message.parts:
            for part_union in context.message.parts:
                part = part_union.root
                if isinstance(part, DataPart):
                    if "loan_id" in part.data:
                        loan_id = part.data["loan_id"]
                    if "action" in part.data:
                        action = part.data["action"]
                    if "financial_data" in part.data:
                        financial_data = part.data["financial_data"]

        if not loan_id:
            logger.error(f"Task {context.task_id}: Missing loan_id")
            task_updater.failed(
                message=task_updater.new_agent_message(
                    parts=[Part(root=DataPart(data={"error": "Missing loan_id"}))]
                )
            )
            return

        try:
            session = await self._adk_runner.session_service.create_session(
                app_name="covenant_service_runner",
                user_id=context.context_id or "default_user",
            )

            # Build prompt based on action
            if action == "calculate_ratios":
                prompt = f"Calculate financial ratios for loan {loan_id} with data: {financial_data}"
            elif action == "predict_breach":
                prompt = f"Predict breach probability for loan {loan_id} and explain with SHAP"
            else:
                prompt = f"Check covenant compliance for loan {loan_id}"

            log_to_file(f"Processing: {action} for loan {loan_id}")

            final_response = None
            async for event in self._adk_runner.run_async(
                session_id=session.id,
                user_id=session.user_id,
                new_message=genai_types.Content(
                    role="user",
                    parts=[genai_types.Part(text=prompt)],
                ),
            ):
                if hasattr(event, "content") and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_response = part.text

            if final_response:
                result_data = {
                    "status": "completed",
                    "action": action,
                    "loan_id": loan_id,
                    "result": final_response,
                    "processed_at": datetime.now().isoformat(),
                }

                task_updater.add_artifact(
                    name=settings.COVENANT_ARTIFACT_NAME,
                    parts=[Part(root=DataPart(data=result_data))],
                )

                task_updater.complete(
                    message=task_updater.new_agent_message(
                        parts=[Part(root=DataPart(data=result_data))]
                    )
                )
                log_to_file(f"Task completed: {context.task_id}")
            else:
                task_updater.failed(
                    message=task_updater.new_agent_message(
                        parts=[Part(root=DataPart(data={"error": "No response from agent"}))]
                    )
                )

        except Exception as e:
            logger.error(f"Task {context.task_id} failed: {e}")
            task_updater.failed(
                message=task_updater.new_agent_message(
                    parts=[Part(root=DataPart(data={"error": str(e)}))]
                )
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        """Handle task cancellation."""
        logger.info(f"Cancelling task: {context.task_id}")
