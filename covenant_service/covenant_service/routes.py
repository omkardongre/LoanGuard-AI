"""
FastAPI REST API Routes for Covenant Service.

Production-level API endpoints for covenant monitoring, compliance,
ML predictions, and risk analysis.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
import logging

from covenant_service.covenant_service.tools import (
    get_loan_data,
    get_covenant_definitions,
    get_latest_financials,
    get_historical_measurements,
    check_covenant_compliance,
    determine_status_color,
    check_cross_default,
    calculate_buffer_percentage,
    calculate_debt_to_ebitda,
    calculate_interest_coverage,
    calculate_current_ratio,
    get_loan_dashboard,
    get_portfolio_dashboard,
    get_covenant_detail,
    predict_breach,
    explain_prediction,
    get_feature_importance,
    get_risk_score,
    calculate_metric_velocity,
    get_risk_velocity,
    calculate_cure_options,
    get_cure_options,
    get_portfolio_concentration,
    calculate_marginal_concentration_impact,
)

logger = logging.getLogger(__name__)

# ============================================
# Request/Response Models
# ============================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    service: str = "covenant-service"
    version: str = "1.0.0"


class LoanResponse(BaseModel):
    """Loan data response."""
    success: bool
    loan_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ComplianceResponse(BaseModel):
    """Compliance check response."""
    success: bool
    loan_id: str
    status: str  # COMPLIANT, WARNING, BREACH
    status_color: str  # GREEN, AMBER, RED
    covenants: List[Dict[str, Any]]
    cross_default_triggered: bool = False


class PredictionRequest(BaseModel):
    """ML prediction request body."""
    metrics: Dict[str, Any] = Field(
        ...,
        description="Financial metrics for prediction",
        example={
            "loan_amnt": 25000,
            "int_rate": 15.0,
            "annual_inc": 65000,
            "dti": 22.0,
            "fico_range_low": 680,
        }
    )


class PredictionResponse(BaseModel):
    """ML prediction response."""
    success: bool
    loan_id: str
    breach_probability: float
    breach_probability_pct: str
    risk_level: str
    model_version: str
    data_source: str


class ShapExplanationResponse(BaseModel):
    """SHAP explanation response."""
    success: bool
    loan_id: str
    base_probability: float
    final_probability: float
    top_factors: List[Dict[str, Any]]
    data_source: str


class VelocityResponse(BaseModel):
    """Risk velocity response."""
    success: bool
    loan_id: str
    velocity_score: float
    trajectory: str  # ACCELERATING, STABLE, DECELERATING
    metrics: Dict[str, Any]


class CureOptionsResponse(BaseModel):
    """Cure options response."""
    success: bool
    loan_id: str
    options: List[Dict[str, Any]]
    recommended_option: Optional[Dict[str, Any]] = None


class DashboardResponse(BaseModel):
    """Dashboard data response."""
    success: bool
    data: Dict[str, Any]


class PortfolioSummaryResponse(BaseModel):
    """Portfolio summary response."""
    success: bool
    data: Dict[str, Any]


# ============================================
# API Router
# ============================================

router = APIRouter(prefix="/api", tags=["covenant"])


# ============================================
# Health & Status Endpoints
# ============================================

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for load balancers and monitoring."""
    return HealthResponse()


@router.get("/status")
async def service_status() -> Dict[str, Any]:
    """Get detailed service status including dependencies."""
    try:
        # Check if ML model is loaded
        from covenant_service.covenant_service.tools.ml_tools import get_predictor
        predictor = get_predictor()
        ml_status = predictor.model is not None
    except Exception:
        ml_status = False
    
    return {
        "service": "covenant-service",
        "version": "1.0.0",
        "status": "healthy",
        "components": {
            "ml_model": {"status": "loaded" if ml_status else "not_loaded"},
            "bigquery": {"status": "configured"},
        }
    }


# ============================================
# Loan Endpoints
# ============================================

