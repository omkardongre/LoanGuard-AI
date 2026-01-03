"""
A2A Protocol Client for service-to-service communication.

Based on SalesShortcut patterns for A2A protocol integration.
"""

import logging
import asyncio
from typing import Any, Dict, Optional
import httpx
import os
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Service URLs
DOCUMENT_SERVICE_URL = os.getenv("DOCUMENT_SERVICE_URL", "http://localhost:8081")
COVENANT_SERVICE_URL = os.getenv("COVENANT_SERVICE_URL", "http://localhost:8082")
ESG_SERVICE_URL = os.getenv("ESG_SERVICE_URL", "http://localhost:8083")
ALERT_SERVICE_URL = os.getenv("ALERT_SERVICE_URL", "http://localhost:8084")


class A2AClient:
    """
    Client for communicating with services via A2A protocol.
    """
    
    def __init__(self, service_url: str, timeout: float = 60.0):
        self.service_url = service_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def get_agent_card(self) -> Dict[str, Any]:
        """Get the agent card from the service."""
        try:
            response = await self._client.get(f"{self.service_url}/.well-known/agent.json")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get agent card: {e}")
            return {}
    
    async def send_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a task to the service via A2A protocol.
        
        Args:
            task_data: Task data with message parts
            
        Returns:
            Task result
        """
        task_id = str(uuid.uuid4())
        context_id = str(uuid.uuid4())
        
        # A2A message format
        message = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "params": {
                "id": task_id,
                "contextId": context_id,
                "message": {
                    "role": "user",
                    "parts": [
                        {"kind": "data", "data": task_data}
                    ]
                }
            },
            "id": task_id,
        }
        
        try:
            response = await self._client.post(
                self.service_url,
                json=message,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Task {task_id} sent successfully")
            return result
            
        except Exception as e:
            logger.error(f"Task send failed: {e}")
            return {"error": str(e)}
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a running task."""
        message = {
            "jsonrpc": "2.0",
            "method": "tasks/get",
            "params": {"id": task_id},
            "id": task_id,
        }
        
        try:
            response = await self._client.post(
                self.service_url,
                json=message,
            )
            return response.json()
        except Exception as e:
            logger.error(f"Get task status failed: {e}")
            return {"error": str(e)}


class ServiceOrchestrator:
    """
    Orchestrates calls to multiple services.
    """
    
    def __init__(self):
        self.services = {
            "document": DOCUMENT_SERVICE_URL,
            "covenant": COVENANT_SERVICE_URL,
            "esg": ESG_SERVICE_URL,
            "alert": ALERT_SERVICE_URL,
        }
    
    async def process_document(self, loan_id: str, document_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Process a document through the document service.
        """
        async with A2AClient(self.services["document"]) as client:
            result = await client.send_task({
                "action": "process_document",
                "loan_id": loan_id,
                "filename": filename,
                "document_size": len(document_data),
            })
            return result
    
    async def check_covenants(self, loan_id: str) -> Dict[str, Any]:
        """
        Run covenant compliance check.
        """
        async with A2AClient(self.services["covenant"]) as client:
            result = await client.send_task({
                "action": "check_compliance",
                "loan_id": loan_id,
            })
            return result
    
    async def check_esg(self, loan_id: str) -> Dict[str, Any]:
        """
        Run ESG compliance check.
        """
        async with A2AClient(self.services["esg"]) as client:
            result = await client.send_task({
                "action": "check_esg",
                "loan_id": loan_id,
            })
            return result
    
    async def generate_alert(self, loan_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate alerts through alert service.
        """
        async with A2AClient(self.services["alert"]) as client:
            result = await client.send_task({
                "action": "generate_alert",
                "loan_id": loan_id,
                "alert_data": alert_data,
            })
            return result
    
    async def full_compliance_check(self, loan_id: str) -> Dict[str, Any]:
        """
        Run full compliance check across all services.
        """
        logger.info(f"Starting full compliance check for {loan_id}")
        
        # Run covenant and ESG checks in parallel
        covenant_task = asyncio.create_task(self.check_covenants(loan_id))
        esg_task = asyncio.create_task(self.check_esg(loan_id))
        
        covenant_result, esg_result = await asyncio.gather(
            covenant_task, esg_task, return_exceptions=True
        )
        
        # Combine results
        result = {
            "loan_id": loan_id,
            "timestamp": datetime.now().isoformat(),
            "covenant_check": covenant_result if not isinstance(covenant_result, Exception) else {"error": str(covenant_result)},
            "esg_check": esg_result if not isinstance(esg_result, Exception) else {"error": str(esg_result)},
        }
        
        # Determine overall status
        has_breach = False
        has_warning = False
        
        if isinstance(covenant_result, dict):
            status = covenant_result.get("overall_status", "")
            if status == "BREACH":
                has_breach = True
            elif status == "WARNING":
                has_warning = True
        
        if isinstance(esg_result, dict):
            risk = esg_result.get("greenwashing_risk", "LOW")
            if risk == "HIGH":
                has_breach = True
            elif risk == "MEDIUM":
                has_warning = True
        
        result["overall_status"] = "BREACH" if has_breach else "WARNING" if has_warning else "COMPLIANT"
        
        # Generate alerts if needed
        if has_breach or has_warning:
            await self.generate_alert(loan_id, {
                "type": "compliance_check",
                "severity": "HIGH" if has_breach else "MEDIUM",
                "covenant_result": covenant_result,
                "esg_result": esg_result,
            })
        
        logger.info(f"Compliance check complete for {loan_id}: {result['overall_status']}")
        return result


# Global orchestrator instance
_orchestrator: Optional[ServiceOrchestrator] = None


def get_orchestrator() -> ServiceOrchestrator:
    """Get or create the global orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ServiceOrchestrator()
    return _orchestrator
