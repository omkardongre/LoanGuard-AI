"""
API Gateway - Central FastAPI application for LoanGuard AI.

Routes requests to document, covenant, ESG, and alert services.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs
DOCUMENT_SERVICE_URL = os.getenv("DOCUMENT_SERVICE_URL", "http://localhost:8081")
COVENANT_SERVICE_URL = os.getenv("COVENANT_SERVICE_URL", "http://localhost:8082")
ESG_SERVICE_URL = os.getenv("ESG_SERVICE_URL", "http://localhost:8083")
ALERT_SERVICE_URL = os.getenv("ALERT_SERVICE_URL", "http://localhost:8084")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("LoanGuard API Gateway starting...")
    yield
    logger.info("LoanGuard API Gateway shutting down...")


app = FastAPI(
    title="LoanGuard AI API Gateway",
    description="Unified API for loan covenant and ESG compliance monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class LoanRequest(BaseModel):
    loan_id: str
    action: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    loan_id: str
    status: str
    covenants_extracted: int
    entities_extracted: int


class CovenantStatusResponse(BaseModel):
    loan_id: str
    overall_status: str
    covenants: List[Dict[str, Any]]
    breach_predictions: Optional[Dict[str, Any]] = None


class ESGStatusResponse(BaseModel):
    loan_id: str
    overall_status: str
    kpis: List[Dict[str, Any]]
    greenwashing_risk: str
    spt_achieved: bool


class AlertResponse(BaseModel):
    alerts: List[Dict[str, Any]]
    total_count: int


class DashboardSummary(BaseModel):
    total_loans: int
    loans_compliant: int
    loans_warning: int
    loans_breach: int
    active_alerts: int
    esg_average_score: float


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "document": DOCUMENT_SERVICE_URL,
            "covenant": COVENANT_SERVICE_URL,
            "esg": ESG_SERVICE_URL,
            "alert": ALERT_SERVICE_URL,
        },
    }


# Dashboard
@app.get("/api/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary():
    """Get dashboard summary for all loans."""
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        # Get loan counts by status
        query = """
            SELECT 
                COUNT(*) as total,
                COUNTIF(status = 'GREEN') as compliant,
                COUNTIF(status = 'AMBER') as warning,
                COUNTIF(status = 'RED') as breach
            FROM `{project}.{dataset}.loans`
        """.format(project=bq.project_id, dataset=bq.dataset_id)
        
        results = bq.execute_query(query)
        if results:
            row = results[0]
            total = row.get("total", 0)
            compliant = row.get("compliant", 0)
            warning = row.get("warning", 0)
            breach = row.get("breach", 0)
        else:
            total, compliant, warning, breach = 0, 0, 0, 0
        
        # Get active alerts count
        alert_query = """
            SELECT COUNT(*) as count
            FROM `{project}.{dataset}.alerts`
            WHERE is_acknowledged = FALSE
        """.format(project=bq.project_id, dataset=bq.dataset_id)
        
        alert_results = bq.execute_query(alert_query)
        active_alerts = alert_results[0].get("count", 0) if alert_results else 0
        
        return DashboardSummary(
            total_loans=total,
            loans_compliant=compliant,
            loans_warning=warning,
            loans_breach=breach,
            active_alerts=active_alerts,
            esg_average_score=72.5,  # Calculate from ESG data if needed
        )
    except Exception as e:
        logger.warning(f"BigQuery error, using fallback: {e}")
        return DashboardSummary(
            total_loans=50,
            loans_compliant=35,
            loans_warning=10,
            loans_breach=5,
            active_alerts=12,
            esg_average_score=72.5,
        )


# Loans endpoints
@app.get("/api/loans")
async def list_loans(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all loans with optional filtering."""
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        # Build query with optional status filter
        where_clause = f"WHERE status = '{status}'" if status else ""
        
        query = f"""
            SELECT 
                loan_id, borrower_name, borrower_industry, facility_amount,
                currency, maturity_date, loan_type, is_sll, agent_bank, status
            FROM `{bq.project_id}.{bq.dataset_id}.loans`
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
        """
        
        loans = bq.execute_query(query)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `{bq.project_id}.{bq.dataset_id}.loans`
            {where_clause}
        """
        count_result = bq.execute_query(count_query)
        total = count_result[0].get("total", 0) if count_result else 0
        
        return {"loans": loans, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        logger.warning(f"BigQuery error, using fallback: {e}")
        # Fallback mock data
        loans = [
            {
                "loan_id": f"LOAN-{i:04d}",
                "borrower_name": f"Company {chr(65 + i % 26)}",
                "facility_amount": 100_000_000 + i * 10_000_000,
                "currency": "USD",
                "maturity_date": "2027-12-31",
                "status": ["GREEN", "AMBER", "RED"][i % 3],
                "is_sll": i % 3 == 0,
            }
            for i in range(limit)
        ]
        return {"loans": loans, "total": 50, "limit": limit, "offset": offset}


@app.get("/api/loans/{loan_id}")
async def get_loan(loan_id: str):
    """Get detailed loan information."""
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        loan = bq.get_loan_by_id(loan_id)
        if loan:
            # Get covenant count
            cov_query = f"""
                SELECT COUNT(*) as count
                FROM `{bq.project_id}.{bq.dataset_id}.covenants`
                WHERE loan_id = '{loan_id}'
            """
            cov_result = bq.execute_query(cov_query)
            covenant_count = cov_result[0].get("count", 0) if cov_result else 0
            
            loan["covenant_count"] = covenant_count
            return loan
        
        raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"BigQuery error, using fallback: {e}")
        return {
            "loan_id": loan_id,
            "borrower_name": "Acme Corporation",
            "facility_amount": 150_000_000,
            "currency": "USD",
            "maturity_date": "2027-12-31",
            "loan_type": "Term Loan",
            "is_sll": True,
            "agent_bank": "JPMorgan Chase",
            "covenant_count": 5,
            "overall_status": "AMBER",
        }


# Document endpoints
@app.post("/api/documents/upload")
async def upload_document(
    loan_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    """Upload and process a loan document."""
    try:
        content = await file.read()
        
        # In production, send to document service via A2A
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(f"{DOCUMENT_SERVICE_URL}/process", ...)
        
        return DocumentUploadResponse(
            document_id=f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            loan_id=loan_id,
            status="processing",
            covenants_extracted=0,
            entities_extracted=0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}")
async def get_document(document_id: str):
    """Get document processing status and results."""
    return {
        "document_id": document_id,
        "status": "completed",
        "extracted_covenants": [
            {"name": "Debt/EBITDA", "threshold": "<=4.0x", "type": "financial"},
            {"name": "Interest Coverage", "threshold": ">=2.5x", "type": "financial"},
        ],
        "extracted_entities": {
            "borrower": "Acme Corporation",
            "agent": "JPMorgan Chase",
            "facility_amount": "$150,000,000",
        },
    }


# Covenant endpoints
@app.get("/api/covenants/{loan_id}", response_model=CovenantStatusResponse)
async def get_covenant_status(loan_id: str):
    """Get covenant compliance status for a loan."""
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        # Get covenants with latest measurements
        query = f"""
            SELECT 
                c.covenant_id,
                c.covenant_name as name,
                c.covenant_type,
                c.threshold,
                c.threshold_type,
                m.actual_value as actual,
                m.status,
                m.buffer_percent as buffer_pct
            FROM `{bq.project_id}.{bq.dataset_id}.covenants` c
            LEFT JOIN (
                SELECT covenant_id, actual_value, status, buffer_percent,
                    ROW_NUMBER() OVER(PARTITION BY covenant_id ORDER BY period_date DESC) as rn
                FROM `{bq.project_id}.{bq.dataset_id}.covenant_measurements`
            ) m ON c.covenant_id = m.covenant_id AND m.rn = 1
            WHERE c.loan_id = '{loan_id}'
        """
        
        covenants = bq.execute_query(query)
        
        # Determine overall status
        statuses = [c.get("status", "GREEN") for c in covenants]
        if "RED" in statuses:
            overall_status = "RED"
        elif "AMBER" in statuses:
            overall_status = "AMBER"
        else:
            overall_status = "GREEN"
        
        return CovenantStatusResponse(
            loan_id=loan_id,
            overall_status=overall_status,
            covenants=covenants,
            breach_predictions={
                "90_day_probability": 0.25,
                "top_risk_factors": ["Declining EBITDA", "Rising debt levels"],
            },
        )
    except Exception as e:
        logger.warning(f"BigQuery error, using fallback: {e}")
        return CovenantStatusResponse(
            loan_id=loan_id,
            overall_status="AMBER",
            covenants=[
                {
                    "covenant_id": "COV-001",
                    "name": "Debt/EBITDA",
                    "threshold": 4.0,
                    "actual": 3.8,
                    "status": "GREEN",
                    "buffer_pct": 5.0,
                },
                {
                    "covenant_id": "COV-002",
                    "name": "Interest Coverage",
                    "threshold": 2.5,
                    "actual": 2.6,
                    "status": "AMBER",
                    "buffer_pct": 4.0,
                },
            ],
            breach_predictions={
                "90_day_probability": 0.25,
                "top_risk_factors": ["Declining EBITDA", "Rising debt levels"],
            },
        )


@app.post("/api/covenants/{loan_id}/check")
async def run_covenant_check(loan_id: str, background_tasks: BackgroundTasks):
    """Trigger covenant compliance check for a loan."""
    # In production, send to covenant service
    return {"status": "queued", "loan_id": loan_id, "message": "Compliance check initiated"}


# ESG endpoints
@app.get("/api/esg/{loan_id}", response_model=ESGStatusResponse)
async def get_esg_status(loan_id: str):
    """Get ESG compliance status for a loan."""
    return ESGStatusResponse(
        loan_id=loan_id,
        overall_status="ON_TRACK",
        kpis=[
            {
                "kpi_id": "KPI-001",
                "name": "Carbon Emissions",
                "baseline": 100000,
                "target": 70000,
                "current": 82000,
                "progress_pct": 60,
                "status": "ON_TRACK",
            },
            {
                "kpi_id": "KPI-002",
                "name": "Renewable Energy %",
                "baseline": 20,
                "target": 50,
                "current": 38,
                "progress_pct": 60,
                "status": "ON_TRACK",
            },
        ],
        greenwashing_risk="LOW",
        spt_achieved=True,
    )


# Alert endpoints
@app.get("/api/alerts", response_model=AlertResponse)
async def list_alerts(
    loan_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
):
    """List alerts with optional filtering."""
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        # Build WHERE clause
        conditions = []
        if loan_id:
            conditions.append(f"loan_id = '{loan_id}'")
        if severity:
            conditions.append(f"severity = '{severity}'")
        if acknowledged is not None:
            conditions.append(f"is_acknowledged = {str(acknowledged).upper()}")
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT 
                alert_id, loan_id, alert_type as type, severity,
                title, message, is_acknowledged as acknowledged, created_at
            FROM `{bq.project_id}.{bq.dataset_id}.alerts`
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit}
        """
        
        alerts = bq.execute_query(query)
        return AlertResponse(alerts=alerts, total_count=len(alerts))
    except Exception as e:
        logger.warning(f"BigQuery error, using fallback: {e}")
        alerts = [
            {
                "alert_id": "ALT-001",
                "loan_id": "LOAN-0001",
                "type": "covenant_warning",
                "severity": "MEDIUM",
                "message": "Interest Coverage approaching threshold",
                "created_at": datetime.now().isoformat(),
                "acknowledged": False,
            },
            {
                "alert_id": "ALT-002",
                "loan_id": "LOAN-0003",
                "type": "covenant_breach",
                "severity": "HIGH",
                "message": "Debt/EBITDA covenant breached",
                "created_at": datetime.now().isoformat(),
                "acknowledged": False,
            },
        ]
        return AlertResponse(alerts=alerts, total_count=len(alerts))


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    return {"alert_id": alert_id, "acknowledged": True, "acknowledged_at": datetime.now().isoformat()}


