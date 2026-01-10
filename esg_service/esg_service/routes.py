"""
FastAPI REST API Routes for ESG Service.

Production-level API endpoints for ESG monitoring, greenwashing detection,
KPI tracking, SPT validation, and ESG ratings.

This service exposes the HERO feature: Greenwashing Detection.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
import logging

from esg_service.esg_service.tools import (
    # KPI tools
    get_kpi_definitions,
    get_current_kpi_values,
    calculate_kpi_progress,
    get_kpi_trend,
    # SPT tools
    get_spt_definitions,
    validate_spt_achievement,
    calculate_margin_adjustment,
    check_verification_status,
    # Rating tools
    get_esg_rating,
    get_rating_history,
    compare_peer_ratings,
    get_rating_breakdown,
    # Greenwashing tools
    analyze_esg_claims,
    check_verification_gaps,
    compare_claims_vs_actions,
    calculate_greenwashing_score,
    # V8 Greenwashing Detection (HERO)
    detect_greenwashing_sync,
    analyze_greenwashing,
    get_greenwashing_detector,
)

logger = logging.getLogger(__name__)


# ============================================
# Request/Response Models
# ============================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    service: str = "esg-service"
    version: str = "1.0.0"
    hero_feature: str = "Greenwashing Detection"


class GreenwashingRequest(BaseModel):
    """Request for greenwashing detection."""
    company_name: str = Field(..., description="Company name to analyze")
    claim_text: str = Field(..., description="ESG claim to verify")
    verbose: bool = Field(False, description="Include detailed evidence")


class GreenwashingResponse(BaseModel):
    """Greenwashing detection response."""
    success: bool
    company: str
    claim: str
    risk_level: str  # VERY_HIGH, HIGH, MEDIUM, LOW
    risk_score: float  # 0-100
    verdict: str  # LIKELY_GREENWASHING, POSSIBLE_GREENWASHING, LIKELY_GENUINE
    evidence_count: int
    key_findings: List[str]
    sources_searched: int


class KPIResponse(BaseModel):
    """KPI data response."""
    success: bool
    loan_id: str
    kpis: List[Dict[str, Any]]


class SPTResponse(BaseModel):
    """SPT validation response."""
    success: bool
    loan_id: str
    spts: List[Dict[str, Any]]
    margin_adjustment: Optional[float] = None


class RatingResponse(BaseModel):
    """ESG rating response."""
    success: bool
    borrower_id: str
    rating: Optional[str] = None
    score: Optional[float] = None
    breakdown: Optional[Dict[str, Any]] = None


# ============================================
# API Router
# ============================================

router = APIRouter(prefix="/api/esg", tags=["esg"])


# ============================================
# Health & Status Endpoints
# ============================================

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for ESG service."""
    return HealthResponse()


@router.get("/status")
async def service_status() -> Dict[str, Any]:
    """Get ESG service status including greenwashing detector."""
    detector = get_greenwashing_detector()
    
    return {
        "service": "esg-service",
        "version": "1.0.0",
        "status": "healthy",
        "hero_feature": "Greenwashing Detection",
        "capabilities": {
            "greenwashing_detection": True,
            "esg_ratings": True,
            "kpi_tracking": True,
            "spt_validation": True,
        },
        "greenwashing_detector": {
            "available": detector.available,
            "search_engine_configured": detector.search_engine_id is not None,
        }
    }


# ============================================
# Greenwashing Detection (HERO FEATURE)
# ============================================

@router.post("/greenwashing/detect", response_model=GreenwashingResponse)
async def detect_greenwashing(
    request: GreenwashingRequest,
) -> GreenwashingResponse:
    """
    Detect potential greenwashing in ESG claims (HERO FEATURE).
    
    Uses Google Custom Search to find contradicting evidence and
    verify company ESG claims against public information.
    
    Risk Levels:
    - VERY_HIGH (70-100): Strong contradicting evidence
    - HIGH (50-70): Multiple concerning signals
    - MEDIUM (30-50): Some inconsistencies
    - LOW (0-30): Claim appears genuine
    """
    try:
        result = detect_greenwashing_sync(
            company_name=request.company_name,
            claim_text=request.claim_text,
        )
        
        risk_level = result.get("risk_level", "UNKNOWN")
        risk_score = result.get("risk_score", 0)
        
        # Map risk level to verdict
        if risk_score >= 70:
            verdict = "LIKELY_GREENWASHING"
        elif risk_score >= 40:
            verdict = "POSSIBLE_GREENWASHING"
        else:
            verdict = "LIKELY_GENUINE"
        
        return GreenwashingResponse(
            success=True,
            company=request.company_name,
            claim=request.claim_text,
            risk_level=risk_level,
            risk_score=risk_score,
            verdict=verdict,
            evidence_count=result.get("evidence_count", 0),
            key_findings=result.get("key_findings", [])[:5],
            sources_searched=result.get("sources_searched", 0),
        )
        
    except Exception as e:
        logger.exception(f"Greenwashing detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/greenwashing/analyze/{borrower_id}")
