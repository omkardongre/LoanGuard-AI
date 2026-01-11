"""
Subscription Tracker Agent - Track Capital Calls and Subscription Facilities.

Production-level implementation for Fund Finance subscription tracking.
Based on LMA Fund Finance research: "Subscription facilities cornerstone"
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class SubscriptionTrackerAgent:
    """
    Subscription Tracker Agent for Fund Finance.
    
    Features:
    - Capital call tracking
    - Subscription facility utilization
    - Borrowing base calculation
    - Default LP monitoring
    """
    
    # Industry standard advance rates
    ADVANCE_RATES = {
        "investment_grade": 0.95,  # 95% for IG LPs
        "standard": 0.85,  # 85% typical
        "conservative": 0.80,  # 80% conservative
    }
    
    def __init__(self):
        """Initialize Subscription Tracker Agent."""
        self.bq = BigQueryClient()
    
    def get_subscription_facility(self, facility_id: str) -> Dict[str, Any]:
        """
        Get subscription facility details.
        
        Args:
            facility_id: Subscription facility identifier
            
        Returns:
            Facility details
        """
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.subscription_facilities`
                WHERE facility_id = '{facility_id}'
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": False, "error": f"Facility {facility_id} not found"}
            
            return {
                "success": True,
                "facility": results[0],
                "source": "BigQuery"
            }
            
        except Exception as e:
            logger.error(f"Failed to get subscription facility: {e}")
            return {"success": False, "error": str(e)}
    
    def calculate_borrowing_base(self, fund_id: str) -> Dict[str, Any]:
        """
        Calculate borrowing base from LP commitments.
        
        Borrowing base = (Included LP Commitments - Exclusions) * Advance Rate
        
        Args:
            fund_id: Fund identifier
            
        Returns:
            Borrowing base calculation
        """
        try:
            # Get all LP positions
            query = f"""
                SELECT 
                    lp_name,
                    lp_type,
                    commitment_amount,
                    called_amount,
                    uncalled_commitment
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.lp_positions`
                WHERE fund_id = '{fund_id}'
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": True, "fund_id": fund_id, "borrowing_base": 0, "message": "No LP positions found", "source": "BigQuery"}
            
            total_commitments = sum(r.get("commitment_amount", 0) for r in results)
            total_uncalled = sum(r.get("uncalled_commitment", 0) or 
                                (r.get("commitment_amount", 0) - r.get("called_amount", 0)) 
                                for r in results)
            
            # Apply standard advance rate to uncalled commitments
            advance_rate = self.ADVANCE_RATES["standard"]
            borrowing_base = total_uncalled * advance_rate
            
            return {
                "success": True,
                "fund_id": fund_id,
                "total_lps": len(results),
                "total_commitments": total_commitments,
                "total_uncalled": total_uncalled,
                "advance_rate": advance_rate,
                "borrowing_base": round(borrowing_base, 2),
                "excluded_amount": 0,  # No exclusions in basic calculation
                "source": "BigQuery"
            }
            
        except Exception as e:
            logger.error(f"Borrowing base calculation error: {e}")
            return {"success": False, "error": str(e)}
    
    def create_capital_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new capital call.
        
        Args:
            call_data: Capital call details
            
        Returns:
            Creation result
        """
        try:
            call_id = call_data.get("call_id") or f"CALL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            fund_id = call_data.get("fund_id", "")
            call_amount = call_data.get("call_amount", 0)
            call_date = call_data.get("call_date", str(date.today()))
            due_date = call_data.get("due_date", str(date.today() + timedelta(days=10)))
            purpose = call_data.get("purpose", "Investment")
            investment_name = call_data.get("investment_name", "")
            
            query = f"""
                INSERT INTO `{self.bq.project_id}.{self.bq.dataset_id}.capital_calls`
                (call_id, fund_id, call_amount, call_date, due_date, purpose,
                 amount_received, outstanding_amount, status, investment_name, created_at)
                VALUES (
                    '{call_id}',
                    '{fund_id}',
                    {call_amount},
                    '{call_date}',
                    '{due_date}',
                    '{purpose}',
                    0,
                    {call_amount},
                    'PENDING',
                    '{investment_name.replace("'", "''")}',
                    CURRENT_TIMESTAMP()
                )
            """
            
            self.bq.execute_query(query)
            
            return {
                "success": True,
                "call_id": call_id,
                "call_amount": call_amount,
                "due_date": due_date,
                "message": "Capital call created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to create capital call: {e}")
            return {"success": False, "error": str(e)}
    
    def get_capital_calls(self, fund_id: str, status: str = None) -> Dict[str, Any]:
        """
        Get capital calls for a fund.
        
        Args:
            fund_id: Fund identifier
            status: Optional status filter (PENDING, PARTIAL, COMPLETE, DEFAULTED)
            
        Returns:
            Capital calls list
        """
        try:
            if status:
                query = f"""
                    SELECT *
                    FROM `{self.bq.project_id}.{self.bq.dataset_id}.capital_calls`
                    WHERE fund_id = '{fund_id}' AND status = '{status}'
                    ORDER BY due_date ASC
                """
            else:
                query = f"""
                    SELECT *
                    FROM `{self.bq.project_id}.{self.bq.dataset_id}.capital_calls`
                    WHERE fund_id = '{fund_id}'
                    ORDER BY due_date ASC
                """
            
            results = self.bq.execute_query(query)
            
            # Calculate totals
            total_called = sum(r.get("call_amount", 0) for r in results)
            total_received = sum(r.get("amount_received", 0) or 0 for r in results)
            total_outstanding = sum(r.get("outstanding_amount", 0) or 0 for r in results)
            
            return {
                "success": True,
                "fund_id": fund_id,
                "call_count": len(results),
                "total_called": total_called,
                "total_received": total_received,
                "total_outstanding": total_outstanding,
                "calls": results,
                "source": "BigQuery"
            }
            
        except Exception as e:
            logger.error(f"Failed to get capital calls: {e}")
            return {"success": False, "error": str(e), "calls": []}
    
    def get_overdue_calls(self, fund_id: str = None) -> Dict[str, Any]:
        """
        Get overdue capital calls (past due date, not fully received).
        
        Args:
            fund_id: Optional fund filter
            
        Returns:
            Overdue calls list
        """
        try:
            if fund_id:
                query = f"""
                    SELECT *
                    FROM `{self.bq.project_id}.{self.bq.dataset_id}.capital_calls`
                    WHERE fund_id = '{fund_id}'
                    AND due_date < CURRENT_DATE()
                    AND status IN ('PENDING', 'PARTIAL')
                    ORDER BY due_date ASC
                """
            else:
                query = f"""
                    SELECT *
                    FROM `{self.bq.project_id}.{self.bq.dataset_id}.capital_calls`
                    WHERE due_date < CURRENT_DATE()
                    AND status IN ('PENDING', 'PARTIAL')
                    ORDER BY due_date ASC
                """
            
            results = self.bq.execute_query(query)
            
            total_overdue = sum(r.get("outstanding_amount", 0) or 0 for r in results)
            
            return {
                "success": True,
                "overdue_count": len(results),
                "total_overdue_amount": total_overdue,
                "overdue_calls": results,
                "source": "BigQuery"
            }
            
        except Exception as e:
            logger.error(f"Failed to get overdue calls: {e}")
            return {"success": False, "error": str(e), "overdue_calls": []}
    
    def update_call_payment(
        self, 
        call_id: str, 
        payment_amount: float
    ) -> Dict[str, Any]:
        """
        Record payment received for a capital call.
        
        Args:
            call_id: Capital call identifier
            payment_amount: Amount received
            
        Returns:
            Update result
        """
        try:
            # Get current call status
            get_query = f"""
                SELECT call_amount, amount_received, outstanding_amount
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.capital_calls`
                WHERE call_id = '{call_id}'
            """
            
            results = self.bq.execute_query(get_query)
            
            if not results:
                return {"success": False, "error": f"Call {call_id} not found"}
            
            current = results[0]
            call_amount = current.get("call_amount", 0)
            prev_received = current.get("amount_received", 0) or 0
            new_received = prev_received + payment_amount
            new_outstanding = call_amount - new_received
            
            # Determine new status
            if new_outstanding <= 0:
                new_status = "COMPLETE"
                new_outstanding = 0
            elif new_received > 0:
                new_status = "PARTIAL"
            else:
                new_status = "PENDING"
            
            # Update
            update_query = f"""
                UPDATE `{self.bq.project_id}.{self.bq.dataset_id}.capital_calls`
                SET amount_received = {new_received},
                    outstanding_amount = {new_outstanding},
                    status = '{new_status}'
                WHERE call_id = '{call_id}'
            """
            
            self.bq.execute_query(update_query)
            
            return {
                "success": True,
                "call_id": call_id,
                "payment_recorded": payment_amount,
                "total_received": new_received,
                "outstanding": new_outstanding,
                "new_status": new_status,
            }
            
        except Exception as e:
            logger.error(f"Failed to update call payment: {e}")
            return {"success": False, "error": str(e)}
    
    def get_fund_call_summary(self, fund_id: str) -> Dict[str, Any]:
        """
        Get capital call summary for a fund.
        
        Args:
            fund_id: Fund identifier
            
        Returns:
            Call summary
        """
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(call_amount) as total_called,
                    SUM(amount_received) as total_received,
                    SUM(outstanding_amount) as total_outstanding,
                    COUNTIF(status = 'PENDING') as pending_calls,
                    COUNTIF(status = 'PARTIAL') as partial_calls,
                    COUNTIF(status = 'COMPLETE') as complete_calls,
                    COUNTIF(status = 'DEFAULTED') as defaulted_calls
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.capital_calls`
                WHERE fund_id = '{fund_id}'
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": True, "fund_id": fund_id, "message": "No capital calls found"}
            
            row = results[0]
            total_called = row.get("total_called", 0) or 0
            total_received = row.get("total_received", 0) or 0
            
            return {
                "success": True,
                "fund_id": fund_id,
                "total_calls": row.get("total_calls", 0),
                "total_called": total_called,
                "total_received": total_received,
                "total_outstanding": row.get("total_outstanding", 0) or 0,
                "collection_rate": round(total_received / total_called * 100, 1) if total_called > 0 else 0,
                "by_status": {
                    "pending": row.get("pending_calls", 0),
                    "partial": row.get("partial_calls", 0),
                    "complete": row.get("complete_calls", 0),
                    "defaulted": row.get("defaulted_calls", 0),
                },
                "source": "BigQuery"
            }
            
        except Exception as e:
            logger.error(f"Fund call summary error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_subscription_tracker: Optional[SubscriptionTrackerAgent] = None


def get_subscription_tracker() -> SubscriptionTrackerAgent:
    """Get or create Subscription Tracker singleton."""
    global _subscription_tracker
    if _subscription_tracker is None:
        _subscription_tracker = SubscriptionTrackerAgent()
    return _subscription_tracker


# Convenience functions
def get_subscription_facility(facility_id: str) -> Dict[str, Any]:
    """Get subscription facility details."""
    return get_subscription_tracker().get_subscription_facility(facility_id)


def calculate_borrowing_base(fund_id: str) -> Dict[str, Any]:
    """Calculate borrowing base from LP commitments."""
    return get_subscription_tracker().calculate_borrowing_base(fund_id)


def create_capital_call(call_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new capital call."""
    return get_subscription_tracker().create_capital_call(call_data)


def get_capital_calls(fund_id: str, status: str = None) -> Dict[str, Any]:
    """Get capital calls for a fund."""
    return get_subscription_tracker().get_capital_calls(fund_id, status)


def get_overdue_calls(fund_id: str = None) -> Dict[str, Any]:
    """Get overdue capital calls."""
    return get_subscription_tracker().get_overdue_calls(fund_id)
