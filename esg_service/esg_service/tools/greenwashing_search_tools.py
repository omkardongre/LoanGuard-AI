"""
Enhanced Greenwashing Detection with External Search - V6 P0 Feature

Cross-checks ESG claims against external news sources using Google Custom Search API.
This is the HERO FEATURE for the demo - catches greenwashing before regulators do.

Market Context:
- DWS fined €25M for greenwashing (2025)
- CMA enforcement starting Autumn 2025
- HSBC exited Net-Zero Banking Alliance over greenwashing fears
"""

import logging
import os
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import aiohttp

logger = logging.getLogger(__name__)


class GreenwashingRisk(Enum):
    """Greenwashing risk levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ClaimVerdict(Enum):
    """Verification verdict for ESG claims."""
    VERIFIED = "VERIFIED"
    QUESTIONABLE = "QUESTIONABLE"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"


# Vague ESG terms that require quantification (from EBA greenwashing report)
VAGUE_TERMS = [
    "eco-friendly", "sustainable", "green", "clean", "natural",
    "environmentally conscious", "planet-friendly", "carbon neutral",
    "net zero", "climate positive", "eco", "renewable",
    "environmentally friendly", "carbon negative", "climate neutral",
]

# Terms indicating third-party verification
VERIFICATION_TERMS = [
    "certified", "verified", "audited", "third-party",
    "iso 14001", "iso 50001", "science-based targets", "sbti",
    "cdp", "gri", "sasb", "tcfd", "leed", "breeam",
]

# Negative keywords for contradiction search
NEGATIVE_KEYWORDS = [
    "fine", "fined", "penalty", "lawsuit", "violation",
    "controversy", "scandal", "pollution", "accused",
    "investigation", "fraud", "misleading", "greenwashing",
    "criticized", "criticized", "emissions", "spill",
]


@dataclass
class SearchResult:
    """Search result from external source."""
    title: str
    link: str
    snippet: str
    source: str
    is_negative: bool
    severity: str


class GreenwashingDetector:
    """
    Detect ESG greenwashing by verifying claims against external sources.
    Uses Google Custom Search API for real-time verification.
    """
    
    def __init__(
        self,
        search_api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None,
    ):
        """
        Initialize detector with Google Custom Search credentials.
        
        Args:
            search_api_key: Google API key (defaults to env var)
            search_engine_id: Custom Search Engine ID (defaults to env var)
        """
        self.search_api_key = search_api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.search_enabled = bool(self.search_api_key and self.search_engine_id)
        
        if not self.search_enabled:
            logger.warning(
                "Google Search API not configured. "
                "Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID for full functionality."
            )
    
    async def detect_greenwashing(
        self,
        borrower_name: str,
        esg_claims: List[Dict[str, Any]],
        include_external_search: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze ESG claims for potential greenwashing.
        
        Args:
            borrower_name: Company name
            esg_claims: List of claims like {"text": "Carbon neutral by 2030", "category": "emissions"}
            include_external_search: Whether to search external sources
        
        Returns:
            Comprehensive greenwashing analysis with risk score
        """
        results = []
        
        for claim in esg_claims:
            claim_text = claim.get("text", "")
            category = claim.get("category", "general")
            
            # 1. Analyze claim language for red flags
            language_analysis = self._analyze_language(claim_text)
            
            # 2. Search for external evidence (if enabled)
            contradictions = []
            supporting = []
            
            if include_external_search and self.search_enabled:
                contradictions = await self._search_contradictions(
                    borrower_name, claim_text
                )
                supporting = await self._search_supporting(
                    borrower_name, claim_text
                )
            
            # 3. Calculate verification score
            score = self._calculate_verification_score(
                language_analysis, contradictions, supporting
            )
            
            # 4. Determine verdict and risk
            verdict = self._get_verdict(score)
            risk_level = self._get_risk_level(score, contradictions)
            
            results.append({
                "claim": claim_text,
                "category": category,
                "verification_score": round(score, 2),
                "verdict": verdict.value,
                "risk_level": risk_level.value,
                "language_analysis": {
                    "vague_terms_found": language_analysis["vague_terms"],
                    "has_quantification": language_analysis["has_numbers"],
                    "has_timeline": language_analysis["has_timeline"],
                    "has_verification": language_analysis["has_verification"],
                    "flags": language_analysis["flags"],
                },
                "contradictions": [
                    {
                        "title": c.title,
                        "source": c.link,
                        "snippet": c.snippet,
                        "severity": c.severity,
                    }
                    for c in contradictions[:3]
                ],
                "supporting_evidence": [
                    {
                        "title": s.title,
                        "source": s.link,
                        "snippet": s.snippet,
                    }
                    for s in supporting[:3]
                ],
            })
        
        # Overall assessment
        if results:
            avg_score = sum(r["verification_score"] for r in results) / len(results)
            high_risk = [r for r in results if r["risk_level"] == "HIGH"]
            contradicted = [r for r in results if r["verdict"] == "CONTRADICTED"]
        else:
            avg_score = 1.0
            high_risk = []
            contradicted = []
        
        overall_risk = self._determine_overall_risk(avg_score, high_risk, contradicted)
        
        return {
            "success": True,
            "borrower": borrower_name,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "claims_analyzed": len(esg_claims),
            "results": results,
            "overall_score": round(avg_score, 2),
            "overall_risk": overall_risk.value,
            "high_risk_claims": len(high_risk),
            "contradicted_claims": len(contradicted),
            "external_search_enabled": self.search_enabled and include_external_search,
            "recommendation": self._get_recommendation(overall_risk, high_risk, contradicted),
            "regulatory_context": {
                "dws_fine_2025": "€25M for ESG greenwashing",
                "cma_enforcement": "Starting Autumn 2025",
                "risk_if_undetected": "Up to €25M+ in regulatory fines",
            },
        }
    
    def _analyze_language(self, claim_text: str) -> Dict[str, Any]:
        """Analyze ESG claim language for red flags."""
        text_lower = claim_text.lower()
        flags = []
        
        # Check for vague terms
        vague_found = [term for term in VAGUE_TERMS if term in text_lower]
        
        # Check for quantification (numbers/percentages)
        import re
        has_numbers = bool(re.search(r'\d+(?:\.\d+)?%?', claim_text))
        
        # Check for timeline
        timeline_patterns = [
            r'by 20\d{2}', r'within \d+ years?', r'by the end of',
            r'target.*20\d{2}', r'goal.*20\d{2}',
        ]
        has_timeline = any(re.search(p, text_lower) for p in timeline_patterns)
        
        # Check for verification claims
        has_verification = any(term in text_lower for term in VERIFICATION_TERMS)
        
        # Generate flags
        if vague_found and not has_numbers:
            flags.append({
                "type": "VAGUE_NO_METRICS",
                "severity": "MEDIUM",
                "description": f"Vague terms ({', '.join(vague_found[:3])}) without quantification",
            })
        
        if not has_timeline:
            flags.append({
                "type": "NO_TIMELINE",
                "severity": "LOW",
                "description": "No specific timeline or target date",
            })
        
        if not has_verification and vague_found:
            flags.append({
                "type": "NO_THIRD_PARTY_VERIFICATION",
                "severity": "MEDIUM",
                "description": "No mention of third-party certification or verification",
            })
        
        return {
            "vague_terms": vague_found,
            "has_numbers": has_numbers,
            "has_timeline": has_timeline,
            "has_verification": has_verification,
            "flags": flags,
            "flag_count": len(flags),
        }
    
    async def _search_contradictions(
        self,
        company: str,
        claim: str,
    ) -> List[SearchResult]:
        """Search for news that contradicts the ESG claim."""
        queries = [
            f"{company} environmental fine",
            f"{company} pollution violation",
            f"{company} greenwashing",
            f"{company} ESG controversy",
            f"{company} emissions scandal",
        ]
        
        contradictions = []
        
        for query in queries[:3]:  # Limit to 3 queries to manage API costs
            try:
                results = await self._google_search(query, num=3)
                for r in results:
                    if self._is_negative_news(r.get("snippet", "")):
                        severity = "HIGH" if any(
                            kw in r.get("snippet", "").lower()
                            for kw in ["fine", "fined", "penalty", "lawsuit"]
                        ) else "MEDIUM"
                        
                        contradictions.append(SearchResult(
                            title=r.get("title", ""),
                            link=r.get("link", ""),
                            snippet=r.get("snippet", ""),
                            source=r.get("displayLink", ""),
                            is_negative=True,
                            severity=severity,
                        ))
            except Exception as e:
                logger.warning(f"Search error for query '{query}': {e}")
        
        return contradictions
    
    async def _search_supporting(
        self,
        company: str,
        claim: str,
    ) -> List[SearchResult]:
        """Search for evidence supporting the ESG claim."""
        # Extract key terms from claim
        queries = [
            f"{company} sustainability report",
            f"{company} ESG certification verified",
            f"{company} carbon reduction progress",
        ]
        
        supporting = []
        
        for query in queries[:2]:  # Limit queries
            try:
                results = await self._google_search(query, num=3)
                for r in results:
                    if not self._is_negative_news(r.get("snippet", "")):
                        supporting.append(SearchResult(
                            title=r.get("title", ""),
                            link=r.get("link", ""),
                            snippet=r.get("snippet", ""),
                            source=r.get("displayLink", ""),
                            is_negative=False,
                            severity="LOW",
                        ))
            except Exception as e:
                logger.warning(f"Search error for query '{query}': {e}")
        
        return supporting
    
    async def _google_search(
        self,
        query: str,
        num: int = 5,
    ) -> List[Dict[str, Any]]:
        """Execute Google Custom Search API request."""
        if not self.search_enabled:
            return []
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.search_api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num, 10),
            "dateRestrict": "y2",  # Last 2 years
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("items", [])
                    else:
                        logger.warning(f"Search API returned status {resp.status}")
                        return []
        except asyncio.TimeoutError:
            logger.warning(f"Search timeout for query: {query}")
            return []
        except Exception as e:
            logger.error(f"Search API error: {e}")
            return []
    
    def _is_negative_news(self, text: str) -> bool:
        """Check if text contains negative ESG indicators."""
        text_lower = text.lower()
        return any(kw in text_lower for kw in NEGATIVE_KEYWORDS)
    
    def _calculate_verification_score(
        self,
        language_analysis: Dict[str, Any],
        contradictions: List[SearchResult],
        supporting: List[SearchResult],
    ) -> float:
        """Calculate verification score (0-1, higher = more trustworthy)."""
        base_score = 0.5
        
        # Language quality adjustments
        if language_analysis["has_numbers"]:
            base_score += 0.15
        if language_analysis["has_timeline"]:
            base_score += 0.1
        if language_analysis["has_verification"]:
            base_score += 0.15
        
        # Vague terms penalty
        base_score -= len(language_analysis["vague_terms"]) * 0.05
        
        # External evidence adjustments
        high_severity_contradictions = sum(
            1 for c in contradictions if c.severity == "HIGH"
        )
        base_score -= high_severity_contradictions * 0.2
        base_score -= (len(contradictions) - high_severity_contradictions) * 0.1
        
        # Supporting evidence
        base_score += len(supporting) * 0.05
        
        return max(0.0, min(1.0, base_score))
    
    def _get_verdict(self, score: float) -> ClaimVerdict:
        """Get verification verdict based on score."""
        if score >= 0.7:
            return ClaimVerdict.VERIFIED
        elif score >= 0.4:
            return ClaimVerdict.QUESTIONABLE
        elif score >= 0.2:
            return ClaimVerdict.UNVERIFIED
        else:
            return ClaimVerdict.CONTRADICTED
    
    def _get_risk_level(
        self,
        score: float,
        contradictions: List[SearchResult],
    ) -> GreenwashingRisk:
        """Get risk level based on score and contradictions."""
        high_severity = any(c.severity == "HIGH" for c in contradictions)
        
        if score < 0.3 or high_severity:
            return GreenwashingRisk.HIGH
        elif score < 0.6:
            return GreenwashingRisk.MEDIUM
        else:
            return GreenwashingRisk.LOW
    
    def _determine_overall_risk(
        self,
        avg_score: float,
        high_risk: List[Dict],
        contradicted: List[Dict],
    ) -> GreenwashingRisk:
        """Determine overall greenwashing risk."""
        if contradicted or len(high_risk) >= 2:
            return GreenwashingRisk.HIGH
        elif high_risk or avg_score < 0.5:
            return GreenwashingRisk.MEDIUM
        else:
            return GreenwashingRisk.LOW
    
    def _get_recommendation(
        self,
        risk: GreenwashingRisk,
        high_risk: List[Dict],
        contradicted: List[Dict],
    ) -> str:
        """Get recommendation based on analysis."""
        if risk == GreenwashingRisk.HIGH:
            if contradicted:
                return (
                    "🚨 URGENT: Found contradictions to ESG claims. "
                    "Immediate review required before regulatory exposure. "
                    "Request detailed documentation and third-party verification."
                )
            return (
                "⚠️ HIGH RISK: Multiple claims flagged for greenwashing indicators. "
                "Request supporting documentation and consider enhanced due diligence."
            )
        elif risk == GreenwashingRisk.MEDIUM:
            return (
                "⚠️ MODERATE RISK: Some claims need additional verification. "
                "Request supporting evidence for flagged claims."
            )
        else:
            return (
                "✅ LOW RISK: ESG claims appear substantiated. "
                "Continue standard monitoring."
            )


# Synchronous wrapper for non-async contexts
def detect_greenwashing_sync(
    borrower_name: str,
    esg_claims: List[Dict[str, Any]],
    search_api_key: Optional[str] = None,
    search_engine_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Synchronous wrapper for greenwashing detection.
    
    Args:
        borrower_name: Company name
        esg_claims: List of ESG claims
        search_api_key: Optional Google API key
        search_engine_id: Optional Search Engine ID
    
    Returns:
        Greenwashing analysis result
    """
    detector = GreenwashingDetector(search_api_key, search_engine_id)
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        detector.detect_greenwashing(borrower_name, esg_claims)
    )


# Tool function for ADK agent
def analyze_greenwashing(
    borrower_name: str,
    claims: List[str],
    categories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    ADK Tool: Analyze ESG claims for greenwashing.
    
    Args:
        borrower_name: Company name
        claims: List of ESG claim texts
        categories: Optional list of categories for each claim
    
    Returns:
        Greenwashing analysis with risk assessment
    """
    categories = categories or ["general"] * len(claims)
    
    esg_claims = [
        {"text": claim, "category": cat}
        for claim, cat in zip(claims, categories)
    ]
    
    return detect_greenwashing_sync(borrower_name, esg_claims)
