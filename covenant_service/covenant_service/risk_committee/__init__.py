"""
Risk Committee __init__.py

Exports for the Multi-Agent Risk Committee module.
"""

from .state import (
    DecisionVote,
    RiskLevel,
    AgentAssessment,
    LoanApplication,
    CommitteeState,
)

from .agents import (
    CreditRiskAssessor,
    ESGRiskAgent,
    MarketContextAgent,
    DevilsAdvocateAgent,
    SynthesizerAgent,
)

from .workflow import (
    RiskCommitteeWorkflow,
    run_risk_committee,
)

from .pdf_generator import (
    CreditDecisionPDFGenerator,
    generate_credit_decision_pdf,
)

from .debate_workflow import (
    MultiRoundDebateWorkflow,
    run_multi_round_debate,
)

__all__ = [
    # State
    "DecisionVote",
    "RiskLevel",
    "AgentAssessment",
    "LoanApplication",
    "CommitteeState",
    # Agents
    "CreditRiskAssessor",
    "ESGRiskAgent",
    "MarketContextAgent",
    "DevilsAdvocateAgent",
    "SynthesizerAgent",
    # Workflow
    "RiskCommitteeWorkflow",
    "run_risk_committee",
    # PDF
    "CreditDecisionPDFGenerator",
    "generate_credit_decision_pdf",
    # Debate
    "MultiRoundDebateWorkflow",
    "run_multi_round_debate",
]