@router.get("/loans", response_model=Dict[str, Any])
async def list_loans(
    status: Optional[str] = Query(None, description="Filter by loan status"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
) -> Dict[str, Any]:
    """List all loans with optional filtering."""
    try:
        result = get_portfolio_dashboard()
        if result.get("success"):
            return {
                "success": True,
                "count": result.get("total_loans", 0),
                "loans": result.get("loan_summaries", [])[:limit],
            }
        return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        logger.exception("Error listing loans")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: str = Path(..., description="Loan identifier"),
) -> LoanResponse:
    """Get detailed loan information."""
    try:
        result = get_loan_data(loan_id)
        if result:
            return LoanResponse(success=True, loan_id=loan_id, data=result)
        return LoanResponse(
            success=False,
            loan_id=loan_id,
            error=f"Loan {loan_id} not found"
        )
    except Exception as e:
        logger.exception(f"Error getting loan {loan_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/covenants")
async def get_loan_covenants(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Dict[str, Any]:
    """Get all covenants for a specific loan."""
    try:
        covenants = get_covenant_definitions(loan_id)
        return {
            "success": True,
            "loan_id": loan_id,
            "covenants": covenants or [],
            "count": len(covenants) if covenants else 0,
        }
    except Exception as e:
        logger.exception(f"Error getting covenants for {loan_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/dashboard", response_model=DashboardResponse)
async def get_loan_dashboard_endpoint(
    loan_id: str = Path(..., description="Loan identifier"),
) -> DashboardResponse:
    """Get comprehensive dashboard data for a loan."""
    try:
        result = get_loan_dashboard(loan_id)
        return DashboardResponse(success=result.get("success", False), data=result)
    except Exception as e:
        logger.exception(f"Error getting dashboard for {loan_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Compliance Endpoints
# ============================================

@router.get("/loans/{loan_id}/compliance", response_model=ComplianceResponse)
async def check_loan_compliance(
    loan_id: str = Path(..., description="Loan identifier"),
) -> ComplianceResponse:
    """Check compliance status for all covenants on a loan."""
    try:
        # Get covenant definitions
        covenants = get_covenant_definitions(loan_id)
        if not covenants:
            return ComplianceResponse(
                success=True,
                loan_id=loan_id,
                status="NO_COVENANTS",
                status_color="GRAY",
                covenants=[],
                cross_default_triggered=False,
            )
        
        # Get latest measurements
        financials = get_latest_financials(loan_id)
        
        # Check each covenant
        covenant_results = []
        has_breach = False
        has_warning = False
        
        for covenant in covenants:
            result = check_covenant_compliance(
                current_value=financials.get(covenant.get("metric_name"), 0),
                threshold=covenant.get("threshold_value", 0),
                threshold_type=covenant.get("threshold_type", "MAX"),
            )
            
            status_color = determine_status_color(
                current_value=financials.get(covenant.get("metric_name"), 0),
                threshold=covenant.get("threshold_value", 0),
                threshold_type=covenant.get("threshold_type", "MAX"),
            )
            
            buffer = calculate_buffer_percentage(
                current_value=financials.get(covenant.get("metric_name"), 0),
                threshold=covenant.get("threshold_value", 0),
            )
            
            if result.get("status") == "BREACH":
                has_breach = True
            elif result.get("status") == "WARNING":
                has_warning = True
            
            covenant_results.append({
                "covenant_id": covenant.get("covenant_id"),
                "covenant_type": covenant.get("covenant_type"),
                "metric_name": covenant.get("metric_name"),
                "current_value": financials.get(covenant.get("metric_name"), 0),
                "threshold": covenant.get("threshold_value"),
                "status": result.get("status"),
                "status_color": status_color.get("color", "GRAY"),
                "buffer_pct": buffer.get("buffer_percentage", 0),
            })
        
        # Check cross-default
        cross_default = check_cross_default(loan_id) if has_breach else {"triggered": False}
        
        overall_status = "BREACH" if has_breach else ("WARNING" if has_warning else "COMPLIANT")
        overall_color = "RED" if has_breach else ("AMBER" if has_warning else "GREEN")
        
        return ComplianceResponse(
            success=True,
            loan_id=loan_id,
            status=overall_status,
            status_color=overall_color,
            covenants=covenant_results,
            cross_default_triggered=cross_default.get("triggered", False),
        )
    except Exception as e:
        logger.exception(f"Error checking compliance for {loan_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/covenants/{covenant_id}")
async def get_covenant_detail_endpoint(
    loan_id: str = Path(..., description="Loan identifier"),
    covenant_id: str = Path(..., description="Covenant identifier"),
) -> Dict[str, Any]:
    """Get detailed information about a specific covenant."""
    try:
        result = get_covenant_detail(covenant_id)
        return result
    except Exception as e:
        logger.exception(f"Error getting covenant detail {covenant_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ML Prediction Endpoints
# ============================================

@router.get("/loans/{loan_id}/predictions", response_model=PredictionResponse)
async def get_breach_prediction(
    loan_id: str = Path(..., description="Loan identifier"),
) -> PredictionResponse:
    """Get ML-based breach probability prediction for a loan."""
    try:
        # Get loan financials
        financials = get_latest_financials(loan_id)
        
        # Run prediction
        result = predict_breach(loan_id, financials or {})
        
        return PredictionResponse(
            success=result.get("success", False),
            loan_id=loan_id,
            breach_probability=result.get("breach_probability", 0),
            breach_probability_pct=result.get("breach_probability_pct", "0%"),
            risk_level=result.get("risk_level", "UNKNOWN"),
            model_version=result.get("model_version", "2.0.0"),
            data_source=result.get("data_source", "Lending Club 2007-2018"),
        )
    except Exception as e:
        logger.exception(f"Error predicting breach for {loan_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loans/{loan_id}/predictions")
async def predict_breach_with_metrics(
    loan_id: str = Path(..., description="Loan identifier"),
    request: PredictionRequest = ...,
) -> PredictionResponse:
    """Predict breach probability with custom metrics."""
    try:
        result = predict_breach(loan_id, request.metrics)
        
        return PredictionResponse(
            success=result.get("success", False),
            loan_id=loan_id,
            breach_probability=result.get("breach_probability", 0),
            breach_probability_pct=result.get("breach_probability_pct", "0%"),
            risk_level=result.get("risk_level", "UNKNOWN"),
            model_version=result.get("model_version", "2.0.0"),
            data_source=result.get("data_source", "Lending Club 2007-2018"),
        )
    except Exception as e:
        logger.exception(f"Error predicting breach for {loan_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/predictions/explain", response_model=ShapExplanationResponse)
async def get_prediction_explanation(
    loan_id: str = Path(..., description="Loan identifier"),
    top_n: int = Query(10, ge=1, le=20, description="Number of top factors to return"),
) -> ShapExplanationResponse:
    """Get SHAP-based explanation for breach prediction."""
    try:
        # Get loan financials
        financials = get_latest_financials(loan_id)
        
        # Get prediction for final probability
        prediction = predict_breach(loan_id, financials or {})
        
        # Get explanation
        result = explain_prediction(loan_id, financials or {}, top_n=top_n)
        
        return ShapExplanationResponse(
            success=result.get("success", False),
            loan_id=loan_id,
            base_probability=result.get("base_probability", 0.5),
            final_probability=prediction.get("breach_probability", 0.5),
            top_factors=result.get("top_factors", []),
            data_source="Lending Club 2007-2018",
        )
    except Exception as e:
        logger.exception(f"Error explaining prediction for {loan_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/feature-importance")
async def get_ml_feature_importance() -> Dict[str, Any]:
    """Get global feature importance from trained ML model."""
    try:
        result = get_feature_importance()
        return result
    except Exception as e:
        logger.exception("Error getting feature importance")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/risk-score")
async def get_loan_risk_score(
    loan_id: str = Path(..., description="Loan identifier"),
) -> Dict[str, Any]:
    """Get composite risk score for a loan."""
    try:
        financials = get_latest_financials(loan_id)
        result = get_risk_score(loan_id, financials or {})
        return result
    except Exception as e:
        logger.exception(f"Error getting risk score for {loan_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Risk Velocity Endpoints
# ============================================

@router.get("/loans/{loan_id}/velocity", response_model=VelocityResponse)
async def get_loan_velocity(
    loan_id: str = Path(..., description="Loan identifier"),
) -> VelocityResponse:
    """Get risk velocity indicator for a loan."""
    try:
        result = get_risk_velocity(loan_id)
        
        return VelocityResponse(
            success=result.get("success", False),
            loan_id=loan_id,
            velocity_score=result.get("velocity_score", 0),
            trajectory=result.get("trajectory", "STABLE"),
            metrics=result.get("metrics", {}),
        )
    except Exception as e:
        logger.exception(f"Error getting velocity for {loan_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans/{loan_id}/velocity/{metric}")
async def get_metric_velocity(
    loan_id: str = Path(..., description="Loan identifier"),
    metric: str = Path(..., description="Metric name (e.g., debt_to_ebitda)"),
) -> Dict[str, Any]:
    """Get velocity for a specific metric."""
    try:
        result = calculate_metric_velocity(
            metric_name=metric,
            loan_id=loan_id,
        )
        return result
    except Exception as e:
        logger.exception(f"Error getting metric velocity for {loan_id}/{metric}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Cure Calculator Endpoints
# ============================================

@router.post("/loans/{loan_id}/cure/calculate", response_model=CureOptionsResponse)
async def calculate_cure(
    loan_id: str = Path(..., description="Loan identifier"),
) -> CureOptionsResponse:
    """Calculate cure options for a loan in breach or approaching breach."""
    try:
        result = get_cure_options(loan_id)
        
        return CureOptionsResponse(
            success=result.get("success", False),
            loan_id=loan_id,
            options=result.get("options", []),
            recommended_option=result.get("recommended_option"),
        )
    except Exception as e:
        logger.exception(f"Error calculating cure for {loan_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Portfolio Endpoints
# ============================================

@router.get("/portfolio/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary() -> PortfolioSummaryResponse:
    """Get portfolio-level summary including all loans."""
    try:
        result = get_portfolio_dashboard()
        return PortfolioSummaryResponse(
            success=result.get("success", False),
            data=result,
        )
    except Exception as e:
        logger.exception("Error getting portfolio summary")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/concentration")
async def get_concentration_analysis() -> Dict[str, Any]:
    """
    Get portfolio concentration analysis.
    
    Calculates HHI (Herfindahl-Hirschman Index) and exposure percentages
    across multiple dimensions: borrower, loan type, status, currency.
    Includes regulatory alerts for concentration breaches.
    """
    try:
        result = get_portfolio_concentration()
        return result
    except Exception as e:
        logger.exception("Error getting portfolio concentration")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/concentration/impact")
async def calculate_concentration_impact(
    loan_amount: float = Query(..., description="Proposed loan amount"),
    borrower_name: str = Query(..., description="Borrower name"),
    loan_type: str = Query("TERM", description="Loan type"),
) -> Dict[str, Any]:
    """
    Calculate marginal impact of a new loan on portfolio concentration.
    
    Useful for credit officers evaluating new loan applications.
    """
    try:
        result = calculate_marginal_concentration_impact(
            loan_amount=loan_amount,
            borrower_name=borrower_name,
            loan_type=loan_type,
        )
        return result
    except Exception as e:
        logger.exception("Error calculating concentration impact")
        raise HTTPException(status_code=500, detail=str(e))


# Export router for inclusion in main app
__all__ = ["router"]