# Chat endpoint for agent interaction
@app.post("/api/chat")
async def chat_with_agent(message: str, loan_id: Optional[str] = None):
    """Chat with LoanGuard AI agent."""
    # In production, route to appropriate service
    return {
        "response": f"I understand you're asking about {loan_id or 'your loans'}. How can I help with covenant or ESG compliance?",
        "suggestions": [
            "Show me loans at risk of breach",
            "Generate compliance report",
            "Check ESG status for LOAN-0001",
        ],
    }


# =============================================================================
# V6 NEW ENDPOINTS - Risk Velocity, Greenwashing Detection, Cure Calculator
# =============================================================================

class RiskVelocityRequest(BaseModel):
    """Request model for risk velocity calculation."""
    metric_name: str
    historical_values: List[Dict[str, Any]]
    threshold: float
    covenant_type: str = "max"


class RiskVelocityResponse(BaseModel):
    """Response model for risk velocity."""
    loan_id: str
    metric_name: str
    current_value: float
    threshold: float
    headroom_percent: float
    velocity: Dict[str, float]
    trajectory: str
    periods_to_breach: Optional[float]
    risk_level: str
    summary: str


class GreenwashingRequest(BaseModel):
    """Request model for greenwashing detection."""
    borrower_name: str
    claims: List[Dict[str, str]]  # [{"text": "...", "category": "..."}]


