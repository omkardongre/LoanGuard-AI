"""
Multi-Agent Debate Pattern for compliance verification.

Based on AegisAgent winner pattern for adversarial challenging.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class DebateRole(Enum):
    """Roles in the debate."""
    EVIDENCE_CURATOR = "evidence_curator"
    POLICY_INTERPRETER = "policy_interpreter"
    COMPLIANCE_REVIEWER = "compliance_reviewer"
    DEVIL_ADVOCATE = "devil_advocate"


@dataclass
class DebateArgument:
    """A single argument in the debate."""
    role: DebateRole
    position: str
    evidence: List[str]
    confidence: float
    citations: List[str]


@dataclass
class DebateResult:
    """Result of a multi-agent debate."""
    consensus: bool
    final_decision: str
    confidence: float
    arguments: List[DebateArgument]
    dissenting_views: List[str]
    audit_trail: List[Dict[str, Any]]


class DebateAgent:
    """
    Multi-agent debate system for compliance verification.
    
    Based on AegisAgent pattern:
    - Evidence Curator: Gathers and validates evidence
    - Policy Interpreter: Interprets covenant/ESG rules
    - Compliance Reviewer: Makes compliance determination
    - Devil's Advocate: Challenges assumptions
    """
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.debate_rounds = 3
        self.consensus_threshold = 0.75
    
    async def gather_evidence(
        self,
        loan_id: str,
        covenant_type: str,
        measurements: Dict[str, Any],
    ) -> DebateArgument:
        """Evidence Curator agent."""
        evidence = []
        citations = []
        
        # Gather financial measurements
        if "current_value" in measurements:
            evidence.append(f"Current {covenant_type} value: {measurements['current_value']}")
            citations.append(f"Measurement dated {measurements.get('date', 'N/A')}")
        
        if "threshold" in measurements:
            evidence.append(f"Covenant threshold: {measurements['threshold']}")
            citations.append("Credit Agreement Section 7.1")
        
        if "historical" in measurements:
            trend = measurements["historical"]
            evidence.append(f"Historical trend: {trend.get('direction', 'stable')}")
            evidence.append(f"30-day average: {trend.get('avg_30d', 'N/A')}")
        
        # Calculate evidence strength
        evidence_count = len(evidence)
        confidence = min(0.95, 0.5 + evidence_count * 0.1)
        
        return DebateArgument(
            role=DebateRole.EVIDENCE_CURATOR,
            position=f"Evidence gathered for {covenant_type} compliance assessment",
            evidence=evidence,
            confidence=confidence,
            citations=citations,
        )
    
    async def interpret_policy(
        self,
        covenant_type: str,
        covenant_definition: Dict[str, Any],
        evidence: DebateArgument,
    ) -> DebateArgument:
        """Policy Interpreter agent."""
        interpretations = []
        citations = []
        
        threshold = covenant_definition.get("threshold")
        operator = covenant_definition.get("operator", "<=")
        
        if threshold:
            if operator == "<=":
                interpretations.append(f"Covenant requires {covenant_type} to be at or below {threshold}")
            elif operator == ">=":
                interpretations.append(f"Covenant requires {covenant_type} to be at or above {threshold}")
            citations.append(f"Credit Agreement: {covenant_definition.get('section', 'Section 7')}")
        
        # Check for cure periods
        if covenant_definition.get("cure_period"):
            cure_days = covenant_definition["cure_period"]
            interpretations.append(f"Cure period of {cure_days} days applies before default")
            citations.append("Credit Agreement Section 8.1(a)")
        
        # Check for material adverse change clause
        if covenant_definition.get("mac_clause"):
            interpretations.append("Material Adverse Change clause may affect interpretation")
            citations.append("Credit Agreement Section 1.1 Definitions")
        
        confidence = 0.85 if len(interpretations) >= 2 else 0.70
        
        return DebateArgument(
            role=DebateRole.POLICY_INTERPRETER,
            position="Policy interpretation complete",
            evidence=interpretations,
            confidence=confidence,
            citations=citations,
        )
    
    async def review_compliance(
        self,
        measurements: Dict[str, Any],
        policy: DebateArgument,
        evidence: DebateArgument,
    ) -> DebateArgument:
        """Compliance Reviewer agent."""
        findings = []
        citations = []
        
        current_value = measurements.get("current_value")
        threshold = measurements.get("threshold")
        operator = measurements.get("operator", "<=")
        
        if current_value is not None and threshold is not None:
            if operator == "<=" and current_value <= threshold:
                findings.append(f"COMPLIANT: {current_value} <= {threshold}")
                status = "compliant"
            elif operator == ">=" and current_value >= threshold:
                findings.append(f"COMPLIANT: {current_value} >= {threshold}")
                status = "compliant"
            else:
                findings.append(f"BREACH: {current_value} exceeds threshold {threshold}")
                status = "breach"
                
                # Check buffer
                if operator == "<=":
                    buffer = (threshold - current_value) / threshold * 100
                    findings.append(f"Buffer: {buffer:.1f}% (negative indicates breach)")
        else:
            findings.append("INSUFFICIENT DATA: Cannot determine compliance")
            status = "unknown"
        
        citations.extend(evidence.citations)
        citations.extend(policy.citations)
        
        confidence = 0.90 if status in ["compliant", "breach"] else 0.50
        
        return DebateArgument(
            role=DebateRole.COMPLIANCE_REVIEWER,
            position=f"Compliance status: {status.upper()}",
            evidence=findings,
            confidence=confidence,
            citations=citations,
        )
    
    async def challenge_assumptions(
        self,
        compliance_review: DebateArgument,
        measurements: Dict[str, Any],
    ) -> DebateArgument:
        """Devil's Advocate agent - challenges the compliance determination."""
        challenges = []
        citations = []
        
        # Challenge data freshness
        measurement_age = measurements.get("days_since_measurement", 0)
        if measurement_age > 30:
            challenges.append(f"DATA STALENESS: Measurement is {measurement_age} days old")
            citations.append("Best practice: measurements should be < 30 days old")
        
        # Challenge calculation methodology
        if measurements.get("calculation_method") == "estimated":
            challenges.append("ESTIMATION RISK: Values are estimated, not audited")
            citations.append("GAAP requires audited financials for covenant compliance")
        
        # Challenge trend direction
        if measurements.get("trend") == "deteriorating":
            challenges.append("TREND WARNING: Metrics are deteriorating over time")
            challenges.append("Current compliance may not predict future compliance")
        
        # Challenge threshold interpretation
        if measurements.get("has_amendments"):
            challenges.append("AMENDMENT RISK: Covenant may have been amended")
            citations.append("Check for recent credit agreement amendments")
        
        # If no challenges, note the strength of the determination
        if not challenges:
            challenges.append("No significant challenges to compliance determination")
            challenges.append("Evidence and policy interpretation appear sound")
        
        confidence = max(0.4, 1.0 - len(challenges) * 0.15)
        
        return DebateArgument(
            role=DebateRole.DEVIL_ADVOCATE,
            position="Challenges to compliance determination" if challenges else "No challenges",
            evidence=challenges,
            confidence=confidence,
            citations=citations,
        )
    
    async def conduct_debate(
        self,
        loan_id: str,
        covenant_type: str,
        measurements: Dict[str, Any],
        covenant_definition: Dict[str, Any],
    ) -> DebateResult:
        """
        Conduct a full multi-agent debate on compliance.
        
        Args:
            loan_id: Loan identifier
            covenant_type: Type of covenant
            measurements: Current measurements
            covenant_definition: Covenant rules
            
        Returns:
            DebateResult with consensus and audit trail
        """
        logger.info(f"Starting compliance debate for loan {loan_id}, covenant {covenant_type}")
        
        audit_trail = []
        arguments = []
        
        # Round 1: Evidence gathering
        evidence = await self.gather_evidence(loan_id, covenant_type, measurements)
        arguments.append(evidence)
        audit_trail.append({
            "round": 1,
            "agent": evidence.role.value,
            "action": "gather_evidence",
            "confidence": evidence.confidence,
        })
        
        # Round 2: Policy interpretation
        policy = await self.interpret_policy(covenant_type, covenant_definition, evidence)
        arguments.append(policy)
        audit_trail.append({
            "round": 2,
            "agent": policy.role.value,
            "action": "interpret_policy",
            "confidence": policy.confidence,
        })
        
        # Round 3: Compliance review
        compliance = await self.review_compliance(measurements, policy, evidence)
        arguments.append(compliance)
        audit_trail.append({
            "round": 3,
            "agent": compliance.role.value,
            "action": "review_compliance",
            "confidence": compliance.confidence,
        })
        
        # Round 4: Devil's advocate challenge
        challenge = await self.challenge_assumptions(compliance, measurements)
        arguments.append(challenge)
        audit_trail.append({
            "round": 4,
            "agent": challenge.role.value,
            "action": "challenge_assumptions",
            "confidence": challenge.confidence,
        })
        
        # Calculate consensus
        avg_confidence = sum(a.confidence for a in arguments) / len(arguments)
        consensus = avg_confidence >= self.consensus_threshold
        
        # Extract dissenting views
        dissenting_views = []
        if challenge.confidence < 0.6:
            dissenting_views.extend(challenge.evidence)
        
        # Determine final decision
        final_decision = compliance.position
        if not consensus:
            final_decision = f"INCONCLUSIVE - {compliance.position} (low confidence)"
        
        result = DebateResult(
            consensus=consensus,
            final_decision=final_decision,
            confidence=avg_confidence,
            arguments=arguments,
            dissenting_views=dissenting_views,
            audit_trail=audit_trail,
        )
        
        logger.info(f"Debate complete: {final_decision} (confidence: {avg_confidence:.2f})")
        
        return result


async def verify_compliance_with_debate(
    loan_id: str,
    covenant_type: str,
    current_value: float,
    threshold: float,
    operator: str = "<=",
    additional_context: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Verify compliance using multi-agent debate.
    
    Args:
        loan_id: Loan identifier
        covenant_type: Type of covenant
        current_value: Current measurement value
        threshold: Covenant threshold
        operator: Comparison operator
        additional_context: Additional context for debate
        
    Returns:
        Compliance verification result
    """
    debate_agent = DebateAgent()
    
    measurements = {
        "current_value": current_value,
        "threshold": threshold,
        "operator": operator,
        **(additional_context or {}),
    }
    
    covenant_definition = {
        "threshold": threshold,
        "operator": operator,
        "covenant_type": covenant_type,
    }
    
    result = await debate_agent.conduct_debate(
        loan_id, covenant_type, measurements, covenant_definition
    )
    
    return {
        "loan_id": loan_id,
        "covenant_type": covenant_type,
        "decision": result.final_decision,
        "consensus": result.consensus,
        "confidence": result.confidence,
        "dissenting_views": result.dissenting_views,
        "audit_trail": result.audit_trail,
    }
