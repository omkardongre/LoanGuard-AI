"""
Risk Committee State definitions.

Defines the state structure for multi-agent credit risk decision workflow.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class DecisionVote(Enum):
    """Agent vote for credit decision."""
    APPROVE = "approve"
    DECLINE = "decline"
    REFER = "refer"
    CAUTION = "caution"


class RiskLevel(Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentAssessment:
    """Individual agent's assessment."""
    agent_name: str
    vote: DecisionVote
    confidence: float
    reasoning: str
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LoanApplication:
    """Loan application data for assessment."""
    loan_id: str
    borrower_name: str
    sector: str
    amount: float
    term_months: int = 60
    interest_rate: float = 0.05
    collateral_value: float = 0.0
    existing_debt: float = 0.0
    annual_revenue: float = 0.0
    credit_score: int = 700
    location: str = ""
    # Employment data for ML model (required for production)
    employment_length: str = "5 years"
    home_ownership: str = "RENT"


@dataclass
class CommitteeState:
    """
    State for the Risk Committee workflow.
    
    Tracks the loan application, all agent assessments,
    and the final synthesized decision.
    """
    # Input
    loan_application: LoanApplication
    
    # Agent assessments (populated during workflow)
    credit_risk_assessment: Optional[AgentAssessment] = None
    esg_risk_assessment: Optional[AgentAssessment] = None
    market_context_assessment: Optional[AgentAssessment] = None
    devils_advocate_assessment: Optional[AgentAssessment] = None
    
    # Synthesis
    final_decision: Optional[DecisionVote] = None
    final_confidence: float = 0.0
    final_reasoning: str = ""
    consensus_achieved: bool = False
    
    # Audit trail
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    workflow_started: datetime = field(default_factory=datetime.utcnow)
    workflow_completed: Optional[datetime] = None
    
    # Debate/Iteration tracking
    current_round: int = 1
    max_rounds: int = 2
    round_history: List[Dict[str, Any]] = field(default_factory=list)
    convergence_achieved: bool = False
    convergence_round: Optional[int] = None
    
    def add_audit_entry(self, agent: str, action: str, details: Dict[str, Any]) -> None:
        """Add an entry to the audit trail."""
        self.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "action": action,
            "details": details
        })
    
    def get_all_assessments(self) -> List[AgentAssessment]:
        """Get all completed assessments."""
        assessments = []
        for assessment in [
            self.credit_risk_assessment,
            self.esg_risk_assessment,
            self.market_context_assessment,
            self.devils_advocate_assessment
        ]:
            if assessment is not None:
                assessments.append(assessment)
        return assessments
    
    def get_vote_summary(self) -> Dict[str, int]:
        """Summarize votes from all agents."""
        votes = {"approve": 0, "decline": 0, "refer": 0, "caution": 0}
        for assessment in self.get_all_assessments():
            votes[assessment.vote.value] += 1
        return votes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for API response."""
        assessments = self.get_all_assessments()
        return {
            "loan_id": self.loan_application.loan_id,
            "borrower_name": self.loan_application.borrower_name,
            "sector": self.loan_application.sector,
            "amount": self.loan_application.amount,
            "final_decision": self.final_decision.value if self.final_decision else None,
            "final_confidence": self.final_confidence,
            "final_reasoning": self.final_reasoning,
            "consensus_achieved": self.consensus_achieved,
            "agent_votes": [
                {
                    "agent": a.agent_name,
                    "vote": a.vote.value,
                    "confidence": a.confidence,
                    "reasoning": a.reasoning,
                    "risk_factors": a.risk_factors,
                    "recommendations": a.recommendations
                }
                for a in assessments
            ],
            "vote_summary": self.get_vote_summary(),
            "audit_trail": self.audit_trail,
            "workflow_started": self.workflow_started.isoformat(),
            "workflow_completed": self.workflow_completed.isoformat() if self.workflow_completed else None,
            "total_agents": len(assessments),
            # Debate tracking
            "rounds_completed": self.current_round,
            "max_rounds": self.max_rounds,
            "convergence_achieved": self.convergence_achieved,
            "convergence_round": self.convergence_round,
            "round_history": self.round_history
        }

