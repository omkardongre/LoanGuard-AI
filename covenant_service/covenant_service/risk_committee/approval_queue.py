"""
Approval Queue - Production Level.

Manages human approval workflow for REFER decisions.
Provides pending queue, approval/rejection, and audit trail.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import os
import threading


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """
    Represents a human approval request for a REFER decision.
    
    Created when the Risk Committee votes REFER, requiring
    escalation to a human manager for final decision.
    """
    request_id: str
    loan_id: str
    borrower_name: str
    amount: float
    sector: str
    
    # Committee decision details
    committee_decision: str  # "refer"
    committee_confidence: float
    committee_reasoning: str
    vote_breakdown: Dict[str, int]
    
    # Workflow timestamps
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    # Status
    status: ApprovalStatus = ApprovalStatus.PENDING
    
    # Reviewer details (filled when reviewed)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
    final_decision: Optional[str] = None  # "approved", "rejected"
    
    # Audit trail
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        data['reviewed_at'] = self.reviewed_at.isoformat() if self.reviewed_at else None
        data['status'] = self.status.value
        return data
    
    def add_audit_entry(self, action: str, actor: str, details: Dict[str, Any] = None):
        """Add entry to audit trail."""
        self.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "actor": actor,
            "details": details or {}
        })


class ApprovalQueue:
    """
    Manages the approval queue for REFER decisions.
    
    Production implementation stores in-memory with optional
    persistence. For full production, integrate with database.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the approval queue.
        
        Args:
            storage_path: Optional path for JSON persistence
        """
        self._requests: Dict[str, ApprovalRequest] = {}
        self._lock = threading.RLock()
        self._storage_path = storage_path
        
        # Load existing requests if storage exists
        if storage_path and os.path.exists(storage_path):
            self._load_from_storage()
    
    def create_request(
        self,
        loan_id: str,
        borrower_name: str,
        amount: float,
        sector: str,
        committee_confidence: float,
        committee_reasoning: str,
        vote_breakdown: Dict[str, int],
        expiry_hours: int = 72
    ) -> ApprovalRequest:
        """
        Create a new approval request from a REFER decision.
        
        Args:
            loan_id: The loan identifier
            borrower_name: Name of the borrower
            amount: Loan amount
            sector: Business sector
            committee_confidence: Committee confidence score
            committee_reasoning: Committee reasoning text
            vote_breakdown: Dict with vote counts per decision
            expiry_hours: Hours until request expires (default 72)
            
        Returns:
            The created ApprovalRequest
        """
        with self._lock:
            request_id = f"APR-{uuid.uuid4().hex[:8].upper()}"
            
            now = datetime.utcnow()
            # Note: expiry is optional, not currently used
            
            request = ApprovalRequest(
                request_id=request_id,
                loan_id=loan_id,
                borrower_name=borrower_name,
                amount=amount,
                sector=sector,
                committee_decision="refer",
                committee_confidence=committee_confidence,
                committee_reasoning=committee_reasoning,
                vote_breakdown=vote_breakdown,
                created_at=now,
                expires_at=None,  # Optional expiry
                status=ApprovalStatus.PENDING
            )
            
            request.add_audit_entry(
                action="created",
                actor="system",
                details={"reason": "Risk Committee REFER decision"}
            )
            
            self._requests[request_id] = request
            self._save_to_storage()
            
            return request
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific approval request by ID."""
        with self._lock:
            return self._requests.get(request_id)
    
    def get_pending(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        with self._lock:
            return [
                r for r in self._requests.values()
                if r.status == ApprovalStatus.PENDING
            ]
    
    def get_by_loan_id(self, loan_id: str) -> List[ApprovalRequest]:
        """Get all approval requests for a specific loan."""
        with self._lock:
            return [
                r for r in self._requests.values()
                if r.loan_id == loan_id
            ]
    
    def get_history(
        self,
        limit: int = 50,
        status_filter: Optional[ApprovalStatus] = None
    ) -> List[ApprovalRequest]:
        """
        Get approval history with optional filtering.
        
        Args:
            limit: Maximum number of results
            status_filter: Optional status to filter by
            
        Returns:
            List of approval requests sorted by created_at descending
        """
        with self._lock:
            requests = list(self._requests.values())
            
            if status_filter:
                requests = [r for r in requests if r.status == status_filter]
            
            # Sort by created_at descending
            requests.sort(key=lambda r: r.created_at, reverse=True)
            
            return requests[:limit]
    
    def approve(
        self,
        request_id: str,
        reviewer: str,
        notes: str = ""
    ) -> ApprovalRequest:
        """
        Approve a pending request.
        
        Args:
            request_id: The request to approve
            reviewer: Email/name of the reviewer
            notes: Optional approval notes
            
        Returns:
            The updated ApprovalRequest
            
        Raises:
            ValueError: If request not found or not pending
        """
        with self._lock:
            request = self._requests.get(request_id)
            
            if not request:
                raise ValueError(f"Request {request_id} not found")
            
            if request.status != ApprovalStatus.PENDING:
                raise ValueError(f"Request {request_id} is not pending (status: {request.status.value})")
            
            request.status = ApprovalStatus.APPROVED
            request.final_decision = "approved"
            request.reviewed_by = reviewer
            request.reviewed_at = datetime.utcnow()
            request.reviewer_notes = notes
            
            request.add_audit_entry(
                action="approved",
                actor=reviewer,
                details={"notes": notes}
            )
            
            self._save_to_storage()
            
            return request
    
    def reject(
        self,
        request_id: str,
        reviewer: str,
        notes: str = ""
    ) -> ApprovalRequest:
        """
        Reject a pending request.
        
        Args:
            request_id: The request to reject
            reviewer: Email/name of the reviewer
            notes: Optional rejection notes
            
        Returns:
            The updated ApprovalRequest
            
        Raises:
            ValueError: If request not found or not pending
        """
        with self._lock:
            request = self._requests.get(request_id)
            
            if not request:
                raise ValueError(f"Request {request_id} not found")
            
            if request.status != ApprovalStatus.PENDING:
                raise ValueError(f"Request {request_id} is not pending (status: {request.status.value})")
            
            request.status = ApprovalStatus.REJECTED
            request.final_decision = "rejected"
            request.reviewed_by = reviewer
            request.reviewed_at = datetime.utcnow()
            request.reviewer_notes = notes
            
            request.add_audit_entry(
                action="rejected",
                actor=reviewer,
                details={"notes": notes}
            )
            
            self._save_to_storage()
            
            return request
    
    def _save_to_storage(self):
        """Save requests to JSON storage if configured."""
        if not self._storage_path:
            return
        
        try:
            data = {
                request_id: request.to_dict()
                for request_id, request in self._requests.items()
            }
            
            with open(self._storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            # Log but don't fail
            print(f"Warning: Failed to save approval queue: {e}")
    
    def _load_from_storage(self):
        """Load requests from JSON storage."""
        try:
            with open(self._storage_path, 'r') as f:
                data = json.load(f)
            
            for request_id, request_data in data.items():
                # Reconstruct ApprovalRequest
                request_data['created_at'] = datetime.fromisoformat(request_data['created_at'])
                if request_data.get('reviewed_at'):
                    request_data['reviewed_at'] = datetime.fromisoformat(request_data['reviewed_at'])
                if request_data.get('expires_at'):
                    request_data['expires_at'] = datetime.fromisoformat(request_data['expires_at'])
                request_data['status'] = ApprovalStatus(request_data['status'])
                
                self._requests[request_id] = ApprovalRequest(**request_data)
        except Exception as e:
            print(f"Warning: Failed to load approval queue: {e}")


class BigQueryApprovalQueue(ApprovalQueue):
    """
    Production-level BigQuery-backed approval queue.
    
    Persists all approval requests to BigQuery for durability
    and queryability. Falls back to in-memory + JSON if BigQuery unavailable.
    """
    
    TABLE_NAME = "approval_requests"
    
    def __init__(self, storage_path: Optional[str] = None):
        super().__init__(storage_path=storage_path)
        self._bq_client = None
        self._bq_available = False
        self._init_bigquery()
    
    def _init_bigquery(self):
        """Initialize BigQuery connection."""
        try:
            from common.bigquery_client import get_bigquery_client
            self._bq_client = get_bigquery_client()
            
            # Create table if not exists
            self._ensure_table_exists()
            self._bq_available = True
            
            # Load existing requests from BigQuery
            self._load_from_bigquery()
        except Exception as e:
            print(f"BigQuery init failed, using file persistence: {e}")
            self._bq_available = False
    
    def _ensure_table_exists(self):
        """Create the approval_requests table if it doesn't exist."""
        if self._bq_client.table_exists(self.TABLE_NAME):
            return
        
        try:
            from google.cloud import bigquery as bq
            
            schema = [
                bq.SchemaField("request_id", "STRING", mode="REQUIRED"),
                bq.SchemaField("loan_id", "STRING", mode="REQUIRED"),
                bq.SchemaField("borrower_name", "STRING"),
                bq.SchemaField("amount", "FLOAT64"),
                bq.SchemaField("sector", "STRING"),
                bq.SchemaField("committee_decision", "STRING"),
                bq.SchemaField("committee_confidence", "FLOAT64"),
                bq.SchemaField("committee_reasoning", "STRING"),
                bq.SchemaField("vote_breakdown", "STRING"),  # JSON
                bq.SchemaField("created_at", "TIMESTAMP"),
                bq.SchemaField("expires_at", "TIMESTAMP"),
                bq.SchemaField("status", "STRING"),
                bq.SchemaField("reviewed_by", "STRING"),
                bq.SchemaField("reviewed_at", "TIMESTAMP"),
                bq.SchemaField("reviewer_notes", "STRING"),
                bq.SchemaField("final_decision", "STRING"),
                bq.SchemaField("audit_trail", "STRING"),  # JSON
            ]
            
            table_id = self._bq_client.get_full_table_id(self.TABLE_NAME)
            table = bq.Table(table_id, schema=schema)
            self._bq_client.client.create_table(table)
            print(f"Created BigQuery table: {table_id}")
        except Exception as e:
            print(f"Failed to create table: {e}")
    
    def _load_from_bigquery(self):
        """Load pending requests from BigQuery."""
        try:
            query = f"""
                SELECT * FROM `{self._bq_client.get_full_table_id(self.TABLE_NAME)}`
                WHERE status = 'pending'
            """
            rows = self._bq_client.execute_query(query)
            
            for row in rows:
                request = self._row_to_request(row)
                self._requests[request.request_id] = request
        except Exception as e:
            print(f"Failed to load from BigQuery: {e}")
    
    def _row_to_request(self, row: Dict[str, Any]) -> ApprovalRequest:
        """Convert BigQuery row to ApprovalRequest."""
        return ApprovalRequest(
            request_id=row['request_id'],
            loan_id=row['loan_id'],
            borrower_name=row.get('borrower_name', ''),
            amount=row.get('amount', 0.0),
            sector=row.get('sector', ''),
            committee_decision=row.get('committee_decision', 'refer'),
            committee_confidence=row.get('committee_confidence', 0.0),
            committee_reasoning=row.get('committee_reasoning', ''),
            vote_breakdown=json.loads(row.get('vote_breakdown', '{}')),
            created_at=row.get('created_at', datetime.utcnow()),
            expires_at=row.get('expires_at'),
            status=ApprovalStatus(row.get('status', 'pending')),
            reviewed_by=row.get('reviewed_by'),
            reviewed_at=row.get('reviewed_at'),
            reviewer_notes=row.get('reviewer_notes'),
            final_decision=row.get('final_decision'),
            audit_trail=json.loads(row.get('audit_trail', '[]'))
        )
    
    def _save_to_bigquery(self, request: ApprovalRequest):
        """Save request to BigQuery."""
        if not self._bq_available:
            return
        
        try:
            row = {
                'request_id': request.request_id,
                'loan_id': request.loan_id,
                'borrower_name': request.borrower_name,
                'amount': request.amount,
                'sector': request.sector,
                'committee_decision': request.committee_decision,
                'committee_confidence': request.committee_confidence,
                'committee_reasoning': request.committee_reasoning,
                'vote_breakdown': json.dumps(request.vote_breakdown),
                'created_at': request.created_at.isoformat(),
                'expires_at': request.expires_at.isoformat() if request.expires_at else None,
                'status': request.status.value,
                'reviewed_by': request.reviewed_by,
                'reviewed_at': request.reviewed_at.isoformat() if request.reviewed_at else None,
                'reviewer_notes': request.reviewer_notes,
                'final_decision': request.final_decision,
                'audit_trail': json.dumps(request.audit_trail)
            }
            
            self._bq_client.insert_rows(self.TABLE_NAME, [row])
        except Exception as e:
            print(f"Failed to save to BigQuery: {e}")
    
    def _update_in_bigquery(self, request: ApprovalRequest):
        """Update request in BigQuery."""
        if not self._bq_available:
            return
        
        try:
            # BigQuery doesn't support UPDATE via streaming API
            # For production, use DML query
            query = f"""
                UPDATE `{self._bq_client.get_full_table_id(self.TABLE_NAME)}`
                SET 
                    status = '{request.status.value}',
                    reviewed_by = '{request.reviewed_by or ''}',
                    reviewed_at = TIMESTAMP('{request.reviewed_at.isoformat() if request.reviewed_at else '1970-01-01'}'),
                    reviewer_notes = '{(request.reviewer_notes or '').replace("'", "''")}',
                    final_decision = '{request.final_decision or ''}',
                    audit_trail = '{json.dumps(request.audit_trail).replace("'", "''")}'
                WHERE request_id = '{request.request_id}'
            """
            self._bq_client.execute_query(query)
        except Exception as e:
            print(f"Failed to update BigQuery: {e}")
    
    def create_request(self, *args, **kwargs) -> ApprovalRequest:
        """Create request with BigQuery persistence."""
        request = super().create_request(*args, **kwargs)
        self._save_to_bigquery(request)
        return request
    
    def approve(self, *args, **kwargs) -> ApprovalRequest:
        """Approve request with BigQuery update."""
        request = super().approve(*args, **kwargs)
        self._update_in_bigquery(request)
        return request
    
    def reject(self, *args, **kwargs) -> ApprovalRequest:
        """Reject request with BigQuery update."""
        request = super().reject(*args, **kwargs)
        self._update_in_bigquery(request)
        return request


# Global singleton instance
_approval_queue: Optional[ApprovalQueue] = None


def get_approval_queue() -> ApprovalQueue:
    """Get the global approval queue instance.
    
    Uses BigQuery-backed queue in production, falls back to file-based.
    """
    global _approval_queue
    
    if _approval_queue is None:
        storage_path = os.environ.get(
            "APPROVAL_QUEUE_STORAGE",
            "/tmp/approval_queue.json"
        )
        
        # Try BigQuery first, fall back to file-based
        use_bigquery = os.environ.get("USE_BIGQUERY_APPROVAL", "true").lower() == "true"
        
        if use_bigquery:
            try:
                _approval_queue = BigQueryApprovalQueue(storage_path=storage_path)
                print("Using BigQuery-backed approval queue")
            except Exception as e:
                print(f"BigQuery unavailable, using file-based: {e}")
                _approval_queue = ApprovalQueue(storage_path=storage_path)
        else:
            _approval_queue = ApprovalQueue(storage_path=storage_path)
    
    return _approval_queue

