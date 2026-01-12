"""
FastAPI REST API Routes for ESG Service.

Production-level API endpoints for ESG monitoring, greenwashing detection,
KPI tracking, SPT validation, and ESG ratings.

This service exposes the HERO feature: Greenwashing Detection.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Path, Response
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


# ============================================
# SLL Monitoring Module (P0 - WINNING_STRATEGY_FINAL.md)
# Based on LMA SLLP (Sustainability-Linked Loan Principles)
# ============================================

from esg_service.esg_service.tools.sll_kpi_extractor import (
    extract_sll_kpis_from_document,
    get_loan_sll_kpis,
    get_sll_kpi_extractor,
)
from esg_service.esg_service.tools.spt_tools import (
    get_spt_definitions,
    validate_spt_achievement,
    calculate_margin_adjustment,
)


class SLLKPIRequest(BaseModel):
    """Request for SLL KPI extraction."""
    loan_id: str = Field(..., description="Loan identifier")
    document_text: str = Field(..., description="Raw document text")
    document_id: Optional[str] = Field(None, description="Source document ID")
    save_to_db: bool = Field(True, description="Save to BigQuery")


class SLLMarginRequest(BaseModel):
    """Request for margin adjustment calculation."""
    loan_id: str = Field(..., description="Loan identifier")


# GET /sll/loan/{loan_id}/kpis - Get loan SLL KPIs
@router.get("/sll/loan/{loan_id}/kpis")
async def get_sll_kpis(
    loan_id: str = Path(..., description="Loan identifier"),
):
    """
    Get all SLL KPIs for a specific loan from BigQuery.
    
    Returns:
        KPI list with verification status, achievement probability
    """
    try:
        result = get_loan_sll_kpis(loan_id)
        return result
    except Exception as e:
        logger.exception(f"SLL KPI fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /sll/kpis/extract - Extract KPIs from document
@router.post("/sll/kpis/extract")
async def extract_sll_kpis(request: SLLKPIRequest):
    """
    Extract SLL KPIs from document text using Gemini AI.
    
    Returns:
        Extracted KPIs with types, baselines, targets
    """
    try:
        result = extract_sll_kpis_from_document(
            loan_id=request.loan_id,
            document_text=request.document_text,
            document_id=request.document_id,
            save_to_db=request.save_to_db,
        )
        return result
    except Exception as e:
        logger.exception(f"SLL KPI extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /sll/loan/{loan_id}/spts - Get SPT definitions
@router.get("/sll/loan/{loan_id}/spts")
async def get_loan_spts(
    loan_id: str = Path(..., description="Loan identifier"),
):
    """
    Get SPT (Sustainability Performance Target) definitions for a loan.
    
    Returns:
        SPT list with target values, achievement status
    """
    try:
        result = get_spt_definitions(loan_id)
        return result
    except Exception as e:
        logger.exception(f"SPT fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /sll/loan/{loan_id}/spts/validate - Validate SPT achievement
@router.get("/sll/loan/{loan_id}/spts/validate")
async def validate_loan_spts(
    loan_id: str = Path(..., description="Loan identifier"),
):
    """
    Validate SPT achievement against actual values.
    
    Returns:
        Validation results per SPT
    """
    try:
        result = validate_spt_achievement(loan_id)
        return result
    except Exception as e:
        logger.exception(f"SPT validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /sll/loan/{loan_id}/margin - Calculate margin adjustment
@router.get("/sll/loan/{loan_id}/margin")
async def calculate_loan_margin_adjustment(
    loan_id: str = Path(..., description="Loan identifier"),
):
    """
    Calculate margin adjustment based on SPT achievement.
    Two-way pricing per LMA SLLP guidelines.
    
    Returns:
        Margin adjustment in basis points, direction
    """
    try:
        result = calculate_margin_adjustment(loan_id)
        return result
    except Exception as e:
        logger.exception(f"Margin calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /sll/portfolio/summary - Portfolio SLL summary
@router.get("/sll/portfolio/summary")
async def get_sll_portfolio_summary():
    """
    Get SLL portfolio summary statistics from BigQuery.
    
    Returns:
        Total SLL loans, KPIs, verification rates, achievement probabilities
    """
    try:
        bq = BigQueryClient()
        
        # Portfolio-level SLL statistics
        query = f"""
            WITH sll_stats AS (
                SELECT 
                    loan_id,
                    COUNT(*) as kpi_count,
                    COUNTIF(verification_status = 'VERIFIED') as verified_count,
                    AVG(achievement_probability) as avg_achievement_prob
                FROM `{bq.project_id}.{bq.dataset_id}.sll_kpis`
                GROUP BY loan_id
            ),
            spt_stats AS (
                SELECT
                    COUNT(*) as total_spts,
                    COUNTIF(status = 'ACHIEVED') as achieved_spts,
                    AVG(margin_impact_bps) as avg_margin_impact
                FROM `{bq.project_id}.{bq.dataset_id}.sll_spts`
            )
            SELECT 
                COUNT(DISTINCT s.loan_id) as sll_loan_count,
                COALESCE(SUM(s.kpi_count), 0) as total_kpis,
                COALESCE(SUM(s.verified_count), 0) as verified_kpis,
                COALESCE(AVG(s.avg_achievement_prob), 0) as avg_achievement_probability,
                COALESCE(sp.total_spts, 0) as total_spts,
                COALESCE(sp.achieved_spts, 0) as achieved_spts,
                COALESCE(sp.avg_margin_impact, 0) as avg_margin_impact_bps
            FROM sll_stats s
            CROSS JOIN spt_stats sp
        """
        
        results = bq.execute_query(query)
        
        if results:
            row = results[0]
            return {
                "success": True,
                "sll_loan_count": row.get("sll_loan_count", 0),
                "total_kpis": row.get("total_kpis", 0),
                "verified_kpis": row.get("verified_kpis", 0),
                "verification_rate": round(
                    (row.get("verified_kpis", 0) / max(row.get("total_kpis", 1), 1)) * 100, 1
                ),
                "avg_achievement_probability": round(row.get("avg_achievement_probability", 0) * 100, 1),
                "total_spts": row.get("total_spts", 0),
                "achieved_spts": row.get("achieved_spts", 0),
                "spt_achievement_rate": round(
                    (row.get("achieved_spts", 0) / max(row.get("total_spts", 1), 1)) * 100, 1
                ),
                "avg_margin_impact_bps": row.get("avg_margin_impact_bps", 0),
                "source": "BigQuery",
            }
        else:
            return {
                "success": True,
                "sll_loan_count": 0,
                "total_kpis": 0,
                "verified_kpis": 0,
                "verification_rate": 0,
                "avg_achievement_probability": 0,
                "total_spts": 0,
                "achieved_spts": 0,
                "spt_achievement_rate": 0,
                "avg_margin_impact_bps": 0,
                "source": "BigQuery",
            }
    except Exception as e:
        logger.exception(f"SLL portfolio summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Fund Finance Module (P0 - WINNING_STRATEGY_FINAL.md)

# ============================================

from esg_service.esg_service.tools.nav_monitor import (
    get_nav_facility,
    calculate_nav_ltv,
    get_nav_buffer_analysis,
    create_nav_facility,
    get_nav_portfolio_summary,
)
from esg_service.esg_service.tools.lp_transparency import (
    get_lp_positions,
    get_fund_leverage_exposure,
    get_lp_leverage,
    create_lp_position,
)
from esg_service.esg_service.tools.ilpa_compliance import (
    check_ilpa_compliance,
    validate_ilpa_compliance,
)
from esg_service.esg_service.tools.subscription_tracker import (
    calculate_borrowing_base,
    create_capital_call,
    get_capital_calls,
    get_overdue_calls,
)


# Request Models for Fund Finance
class NAVFacilityRequest(BaseModel):
    """Request for creating NAV facility."""
    fund_id: str = Field(..., description="Fund identifier")
    fund_name: str = Field(..., description="Fund name")
    fund_type: str = Field("PE", description="Fund type: PE, VC, RE, Infrastructure")
    nav_value: float = Field(..., description="Current NAV value")
    facility_amount: float = Field(..., description="Total facility amount")
    drawn_amount: float = Field(0, description="Currently drawn amount")
    ltv_covenant_threshold: float = Field(0.15, description="LTV covenant threshold (e.g., 0.15 for 15%)")


class CapitalCallRequest(BaseModel):
    """Request for creating capital call."""
    fund_id: str = Field(..., description="Fund identifier")
    call_amount: float = Field(..., description="Amount to call")
    purpose: str = Field("Investment", description="Purpose: Investment, Management Fee, Expenses")
    due_date: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")


class LPPositionRequest(BaseModel):
    """Request for creating LP position."""
    fund_id: str = Field(..., description="Fund identifier")
    lp_name: str = Field(..., description="LP name")
    lp_type: str = Field("Institutional", description="LP type: Pension, Insurance, Endowment")
    commitment_amount: float = Field(..., description="Commitment amount")
    is_lpac_member: bool = Field(False, description="Is LP an LPAC member")


# GET /api/fund-finance/nav/{id} - Get NAV facility details
@router.get("/fund-finance/nav/{facility_id}")
async def get_nav_facility_details(
    facility_id: str = Path(..., description="NAV facility identifier"),
) -> Dict[str, Any]:
    """
    Get NAV facility details.
    
    Returns facility information including current LTV ratio and buffer analysis.
    """
    try:
        result = get_nav_facility(facility_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Facility not found"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"NAV facility retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /api/fund-finance/nav/create - Create NAV facility
@router.post("/fund-finance/nav/create")
async def create_nav_facility_endpoint(
    request: NAVFacilityRequest,
) -> Dict[str, Any]:
    """
    Create a new NAV facility.
    
    Calculates initial LTV ratio and buffer percentage.
    Based on ILPA July 2024 NAV-Based Facilities Guidance.
    """
    try:
        result = create_nav_facility({
            "fund_id": request.fund_id,
            "fund_name": request.fund_name,
            "fund_type": request.fund_type,
            "nav_value": request.nav_value,
            "facility_amount": request.facility_amount,
            "drawn_amount": request.drawn_amount,
            "ltv_covenant_threshold": request.ltv_covenant_threshold,
        })
        return result
    except Exception as e:
        logger.exception(f"NAV facility creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/fund-finance/ltv/{id} - Calculate current LTV
@router.get("/fund-finance/ltv/{facility_id}")
async def calculate_ltv_endpoint(
    facility_id: str = Path(..., description="NAV facility identifier"),
) -> Dict[str, Any]:
    """
    Calculate current LTV ratio for NAV facility.
    
    Returns LTV percentage, covenant threshold, buffer percentage,
    and NAV decline percentage that would trigger covenant breach.
    """
    try:
        result = calculate_nav_ltv(facility_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Facility not found"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"LTV calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/fund-finance/buffer/{id} - Get buffer analysis
@router.get("/fund-finance/buffer/{facility_id}")
async def get_buffer_analysis_endpoint(
    facility_id: str = Path(..., description="NAV facility identifier"),
) -> Dict[str, Any]:
    """
    Get detailed buffer analysis for NAV facility.
    
    Includes stress scenarios showing LTV impact at various NAV decline levels,
    and calculates the NAV decline percentage required to breach covenant.
    """
    try:
        result = get_nav_buffer_analysis(facility_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Facility not found"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Buffer analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /api/fund-finance/ilpa/check - Validate ILPA compliance
@router.post("/fund-finance/ilpa/check/{facility_id}")
async def check_ilpa_compliance_endpoint(
    facility_id: str = Path(..., description="NAV facility identifier"),
) -> Dict[str, Any]:
    """
    Check ILPA compliance for NAV facility.
    
    Validates facility against ILPA July 2024 NAV-Based Facilities Guidance:
    - LPA provisions addressing NAV facilities
    - Leverage limits defined
    - LPAC consent obtained
    - Required disclosures provided
    
    Returns compliance score and recommendations.
    """
    try:
        result = check_ilpa_compliance(facility_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Facility not found"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"ILPA compliance check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/fund-finance/lp/{fund_id}/transparency - LP transparency data
@router.get("/fund-finance/lp/{fund_id}/transparency")
async def get_lp_transparency_endpoint(
    fund_id: str = Path(..., description="Fund identifier"),
) -> Dict[str, Any]:
    """
    Get LP transparency data including aggregate leverage exposure.
    
    ILPA Guidance: "LPs calling for greater visibility on fund-level leverage"
    
    Returns fund-level leverage breakdown including NAV and subscription facilities.
    """
    try:
        positions = get_lp_positions(fund_id)
        leverage = get_fund_leverage_exposure(fund_id)
        
        return {
            "success": True,
            "fund_id": fund_id,
            "lp_positions": positions,
            "leverage_exposure": leverage,
        }
    except Exception as e:
        logger.exception(f"LP transparency error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/fund-finance/portfolio - Portfolio summary
@router.get("/fund-finance/portfolio")
async def get_fund_finance_portfolio_summary() -> Dict[str, Any]:
    """
    Get portfolio-level NAV facility summary.
    
    Aggregates all NAV facilities with total exposure, average LTV,
    and facilities in breach or warning status.
    """
    try:
        result = get_nav_portfolio_summary()
        return result
    except Exception as e:
        logger.exception(f"Portfolio summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /api/fund-finance/capital-call/create - Create capital call
@router.post("/fund-finance/capital-call/create")
async def create_capital_call_endpoint(
    request: CapitalCallRequest,
) -> Dict[str, Any]:
    """
    Create a new capital call for a fund.
    
    Used for subscription facility tracking and LP obligation monitoring.
    """
    try:
        result = create_capital_call({
            "fund_id": request.fund_id,
            "call_amount": request.call_amount,
            "purpose": request.purpose,
            "due_date": request.due_date,
        })
        return result
    except Exception as e:
        logger.exception(f"Capital call creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/fund-finance/capital-calls/{fund_id} - Get capital calls
@router.get("/fund-finance/capital-calls/{fund_id}")
async def get_fund_capital_calls(
    fund_id: str = Path(..., description="Fund identifier"),
    status: Optional[str] = Query(None, description="Filter by status: PENDING, PARTIAL, COMPLETE"),
) -> Dict[str, Any]:
    """
    Get capital calls for a fund.
    
    Includes total called, received, and outstanding amounts.
    """
    try:
        result = get_capital_calls(fund_id, status)
        return result
    except Exception as e:
        logger.exception(f"Capital calls retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/fund-finance/overdue-calls - Get overdue calls
@router.get("/fund-finance/overdue-calls")
async def get_overdue_capital_calls(
    fund_id: Optional[str] = Query(None, description="Optional fund filter"),
) -> Dict[str, Any]:
    """
    Get overdue capital calls.
    
    Returns calls past due date that have not been fully paid.
    Critical for subscription facility borrowing base impact.
    """
    try:
        result = get_overdue_calls(fund_id)
        return result
    except Exception as e:
        logger.exception(f"Overdue calls retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/fund-finance/borrowing-base/{fund_id} - Calculate borrowing base
@router.get("/fund-finance/borrowing-base/{fund_id}")
async def calculate_borrowing_base_endpoint(
    fund_id: str = Path(..., description="Fund identifier"),
) -> Dict[str, Any]:
    """
    Calculate borrowing base from LP commitments.
    
    Borrowing base = (Included LP Commitments - Exclusions) * Advance Rate
    
    Used for subscription facility availability calculation.
    """
    try:
        result = calculate_borrowing_base(fund_id)
        return result
    except Exception as e:
        logger.exception(f"Borrowing base calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /api/fund-finance/lp/create - Create LP position
@router.post("/fund-finance/lp/create")
async def create_lp_position_endpoint(
    request: LPPositionRequest,
) -> Dict[str, Any]:
    """
    Create a new LP position for a fund.
    
    Tracks LP commitments for subscription facility and leverage exposure.
    """
    try:
        result = create_lp_position({
            "fund_id": request.fund_id,
            "lp_name": request.lp_name,
            "lp_type": request.lp_type,
            "commitment_amount": request.commitment_amount,
            "is_lpac_member": request.is_lpac_member,
        })
        return result
    except Exception as e:
        logger.exception(f"LP position creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Transition Loans Module Endpoints (P1)
# Based on LMA Transition Loan Principles (October 2025)
# ============================================

# Import Transition Loans tools
from esg_service.esg_service.tools import (
    validate_transition_loan,
    get_tlp_summary,
    assess_carbon_lockin,
    get_portfolio_lockin_summary,
    screen_dnsh,
    get_portfolio_dnsh_summary,
    generate_tlp_report,
    get_tlp_portfolio_report,
)


class TransitionLoanRequest(BaseModel):
    """Request for transition loan assessment."""
    loan_id: str = Field(..., description="Loan identifier")


class CarbonLockinRequest(BaseModel):
    """Request for carbon lock-in assessment."""
    loan_id: Optional[str] = Field(None, description="Loan identifier")
    project_lifetime_years: Optional[int] = Field(None, description="Asset operational lifetime")
    utilization_rate: Optional[float] = Field(None, ge=0, le=1, description="Utilization rate 0-1")
    emissions_trajectory: Optional[str] = Field(None, description="DECREASING, STABLE, INCREASING")
    cumulative_emissions_tco2: Optional[float] = Field(None, description="Total lifetime emissions")
    displaceability: Optional[str] = Field(None, description="YES, PARTIAL, NO")
    reversibility: Optional[str] = Field(None, description="YES, PARTIAL, NO")
    best_available_tech: Optional[bool] = Field(None, description="Using best-available technology")


class DNSHScreeningRequest(BaseModel):
    """Request for DNSH screening."""
    loan_id: Optional[str] = Field(None, description="Loan identifier")


# GET /api/transition/validate/{loan_id} - Validate TLP compliance
@router.get("/transition/validate/{loan_id}")
async def validate_tlp_endpoint(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Dict[str, Any]:
    """
    Validate Transition Loan Principles compliance.
    
    Scores 5 TLP principles:
    1. Entity-Level Transition Strategy
    2. Use of Proceeds
    3. Process for Project Evaluation and Selection
    4. Management of Proceeds
    5. Reporting
    
    Based on LMA Guide to Transition Loans (October 2025).
    """
    try:
        result = validate_transition_loan(loan_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Loan not found"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"TLP validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/transition/summary - Get TLP portfolio summary
@router.get("/transition/summary")
async def get_tlp_summary_endpoint() -> Dict[str, Any]:
    """
    Get portfolio-level TLP compliance summary.
    
    Returns aggregate statistics on transition loan compliance.
    """
    try:
        result = get_tlp_summary()
        return result
    except Exception as e:
        logger.exception(f"TLP summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /api/transition/carbon-lockin - Assess carbon lock-in risk
@router.post("/transition/carbon-lockin")
async def assess_carbon_lockin_endpoint(
    request: CarbonLockinRequest,
) -> Dict[str, Any]:
    """
    Assess carbon lock-in risk for a transition project.
    
    Based on LMA TLP Section 3.2.1 iv - 8 assessment criteria:
    - Project lifetime
    - Utilization rates
    - Emissions trajectory
    - Cumulative emissions
    - Displaceability
    - Reversibility
    - Best-available technology
    - End-use emissions
    """
    try:
        if request.loan_id:
            result = assess_carbon_lockin(loan_id=request.loan_id)
        else:
            asset_data = {
                "project_lifetime_years": request.project_lifetime_years,
                "utilization_rate": request.utilization_rate,
                "emissions_trajectory": request.emissions_trajectory,
                "cumulative_emissions_tco2": request.cumulative_emissions_tco2,
                "displaceability": request.displaceability,
                "reversibility": request.reversibility,
                "best_available_tech": request.best_available_tech,
            }
            result = assess_carbon_lockin(asset_data=asset_data)
        return result
    except Exception as e:
        logger.exception(f"Carbon lock-in assessment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/transition/carbon-lockin/summary - Get portfolio lock-in summary
@router.get("/transition/carbon-lockin/summary")
async def get_lockin_summary_endpoint() -> Dict[str, Any]:
    """
    Get portfolio-level carbon lock-in risk summary.
    
    Returns aggregate statistics on carbon lock-in risk across transition loans.
    """
    try:
        result = get_portfolio_lockin_summary()
        return result
    except Exception as e:
        logger.exception(f"Carbon lock-in summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /api/transition/dnsh/screen - DNSH screening
@router.post("/transition/dnsh/screen")
async def screen_dnsh_endpoint(
    request: DNSHScreeningRequest,
) -> Dict[str, Any]:
    """
    Screen project for Do No Significant Harm (DNSH) compliance.
    
    Checks 6 EU Taxonomy environmental objectives:
    1. Climate change mitigation
    2. Climate change adaptation
    3. Sustainable use of water and marine resources
    4. Transition to a circular economy
    5. Pollution prevention and control
    6. Protection of biodiversity and ecosystems
    """
    try:
        result = screen_dnsh(loan_id=request.loan_id)
        return result
    except Exception as e:
        logger.exception(f"DNSH screening error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/transition/dnsh/summary - Get portfolio DNSH summary
@router.get("/transition/dnsh/summary")
async def get_dnsh_summary_endpoint() -> Dict[str, Any]:
    """
    Get portfolio-level DNSH screening summary.
    
    Returns aggregate statistics on DNSH compliance across transition loans.
    """
    try:
        result = get_portfolio_dnsh_summary()
        return result
    except Exception as e:
        logger.exception(f"DNSH summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/transition/report/{loan_id} - Generate TLP report
@router.get("/transition/report/{loan_id}")
async def generate_tlp_report_endpoint(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Dict[str, Any]:
    """
    Generate TLP-compliant report for a transition loan.
    
    LMA Principle 5 (Reporting) - MANDATORY requirements:
    1. List of Transition Projects funded
    2. Amounts allocated to each project
    3. Expected AND achieved impact of each project
    """
    try:
        result = generate_tlp_report(loan_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Report generation failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"TLP report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/transition/report/portfolio - Get portfolio TLP report
@router.get("/transition/report/portfolio")
async def get_portfolio_report_endpoint() -> Dict[str, Any]:
    """
    Generate portfolio-level TLP report.
    
    Aggregates data across all transition loans for regulatory reporting.
    """
    try:
        result = get_tlp_portfolio_report()
        return result
    except Exception as e:
        logger.exception(f"Portfolio TLP report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SLLB & Regional Module Endpoints (P1/P2)
# Based on ICMA SLLBG, SARB ZARONIA, SFDR 2.0
# ============================================

# Import SLLB & Regional tools
from esg_service.esg_service.tools import (
    create_sllb_portfolio,
    get_sllb_portfolio,
    add_sll_to_sllb,
    get_sllb_summary,
    evaluate_sll_eligibility,
    assess_jibar_transition,
    initiate_zaronia_transition,
    get_zaronia_transition_summary,
    classify_sfdr_product,
    get_sfdr_portfolio_summary,
)


class SLLBPortfolioRequest(BaseModel):
    """Request for SLLB portfolio creation."""
    bond_isin: Optional[str] = Field(None, description="Bond ISIN")
    bond_name: str = Field(..., description="Bond name")
    issuer_name: str = Field(..., description="Issuer name")
    issue_date: Optional[str] = Field(None, description="Issue date YYYY-MM-DD")
    maturity_date: Optional[str] = Field(None, description="Maturity date YYYY-MM-DD")
    bond_amount: float = Field(..., description="Bond amount")
    currency: str = Field(default="USD", description="Currency code")
    sustainability_objective: Optional[str] = Field(None, description="Single sustainability objective")


class AddSLLRequest(BaseModel):
    """Request to add SLL to SLLB portfolio."""
    loan_id: str = Field(..., description="SLL loan ID")
    borrower_sector: Optional[str] = Field(None, description="Borrower sector")
    borrower_geography: Optional[str] = Field(None, description="Borrower geography")
    loan_amount: float = Field(..., description="SLL amount")
    allocated_to_bond: Optional[float] = Field(None, description="Amount allocated to bond")
    kpi_type: Optional[str] = Field(None, description="KPI type")
    spt_description: Optional[str] = Field(None, description="SPT description")


# POST /api/sllb/portfolio/create - Create SLLB portfolio
@router.post("/sllb/portfolio/create")
async def create_sllb_portfolio_endpoint(
    request: SLLBPortfolioRequest,
) -> Dict[str, Any]:
    """
    Create a new SLLB portfolio.
    
    ICMA SLLBG Component 1: Use of Proceeds - 
    Bond proceeds allocated to eligible SLLs.
    """
    try:
        result = create_sllb_portfolio({
            "bond_isin": request.bond_isin,
            "bond_name": request.bond_name,
            "issuer_name": request.issuer_name,
            "issue_date": request.issue_date,
            "maturity_date": request.maturity_date,
            "bond_amount": request.bond_amount,
            "currency": request.currency,
            "sustainability_objective": request.sustainability_objective,
        })
        return result
    except Exception as e:
        logger.exception(f"SLLB portfolio creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/sllb/portfolio/{portfolio_id} - Get SLLB portfolio
@router.get("/sllb/portfolio/{portfolio_id}")
async def get_sllb_portfolio_endpoint(
    portfolio_id: str = Path(..., description="Portfolio ID"),
) -> Dict[str, Any]:
    """
    Get SLLB portfolio details with eligible SLLs.
    
    Includes sector and geography breakdowns per ICMA reporting.
    """
    try:
        result = get_sllb_portfolio(portfolio_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"SLLB portfolio retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /api/sllb/portfolio/{portfolio_id}/add-sll - Add SLL to portfolio
@router.post("/sllb/portfolio/{portfolio_id}/add-sll")
async def add_sll_to_sllb_endpoint(
    portfolio_id: str,
    request: AddSLLRequest,
) -> Dict[str, Any]:
    """
    Add an eligible SLL to SLLB portfolio.
    
    ICMA SLLBG Component 3: Management of Proceeds.
    """
    try:
        result = add_sll_to_sllb(portfolio_id, request.loan_id, {
            "borrower_sector": request.borrower_sector,
            "borrower_geography": request.borrower_geography,
            "loan_amount": request.loan_amount,
            "allocated_to_bond": request.allocated_to_bond or request.loan_amount,
            "kpi_type": request.kpi_type,
            "spt_description": request.spt_description,
        })
        return result
    except Exception as e:
        logger.exception(f"Add SLL error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/sllb/summary - Get SLLB portfolio summary
@router.get("/sllb/summary")
async def get_sllb_summary_endpoint() -> Dict[str, Any]:
    """
    Get aggregate SLLB portfolio summary.
    
    ICMA SLLBG Component 4: Reporting.
    """
    try:
        result = get_sllb_summary()
        return result
    except Exception as e:
        logger.exception(f"SLLB summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/sllb/eligibility/{loan_id} - Evaluate SLL eligibility
@router.get("/sllb/eligibility/{loan_id}")
async def evaluate_eligibility_endpoint(
    loan_id: str = Path(..., description="Loan ID"),
) -> Dict[str, Any]:
    """
    Evaluate SLL eligibility for SLLB inclusion.
    
    ICMA SLLBG Component 2: Process for SLL Evaluation & Selection.
    Scores: SLLP alignment, KPI materiality, SPT ambition, verification.
    """
    try:
        result = evaluate_sll_eligibility(loan_id)
        return result
    except Exception as e:
        logger.exception(f"Eligibility evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/zaronia/assess/{loan_id} - Assess JIBAR transition
@router.get("/zaronia/assess/{loan_id}")
async def assess_jibar_transition_endpoint(
    loan_id: str = Path(..., description="Loan ID"),
) -> Dict[str, Any]:
    """
    Assess loan's JIBAR to ZARONIA transition readiness.
    
    JIBAR discontinuation deadline: December 31, 2026.
    ZARONIA = South African Rand Overnight Index Average.
    """
    try:
        result = assess_jibar_transition(loan_id)
        return result
    except Exception as e:
        logger.exception(f"JIBAR assessment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /api/zaronia/initiate/{loan_id} - Initiate transition
@router.post("/zaronia/initiate/{loan_id}")
async def initiate_zaronia_endpoint(
    loan_id: str = Path(..., description="Loan ID"),
) -> Dict[str, Any]:
    """
    Initiate JIBAR to ZARONIA transition.
    
    Creates transition record and recommended next steps.
    """
    try:
        result = initiate_zaronia_transition(loan_id)
        return result
    except Exception as e:
        logger.exception(f"ZARONIA initiation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/zaronia/summary - Get transition summary
@router.get("/zaronia/summary")
async def get_zaronia_summary_endpoint() -> Dict[str, Any]:
    """
    Get portfolio-level JIBAR transition summary.
    
    Shows completion rates and days to deadline.
    """
    try:
        result = get_zaronia_transition_summary()
        return result
    except Exception as e:
        logger.exception(f"ZARONIA summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/sfdr/classify/{product_id} - Classify under SFDR 2.0
@router.get("/sfdr/classify/{product_id}")
async def classify_sfdr_endpoint(
    product_id: str = Path(..., description="Product ID"),
) -> Dict[str, Any]:
    """
    Classify financial product under SFDR 2.0.
    
    New categories (replacing Article 8/9):
    - Article 7: Transition (70% threshold)
    - Article 8: ESG Basics (70% threshold)
    - Article 9: Sustainable (70% threshold)
    """
    try:
        result = classify_sfdr_product(product_id)
        return result
    except Exception as e:
        logger.exception(f"SFDR classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# GET /api/sfdr/summary - Get SFDR classification summary
@router.get("/sfdr/summary")
async def get_sfdr_summary_endpoint() -> Dict[str, Any]:
    """
    Get portfolio-level SFDR 2.0 classification summary.
    
    Shows distribution across new categories.
    """
    try:
        result = get_sfdr_portfolio_summary()
        return result
    except Exception as e:
        logger.exception(f"SFDR summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Social Loans Module (SLP March 2025)
# ============================================

# Import Social Loans tools
from esg_service.esg_service.tools.social_loan_validator import (
    validate_social_loan,
    get_social_loan_summary,
    save_social_loan_assessment,
    SLP_CATEGORIES,
    SLP_TARGET_POPULATIONS,
)
from esg_service.esg_service.tools.social_impact_tracker import (
    get_social_loan_impact,
    update_social_impact,
    generate_social_impact_report,
    get_portfolio_social_impact,
    SOCIAL_KPIS,
)


# Request/Response Models for Social Loans
class SocialLoanValidateRequest(BaseModel):
    """Request for social loan validation."""
    loan_id: str = Field(..., description="Loan identifier")
    loan_purpose: Optional[str] = Field(None, description="Loan purpose description for classification")


class SocialLoanValidateResponse(BaseModel):
    """Response for social loan validation."""
    success: bool
    loan_id: str
    is_social_loan: bool
    is_slp_compliant: bool
    social_category: str
    target_populations: List[str]
    scores: Dict[str, float]
    recommendations: List[str]


class SocialImpactUpdateRequest(BaseModel):
    """Request for updating social impact metrics."""
    metrics: Dict[str, Any] = Field(..., description="Impact metrics to update")


# POST /api/social/validate - Validate SLP compliance
@router.post("/social/validate")
async def validate_social_loan_endpoint(
    request: SocialLoanValidateRequest,
) -> Dict[str, Any]:
    """
    Validate a loan against Social Loan Principles (SLP March 2025).
    
    Performs classification into 6 eligible categories:
    1. Affordable Basic Infrastructure
    2. Access to Essential Services
    3. Affordable Housing
    4. Employment Generation
    5. Food Security & Sustainable Food Systems
    6. Socioeconomic Advancement & Empowerment
    
    Returns SLP compliance score across 4 components:
    - Use of Proceeds (35%)
    - Project Evaluation (25%)
    - Proceeds Management (20%)
    - Reporting (20%)
    """
    try:
        result = validate_social_loan(
            loan_id=request.loan_id,
            loan_purpose=request.loan_purpose,
        )
        
        # Save assessment to BigQuery
        if result.get("success") and result.get("is_social_loan"):
            save_social_loan_assessment(request.loan_id, result)
        
        return result
        
    except Exception as e:
        logger.exception(f"Social loan validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/social/loan/{loan_id} - Get social loan details
@router.get("/social/loan/{loan_id}")
async def get_social_loan_endpoint(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Dict[str, Any]:
    """
    Get social loan classification and compliance details.
    
    Returns existing assessment or triggers new validation.
    """
    try:
        # First try to get existing assessment via validation (returns cached)
        result = validate_social_loan(loan_id=loan_id)
        return result
        
    except Exception as e:
        logger.exception(f"Get social loan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/social/impact/{loan_id} - Get social impact metrics
@router.get("/social/impact/{loan_id}")
async def get_social_impact_endpoint(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Dict[str, Any]:
    """
    Get social impact metrics for a loan.
    
    Returns impact KPIs, beneficiary data, and reporting status.
    Implements ICMA Handbook 2025 recommended social KPIs.
    """
    try:
        result = get_social_loan_impact(loan_id=loan_id)
        return result
        
    except Exception as e:
        logger.exception(f"Get social impact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# PUT /api/social/impact/{loan_id} - Update impact metrics
@router.put("/social/impact/{loan_id}")
async def update_social_impact_endpoint(
    loan_id: str = Path(..., description="Loan identifier"),
    request: SocialImpactUpdateRequest = None,
) -> Dict[str, Any]:
    """
    Update social impact metrics for a loan.
    
    Supports metrics like:
    - beneficiaries_reached
    - jobs_created
    - housing_units_created
    - students_enrolled
    - etc.
    """
    try:
        result = update_social_impact(
            loan_id=loan_id,
            metrics=request.metrics if request else {},
        )
        return result
        
    except Exception as e:
        logger.exception(f"Update social impact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/social/report/{loan_id} - Generate impact report
@router.get("/social/report/{loan_id}")
async def generate_social_report_endpoint(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Dict[str, Any]:
    """
    Generate annual impact report for a social loan.
    
    Required by SLP 2025 Component 4 (mandatory annual reporting).
    """
    try:
        result = generate_social_impact_report(loan_id=loan_id)
        return result
        
    except Exception as e:
        logger.exception(f"Generate social report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/social/summary - Get portfolio summary
@router.get("/social/summary")
async def get_social_summary_endpoint() -> Dict[str, Any]:
    """
    Get portfolio-level social loan summary.
    
    Returns aggregated data across all social loans:
    - Total loans by category
    - Total beneficiaries
    - Average compliance scores
    """
    try:
        result = get_social_loan_summary()
        return result
        
    except Exception as e:
        logger.exception(f"Get social summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/social/portfolio-impact - Get portfolio impact
@router.get("/social/portfolio-impact")
async def get_portfolio_impact_endpoint() -> Dict[str, Any]:
    """
    Get portfolio-wide social impact aggregation.
    
    Aggregates impact metrics across all social loans.
    """
    try:
        result = get_portfolio_social_impact()
        return result
        
    except Exception as e:
        logger.exception(f"Get portfolio impact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /api/social/categories - Get SLP eligible categories
@router.get("/social/categories")
async def get_social_categories_endpoint() -> Dict[str, Any]:
    """
    Get list of SLP eligible social project categories.
    
    Based on SLP March 2025 Appendix 1.
    """
    return {
        "success": True,
        "slp_version": "March 2025",
        "categories": SLP_CATEGORIES,
        "target_populations": SLP_TARGET_POPULATIONS,
        "category_kpis": SOCIAL_KPIS,
    }


# ============================================
# Report Export Endpoints (NEW - V10.1)
# ============================================

# POST /api/reports/tlp/{loan_id}/pdf - Generate TLP PDF Report
@router.post("/reports/tlp/{loan_id}/pdf")
async def generate_tlp_pdf_endpoint(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Response:
    """
    Generate LMA-compliant TLP PDF report for a transition loan.
    
    Based on LMA TLP Principle 5 (Reporting) - October 2025.
    Includes all mandatory sections:
    1. List of Transition Projects
    2. Amounts allocated
    3. Expected impact
    4. Achieved impact
    """
    try:
        from esg_service.tools.tlp_report_pdf import generate_tlp_pdf
        
        pdf_bytes = generate_tlp_pdf(loan_id)
        
        filename = f"TLP_Report_{loan_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        logger.exception(f"TLP PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /api/reports/tlp/portfolio/pdf - Generate Portfolio TLP PDF
@router.post("/reports/tlp/portfolio/pdf")
async def generate_tlp_portfolio_pdf_endpoint() -> Response:
    """
    Generate portfolio-level TLP PDF report.
    
    Summarizes all transition loans in the portfolio.
    """
    try:
        from esg_service.tools.tlp_report_pdf import generate_tlp_portfolio_pdf
        
        pdf_bytes = generate_tlp_portfolio_pdf()
        
        filename = f"TLP_Portfolio_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        logger.exception(f"TLP portfolio PDF error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /api/reports/pptx/loan/{loan_id} - Generate Loan PowerPoint
@router.post("/reports/pptx/loan/{loan_id}")
async def generate_loan_pptx_endpoint(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Response:
    """
    Generate Risk Committee PowerPoint presentation for a loan.
    
    Creates 8-slide board-ready presentation with:
    - Executive summary
    - Covenant compliance overview
    - ML breach predictions
    - ESG/TLP status
    - Recommendations
    """
    try:
        from common.pptx_report_generator import generate_loan_pptx
        from common.bigquery_client import BigQueryClient
        
        bq = BigQueryClient()
        
        # Get loan data
        loan_query = f"""
            SELECT * FROM `{bq.project_id}.{bq.dataset_id}.loans`
            WHERE loan_id = '{loan_id}'
        """
        loans = bq.execute_query(loan_query)
        if not loans:
            raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")
        
        loan_data = loans[0]
        
        # Get covenants
        cov_query = f"""
            SELECT * FROM `{bq.project_id}.{bq.dataset_id}.covenant_measurements`
            WHERE loan_id = '{loan_id}'
            ORDER BY measurement_date DESC
        """
        covenants = bq.execute_query(cov_query) or []
        
        # Get predictions
        pred_query = f"""
            SELECT * FROM `{bq.project_id}.{bq.dataset_id}.ml_predictions`
            WHERE loan_id = '{loan_id}'
            ORDER BY prediction_date DESC
            LIMIT 1
        """
        predictions = bq.execute_query(pred_query)
        predictions = predictions[0] if predictions else None
        
        # Get ESG data
        esg_query = f"""
            SELECT * FROM `{bq.project_id}.{bq.dataset_id}.esg_assessments`
            WHERE loan_id = '{loan_id}'
            ORDER BY assessment_date DESC
            LIMIT 1
        """
        esg_data = bq.execute_query(esg_query)
        esg_data = esg_data[0] if esg_data else None
        
        # Generate presentation
        pptx_bytes = generate_loan_pptx(loan_data, covenants, predictions, esg_data)
        
        filename = f"Risk_Committee_{loan_id}_{datetime.now().strftime('%Y%m%d')}.pptx"
        
        return Response(
            content=pptx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"PPTX generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# POST /api/reports/pptx/portfolio - Generate Portfolio PowerPoint
@router.post("/reports/pptx/portfolio")
async def generate_portfolio_pptx_endpoint() -> Response:
    """
    Generate Risk Committee PowerPoint for entire portfolio.
    
    Creates portfolio-level board presentation with aggregated metrics.
    """
    try:
        from common.pptx_report_generator import generate_portfolio_pptx
        from common.bigquery_client import BigQueryClient
        
        bq = BigQueryClient()
        
        # Get portfolio summary
        summary_query = f"""
            SELECT 
                COUNT(*) as total_loans,
                SUM(facility_amount) as total_exposure,
                COUNTIF(overall_status = 'GREEN') as loans_compliant,
                COUNTIF(overall_status = 'AMBER') as loans_warning,
                COUNTIF(overall_status = 'RED') as loans_breach,
                AVG(esg_score) as esg_average_score
            FROM `{bq.project_id}.{bq.dataset_id}.loans`
        """
        summary_result = bq.execute_query(summary_query)
        summary = summary_result[0] if summary_result else {}
        
        # Get loans
        loans_query = f"""
            SELECT * FROM `{bq.project_id}.{bq.dataset_id}.loans`
            ORDER BY facility_amount DESC
            LIMIT 50
        """
        loans = bq.execute_query(loans_query) or []
        
        # Generate presentation
        pptx_bytes = generate_portfolio_pptx(summary, loans)
        
        filename = f"Risk_Committee_Portfolio_{datetime.now().strftime('%Y%m%d')}.pptx"
        
        return Response(
            content=pptx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        logger.exception(f"Portfolio PPTX error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["router"]

