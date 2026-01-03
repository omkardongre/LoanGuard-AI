"""
Google Custom Search API for ESG news monitoring.

Based on SalesShortcut pattern for web search integration.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)

# Configuration
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"


class GoogleSearchClient:
    """
    Google Custom Search API client for ESG news monitoring.
    """
    
    def __init__(self):
        self.api_key = GOOGLE_SEARCH_API_KEY
        self.engine_id = GOOGLE_SEARCH_ENGINE_ID
        self._client = None
    
    @property
    def available(self) -> bool:
        """Check if search is configured."""
        return bool(self.api_key and self.engine_id)
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        date_restrict: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform a Google search.
        
        Args:
            query: Search query
            num_results: Number of results (max 10 per request)
            date_restrict: Date restriction (e.g., "d7" for last 7 days)
            
        Returns:
            List of search results
        """
        if not self.available:
            logger.warning("Google Search not configured, returning mock results")
            return self._mock_results(query)
        
        params = {
            "key": self.api_key,
            "cx": self.engine_id,
            "q": query,
            "num": min(num_results, 10),
        }
        
        if date_restrict:
            params["dateRestrict"] = date_restrict
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(SEARCH_API_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet"),
                        "source": item.get("displayLink"),
                    })
                
                logger.info(f"Search returned {len(results)} results for: {query}")
                return results
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _mock_results(self, query: str) -> List[Dict[str, Any]]:
        """Return mock results for development."""
        return [
            {
                "title": f"ESG News: {query}",
                "link": "https://example.com/esg-news",
                "snippet": f"Latest developments regarding {query} in the loan market...",
                "source": "example.com",
            },
            {
                "title": f"Sustainability Report: {query}",
                "link": "https://example.com/sustainability",
                "snippet": f"Company announces new sustainability targets related to {query}...",
                "source": "example.com",
            },
        ]


async def search_esg_news(
    company_name: str,
    topics: List[str] = None,
    days_back: int = 30,
) -> Dict[str, Any]:
    """
    Search for ESG-related news about a company.
    
    Args:
        company_name: Company to search for
        topics: ESG topics to include
        days_back: How many days back to search
        
    Returns:
        Aggregated ESG news results
    """
    client = GoogleSearchClient()
    
    default_topics = [
        "ESG rating",
        "sustainability",
        "carbon emissions",
        "governance",
        "environmental impact",
    ]
    topics = topics or default_topics
    
    all_results = []
    
    for topic in topics[:3]:  # Limit to 3 topics to save API calls
        query = f"{company_name} {topic}"
        date_restrict = f"d{days_back}"
        
        results = await client.search(query, num_results=5, date_restrict=date_restrict)
        
        for result in results:
            result["topic"] = topic
            all_results.append(result)
    
    # Deduplicate by link
    seen_links = set()
    unique_results = []
    for result in all_results:
        if result["link"] not in seen_links:
            seen_links.add(result["link"])
            unique_results.append(result)
    
    return {
        "company": company_name,
        "search_date": datetime.now().isoformat(),
        "days_searched": days_back,
        "total_results": len(unique_results),
        "results": unique_results,
    }


async def search_regulatory_updates(
    region: str = "EU",
    topics: List[str] = None,
) -> Dict[str, Any]:
    """
    Search for regulatory updates related to ESG/sustainability.
    
    Args:
        region: Geographic region
        topics: Regulatory topics
        
    Returns:
        Regulatory news results
    """
    client = GoogleSearchClient()
    
    default_topics = [
        "SFDR regulation",
        "EU Taxonomy",
        "sustainability disclosure",
        "green loan requirements",
    ]
    topics = topics or default_topics
    
    all_results = []
    
    for topic in topics[:3]:
        query = f"{region} {topic} regulation 2025"
        results = await client.search(query, num_results=5, date_restrict="m3")
        
        for result in results:
            result["topic"] = topic
            all_results.append(result)
    
    return {
        "region": region,
        "search_date": datetime.now().isoformat(),
        "total_results": len(all_results),
        "results": all_results,
    }


async def monitor_greenwashing_alerts(
    company_name: str,
) -> Dict[str, Any]:
    """
    Monitor for greenwashing allegations about a company.
    
    Args:
        company_name: Company to monitor
        
    Returns:
        Greenwashing alert results
    """
    client = GoogleSearchClient()
    
    queries = [
        f"{company_name} greenwashing",
        f"{company_name} ESG controversy",
        f"{company_name} sustainability misleading",
    ]
    
    alerts = []
    
    for query in queries:
        results = await client.search(query, num_results=5, date_restrict="m6")
        
        for result in results:
            # Simple sentiment analysis based on keywords
            snippet = result.get("snippet", "").lower()
            risk_keywords = ["accused", "lawsuit", "investigation", "fine", "penalty", "misleading"]
            
            risk_score = sum(1 for kw in risk_keywords if kw in snippet)
            
            if risk_score > 0:
                alerts.append({
                    **result,
                    "risk_score": risk_score,
                    "risk_level": "HIGH" if risk_score >= 2 else "MEDIUM",
                })
    
    return {
        "company": company_name,
        "search_date": datetime.now().isoformat(),
        "alert_count": len(alerts),
        "alerts": sorted(alerts, key=lambda x: x["risk_score"], reverse=True),
    }
