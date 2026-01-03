"""
Agent executor for ESG Service.
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
from esg_service.esg_service.agent import esg_agent

logger = logging.getLogger(__name__)

log_file = Path.cwd() / "esg_service" / "esg_service.log"


class ESGAgentExecutor(AgentExecutor):
    """Executes the ESG Agent logic in response to A2A requests."""

    def __init__(self):
        self._adk_agent = esg_agent
        self._adk_runner = Runner(
            app_name="esg_service_runner",
            agent=self._adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
        )
        logger.info("ESGAgentExecutor initialized with ADK Runner.")

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        """Execute ESG compliance request."""
        task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        if not context.current_task:
            task_updater.submit(message=context.message)

        task_updater.start_work(
            message=task_updater.new_agent_message(
                parts=[Part(root=DataPart(data={"status": "Analyzing ESG compliance..."}))]
            )
        )

        loan_id: Optional[str] = None
        action: str = "track_kpis"

        if context.message and context.message.parts:
            for part_union in context.message.parts:
                part = part_union.root
                if isinstance(part, DataPart):
                    if "loan_id" in part.data:
                        loan_id = part.data["loan_id"]
                    if "action" in part.data:
                        action = part.data["action"]

        if not loan_id:
            task_updater.failed(
                message=task_updater.new_agent_message(
                    parts=[Part(root=DataPart(data={"error": "Missing loan_id"}))]
                )
            )
            return

        try:
            session = await self._adk_runner.session_service.create_session(
                app_name="esg_service_runner",
                user_id=context.context_id or "default_user",
            )

            if action == "validate_spt":
                prompt = f"Validate SPT achievement for loan {loan_id}"
            elif action == "detect_greenwashing":
                prompt = f"Analyze greenwashing risk for loan {loan_id}"
            else:
                prompt = f"Track ESG KPIs for loan {loan_id}"

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
                    name=settings.ESG_ARTIFACT_NAME,
                    parts=[Part(root=DataPart(data=result_data))],
                )

                task_updater.complete(
                    message=task_updater.new_agent_message(
                        parts=[Part(root=DataPart(data=result_data))]
                    )
                )
            else:
                task_updater.failed(
                    message=task_updater.new_agent_message(
                        parts=[Part(root=DataPart(data={"error": "No response"}))]
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
        logger.info(f"Cancelling task: {context.task_id}")
