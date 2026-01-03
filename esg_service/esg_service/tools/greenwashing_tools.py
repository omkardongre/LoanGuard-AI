"""
Greenwashing detection tools.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Vague terms that may indicate greenwashing
VAGUE_TERMS = [
    "eco-friendly", "sustainable", "green", "clean", "natural",
    "environmentally conscious", "planet-friendly", "carbon neutral",
    "net zero", "climate positive",
]

# Terms that require verification
CLAIMS_REQUIRING_VERIFICATION = [
    "certified", "verified", "audited", "third-party",
    "ISO 14001", "science-based targets", "SBTi",
]


def analyze_esg_claims(
    claims_text: str,
    loan_id: str,
) -> Dict[str, Any]:
    """
    Analyze ESG claims for potential greenwashing.

    Args:
        claims_text: Text containing ESG claims
        loan_id: Loan identifier

    Returns:
        Analysis of ESG claims
    """
    findings = []
    text_lower = claims_text.lower()

    # Check for vague terms
    vague_found = []
    for term in VAGUE_TERMS:
        if term in text_lower:
            vague_found.append(term)
            findings.append({
                "type": "VAGUE_CLAIM",
                "term": term,
                "severity": "MEDIUM",
                "recommendation": f"Quantify or remove vague term '{term}'",
            })

    # Check for claims requiring verification
    verification_claims = []
    for term in CLAIMS_REQUIRING_VERIFICATION:
        if term in text_lower:
            verification_claims.append(term)

    # Check for quantified claims
    numbers = re.findall(r'\d+(?:\.\d+)?%', claims_text)
    quantified = len(numbers) > 0

    return {
        "success": True,
        "loan_id": loan_id,
        "vague_terms_found": vague_found,
        "verification_claims": verification_claims,
        "quantified_claims": quantified,
        "findings": findings,
        "claim_quality": "HIGH" if quantified and not vague_found else "MEDIUM" if quantified else "LOW",
    }


def check_verification_gaps(
    loan_id: str,
    claimed_certifications: List[str],
    verified_certifications: List[str],
) -> Dict[str, Any]:
    """
    Check for gaps between claimed and verified certifications.

    Args:
        loan_id: Loan identifier
        claimed_certifications: List of claimed certifications
        verified_certifications: List of verified certifications

    Returns:
        Gap analysis
    """
    claimed_set = set(c.lower() for c in claimed_certifications)
    verified_set = set(v.lower() for v in verified_certifications)
    
    gaps = claimed_set - verified_set
    verified_matches = claimed_set & verified_set

    if gaps:
        risk_level = "HIGH" if len(gaps) > 2 else "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "success": True,
        "loan_id": loan_id,
        "claimed_count": len(claimed_certifications),
        "verified_count": len(verified_certifications),
        "gaps": list(gaps),
        "verified_matches": list(verified_matches),
        "gap_count": len(gaps),
        "verification_rate": round(len(verified_matches) / len(claimed_set) * 100, 1) if claimed_set else 100,
        "risk_level": risk_level,
    }


def compare_claims_vs_actions(
    loan_id: str,
    esg_claims: Dict[str, Any],
    actual_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compare ESG claims against actual performance metrics.

    Args:
        loan_id: Loan identifier
        esg_claims: Dictionary of ESG claims
        actual_metrics: Dictionary of actual performance

    Returns:
        Comparison analysis
    """
    inconsistencies = []
    
    # Compare carbon claims
    claimed_carbon = esg_claims.get("carbon_reduction_claimed", 0)
    actual_carbon = actual_metrics.get("carbon_reduction_actual", 0)
    
    if claimed_carbon > 0 and actual_carbon > 0:
        variance = ((claimed_carbon - actual_carbon) / claimed_carbon) * 100
        if variance > 20:
            inconsistencies.append({
                "metric": "carbon_reduction",
                "claimed": claimed_carbon,
                "actual": actual_carbon,
                "variance_pct": round(variance, 1),
                "severity": "HIGH" if variance > 50 else "MEDIUM",
            })

    # Compare renewable energy claims
    claimed_renewable = esg_claims.get("renewable_energy_claimed", 0)
    actual_renewable = actual_metrics.get("renewable_energy_actual", 0)
    
    if claimed_renewable > 0 and actual_renewable > 0:
        variance = ((claimed_renewable - actual_renewable) / claimed_renewable) * 100
        if variance > 10:
            inconsistencies.append({
                "metric": "renewable_energy",
                "claimed": claimed_renewable,
                "actual": actual_renewable,
                "variance_pct": round(variance, 1),
                "severity": "HIGH" if variance > 30 else "MEDIUM",
            })

    if inconsistencies:
        max_severity = max(i["severity"] for i in inconsistencies)
        risk_level = "HIGH" if max_severity == "HIGH" else "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "success": True,
        "loan_id": loan_id,
        "inconsistency_count": len(inconsistencies),
        "inconsistencies": inconsistencies,
        "risk_level": risk_level,
        "recommendation": "Review and reconcile discrepancies" if inconsistencies else "Claims align with metrics",
    }


def calculate_greenwashing_score(
    claim_analysis: Dict[str, Any],
    verification_gaps: Dict[str, Any],
    claims_vs_actions: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate overall greenwashing risk score.

    Args:
        claim_analysis: Results from analyze_esg_claims
        verification_gaps: Results from check_verification_gaps
        claims_vs_actions: Results from compare_claims_vs_actions

    Returns:
        Composite greenwashing risk score
    """
    try:
        # Score components (0-100, higher = more risk)
        
        # Vague claims component
        vague_count = len(claim_analysis.get("vague_terms_found", []))
        vague_score = min(vague_count * 15, 40)
        
        # Verification gaps component
        gap_count = verification_gaps.get("gap_count", 0)
        verification_rate = verification_gaps.get("verification_rate", 100)
        verification_score = min((100 - verification_rate) * 0.5 + gap_count * 10, 30)
        
        # Claims vs actions component
        inconsistency_count = len(claims_vs_actions.get("inconsistencies", []))
        high_severity = sum(
            1 for i in claims_vs_actions.get("inconsistencies", [])
            if i.get("severity") == "HIGH"
        )
        actions_score = min(inconsistency_count * 10 + high_severity * 15, 30)
        
        # Composite score
        total_score = vague_score + verification_score + actions_score
        
        # Risk level
        if total_score >= 60:
            risk_level = "HIGH"
        elif total_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "success": True,
            "greenwashing_score": round(total_score, 1),
            "risk_level": risk_level,
            "score_breakdown": {
                "vague_claims_score": round(vague_score, 1),
                "verification_gaps_score": round(verification_score, 1),
                "claims_actions_score": round(actions_score, 1),
            },
            "max_score": 100,
            "recommendation": _get_greenwashing_recommendation(risk_level),
        }
    except Exception as e:
        logger.error(f"Greenwashing score calculation error: {e}")
        return {"success": False, "error": str(e)}


def _get_greenwashing_recommendation(risk_level: str) -> str:
    """Get recommendation based on risk level."""
    recommendations = {
        "HIGH": "Immediate review required. Request additional verification and clarification of ESG claims.",
        "MEDIUM": "Enhanced monitoring recommended. Request documentation for unverified claims.",
        "LOW": "Standard monitoring. ESG claims appear substantiated.",
    }
    return recommendations.get(risk_level, "Review ESG documentation.")
