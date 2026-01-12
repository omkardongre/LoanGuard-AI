"""
Voice Alert Agent for LoanGuard AI.

Handles voice-based alerts and notifications using ElevenLabs Conversational AI.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from common.bigquery_client import get_bigquery_client
from voice_service.voice_service.tools.phone_call import (
    make_call,
    validate_us_phone_number
)
from voice_service.voice_service.prompts import (
    COVENANT_BREACH_ALERT_PROMPT,
    BORROWER_OUTREACH_PROMPT,
    PAYMENT_REMINDER_PROMPT
)

logger = logging.getLogger(__name__)


class VoiceAlertAgent:
    """Agent for making voice calls via ElevenLabs Conversational AI."""
    
    def __init__(self):
        self.bq_client = get_bigquery_client()
    
    async def make_covenant_breach_call(
        self,
        loan_id: str,
        breach_type: str,
        severity: str,
        phone_number: str,
        threshold: Optional[str] = None,
        actual_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make a voice call to alert about a covenant breach.
        
        Args:
            loan_id: Loan identifier
            breach_type: Type of covenant breached
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
            phone_number: Phone number to call (Risk Committee)
            threshold: Covenant threshold value
            actual_value: Actual value that triggered breach
            
        Returns:
            Call result with status, transcript, and conversation_id
        """
        logger.info(f"Making covenant breach call for loan {loan_id}")
        
        # Validate phone number
        validation = validate_us_phone_number(phone_number)
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
                "loan_id": loan_id
            }
        
        # Get loan details from BigQuery (parameterized query to prevent SQL injection)
        try:
            from google.cloud import bigquery
            
            loan_query = f"""
            SELECT 
                loan_id,
                borrower_name,
                amount,
                currency,
                loan_officer
            FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.loans`
            WHERE loan_id = @loan_id
            LIMIT 1
            """
            params = [bigquery.ScalarQueryParameter("loan_id", "STRING", loan_id)]
            results = self.bq_client.execute_query(loan_query, params)
            
            if not results:
                return {
                    "success": False,
                    "error": f"Loan {loan_id} not found in database",
                    "loan_id": loan_id
                }
            
            loan_data = results[0]
        except Exception as e:
            logger.error(f"Failed to fetch loan data: {e}")
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "loan_id": loan_id
            }
        
        # Build system prompt with loan details
        detected_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        loan_details_str = json.dumps({
            "borrower": loan_data.get("borrower_name"),
            "amount": f"${loan_data.get('amount'):,.2f}" if loan_data.get('amount') else "N/A",
            "currency": loan_data.get("currency", "USD"),
            "loan_officer": loan_data.get("loan_officer"),
            "threshold": threshold,
            "actual_value": actual_value
        }, indent=2)
        
        system_prompt = COVENANT_BREACH_ALERT_PROMPT.format(
            loan_id=loan_id,
            breach_type=breach_type,
            severity=severity,
            detected_date=detected_date,
            loan_details=loan_details_str
        )
        
        first_message = f"This is LoanGuard AI calling with a {severity.lower()} priority covenant breach alert on loan {loan_id}."
        
        # Make the call
        try:
            call_result = await make_call(
                to_number=validation["normalized"],
                system_prompt=system_prompt,
                first_message=first_message,
                poll_interval=2.0
            )
            
            # Log call to BigQuery
            await self._log_call_to_bigquery(
                conversation_id=call_result.get("conversation_id"),
                call_type="covenant_breach",
                loan_id=loan_id,
                phone_number=validation["normalized"],
                status=call_result.get("status"),
                transcript=call_result.get("transcript", [])
            )
            
            return {
                "success": True,
                "loan_id": loan_id,
                "call_result": call_result
            }
        except Exception as e:
            logger.error(f"Call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "loan_id": loan_id
            }
    
    async def make_borrower_outreach_call(
        self,
        loan_id: str,
        borrower_name: str,
        phone_number: str,
        warning_indicators: List[str]
    ) -> Dict[str, Any]:
        """
        Make a proactive outreach call to a borrower showing early warning signs.
        
        Args:
            loan_id: Loan identifier
            borrower_name: Borrower's name
            phone_number: Borrower's phone number
            warning_indicators: List of early warning indicators
            
        Returns:
            Call result with status, transcript, and conversation_id
        """
        logger.info(f"Making borrower outreach call for loan {loan_id}")
        
        # Validate phone number
        validation = validate_us_phone_number(phone_number)
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
                "loan_id": loan_id
            }
        
        # Get borrower details if available
        borrower_details = {
            "name": borrower_name,
            "loan_id": loan_id
        }
        
        system_prompt = BORROWER_OUTREACH_PROMPT.format(
            borrower_name=borrower_name,
            loan_id=loan_id,
            warning_indicators=", ".join(warning_indicators),
            borrower_details=json.dumps(borrower_details, indent=2)
        )
        
        first_message = f"Good afternoon, this is Alex from LoanGuard Risk Management. I'm calling regarding your business loan. Is this a good time for a quick 2-minute check-in?"
        
        # Make the call
        try:
            call_result = await make_call(
                to_number=validation["normalized"],
                system_prompt=system_prompt,
                first_message=first_message,
                poll_interval=2.0
            )
            
            # Log call
            await self._log_call_to_bigquery(
                conversation_id=call_result.get("conversation_id"),
                call_type="borrower_outreach",
                loan_id=loan_id,
                phone_number=validation["normalized"],
                status=call_result.get("status"),
                transcript=call_result.get("transcript", [])
            )
            
            return {
                "success": True,
                "loan_id": loan_id,
                "call_result": call_result
            }
        except Exception as e:
            logger.error(f"Call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "loan_id": loan_id
            }
    
    async def _log_call_to_bigquery(
        self,
        conversation_id: str,
        call_type: str,
        loan_id: str,
        phone_number: str,
        status: str,
        transcript: List[Dict]
    ):
        """Log call details to BigQuery for analytics."""
        try:
            from google.cloud import bigquery
            
            # Create table if it doesn't exist
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{self.bq_client.project_id}.{self.bq_client.dataset_id}.voice_calls` (
              conversation_id STRING NOT NULL,
              call_type STRING NOT NULL,
              loan_id STRING,
              phone_number STRING NOT NULL,
              status STRING NOT NULL,
              transcript JSON,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
            );
            """
            
            self.bq_client.execute_query(create_table_query)
            
            # Insert call log with parameterized query (prevents SQL injection)
            transcript_json = json.dumps(transcript)
            insert_query = f"""
            INSERT INTO `{self.bq_client.project_id}.{self.bq_client.dataset_id}.voice_calls`
            (conversation_id, call_type, loan_id, phone_number, status, transcript, created_at)
            VALUES (@conversation_id, @call_type, @loan_id, @phone_number, @status, 
                    JSON @transcript, CURRENT_TIMESTAMP())
            """
            
            params = [
                bigquery.ScalarQueryParameter("conversation_id", "STRING", conversation_id),
                bigquery.ScalarQueryParameter("call_type", "STRING", call_type),
                bigquery.ScalarQueryParameter("loan_id", "STRING", loan_id),
                bigquery.ScalarQueryParameter("phone_number", "STRING", phone_number),
                bigquery.ScalarQueryParameter("status", "STRING", status),
                bigquery.ScalarQueryParameter("transcript", "STRING", transcript_json),
            ]
            
            self.bq_client.execute_query(insert_query, params)
            logger.info(f"Logged call {conversation_id} to BigQuery")
        except Exception as e:
            logger.error(f"Failed to log call to BigQuery: {e}")