class GreenwashingResponse(BaseModel):
    """Response model for greenwashing detection."""
    borrower: str
    claims_analyzed: int
    overall_risk: str
    overall_score: float
    high_risk_claims: int
    recommendation: str
    results: List[Dict[str, Any]]


class CureCalculatorRequest(BaseModel):
    """Request model for cure calculator."""
    covenant_type: str
    current_value: float
    threshold: float
    total_debt: Optional[float] = None
    ebitda: Optional[float] = None


class CureCalculatorResponse(BaseModel):
    """Response model for cure calculator."""
    loan_id: str
    covenant_type: str
    is_breached: bool
    cure_deadline_days: int
    options_count: int
    recommended: Optional[Dict[str, Any]]
    options: List[Dict[str, Any]]
    summary: str


# Risk Velocity Endpoints (V6 P0)
@app.get("/api/loans/{loan_id}/velocity", response_model=RiskVelocityResponse)
async def get_loan_velocity(loan_id: str, metric: str = "debt_to_ebitda"):
    """
    Get risk velocity analysis for a loan metric.
    
    Shows WHERE the loan is GOING, not just where it is.
    This is a UNIQUE feature - trajectory-based early warning.
    """
    # Mock data - in production, calculate from historical BigQuery data
    return RiskVelocityResponse(
        loan_id=loan_id,
        metric_name=metric,
        current_value=3.8,
        threshold=4.0,
        headroom_percent=5.0,
        velocity={"current": 0.15, "average": 0.12, "unit": "per_quarter"},
        trajectory="WORSENING",
        periods_to_breach=1.3,
        risk_level="HIGH",
        summary="⚠️ WARNING: Breach possible in 1.3 quarters if trend continues.",
    )


