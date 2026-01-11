"""
ZARONIA Transition Module - Manage JIBAR to ZARONIA rate transition.

Production-level implementation based on SARB guidelines.
JIBAR discontinuation deadline: December 31, 2026.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from common.bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class ZARONIATransitionAgent:
    """
    Manage JIBAR to ZARONIA rate transition.
    
    Based on SARB Guidelines:
    - ZARONIA = Volume-weighted trimmed mean of overnight deposits
    - Credit Adjustment Spread (CAS) = Historical median difference
    - Compounded ZARONIA used for term rates
    - Deadline: December 31, 2026
    
    Reference: research5_lma_linkedin_insights.md, SARB documentation
    """
    
    # Rate transition deadline
    JIBAR_DISCONTINUATION = date(2026, 12, 31)
    
    # JIBAR tenors
    JIBAR_TENORS = ["1M", "3M", "6M", "12M"]
    
    # Transition statuses
    TRANSITION_STATUSES = [
        "NOT_STARTED",
        "ASSESSMENT",
        "DOCUMENTATION",
        "CONVERTED",
        "COMPLETED",
    ]
    
    # Documentation statuses
    DOC_STATUSES = [
        "NOT_STARTED",
        "RATE_SWITCH_PREPARED",
        "COUNTERPARTY_REVIEW",
        "SIGNED",
        "COMPLETED",
    ]
    
    def __init__(self):
        """Initialize ZARONIA Transition Agent."""
        self.bq = BigQueryClient()
    
    def assess_loan_transition(self, loan_id: str) -> Dict[str, Any]:
        """
        Assess a loan's JIBAR transition readiness.
        
        Args:
            loan_id: Loan identifier
            
        Returns:
            Transition assessment
        """
        try:
            # Get loan data
            loan_data = self._get_loan_data(loan_id)
            
            if not loan_data:
                return {"success": False, "error": f"Loan {loan_id} not found"}
            
            # Check if loan uses JIBAR
            rate_type = loan_data.get("rate_type", "")
            if "JIBAR" not in rate_type.upper():
                return {
                    "success": True,
                    "loan_id": loan_id,
                    "requires_transition": False,
                    "message": f"Loan uses {rate_type}, not JIBAR. No transition required.",
                    "source": "BigQuery",
                }
            
            # Check existing transition record
            existing = self._get_transition_record(loan_id)
            if existing:
                return {
                    "success": True,
                    "loan_id": loan_id,
                    "requires_transition": True,
                    "transition_status": existing.get("transition_status"),
                    "documentation_status": existing.get("documentation_status"),
                    "deadline": str(self.JIBAR_DISCONTINUATION),
                    "days_remaining": (self.JIBAR_DISCONTINUATION - date.today()).days,
                    "source": "BigQuery",
                }
            
            # Calculate days to deadline
            days_remaining = (self.JIBAR_DISCONTINUATION - date.today()).days
            
            # Determine urgency
            if days_remaining < 90:
                urgency = "CRITICAL"
            elif days_remaining < 180:
                urgency = "HIGH"
            elif days_remaining < 365:
                urgency = "MEDIUM"
            else:
                urgency = "LOW"
            
            return {
                "success": True,
                "loan_id": loan_id,
                "requires_transition": True,
                "current_rate": rate_type,
                "target_rate": "ZARONIA",
                "transition_status": "NOT_STARTED",
                "deadline": str(self.JIBAR_DISCONTINUATION),
                "days_remaining": days_remaining,
                "urgency": urgency,
                "recommended_actions": [
                    "Review existing loan documentation for fallback provisions",
                    "Assess impact of ZARONIA + CAS on loan economics",
                    "Prepare Rate Switch Agreement per LMA template",
                    "Engage counterparty for transition negotiation",
                ],
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Transition assessment error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_loan_data(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get loan data from BigQuery."""
        try:
            query = f"""
                SELECT 
                    loan_id,
                    borrower_id,
                    facility_amount,
                    interest_rate,
                    rate_type,
                    maturity_date,
                    status
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.loans`
                WHERE loan_id = '{loan_id}'
            """
            results = self.bq.execute_query(query)
            return results[0] if results else None
        except Exception:
            return None
    
    def _get_transition_record(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get existing transition record."""
        try:
            query = f"""
                SELECT *
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.rate_transitions`
                WHERE loan_id = '{loan_id}'
                ORDER BY created_at DESC
                LIMIT 1
            """
            results = self.bq.execute_query(query)
            return results[0] if results else None
        except Exception:
            return None
    
    def initiate_transition(self, loan_id: str) -> Dict[str, Any]:
        """
        Initiate JIBAR to ZARONIA transition for a loan.
        
        Args:
            loan_id: Loan identifier
            
        Returns:
            Transition initiation result
        """
        try:
            transition_id = f"ZART-{loan_id}-{datetime.now().strftime('%Y%m%d')}"
            
            query = f"""
                INSERT INTO `{self.bq.project_id}.{self.bq.dataset_id}.rate_transitions`
                (transition_id, loan_id, original_rate_type, original_rate_name,
                 target_rate_type, target_rate_name, transition_status,
                 deadline_date, fallback_mechanism, documentation_status, created_at)
                VALUES (
                    '{transition_id}',
                    '{loan_id}',
                    'IBOR',
                    'JIBAR',
                    'RFR',
                    'ZARONIA',
                    'ASSESSMENT',
                    DATE('{self.JIBAR_DISCONTINUATION}'),
                    'ISDA_FALLBACK',
                    'NOT_STARTED',
                    CURRENT_TIMESTAMP()
                )
            """
            
            self.bq.execute_query(query)
            
            return {
                "success": True,
                "transition_id": transition_id,
                "loan_id": loan_id,
                "message": "Transition initiated from JIBAR to ZARONIA",
                "next_steps": [
                    "Calculate Credit Adjustment Spread (CAS)",
                    "Prepare Rate Switch Agreement",
                    "Schedule counterparty meeting",
                ],
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Transition initiation error: {e}")
            return {"success": False, "error": str(e)}
    
    def calculate_cas(self, jibar_tenor: str = "3M") -> Dict[str, Any]:
        """
        Calculate Credit Adjustment Spread (CAS) for JIBAR to ZARONIA.
        
        CAS = Historical median difference between JIBAR and compounded ZARONIA
        over a 5-year lookback period (per ISDA methodology).
        
        Note: In production, this would fetch from Bloomberg or SARB.
        Here we provide calculation methodology.
        """
        # CAS values are published by Bloomberg for official use
        # These are illustrative methodology values
        cas_methodology = {
            "1M": {
                "methodology": "5-year median of JIBAR 1M minus compounded ZARONIA 1M",
                "data_source": "Bloomberg SARB JIBAR Fallback Rates",
                "calculation_agent": "Bloomberg Index Services",
            },
            "3M": {
                "methodology": "5-year median of JIBAR 3M minus compounded ZARONIA 3M",
                "data_source": "Bloomberg SARB JIBAR Fallback Rates",
                "calculation_agent": "Bloomberg Index Services",
            },
            "6M": {
                "methodology": "5-year median of JIBAR 6M minus compounded ZARONIA 6M",
                "data_source": "Bloomberg SARB JIBAR Fallback Rates",
                "calculation_agent": "Bloomberg Index Services",
            },
            "12M": {
                "methodology": "5-year median of JIBAR 12M minus compounded ZARONIA 12M",
                "data_source": "Bloomberg SARB JIBAR Fallback Rates",
                "calculation_agent": "Bloomberg Index Services",
            },
        }
        
        return {
            "success": True,
            "tenor": jibar_tenor,
            "cas_details": cas_methodology.get(jibar_tenor, {}),
            "note": "Official CAS values published by Bloomberg. Check SARB for latest rates.",
            "reference": "ISDA 2020 IBOR Fallbacks Protocol",
            "source": "Methodology",
        }
    
    def update_transition_status(
        self, 
        transition_id: str, 
        status: str,
        doc_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update transition status."""
        try:
            updates = [f"transition_status = '{status}'"]
            
            if doc_status:
                updates.append(f"documentation_status = '{doc_status}'")
            
            if status == "CONVERTED":
                updates.append("transition_date = CURRENT_DATE()")
            
            query = f"""
                UPDATE `{self.bq.project_id}.{self.bq.dataset_id}.rate_transitions`
                SET {', '.join(updates)}
                WHERE transition_id = '{transition_id}'
            """
            
            self.bq.execute_query(query)
            
            return {
                "success": True,
                "transition_id": transition_id,
                "new_status": status,
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Status update error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_transition_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio-level JIBAR transition summary."""
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total_transitions,
                    COUNTIF(transition_status = 'COMPLETED') as completed,
                    COUNTIF(transition_status = 'CONVERTED') as converted,
                    COUNTIF(transition_status = 'DOCUMENTATION') as in_documentation,
                    COUNTIF(transition_status = 'ASSESSMENT') as in_assessment,
                    COUNTIF(transition_status = 'NOT_STARTED') as not_started
                FROM `{self.bq.project_id}.{self.bq.dataset_id}.rate_transitions`
                WHERE target_rate_name = 'ZARONIA'
            """
            
            results = self.bq.execute_query(query)
            
            if not results:
                return {"success": True, "total_transitions": 0, "source": "BigQuery"}
            
            row = results[0]
            total = row.get("total_transitions", 0) or 0
            completed = (row.get("completed", 0) or 0) + (row.get("converted", 0) or 0)
            
            return {
                "success": True,
                "deadline": str(self.JIBAR_DISCONTINUATION),
                "days_remaining": (self.JIBAR_DISCONTINUATION - date.today()).days,
                "total_transitions": total,
                "by_status": {
                    "completed": row.get("completed", 0),
                    "converted": row.get("converted", 0),
                    "in_documentation": row.get("in_documentation", 0),
                    "in_assessment": row.get("in_assessment", 0),
                    "not_started": row.get("not_started", 0),
                },
                "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
                "source": "BigQuery",
            }
            
        except Exception as e:
            logger.error(f"Portfolio summary error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_zaronia_agent: Optional[ZARONIATransitionAgent] = None


def get_zaronia_agent() -> ZARONIATransitionAgent:
    """Get or create ZARONIA Transition Agent singleton."""
    global _zaronia_agent
    if _zaronia_agent is None:
        _zaronia_agent = ZARONIATransitionAgent()
    return _zaronia_agent


# Convenience functions
def assess_jibar_transition(loan_id: str) -> Dict[str, Any]:
    """Assess loan's JIBAR transition readiness."""
    return get_zaronia_agent().assess_loan_transition(loan_id)


def initiate_zaronia_transition(loan_id: str) -> Dict[str, Any]:
    """Initiate JIBAR to ZARONIA transition."""
    return get_zaronia_agent().initiate_transition(loan_id)


def get_zaronia_transition_summary() -> Dict[str, Any]:
    """Get portfolio ZARONIA transition summary."""
    return get_zaronia_agent().get_transition_portfolio_summary()


def calculate_jibar_cas(tenor: str = "3M") -> Dict[str, Any]:
    """Get CAS calculation methodology."""
    return get_zaronia_agent().calculate_cas(tenor)
