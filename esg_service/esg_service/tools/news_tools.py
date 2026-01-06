"""
News API Validation Tools.

Production-level tools for validating ESG claims against
real-time news articles using News API.

Enhances greenwashing detection by cross-referencing company
claims with actual news coverage.

API Docs: https://newsapi.org/docs
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import requests

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Configuration
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_BASE_URL = "https://newsapi.org/v2"


class ClaimCredibility(Enum):
    """ESG claim credibility levels."""
    CREDIBLE = "CREDIBLE"           # Strong supporting evidence
    LIKELY_CREDIBLE = "LIKELY_CREDIBLE"  # Some supporting evidence
    UNCERTAIN = "UNCERTAIN"         # Mixed or no evidence
    QUESTIONABLE = "QUESTIONABLE"   # Some contradicting evidence
    LIKELY_FALSE = "LIKELY_FALSE"   # Strong contradicting evidence


class SentimentType(Enum):
    """News article sentiment."""
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    MIXED = "MIXED"


@dataclass
class NewsArticle:
    """News article structure."""
    title: str
    description: str
    source: str
    url: str
    published_at: datetime
    relevance_score: float = 0.0
    sentiment: str = "NEUTRAL"


class NewsValidator:
    """
    Production-grade ESG claim validator using News API.
    
    Cross-references company ESG claims against real-time
    news coverage to detect potential greenwashing.
    """
    
    KEYWORDS_POSITIVE = [
        "achieves", "exceeds", "certified", "awarded", "recognized",
        "sustainable", "green", "environmental leader", "carbon neutral",
        "net zero", "renewable", "clean energy", "sustainability report"
    ]
    
    KEYWORDS_NEGATIVE = [
        "lawsuit", "fine", "violation", "pollution", "scandal",
        "greenwashing", "accused", "investigation", "misleading",
        "false claims", "environmental damage", "toxic", "spill",
        "emissions breach", "regulatory action", "penalty"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from env or parameter."""
        self.api_key = api_key or NEWS_API_KEY
    
    @property
    def available(self) -> bool:
        """Check if News API is configured."""
        return bool(self.api_key)
    
    def search_news(
        self,
        query: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_by: str = "relevancy",
        page_size: int = 10,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Search for news articles.
        
        Args:
            query: Search query
            from_date: Start date for articles
            to_date: End date for articles
            sort_by: Sort option (relevancy, popularity, publishedAt)
            page_size: Number of results
            language: Language code
            
        Returns:
            News search results
        """
        if not self.available:
            return {
                "success": False,
                "error": "News API not configured. Set NEWS_API_KEY.",
            }
        
        # Default to last 30 days
        if from_date is None:
            from_date = datetime.utcnow() - timedelta(days=30)
        if to_date is None:
            to_date = datetime.utcnow()
        
        params = {
            "q": query,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
            "sortBy": sort_by,
            "pageSize": min(page_size, 100),
            "language": language,
            "apiKey": self.api_key,
        }
        
        try:
            response = requests.get(
                f"{NEWS_API_BASE_URL}/everything",
                params=params,
                timeout=30,
            )
            
            if response.status_code == 200:
                data = response.json()
                articles = [
                    {
                        "title": a.get("title", ""),
                        "description": a.get("description", ""),
                        "source": a.get("source", {}).get("name", "Unknown"),
                        "url": a.get("url", ""),
                        "published_at": a.get("publishedAt", ""),
                    }
                    for a in data.get("articles", [])
                ]
                
                return {
                    "success": True,
                    "total_results": data.get("totalResults", 0),
                    "articles": articles,
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "success": False,
                    "error": f"API error {response.status_code}: {error_data.get('message', 'Unknown')}",
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"News API request failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def _analyze_sentiment(self, text: str) -> str:
        """
        Simple keyword-based sentiment analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment classification
        """
        text_lower = text.lower()
        
        positive_count = sum(1 for kw in self.KEYWORDS_POSITIVE if kw in text_lower)
        negative_count = sum(1 for kw in self.KEYWORDS_NEGATIVE if kw in text_lower)
        
        if positive_count > negative_count * 2:
            return "POSITIVE"
        elif negative_count > positive_count * 2:
            return "NEGATIVE"
        elif positive_count > 0 and negative_count > 0:
            return "MIXED"
        else:
            return "NEUTRAL"
    
    def validate_esg_claim(
        self,
        company_name: str,
        claim_text: str,
        days_back: int = 90,
    ) -> Dict[str, Any]:
        """
        Validate a specific ESG claim against news coverage.
        
        Args:
            company_name: Company making the claim
            claim_text: The ESG claim to verify
            days_back: How many days of news to check
            
        Returns:
            Validation result with credibility score
        """
        if not self.available:
            return {"success": False, "error": "News API not configured"}
        
        from_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Search for general company ESG news
        esg_search = self.search_news(
            query=f'"{company_name}" AND (ESG OR sustainability OR environment OR climate)',
            from_date=from_date,
            page_size=20,
        )
        
        # Search for potential negative news
        negative_search = self.search_news(
            query=f'"{company_name}" AND (lawsuit OR fine OR pollution OR scandal OR greenwashing)',
            from_date=from_date,
            page_size=10,
        )
        
        if not esg_search.get("success"):
            return esg_search
        
        # Analyze articles
        esg_articles = esg_search.get("articles", [])
        negative_articles = negative_search.get("articles", []) if negative_search.get("success") else []
        
        supporting_evidence = []
        contradicting_evidence = []
        
        # Analyze ESG articles
        for article in esg_articles:
            combined_text = f"{article.get('title', '')} {article.get('description', '')}"
            sentiment = self._analyze_sentiment(combined_text)
            
            article["sentiment"] = sentiment
            
            if sentiment == "POSITIVE":
                supporting_evidence.append(article)
            elif sentiment == "NEGATIVE":
                contradicting_evidence.append(article)
        
        # Add explicit negative search results
        for article in negative_articles:
            if article not in contradicting_evidence:
                article["sentiment"] = "NEGATIVE"
                contradicting_evidence.append(article)
        
        # Calculate credibility score
        total_articles = len(esg_articles) + len(negative_articles)
        
        if total_articles == 0:
            credibility = "UNCERTAIN"
            credibility_score = 50
        else:
            supporting_count = len(supporting_evidence)
            contradicting_count = len(contradicting_evidence)
            
            # Score: more supporting = higher, more contradicting = lower
            if supporting_count > 0:
                ratio = supporting_count / (supporting_count + contradicting_count)
                credibility_score = ratio * 100
            else:
                credibility_score = 50 - (contradicting_count * 10)
                credibility_score = max(0, min(100, credibility_score))
            
            if credibility_score >= 75:
                credibility = "CREDIBLE"
            elif credibility_score >= 60:
                credibility = "LIKELY_CREDIBLE"
            elif credibility_score >= 40:
                credibility = "UNCERTAIN"
            elif credibility_score >= 25:
                credibility = "QUESTIONABLE"
            else:
                credibility = "LIKELY_FALSE"
        
        return {
            "success": True,
            "company": company_name,
            "claim": claim_text,
            "credibility": credibility,
            "credibility_score": round(credibility_score, 1),
            "total_articles_found": total_articles,
            "supporting_evidence": supporting_evidence[:5],
            "contradicting_evidence": contradicting_evidence[:5],
            "search_period_days": days_back,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    
    def get_company_esg_news(
        self,
        company_name: str,
        days_back: int = 30,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Get recent ESG-related news for a company.
        
        Args:
            company_name: Company name
            days_back: Number of days to search
            page_size: Number of articles
            
        Returns:
            ESG news summary
        """
        from_date = datetime.utcnow() - timedelta(days=days_back)
        
        result = self.search_news(
            query=f'"{company_name}" AND (ESG OR sustainability OR environment OR climate OR carbon)',
            from_date=from_date,
            page_size=page_size,
        )
        
        if not result.get("success"):
            return result
        
        # Analyze sentiment for each article
        articles = result.get("articles", [])
        sentiment_counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0, "MIXED": 0}
        
        for article in articles:
            combined_text = f"{article.get('title', '')} {article.get('description', '')}"
            sentiment = self._analyze_sentiment(combined_text)
            article["sentiment"] = sentiment
            sentiment_counts[sentiment] += 1
        
        # Overall sentiment
        if sentiment_counts["NEGATIVE"] > sentiment_counts["POSITIVE"] * 2:
            overall_sentiment = "NEGATIVE"
        elif sentiment_counts["POSITIVE"] > sentiment_counts["NEGATIVE"] * 2:
            overall_sentiment = "POSITIVE"
        else:
            overall_sentiment = "MIXED"
        
        return {
            "success": True,
            "company": company_name,
            "total_articles": len(articles),
            "overall_sentiment": overall_sentiment,
            "sentiment_breakdown": sentiment_counts,
            "articles": articles,
            "search_period_days": days_back,
        }
    
    def check_for_controversies(
        self,
        company_name: str,
        days_back: int = 180,
    ) -> Dict[str, Any]:
        """
        Check for recent ESG-related controversies.
        
        Args:
            company_name: Company name
            days_back: Number of days to search
            
        Returns:
            Controversy check result
        """
        from_date = datetime.utcnow() - timedelta(days=days_back)
        
        controversy_query = (
            f'"{company_name}" AND '
            "(lawsuit OR fine OR penalty OR investigation OR scandal OR "
            "greenwashing OR pollution OR violation OR toxic OR emissions)"
        )
        
        result = self.search_news(
            query=controversy_query,
            from_date=from_date,
            page_size=20,
        )
        
        if not result.get("success"):
            return result
        
        articles = result.get("articles", [])
        
        # Categorize controversies
        categories = {
            "environmental": [],
            "regulatory": [],
            "greenwashing": [],
            "legal": [],
            "other": [],
        }
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            
            if any(kw in text for kw in ["pollution", "toxic", "spill", "emissions"]):
                categories["environmental"].append(article)
            elif any(kw in text for kw in ["fine", "penalty", "regulatory", "violation"]):
                categories["regulatory"].append(article)
            elif "greenwashing" in text:
                categories["greenwashing"].append(article)
            elif any(kw in text for kw in ["lawsuit", "legal", "court"]):
                categories["legal"].append(article)
            else:
                categories["other"].append(article)
        
        has_controversies = len(articles) > 0
        
        return {
            "success": True,
            "company": company_name,
            "has_controversies": has_controversies,
            "controversy_count": len(articles),
            "categories": {k: len(v) for k, v in categories.items()},
            "articles": articles[:10],
            "search_period_days": days_back,
        }


# Singleton instance
_news_validator: Optional[NewsValidator] = None


def get_news_validator() -> NewsValidator:
    """Get or create news validator singleton."""
    global _news_validator
    if _news_validator is None:
        _news_validator = NewsValidator()
    return _news_validator


def validate_company_claim(
    company_name: str,
    claim_text: str,
    days_back: int = 90,
) -> Dict[str, Any]:
    """
    Convenience function to validate an ESG claim.
    
    Args:
        company_name: Company making the claim
        claim_text: The ESG claim
        days_back: Days of news to check
        
    Returns:
        Validation result
    """
    validator = get_news_validator()
    return validator.validate_esg_claim(company_name, claim_text, days_back)


def get_company_controversies(
    company_name: str,
    days_back: int = 180,
) -> Dict[str, Any]:
    """
    Convenience function to check for controversies.
    
    Args:
        company_name: Company name
        days_back: Days to search
        
    Returns:
        Controversy report
    """
    validator = get_news_validator()
    return validator.check_for_controversies(company_name, days_back)


# Export
__all__ = [
    "NewsValidator",
    "ClaimCredibility",
    "SentimentType",
    "NewsArticle",
    "get_news_validator",
    "validate_company_claim",
    "get_company_controversies",
]