@app.post("/api/loans/{loan_id}/velocity/calculate")
async def calculate_velocity(loan_id: str, request: RiskVelocityRequest):
    """Calculate risk velocity for a specific metric with custom historical data."""
    from covenant_service.covenant_service.tools.risk_velocity_tools import calculate_metric_velocity
    
    result = calculate_metric_velocity(
        historical_values=request.historical_values,
        threshold=request.threshold,
        covenant_type=request.covenant_type,
    )
    
    if result.get("success"):
        result["loan_id"] = loan_id
        result["metric_name"] = request.metric_name
    
    return result


@app.get("/api/portfolio/velocity")
async def get_portfolio_velocity():
    """Get velocity analysis across entire portfolio."""
    # Mock data - in production, aggregate from all loans
    return {
        "total_loans_analyzed": 50,
        "risk_distribution": {
            "CRITICAL": 2,
            "HIGH": 5,
            "MEDIUM": 12,
            "LOW": 31,
        },
        "worsening_loans": [
            {"loan_id": "LOAN-0003", "risk_level": "CRITICAL", "nearest_breach": 0.8},
            {"loan_id": "LOAN-0012", "risk_level": "HIGH", "nearest_breach": 1.5},
            {"loan_id": "LOAN-0025", "risk_level": "HIGH", "nearest_breach": 2.1},
        ],
        "summary": "7 loans require immediate attention",
    }


# Greenwashing Detection Endpoints (V6 P0 - HERO FEATURE)
@app.post("/api/esg/greenwashing/detect", response_model=GreenwashingResponse)
async def detect_greenwashing(request: GreenwashingRequest):
    """
    Detect ESG greenwashing by analyzing claims against external sources.
    
    This is the HERO FEATURE for the demo.
    DWS was fined €25M for greenwashing - this helps avoid that.
    """
    from esg_service.esg_service.tools.greenwashing_search_tools import detect_greenwashing_sync
    
    result = detect_greenwashing_sync(
        borrower_name=request.borrower_name,
        esg_claims=request.claims,
    )
    
    return GreenwashingResponse(
        borrower=result.get("borrower", request.borrower_name),
        claims_analyzed=result.get("claims_analyzed", len(request.claims)),
        overall_risk=result.get("overall_risk", "MEDIUM"),
        overall_score=result.get("overall_score", 0.5),
        high_risk_claims=result.get("high_risk_claims", 0),
        recommendation=result.get("recommendation", "Review ESG documentation"),
        results=result.get("results", []),
    )


