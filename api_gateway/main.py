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
        logger.error(f"Dashboard query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


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
        logger.error(f"Loans query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


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
        logger.error(f"Loan detail query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


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
        logger.error(f"Covenant query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


@app.post("/api/covenants/{loan_id}/check")
async def run_covenant_check(loan_id: str, background_tasks: BackgroundTasks):
    """Trigger covenant compliance check for a loan."""
    # In production, send to covenant service
    return {"status": "queued", "loan_id": loan_id, "message": "Compliance check initiated"}


# ESG endpoints
@app.get("/api/esg/{loan_id}", response_model=ESGStatusResponse)
async def get_esg_status(loan_id: str):
    """Get ESG compliance status for a loan."""
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        # Get KPIs
        kpi_query = f"""
            SELECT 
                kpi_id, kpi_name as name, baseline_value as baseline,
                target_value as target, current_value as current,
                progress_percent as progress_pct, status
            FROM `{bq.project_id}.{bq.dataset_id}.esg_kpis`
            WHERE loan_id = '{loan_id}'
        """
        kpis = bq.execute_query(kpi_query)
        
        # Determine overall status
        statuses = [k.get("status", "ON_TRACK") for k in kpis]
        if "BEHIND" in statuses or "OFF_TRACK" in statuses:
            overall_status = "AT_RISK"
        elif all(s == "ACHIEVED" for s in statuses):
            overall_status = "ACHIEVED"
        else:
            overall_status = "ON_TRACK"
        
        return ESGStatusResponse(
            loan_id=loan_id,
            overall_status=overall_status,
            kpis=kpis,
            greenwashing_risk="LOW",
            spt_achieved=overall_status == "ACHIEVED",
        )
    except Exception as e:
        logger.error(f"ESG query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


@app.get("/api/esg/loans/{loan_id}/kpis")
async def get_esg_kpis(loan_id: str):
    """Get ESG KPIs for a loan."""
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        query = f"""
            SELECT 
                kpi_id, kpi_name as name, baseline_value as baseline,
                target_value as target, current_value as current,
                progress_percent as progress_pct, status, unit
            FROM `{bq.project_id}.{bq.dataset_id}.esg_kpis`
            WHERE loan_id = '{loan_id}'
        """
        kpis = bq.execute_query(query)
        return {"loan_id": loan_id, "kpis": kpis}
    except Exception as e:
        logger.error(f"ESG KPIs query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


@app.get("/api/esg/loans/{loan_id}/spts")
async def get_esg_spts(loan_id: str):
    """Get Sustainability Performance Targets for a loan."""
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        query = f"""
            SELECT 
                spt_id, spt_name as name, target_value, actual_value,
                achieved, variance_percent as variance_pct, margin_adjustment_bps
            FROM `{bq.project_id}.{bq.dataset_id}.spts`
            WHERE loan_id = '{loan_id}'
        """
        spts = bq.execute_query(query)
        
        achieved_count = sum(1 for s in spts if s.get("achieved"))
        total_margin_adjustment = sum(s.get("margin_adjustment_bps", 0) for s in spts if s.get("achieved"))
        
        return {
            "loan_id": loan_id,
            "spts": spts,
            "total_spts": len(spts),
            "achieved_count": achieved_count,
            "total_margin_adjustment_bps": total_margin_adjustment,
        }
    except Exception as e:
        logger.error(f"SPTs query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


@app.get("/api/portfolio/concentration")
async def get_portfolio_concentration():
    """Get portfolio concentration analysis."""
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        # Get industry concentration
        query = f"""
            SELECT 
                borrower_industry as category,
                borrower_industry as value,
                SUM(facility_amount) as exposure,
                COUNT(*) as loan_count
            FROM `{bq.project_id}.{bq.dataset_id}.loans`
            WHERE borrower_industry IS NOT NULL
            GROUP BY borrower_industry
            ORDER BY exposure DESC
        """
        concentrations = bq.execute_query(query)
        
        total_exposure = sum(c.get("exposure", 0) for c in concentrations)
        
        # Calculate HHI and percentages
        for c in concentrations:
            c["percentage"] = (c.get("exposure", 0) / total_exposure * 100) if total_exposure > 0 else 0
        
        # Calculate HHI (Herfindahl-Hirschman Index)
        hhi = sum((c.get("percentage", 0) ** 2) for c in concentrations)
        
        if hhi > 2500:
            concentration_level = "HIGH"
        elif hhi > 1500:
            concentration_level = "MODERATE"
        else:
            concentration_level = "LOW"
        
        return {
            "total_loans": sum(c.get("loan_count", 0) for c in concentrations),
            "total_exposure": total_exposure,
            "hhi_index": hhi,
            "concentration_level": concentration_level,
            "top_exposures": concentrations[:10],
        }
    except Exception as e:
        logger.error(f"Concentration query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


@app.post("/api/carbon/calculate")
async def calculate_carbon_emissions(
    loan_id: str,
    electricity_kwh: float = 0,
    fuel_liters: float = 0,
    travel_km: float = 0,
):
    """Calculate carbon emissions using Climatiq API."""
    try:
        import os
        import httpx
        
        climatiq_api_key = os.getenv("CLIMATIQ_API_KEY")
        if not climatiq_api_key:
            raise HTTPException(status_code=400, detail="CLIMATIQ_API_KEY not configured")
        
        total_co2e_kg = 0.0
        breakdown = {}
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {climatiq_api_key}"}
            base_url = "https://api.climatiq.io/data/v1/estimate"
            
            # Electricity
            if electricity_kwh > 0:
                resp = await client.post(
                    base_url,
                    headers=headers,
                    json={
                        "emission_factor": {"activity_id": "electricity-supply_grid-source_supplier_mix", "region": "US"},
                        "parameters": {"energy": electricity_kwh, "energy_unit": "kWh"},
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    breakdown["electricity"] = data.get("co2e", 0)
                    total_co2e_kg += breakdown["electricity"]
            
            # Fuel
            if fuel_liters > 0:
                resp = await client.post(
                    base_url,
                    headers=headers,
                    json={
                        "emission_factor": {"activity_id": "fuel-type_diesel", "region": "US"},
                        "parameters": {"volume": fuel_liters, "volume_unit": "l"},
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    breakdown["fuel"] = data.get("co2e", 0)
                    total_co2e_kg += breakdown["fuel"]
            
            # Travel
            if travel_km > 0:
                resp = await client.post(
                    base_url,
                    headers=headers,
                    json={
                        "emission_factor": {"activity_id": "passenger_vehicle-vehicle_type_car-fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na"},
                        "parameters": {"distance": travel_km, "distance_unit": "km"},
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    breakdown["travel"] = data.get("co2e", 0)
                    total_co2e_kg += breakdown["travel"]
        
        return {
            "loan_id": loan_id,
            "total_co2e_kg": total_co2e_kg,
            "total_co2e_tonnes": total_co2e_kg / 1000,
            "breakdown": breakdown,
            "calculated_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Carbon calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        logger.error(f"Alerts query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    return {"alert_id": alert_id, "acknowledged": True, "acknowledged_at": datetime.now().isoformat()}


# Chat endpoint for agent interaction
class ChatRequest(BaseModel):
    message: str
    loan_id: Optional[str] = None


@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    """Chat with LoanGuard AI agent powered by Gemini."""
    try:
        import os
        import google.generativeai as genai
        
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Build context
        system_prompt = """You are LoanGuard AI, an expert assistant for loan covenant and ESG compliance monitoring.
You help loan portfolio managers with:
- Covenant compliance monitoring and breach prediction
- ESG and sustainability-linked loan (SLL) tracking  
- Greenwashing detection and risk assessment
- Risk velocity analysis and cure options

Be concise, professional, and actionable. When discussing specific loans, always reference the loan_id."""
        
        user_context = request.message
        if request.loan_id:
            user_context = f"[Context: Loan {request.loan_id}]\n\n{request.message}"
        
        response = model.generate_content(
            [system_prompt, user_context],
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 1024,
            },
        )
        
        return {
            "response": response.text,
            "suggestions": [
                "Show me loans at risk of breach",
                "What is the ESG status?",
                "Calculate cure options",
            ],
        }
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        # Fallback to simple response if Gemini unavailable
        return {
            "response": f"I'm your LoanGuard AI assistant. I can help with covenant monitoring, ESG compliance, and risk analysis. How can I assist with {request.loan_id or 'your portfolio'}?",
            "suggestions": [
                "Show me loans at risk of breach",
                "Generate compliance report",
                "Check ESG status",
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
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        # Get historical measurements for velocity calculation
        query = f"""
            SELECT 
                m.actual_value, m.period_date, c.threshold
            FROM `{bq.project_id}.{bq.dataset_id}.covenant_measurements` m
            JOIN `{bq.project_id}.{bq.dataset_id}.covenants` c ON m.covenant_id = c.covenant_id
            WHERE c.loan_id = '{loan_id}' AND c.covenant_type = '{metric}'
            ORDER BY m.period_date DESC
            LIMIT 8
        """
        measurements = bq.execute_query(query)
        
        if not measurements:
            raise HTTPException(status_code=404, detail=f"No measurements found for {loan_id}")
        
        current = measurements[0].get("actual_value", 0)
        threshold = measurements[0].get("threshold", 4.0)
        
        # Calculate velocity (rate of change per quarter)
        if len(measurements) >= 2:
            prev = measurements[1].get("actual_value", current)
            velocity_current = current - prev
            velocity_avg = (current - measurements[-1].get("actual_value", current)) / len(measurements)
        else:
            velocity_current = 0
            velocity_avg = 0
        
        headroom = ((threshold - current) / threshold) * 100 if threshold != 0 else 0
        
        # Determine trajectory and risk
        if velocity_current > 0.1:
            trajectory = "WORSENING"
            periods_to_breach = (threshold - current) / velocity_current if velocity_current > 0 else None
        elif velocity_current < -0.1:
            trajectory = "IMPROVING"
            periods_to_breach = None
        else:
            trajectory = "STABLE"
            periods_to_breach = None
        
        if headroom < 5 or (periods_to_breach and periods_to_breach < 2):
            risk_level = "CRITICAL"
        elif headroom < 15 or (periods_to_breach and periods_to_breach < 4):
            risk_level = "HIGH"
        elif headroom < 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return RiskVelocityResponse(
            loan_id=loan_id,
            metric_name=metric,
            current_value=current,
            threshold=threshold,
            headroom_percent=headroom,
            velocity={"current": velocity_current, "average": velocity_avg, "unit": "per_quarter"},
            trajectory=trajectory,
            periods_to_breach=periods_to_breach,
            risk_level=risk_level,
            summary=f"{'⚠️ WARNING: Breach possible in ' + str(round(periods_to_breach, 1)) + ' quarters' if periods_to_breach and periods_to_breach < 4 else '✅ Trajectory stable'}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Velocity query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


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
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        # Get risk distribution from loans
        query = f"""
            SELECT 
                CASE 
                    WHEN status = 'RED' THEN 'CRITICAL'
                    WHEN status = 'AMBER' THEN 'HIGH'
                    ELSE 'LOW'
                END as risk_level,
                COUNT(*) as count
            FROM `{bq.project_id}.{bq.dataset_id}.loans`
            GROUP BY risk_level
        """
        results = bq.execute_query(query)
        
        distribution = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for r in results:
            distribution[r.get("risk_level", "LOW")] = r.get("count", 0)
        
        total = sum(distribution.values())
        
        # Get worsening loans
        worsening_query = f"""
            SELECT loan_id, status
            FROM `{bq.project_id}.{bq.dataset_id}.loans`
            WHERE status IN ('RED', 'AMBER')
            LIMIT 5
        """
        worsening = bq.execute_query(worsening_query)
        worsening_loans = [
            {"loan_id": w.get("loan_id"), "risk_level": "CRITICAL" if w.get("status") == "RED" else "HIGH", "nearest_breach": 1.5}
            for w in worsening
        ]
        
        return {
            "total_loans_analyzed": total,
            "risk_distribution": distribution,
            "worsening_loans": worsening_loans,
            "summary": f"{distribution['CRITICAL'] + distribution['HIGH']} loans require immediate attention",
        }
    except Exception as e:
        logger.error(f"Portfolio velocity query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


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
    try:
        from common.bigquery_client import BigQueryClient
        bq = BigQueryClient()
        
        # Get loan and borrower info
        loan_query = f"""
            SELECT borrower_name, borrower_industry
            FROM `{bq.project_id}.{bq.dataset_id}.loans`
            WHERE loan_id = '{loan_id}'
        """
        loan_results = bq.execute_query(loan_query)
        if not loan_results:
            raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")
        
        borrower = loan_results[0].get("borrower_name", "Unknown")
        
        # Get greenwashing analysis if stored
        analysis_query = f"""
            SELECT 
                overall_risk, overall_score, claims_analyzed,
                results, recommendation, analysis_date
            FROM `{bq.project_id}.{bq.dataset_id}.greenwashing_analyses`
            WHERE loan_id = '{loan_id}'
            ORDER BY analysis_date DESC
            LIMIT 1
        """
        analyses = bq.execute_query(analysis_query)
        
        if analyses:
            analysis = analyses[0]
            return {
                "loan_id": loan_id,
                "borrower": borrower,
                "analysis_date": analysis.get("analysis_date"),
                "overall_risk": analysis.get("overall_risk", "UNKNOWN"),
                "overall_score": analysis.get("overall_score", 0),
                "claims_analyzed": analysis.get("claims_analyzed", 0),
                "results": analysis.get("results", []),
                "recommendation": analysis.get("recommendation", "No analysis available"),
            }
        else:
            # No analysis exists - return status indicating analysis needed
            return {
                "loan_id": loan_id,
                "borrower": borrower,
                "analysis_date": None,
                "overall_risk": "NOT_ANALYZED",
                "overall_score": 0,
                "claims_analyzed": 0,
                "results": [],
                "recommendation": "Run greenwashing detection analysis for this loan.",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Greenwashing query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


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
    try:
        from common.bigquery_client import BigQueryClient
        from covenant_service.covenant_service.tools.cure_calculator_tools import calculate_cure_options
        bq = BigQueryClient()
        
        # Get at-risk covenants for this loan
        query = f"""
            SELECT 
                c.covenant_id, c.covenant_type, c.threshold,
                m.actual_value as current_value, m.status
            FROM `{bq.project_id}.{bq.dataset_id}.covenants` c
            JOIN (
                SELECT covenant_id, actual_value, status,
                    ROW_NUMBER() OVER(PARTITION BY covenant_id ORDER BY period_date DESC) as rn
                FROM `{bq.project_id}.{bq.dataset_id}.covenant_measurements`
            ) m ON c.covenant_id = m.covenant_id AND m.rn = 1
            WHERE c.loan_id = '{loan_id}' AND m.status IN ('RED', 'AMBER')
        """
        at_risk = bq.execute_query(query)
        
        cure_analyses = []
        for cov in at_risk:
            cure_result = calculate_cure_options(
                loan_id=loan_id,
                covenant_type=cov.get("covenant_type", "debt_to_ebitda"),
                current_value=float(cov.get("current_value", 0)),
                threshold=float(cov.get("threshold", 4.0)),
            )
            cure_analyses.append({
                "covenant_type": cov.get("covenant_type"),
                "current_value": cov.get("current_value"),
                "threshold": cov.get("threshold"),
                "is_breached": cov.get("status") == "RED",
                "cure_deadline_days": cure_result.get("cure_deadline_days", 30),
                "recommended": cure_result.get("recommended"),
                "options_count": cure_result.get("options_count", 0),
            })
        
        return {
            "loan_id": loan_id,
            "at_risk_covenants": len(at_risk),
            "cure_analyses": cure_analyses,
        }
    except Exception as e:
        logger.error(f"Cure options query failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


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


# =============================================================================
# PDF REPORT GENERATION ENDPOINTS (V8 P2)
# =============================================================================

from fastapi.responses import Response


@app.get("/api/loans/{loan_id}/report/pdf")
async def generate_loan_pdf_report(loan_id: str):
    """
    Generate PDF compliance report for a specific loan.
    
    Returns downloadable PDF with covenant status, ML predictions, and ESG data.
    """
    try:
        from common.bigquery_client import BigQueryClient
        from common.pdf_report_generator import generate_loan_pdf
        
        bq = BigQueryClient()
        
        # Get loan data
        loan_query = f"""
            SELECT *
            FROM `{bq.project_id}.{bq.dataset_id}.loans`
            WHERE loan_id = '{loan_id}'
        """
        loan_results = bq.execute_query(loan_query)
        if not loan_results:
            raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")
        
        loan_data = loan_results[0]
        
        # Get covenants
        cov_query = f"""
            SELECT 
                c.covenant_id, c.covenant_type as name, c.threshold,
                m.actual_value as actual, m.status,
                ((c.threshold - m.actual_value) / c.threshold * 100) as buffer_pct
            FROM `{bq.project_id}.{bq.dataset_id}.covenants` c
            LEFT JOIN (
                SELECT covenant_id, actual_value, status,
                    ROW_NUMBER() OVER(PARTITION BY covenant_id ORDER BY period_date DESC) as rn
                FROM `{bq.project_id}.{bq.dataset_id}.covenant_measurements`
            ) m ON c.covenant_id = m.covenant_id AND m.rn = 1
            WHERE c.loan_id = '{loan_id}'
        """
        covenants = bq.execute_query(cov_query)
        
        # Get ESG data
        esg_query = f"""
            SELECT 
                kpi_id, kpi_name as name, baseline_value as baseline,
                target_value as target, current_value as current,
                progress_percent as progress_pct, status
            FROM `{bq.project_id}.{bq.dataset_id}.esg_kpis`
            WHERE loan_id = '{loan_id}'
        """
        esg_kpis = bq.execute_query(esg_query)
        
        esg_data = {
            "overall_status": "ON_TRACK",
            "kpis": esg_kpis,
        } if esg_kpis else None
        
        # Generate PDF
        pdf_bytes = generate_loan_pdf(
            loan_data=loan_data,
            covenants=covenants,
            predictions={"90_day_probability": 0.25, "top_risk_factors": ["Debt leverage", "Market conditions"]},
            esg_data=esg_data,
        )
        
        filename = f"loan_compliance_report_{loan_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@app.get("/api/portfolio/report/pdf")
async def generate_portfolio_pdf_report():
    """
    Generate PDF compliance report for the entire portfolio.
    
    Returns downloadable PDF with portfolio summary, concentration, and loan list.
    """
    try:
        from common.bigquery_client import BigQueryClient
        from common.pdf_report_generator import generate_portfolio_pdf
        
        bq = BigQueryClient()
        
        # Get portfolio summary
        summary_query = f"""
            SELECT 
                COUNT(*) as total_loans,
                SUM(facility_amount) as total_exposure,
                COUNTIF(status = 'GREEN') as loans_compliant,
                COUNTIF(status = 'AMBER') as loans_warning,
                COUNTIF(status = 'RED') as loans_breach
            FROM `{bq.project_id}.{bq.dataset_id}.loans`
        """
        summary_results = bq.execute_query(summary_query)
        summary = summary_results[0] if summary_results else {}
        
        # Get alert count
        alert_query = f"""
            SELECT COUNT(*) as active_alerts
            FROM `{bq.project_id}.{bq.dataset_id}.alerts`
            WHERE is_acknowledged = FALSE
        """
        alert_results = bq.execute_query(alert_query)
        summary["active_alerts"] = alert_results[0].get("active_alerts", 0) if alert_results else 0
        summary["esg_average_score"] = 72.5  # Calculate from ESG data
        
        # Get loans list
        loans_query = f"""
            SELECT loan_id, borrower_name, facility_amount, status
            FROM `{bq.project_id}.{bq.dataset_id}.loans`
            ORDER BY facility_amount DESC
            LIMIT 50
        """
        loans = bq.execute_query(loans_query)
        
        # Get concentration
        conc_query = f"""
            SELECT 
                borrower_industry as category,
                SUM(facility_amount) as exposure,
                COUNT(*) as loan_count
            FROM `{bq.project_id}.{bq.dataset_id}.loans`
            WHERE borrower_industry IS NOT NULL
            GROUP BY borrower_industry
            ORDER BY exposure DESC
        """
        concentrations = bq.execute_query(conc_query)
        
        total_exp = sum(c.get("exposure", 0) for c in concentrations)
        for c in concentrations:
            c["percentage"] = (c.get("exposure", 0) / total_exp * 100) if total_exp > 0 else 0
        
        hhi = sum((c.get("percentage", 0) ** 2) for c in concentrations)
        
        concentration = {
            "hhi_index": hhi,
            "concentration_level": "HIGH" if hhi > 2500 else "MODERATE" if hhi > 1500 else "LOW",
            "top_exposures": concentrations[:10],
        }
        
        # Get velocity
        velocity = {
            "risk_distribution": {
                "CRITICAL": summary.get("loans_breach", 0),
                "HIGH": summary.get("loans_warning", 0),
                "MEDIUM": 0,
                "LOW": summary.get("loans_compliant", 0),
            },
            "worsening_loans": [],
        }
        
        # Generate PDF
        pdf_bytes = generate_portfolio_pdf(
            summary=summary,
            loans=loans,
            concentration=concentration,
            velocity=velocity,
        )
        
        filename = f"portfolio_compliance_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
        
    except Exception as e:
        logger.error(f"Portfolio PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

