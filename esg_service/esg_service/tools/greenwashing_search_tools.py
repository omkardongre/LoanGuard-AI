"""
Enhanced Greenwashing Detection with External Search - V8 Production

Cross-checks ESG claims against external news sources using:
- Google Custom Search API (primary)
- News API (supplementary validation)

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
from dataclasses import dataclass, field
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class GreenwashingRisk(Enum):
    """Greenwashing risk levels."""
    CRITICAL = "CRITICAL"
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
    "criticism", "criticized", "emissions", "spill",
    "breach", "deceptive", "false claims", "regulators",
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
    published_at: str = ""


@dataclass
class GreenwashingReport:
    """Complete greenwashing analysis report."""
    borrower: str
    analysis_timestamp: str
    claims_analyzed: int
    overall_score: float
    overall_risk: str
    high_risk_claims: int
    contradicted_claims: int
    results: List[Dict[str, Any]] = field(default_factory=list)
    news_alerts: List[Dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""
    external_search_enabled: bool = False
    news_api_enabled: bool = False


class GreenwashingDetector:
    """
    Production-grade greenwashing detection using:
    1. Google Custom Search API - for web-wide contradiction search
    2. News API - for real-time news validation
    
    V8 Enhancement: Added News API integration for enhanced detection.
    """
    
    GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
    NEWS_API_URL = "https://newsapi.org/v2/everything"
    
    def __init__(
        self,
        search_api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None,
        news_api_key: Optional[str] = None,
    ):
        """
        Initialize detector with API credentials.
        
        Args:
            search_api_key: Google API key (defaults to env var)
            search_engine_id: Custom Search Engine ID (defaults to env var)
            news_api_key: News API key (defaults to env var)
        """
        self.search_api_key = search_api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.news_api_key = news_api_key or os.getenv("NEWS_API_KEY")
        
        self.search_enabled = bool(self.search_api_key and self.search_engine_id)
        self.news_enabled = bool(self.news_api_key)
        
        if not self.search_enabled:
            logger.warning(
                "Google Search API not configured. "
                "Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID."
            )
        
        if not self.news_enabled:
            logger.info("News API not configured. News validation disabled.")
    
    async def detect_greenwashing(
        self,
        borrower_name: str,
        esg_claims: List[Dict[str, Any]],
        include_external_search: bool = True,
        include_news_search: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze ESG claims for potential greenwashing.
        
        Args:
            borrower_name: Company name
            esg_claims: List of claims like {"text": "Carbon neutral by 2030", "category": "emissions"}
            include_external_search: Whether to search Google
            include_news_search: Whether to search News API
        
        Returns:
            Comprehensive greenwashing analysis with risk score
        """
        results = []
        news_alerts = []
        
        # 1. Search for general company news alerts (if News API enabled)
        if include_news_search and self.news_enabled:
            news_alerts = await self._search_company_news(borrower_name)
        
        # 2. Analyze each claim
        for claim in esg_claims:
            claim_text = claim.get("text", "")
            category = claim.get("category", "general")
            
            # Analyze claim language for red flags
            language_analysis = self._analyze_language(claim_text)
            
            # Search for external evidence (if enabled)
            contradictions = []
            supporting = []
            
            if include_external_search and self.search_enabled:
                contradictions = await self._search_contradictions(
                    borrower_name, claim_text
                )
                supporting = await self._search_supporting(
                    borrower_name, claim_text
                )
            
            # Calculate verification score
            score = self._calculate_verification_score(
                language_analysis, contradictions, supporting
            )
            
            # Determine verdict and risk
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
            high_risk = [r for r in results if r["risk_level"] in ["HIGH", "CRITICAL"]]
            contradicted = [r for r in results if r["verdict"] == "CONTRADICTED"]
        else:
            avg_score = 1.0
            high_risk = []
            contradicted = []
        
        # Factor in news alerts
        critical_news = [n for n in news_alerts if n.get("severity") == "CRITICAL"]
        if critical_news:
            avg_score = max(0.1, avg_score - 0.2)
        
        overall_risk = self._determine_overall_risk(
            avg_score, high_risk, contradicted, news_alerts
        )
        
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
            "news_alerts": news_alerts,
            "news_alert_count": len(news_alerts),
            "external_search_enabled": self.search_enabled and include_external_search,
            "news_api_enabled": self.news_enabled and include_news_search,
            "recommendation": self._get_recommendation(
                overall_risk, high_risk, contradicted, news_alerts
            ),
            "regulatory_context": {
                "dws_fine_2025": "€25M for ESG greenwashing",
                "cma_enforcement": "Starting Autumn 2025",
                "eu_sfdr": "ESG disclosure requirements",
                "risk_if_undetected": "Up to €25M+ in regulatory fines",
            },
        }
    
    def _analyze_language(self, claim_text: str) -> Dict[str, Any]:
        """Analyze ESG claim language for red flags."""
        import re
        
        text_lower = claim_text.lower()
        flags = []
        
        # Check for vague terms
        vague_found = [term for term in VAGUE_TERMS if term in text_lower]
        
        # Check for quantification (numbers/percentages)
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
    
    async def _search_company_news(
        self,
        company: str,
    ) -> List[Dict[str, Any]]:
        """Search for recent company news related to ESG/greenwashing."""
        if not self.news_enabled:
            return []
        
        queries = [
            f"{company} greenwashing",
            f"{company} ESG controversy",
            f"{company} environmental fine",
        ]
        
        alerts = []
        
        for query in queries:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(
                        self.NEWS_API_URL,
                        params={
                            "q": query,
                            "language": "en",
                            "sortBy": "publishedAt",
                            "pageSize": 5,
                            "apiKey": self.news_api_key,
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        for article in data.get("articles", [])[:3]:
                            title = article.get("title", "").lower()
                            description = article.get("description", "") or ""
                            
                            # Determine severity
                            severity = "LOW"
                            combined_text = f"{title} {description}".lower()
                            
                            if any(kw in combined_text for kw in 
                                   ["fine", "fined", "penalty", "lawsuit", "fraud"]):
                                severity = "CRITICAL"
                            elif any(kw in combined_text for kw in 
                                     ["investigation", "accused", "controversy"]):
                                severity = "HIGH"
                            elif any(kw in combined_text for kw in NEGATIVE_KEYWORDS):
                                severity = "MEDIUM"
                            
                            if severity != "LOW":
                                alerts.append({
                                    "title": article.get("title"),
                                    "source": article.get("source", {}).get("name"),
                                    "url": article.get("url"),
                                    "published_at": article.get("publishedAt"),
                                    "description": description[:200],
                                    "severity": severity,
                                    "query": query,
                                })
            except Exception as e:
                logger.warning(f"News API error for query '{query}': {e}")
        
        # Deduplicate by title
        seen_titles = set()
        unique_alerts = []
        for alert in alerts:
            title_key = alert.get("title", "")[:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_alerts.append(alert)
        
        return unique_alerts
    
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
        
        params = {
            "key": self.search_api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num, 10),
            "dateRestrict": "y2",  # Last 2 years
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.GOOGLE_SEARCH_URL, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("items", [])
                else:
                    logger.warning(f"Search API returned status {response.status_code}")
                    return []
        except httpx.TimeoutException:
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
        """
        Calculate verification score (0-1, higher = more trustworthy).
        
        V8.1 FIX: Improved algorithm to prevent 0% scores and provide
        more nuanced scoring based on evidence ratio.
        
        Scoring logic:
        - Base score starts at 0.5
        - Language quality can add up to +0.4
        - Contradictions reduce score (max -0.35 to preserve floor)
        - Supporting evidence adds up to +0.15
        - Evidence ratio impacts final score
        - Minimum floor of 0.05 (5%) for any analyzed claim
        """
        base_score = 0.5
        
        # Language quality adjustments (+0.4 max)
        if language_analysis["has_numbers"]:
            base_score += 0.15  # Has quantifiable metrics
        if language_analysis["has_timeline"]:
            base_score += 0.10  # Has specific timeline
        if language_analysis["has_verification"]:
            base_score += 0.15  # Claims third-party verification
        
        # Vague terms penalty (max -0.15)
        vague_penalty = min(len(language_analysis["vague_terms"]) * 0.03, 0.15)
        base_score -= vague_penalty
        
        # External evidence adjustments
        high_severity_contradictions = sum(
            1 for c in contradictions if c.severity == "HIGH"
        )
        medium_severity_contradictions = len(contradictions) - high_severity_contradictions
        
        # Cap contradiction penalties to preserve meaningful scores
        # HIGH severity: -0.12 each (max 3 = -0.36)
        # MEDIUM severity: -0.06 each (max 3 = -0.18)
        high_penalty = min(high_severity_contradictions * 0.12, 0.36)
        medium_penalty = min(medium_severity_contradictions * 0.06, 0.18)
        
        # Total contradiction penalty capped at 0.35
        contradiction_penalty = min(high_penalty + medium_penalty, 0.35)
        base_score -= contradiction_penalty
        
        # Supporting evidence bonus (+0.04 each, max +0.15)
        supporting_bonus = min(len(supporting) * 0.04, 0.15)
        base_score += supporting_bonus
        
        # Evidence ratio adjustment: if supporting outweighs contradicting
        if supporting and contradictions:
            ratio = len(supporting) / len(contradictions)
            if ratio > 1.5:
                base_score += 0.05  # More supporting than contradicting
            elif ratio < 0.5:
                base_score -= 0.05  # Much more contradicting
        
        # Ensure minimum floor of 5% for any analyzed claim
        # (0% suggests no analysis was done, which is misleading)
        return max(0.05, min(1.0, base_score))
    
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
        
        if score < 0.2 or (high_severity and len(contradictions) > 2):
            return GreenwashingRisk.CRITICAL
        elif score < 0.3 or high_severity:
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
        news_alerts: List[Dict],
    ) -> GreenwashingRisk:
        """Determine overall greenwashing risk."""
        critical_news = [n for n in news_alerts if n.get("severity") == "CRITICAL"]
        
        if critical_news or len(contradicted) >= 2:
            return GreenwashingRisk.CRITICAL
        elif contradicted or len(high_risk) >= 2:
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
        news_alerts: List[Dict],
    ) -> str:
        """Get recommendation based on analysis."""
        if risk == GreenwashingRisk.CRITICAL:
            critical_news = [n for n in news_alerts if n.get("severity") == "CRITICAL"]
            if critical_news:
                return (
                    "🚨 CRITICAL: Active regulatory/legal issues detected in news. "
                    "Halt ESG-linked lending until full due diligence complete. "
                    "Request legal review and independent ESG audit."
                )
            return (
                "🚨 CRITICAL: Multiple ESG claims are contradicted by external evidence. "
                "Immediate escalation to risk committee required."
            )
        elif risk == GreenwashingRisk.HIGH:
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


# Singleton instance
_detector: Optional[GreenwashingDetector] = None


def get_greenwashing_detector() -> GreenwashingDetector:
    """Get or create greenwashing detector singleton."""
    global _detector
    if _detector is None:
        _detector = GreenwashingDetector()
    return _detector


# Synchronous wrapper for non-async contexts
def detect_greenwashing_sync(
    borrower_name: str,
    esg_claims: List[Dict[str, Any]],
    search_api_key: Optional[str] = None,
    search_engine_id: Optional[str] = None,
    news_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Synchronous wrapper for greenwashing detection.
    
    Args:
        borrower_name: Company name
        esg_claims: List of ESG claims
        search_api_key: Optional Google API key
        search_engine_id: Optional Search Engine ID
        news_api_key: Optional News API key
    
    Returns:
        Greenwashing analysis result
    """
    detector = GreenwashingDetector(search_api_key, search_engine_id, news_api_key)
    
    try:
        # Check if we're in an existing event loop
        loop = asyncio.get_running_loop()
        # If we're here, we're in an async context - create a new thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                detector.detect_greenwashing(borrower_name, esg_claims)
            )
            return future.result()
    except RuntimeError:
        # No event loop running - safe to use asyncio.run
        return asyncio.run(
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


async def detect_greenwashing_async(
    borrower_name: str,
    esg_claims: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Async convenience function for greenwashing detection.
    
    Args:
        borrower_name: Company name
        esg_claims: List of ESG claims
    
    Returns:
        Greenwashing analysis result
    """
    detector = get_greenwashing_detector()
    return await detector.detect_greenwashing(borrower_name, esg_claims)