async def analyze_borrower_greenwashing(
    borrower_id: str = Path(..., description="Borrower identifier"),
) -> Dict[str, Any]:
    """
    Analyze all ESG claims for a borrower for potential greenwashing.
    
    Retrieves stored claims from BigQuery and analyzes each.
    """
    try:
        result = analyze_greenwashing(borrower_id)
        return result
    except Exception as e:
        logger.exception(f"Analyze greenwashing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/greenwashing")
async def get_loan_greenwashing_analysis(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Dict[str, Any]:
    """Get greenwashing analysis for a specific loan."""
    try:
        # Get claims for this loan
        claims = analyze_esg_claims(loan_id)
        
        # Check verification gaps
        gaps = check_verification_gaps(loan_id)
        
        # Compare claims vs actions
        comparison = compare_claims_vs_actions(loan_id)
        
        # Calculate overall greenwashing score
        score = calculate_greenwashing_score(loan_id)
        
        return {
            "success": True,
            "loan_id": loan_id,
            "claims_analysis": claims,
            "verification_gaps": gaps,
            "claims_vs_actions": comparison,
            "greenwashing_score": score,
        }
    except Exception as e:
        logger.exception(f"Loan greenwashing analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ESG KPI Endpoints
# ============================================

@router.get("/loans/{loan_id}/kpis", response_model=KPIResponse)
async def get_loan_kpis(
    loan_id: str = Path(..., description="Loan identifier"),
) -> KPIResponse:
    """Get all ESG KPIs for a loan."""
    try:
        definitions = get_kpi_definitions(loan_id)
        current_values = get_current_kpi_values(loan_id)
        
        kpis = []
        for kpi in definitions or []:
            kpi_id = kpi.get("kpi_id")
            current = next(
                (v for v in (current_values or []) if v.get("kpi_id") == kpi_id),
                {}
            )
            
            progress = calculate_kpi_progress(
                current_value=current.get("current_value", 0),
                target_value=kpi.get("target_value", 0),
            )
            
            kpis.append({
                **kpi,
                "current_value": current.get("current_value"),
                "progress_pct": progress.get("progress_pct", 0),
                "on_track": progress.get("on_track", False),
            })
        
        return KPIResponse(success=True, loan_id=loan_id, kpis=kpis)
        
    except Exception as e:
        logger.exception(f"KPI retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/kpis/{kpi_id}/trend")
async def get_kpi_trend_endpoint(
    loan_id: str = Path(..., description="Loan identifier"),
    kpi_id: str = Path(..., description="KPI identifier"),
    periods: int = Query(4, ge=1, le=12, description="Number of historical periods"),
) -> Dict[str, Any]:
    """Get historical trend for a specific KPI."""
    try:
        trend = get_kpi_trend(loan_id, kpi_id, periods=periods)
        return {
            "success": True,
            "loan_id": loan_id,
            "kpi_id": kpi_id,
            "trend": trend,
        }
    except Exception as e:
        logger.exception(f"KPI trend error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SPT (Sustainability Performance Target) Endpoints
# ============================================

@router.get("/loans/{loan_id}/spts", response_model=SPTResponse)
async def get_loan_spts(
    loan_id: str = Path(..., description="Loan identifier"),
) -> SPTResponse:
    """Get all SPTs for a sustainability-linked loan."""
    try:
        definitions = get_spt_definitions(loan_id)
        
        spts = []
        for spt in definitions or []:
            validation = validate_spt_achievement(loan_id, spt.get("spt_id"))
            
            spts.append({
                **spt,
                "achieved": validation.get("achieved", False),
                "actual_value": validation.get("actual_value"),
                "variance_pct": validation.get("variance_pct", 0),
            })
        
        # Calculate margin adjustment based on SPT achievement
        margin_result = calculate_margin_adjustment(loan_id)
        
        return SPTResponse(
            success=True,
            loan_id=loan_id,
            spts=spts,
            margin_adjustment=margin_result.get("adjustment_bps"),
        )
        
    except Exception as e:
        logger.exception(f"SPT retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/spts/{spt_id}/verification")
async def get_spt_verification_status(
    loan_id: str = Path(..., description="Loan identifier"),
    spt_id: str = Path(..., description="SPT identifier"),
) -> Dict[str, Any]:
    """Get verification status for a specific SPT."""
    try:
        status = check_verification_status(loan_id, spt_id)
        return {
            "success": True,
            "loan_id": loan_id,
            "spt_id": spt_id,
            "verification": status,
        }
    except Exception as e:
        logger.exception(f"SPT verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ESG Rating Endpoints
# ============================================

@router.get("/borrowers/{borrower_id}/rating", response_model=RatingResponse)
async def get_borrower_rating(
    borrower_id: str = Path(..., description="Borrower identifier"),
) -> RatingResponse:
    """Get ESG rating for a borrower."""
    try:
        rating = get_esg_rating(borrower_id)
        breakdown = get_rating_breakdown(borrower_id)
        
        return RatingResponse(
            success=True,
            borrower_id=borrower_id,
            rating=rating.get("rating"),
            score=rating.get("score"),
            breakdown=breakdown,
        )
        
    except Exception as e:
        logger.exception(f"Rating retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/borrowers/{borrower_id}/rating/history")
async def get_borrower_rating_history(
    borrower_id: str = Path(..., description="Borrower identifier"),
    periods: int = Query(4, ge=1, le=20, description="Number of historical periods"),
) -> Dict[str, Any]:
    """Get historical ESG rating data for a borrower."""
    try:
        history = get_rating_history(borrower_id, periods=periods)
        return {
            "success": True,
            "borrower_id": borrower_id,
            "history": history,
        }
    except Exception as e:
        logger.exception(f"Rating history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/borrowers/{borrower_id}/rating/peers")
async def compare_borrower_with_peers(
    borrower_id: str = Path(..., description="Borrower identifier"),
    sector: Optional[str] = Query(None, description="Filter peers by sector"),
) -> Dict[str, Any]:
    """Compare borrower's ESG rating with peer group."""
    try:
        comparison = compare_peer_ratings(borrower_id, sector=sector)
        return {
            "success": True,
            "borrower_id": borrower_id,
            "peer_comparison": comparison,
        }
    except Exception as e:
        logger.exception(f"Peer comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Carbon Emissions Tracking (P2)
# ============================================

from esg_service.esg_service.tools.carbon_tools import (
    get_carbon_tracker,
    calculate_loan_carbon_footprint,
)


class CarbonCalculationRequest(BaseModel):
    """Request for carbon emission calculation."""
    electricity_kwh: float = Field(0, description="Annual electricity in kWh")
    fuel_liters: float = Field(0, description="Annual fuel in liters")
    travel_km: float = Field(0, description="Annual travel in km")
    country_code: str = Field("US", description="Country for emission factors")


@router.get("/carbon/status")
async def carbon_tracker_status() -> Dict[str, Any]:
    """Get carbon tracker status."""
    tracker = get_carbon_tracker()
    return {
        "service": "Carbon Emissions Tracker",
        "api": "Climatiq",
        "available": tracker.available,
        "capabilities": [
            "electricity_emissions",
            "fuel_emissions", 
            "travel_emissions",
            "loan_carbon_footprint",
        ]
    }


@router.post("/loans/{loan_id}/carbon/calculate")
async def calculate_loan_emissions(
    loan_id: str = Path(..., description="Loan identifier"),
    request: CarbonCalculationRequest = ...,
) -> Dict[str, Any]:
    """
    Calculate carbon footprint for a loan's operations.
    
    Aggregates emissions from electricity, fuel, and travel.
    Uses Climatiq API for accurate emission factors.
    """
    try:
        result = calculate_loan_carbon_footprint(
            loan_id=loan_id,
            electricity_kwh=request.electricity_kwh,
            fuel_liters=request.fuel_liters,
            travel_km=request.travel_km,
            country_code=request.country_code,
        )
        return result
    except Exception as e:
        logger.exception(f"Carbon calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/carbon/calculate/electricity")
async def calculate_electricity_emissions(
    kwh: float = Query(..., description="Electricity consumption in kWh"),
    country: str = Query("US", description="Country code"),
) -> Dict[str, Any]:
    """Calculate carbon emissions from electricity consumption."""
    try:
        tracker = get_carbon_tracker()
        result = tracker.calculate_electricity_emissions(kwh, country)
        return result
    except Exception as e:
        logger.exception(f"Electricity calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/carbon/calculate/fuel")
async def calculate_fuel_emissions(
    liters: float = Query(..., description="Fuel consumption in liters"),
    fuel_type: str = Query("diesel", description="Fuel type"),
) -> Dict[str, Any]:
    """Calculate carbon emissions from fuel combustion."""
    try:
        tracker = get_carbon_tracker()
        result = tracker.calculate_fuel_emissions(liters, fuel_type)
        return result
    except Exception as e:
        logger.exception(f"Fuel calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/carbon/calculate/travel")
async def calculate_travel_emissions(
    kilometers: float = Query(..., description="Distance traveled in km"),
    travel_type: str = Query("car", description="Mode of travel"),
) -> Dict[str, Any]:
    """Calculate carbon emissions from travel."""
    try:
        tracker = get_carbon_tracker()
        result = tracker.calculate_travel_emissions(kilometers, travel_type)
        return result
    except Exception as e:
        logger.exception(f"Travel calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/carbon/factors/search")
async def search_emission_factors(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Category filter"),
    region: Optional[str] = Query(None, description="Region filter"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
) -> Dict[str, Any]:
    """Search for available emission factors in Climatiq."""
    try:
        tracker = get_carbon_tracker()
        result = tracker.search_emission_factors(
            query=query,
            category=category,
            region=region,
            limit=limit,
        )
        return result
    except Exception as e:
        logger.exception(f"Emission factor search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# News API Validation (P2)
# ============================================

from esg_service.esg_service.tools.news_tools import (
    get_news_validator,
    validate_company_claim,
    get_company_controversies,
)


class NewsValidationRequest(BaseModel):
    """Request for ESG claim validation against news."""
    company_name: str = Field(..., description="Company name to validate")
    claim_text: str = Field(..., description="ESG claim to validate")
    days_back: int = Field(90, ge=7, le=365, description="Days of news to search")


class NewsSearchRequest(BaseModel):
    """Request for news search."""
    query: str = Field(..., description="Search query")
    days_back: int = Field(30, ge=1, le=90, description="Days of news to search")
    page_size: int = Field(10, ge=1, le=100, description="Number of results")


@router.get("/news/status")
async def news_validator_status() -> Dict[str, Any]:
    """Get News API validator status."""
    validator = get_news_validator()
    return {
        "service": "News API Validator",
        "api": "NewsAPI.org",
        "available": validator.available,
        "capabilities": [
            "esg_news_search",
            "claim_validation",
            "controversy_detection",
            "sentiment_analysis",
        ]
    }


@router.post("/news/validate")
async def validate_esg_claim_news(
    request: NewsValidationRequest,
) -> Dict[str, Any]:
    """
    Validate an ESG claim against real-time news coverage.
    
    Cross-references company claims with news articles to detect
    potential greenwashing or verify claim credibility.
    
    Credibility Levels:
    - CREDIBLE: Strong supporting evidence
    - LIKELY_CREDIBLE: Some supporting evidence
    - UNCERTAIN: Mixed or no evidence
    - QUESTIONABLE: Some contradicting evidence
    - LIKELY_FALSE: Strong contradicting evidence
    """
    try:
        result = validate_company_claim(
            company_name=request.company_name,
            claim_text=request.claim_text,
            days_back=request.days_back,
        )
        return result
    except Exception as e:
        logger.exception(f"News validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies/{company_name}/news")
async def get_company_esg_news(
    company_name: str = Path(..., description="Company name"),
    days_back: int = Query(30, ge=1, le=180, description="Days to search"),
    page_size: int = Query(20, ge=1, le=100, description="Number of articles"),
) -> Dict[str, Any]:
    """
    Get recent ESG-related news for a company.
    
    Returns articles with sentiment analysis.
    """
    try:
        validator = get_news_validator()
        result = validator.get_company_esg_news(
            company_name=company_name,
            days_back=days_back,
            page_size=page_size,
        )
        return result
    except Exception as e:
        logger.exception(f"Company news error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies/{company_name}/controversies")
async def check_company_controversies(
    company_name: str = Path(..., description="Company name"),
    days_back: int = Query(180, ge=30, le=365, description="Days to search"),
) -> Dict[str, Any]:
    """
    Check for ESG-related controversies for a company.
    
    Searches for lawsuits, fines, scandals, and greenwashing accusations.
    Returns categorized controversy report.
    """
    try:
        result = get_company_controversies(
            company_name=company_name,
            days_back=days_back,
        )
        return result
    except Exception as e:
        logger.exception(f"Controversy check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news/search")
async def search_news(
    request: NewsSearchRequest,
) -> Dict[str, Any]:
    """
    Search for news articles matching a query.
    
    Useful for custom ESG research and due diligence.
    """
    try:
        validator = get_news_validator()
        result = validator.search_news(
            query=request.query,
            page_size=request.page_size,
        )
        return result
    except Exception as e:
        logger.exception(f"News search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/news/validation")
async def get_loan_news_validation(
    loan_id: str = Path(..., description="Loan identifier"),
    days_back: int = Query(90, ge=7, le=365, description="Days to search"),
) -> Dict[str, Any]:
    """
    Get news-based validation for a loan's ESG claims.
    
    Fetches borrower info from BigQuery and validates ESG claims against news.
    """
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        # Get loan and borrower info from BigQuery
        loan_query = f"""
            SELECT l.loan_id, l.borrower_name, l.industry
            FROM `{bq.project_id}.{bq.dataset_id}.loans` l
            WHERE l.loan_id = '{loan_id}'
        """
        loan_data = bq.execute_query(loan_query)
        
        if not loan_data:
            raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")
        
        loan = loan_data[0]
        borrower_name = loan.get("borrower_name")
        
        # Get ESG claims for this loan
        claims_query = f"""
            SELECT kpi_name, kpi_type, current_value, target_value, 
                   verification_status, greenwashing_risk_score
            FROM `{bq.project_id}.{bq.dataset_id}.esg_kpis`
            WHERE loan_id = '{loan_id}'
        """
        claims_data = bq.execute_query(claims_query)
        
        validator = get_news_validator()
        
        # Validate each major ESG claim
        validations = []
        for claim in claims_data[:3]:  # Limit to top 3 claims to avoid rate limiting
            if borrower_name and claim.get("kpi_name"):
                claim_text = f"{claim.get('kpi_name')} target of {claim.get('target_value')} {claim.get('kpi_type', '')}"
                try:
                    validation_result = validate_company_claim(
                        company_name=borrower_name,
                        claim_text=claim_text,
                        days_back=days_back,
                    )
                    validations.append({
                        "kpi_name": claim.get("kpi_name"),
                        "claim": claim_text,
                        "validation": validation_result,
                    })
                except Exception as ve:
                    validations.append({
                        "kpi_name": claim.get("kpi_name"),
                        "claim": claim_text,
                        "validation": {"error": str(ve), "credibility": "UNABLE_TO_VERIFY"},
                    })
        
        # Get recent controversies for the borrower
        controversies = {}
        if borrower_name:
            try:
                controversies = get_company_controversies(
                    company_name=borrower_name,
                    days_back=days_back,
                )
            except Exception:
                controversies = {"error": "Unable to fetch controversies"}
        
        return {
            "success": True,
            "loan_id": loan_id,
            "borrower_name": borrower_name,
            "industry": loan.get("industry"),
            "news_validation_available": validator.available,
            "esg_claims_count": len(claims_data),
            "validations": validations,
            "controversies": controversies,
            "analysis_date": datetime.now().isoformat() if 'datetime' in dir() else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Loan news validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["router"]