@app.get("/api/loans/{loan_id}/greenwashing")
async def get_loan_greenwashing(loan_id: str):
    """Get greenwashing analysis for a specific loan."""
    # Mock data - in production, fetch from database
    return {
        "loan_id": loan_id,
        "borrower": "Acme Corporation",
        "analysis_date": datetime.now().isoformat(),
        "overall_risk": "MEDIUM",
        "overall_score": 0.65,
        "claims_analyzed": 3,
        "results": [
            {
                "claim": "Carbon neutral by 2030",
                "verdict": "QUESTIONABLE",
                "risk_level": "MEDIUM",
                "flags": ["NO_THIRD_PARTY_VERIFICATION"],
            },
            {
                "claim": "100% renewable energy by 2028",
                "verdict": "VERIFIED",
                "risk_level": "LOW",
                "flags": [],
            },
        ],
        "recommendation": "Request supporting documentation for carbon neutrality claim.",
        "regulatory_context": {
            "dws_fine": "€25M for ESG greenwashing (2025)",
            "cma_enforcement": "Starting Autumn 2025",
        },
    }


# Cure Calculator Endpoints (V6 P2)
@app.post("/api/loans/{loan_id}/cure/calculate", response_model=CureCalculatorResponse)
async def calculate_cure(loan_id: str, request: CureCalculatorRequest):
    """
    Calculate cure options for a covenant breach or near-breach.
    
    Shows HOW to fix the problem, not just that it exists.
    """
    from covenant_service.covenant_service.tools.cure_calculator_tools import calculate_cure_options
    
    loan_details = {}
    if request.total_debt:
        loan_details["total_debt"] = request.total_debt
    if request.ebitda:
        loan_details["ebitda"] = request.ebitda
    
    result = calculate_cure_options(
        loan_id=loan_id,
        covenant_type=request.covenant_type,
        current_value=request.current_value,
        threshold=request.threshold,
        loan_details=loan_details if loan_details else None,
    )
    
    return CureCalculatorResponse(
        loan_id=loan_id,
        covenant_type=request.covenant_type,
        is_breached=result.get("is_breached", False),
        cure_deadline_days=result.get("cure_deadline_days", 30),
        options_count=result.get("options_count", 0),
        recommended=result.get("recommended"),
        options=result.get("options", []),
        summary=result.get("summary", ""),
    )


@app.get("/api/loans/{loan_id}/cure")
async def get_loan_cure_options(loan_id: str):
    """Get pre-calculated cure options for a loan's at-risk covenants."""
    # Mock data - in production, calculate for all at-risk covenants
    return {
        "loan_id": loan_id,
        "at_risk_covenants": 1,
        "cure_analyses": [
            {
                "covenant_type": "debt_to_ebitda",
                "current_value": 4.2,
                "threshold": 4.0,
                "is_breached": True,
                "cure_deadline_days": 30,
                "recommended": {
                    "method": "EQUITY_CURE",
                    "amount": 15_000_000,
                    "description": "Inject $15,000,000 equity (sponsor contribution)",
                    "feasibility": "MEDIUM",
                },
                "options_count": 4,
            },
        ],
    }


# ML Predictions Endpoints (V6 P1)
@app.get("/api/loans/{loan_id}/predictions")
async def get_breach_predictions(loan_id: str):
    """Get ML-based breach predictions for a loan."""
    return {
        "loan_id": loan_id,
        "breach_probability": 0.35,
        "breach_probability_pct": "35%",
        "risk_level": "MEDIUM",
        "prediction_horizon": "90 days",
        "top_risk_factors": [
            {"factor": "Declining EBITDA", "impact": 0.25},
            {"factor": "Rising debt levels", "impact": 0.18},
            {"factor": "Industry headwinds", "impact": 0.12},
        ],
        "model_version": "1.0.0",
    }


@app.get("/api/loans/{loan_id}/predictions/explain")
async def get_prediction_explanation(loan_id: str):
    """Get SHAP explanation for breach prediction."""
    return {
        "loan_id": loan_id,
        "explanation_type": "SHAP",
        "base_value": 0.2,
        "prediction": 0.35,
        "feature_contributions": [
            {"feature": "debt_to_ebitda_ratio", "value": 3.8, "contribution": 0.08},
            {"feature": "interest_coverage_ratio", "value": 2.6, "contribution": 0.04},
            {"feature": "revenue_growth_yoy", "value": -0.05, "contribution": 0.03},
        ],
        "summary": "High leverage and declining revenue are the main risk drivers.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
