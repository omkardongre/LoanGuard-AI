/**
 * LoanGuard API Client - Production Level
 * 
 * Complete API integration for all backend services.
 * V8 Architecture - 88 endpoints
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// ============================================
// Type Definitions
// ============================================

export interface Loan {
  loan_id: string;
  borrower_name: string;
  borrower_industry?: string;
  facility_amount: number;
  currency: string;
  maturity_date: string;
  loan_type?: string;
  is_sll: boolean;
  agent_bank?: string;
  status: "GREEN" | "AMBER" | "RED";
  covenant_count?: number;
  overall_status?: string;
}

export interface Covenant {
  covenant_id: string;
  loan_id?: string;
  covenant_name?: string;
  name?: string;
  covenant_type?: string;
  threshold: number | string;
  threshold_type?: string;
  actual?: number | string;
  status: "GREEN" | "AMBER" | "RED";
  buffer_pct?: number;
}

export interface CovenantMeasurement {
  measurement_id: string;
  covenant_id: string;
  actual_value: number;
  measurement_date: string;
  is_in_compliance: boolean;
  headroom_percent: number;
}

export interface ESGKpi {
  kpi_id: string;
  loan_id?: string;
  name: string;
  kpi_name?: string;
  baseline: number;
  target: number;
  target_value?: number;
  current: number;
  current_value?: number;
  progress_pct: number;
  on_track?: boolean;
  status: string;
  unit?: string;
}

export interface SPT {
  spt_id: string;
  name: string;
  target_value: number;
  actual_value?: number;
  achieved: boolean;
  variance_pct?: number;
}

export interface Alert {
  alert_id: string;
  loan_id: string;
  type: string;
  alert_type?: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  title?: string;
  message: string;
  created_at: string;
  acknowledged: boolean;
  is_acknowledged?: boolean;
}

export interface DashboardSummary {
  total_loans: number;
  loans_compliant: number;
  loans_warning: number;
  loans_breach: number;
  active_alerts: number;
  esg_average_score: number;
}

export interface RiskVelocity {
  loan_id: string;
  metric_name: string;
  current_value: number;
  threshold: number;
  headroom_percent: number;
  velocity: {
    current: number;
    average: number;
    unit: string;
  };
  trajectory: "IMPROVING" | "STABLE" | "WORSENING";
  periods_to_breach: number | null;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  summary: string;
}

export interface BreachPrediction {
  loan_id: string;
  breach_probability: number;
  breach_probability_pct: string;
  risk_level: string;
  prediction_horizon: string;
  top_risk_factors: Array<{
    factor: string;
    impact: number;
  }>;
  model_version: string;
}

export interface SHAPExplanation {
  loan_id: string;
  explanation_type: string;
  base_value: number;
  prediction: number;
  feature_contributions: Array<{
    feature: string;
    value: number;
    contribution: number;
  }>;
  summary: string;
}

export interface GreenwashingResult {
  success: boolean;
  company?: string;
  borrower?: string;
  claim?: string;
  claims_analyzed: number;
  overall_risk: string;
  overall_score: number;
  risk_level?: string;
  risk_score?: number;
  verdict?: string;
  high_risk_claims?: number;
  evidence_count?: number;
  key_findings?: string[];
  sources_searched?: number;
  recommendation?: string;
  results?: Array<{
    claim: string;
    category?: string;
    verification_score: number;
    verdict: string;
    language_flags?: string[];
    greenwashing_risk: string;
    contradictions?: Array<{
      title: string;
      source: string;
      snippet: string;
      severity?: string;
    }>;
    supporting_evidence?: Array<{
      title: string;
      source: string;
      snippet: string;
    }>;
  }>;
}

export interface CarbonEmissions {
  success: boolean;
  co2e_kg: number;
  co2e_tonnes?: number;
  emission_factor?: {
    id: string;
    name: string;
    source: string;
    region: string;
    year: number;
  };
  source: string;
  calculated_at: string;
}

export interface CureOption {
  method: string;
  amount?: number;
  description: string;
  feasibility: "HIGH" | "MEDIUM" | "LOW";
  timeline_days?: number;
}

export interface CureResult {
  loan_id: string;
  covenant_type: string;
  is_breached: boolean;
  cure_deadline_days: number;
  options_count: number;
  recommended?: CureOption;
  options: CureOption[];
  summary: string;
}

export interface PortfolioConcentration {
  total_loans: number;
  total_exposure: number;
  hhi_index: number;
  concentration_level: "LOW" | "MODERATE" | "HIGH";
  top_exposures: Array<{
    category: string;
    value: string;
    exposure: number;
    percentage: number;
  }>;
}

export interface DocumentParseResult {
  document_id: string;
  loan_id?: string;
  status: string;
  borrower_name?: string;
  lender_name?: string;
  loan_amount?: number;
  currency?: string;
  maturity_date?: string;
  interest_rate?: string;
  covenants_extracted?: number;
  extraction_confidence?: number;
}

// ============================================
// API Helper
// ============================================

async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  
  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`API Error ${res.status}: ${errorText}`);
  }
  
  return res.json();
}

// ============================================
// Dashboard & Portfolio
// ============================================

export async function fetchDashboard(): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>("/api/dashboard");
}

export async function fetchPortfolioVelocity(): Promise<{
  total_loans_analyzed: number;
  risk_distribution: Record<string, number>;
  worsening_loans: Array<{
    loan_id: string;
    risk_level: string;
    nearest_breach: number;
  }>;
  summary: string;
}> {
  return apiRequest("/api/portfolio/velocity");
}

export async function fetchPortfolioConcentration(): Promise<PortfolioConcentration> {
  return apiRequest("/api/portfolio/concentration");
}

// ============================================
// Loans
// ============================================

export async function fetchLoans(params?: {
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<{ loans: Loan[]; total: number; limit: number; offset: number }> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set("status", params.status);
  if (params?.limit) searchParams.set("limit", params.limit.toString());
  if (params?.offset) searchParams.set("offset", params.offset.toString());
  
  const query = searchParams.toString();
  return apiRequest(`/api/loans${query ? `?${query}` : ""}`);
}

export async function fetchLoan(loanId: string): Promise<Loan> {
  return apiRequest(`/api/loans/${loanId}`);
}

// ============================================
// Covenants
// ============================================

export async function fetchCovenants(loanId: string): Promise<{
  loan_id: string;
  overall_status: string;
  covenants: Covenant[];
  breach_predictions?: {
    "90_day_probability": number;
    top_risk_factors: string[];
  };
}> {
  return apiRequest(`/api/covenants/${loanId}`);
}

export async function fetchAllCovenants(): Promise<{
  success: boolean;
  covenants: Covenant[];
  total: number;
}> {
  // Fetch from covenant service directly
  return apiRequest("/api/covenants/all");
}

export async function triggerCovenantCheck(loanId: string): Promise<{
  status: string;
  loan_id: string;
  message: string;
}> {
  return apiRequest(`/api/covenants/${loanId}/check`, { method: "POST" });
}

// ============================================
// Risk Velocity
// ============================================

export async function fetchLoanVelocity(
  loanId: string,
  metric?: string
): Promise<RiskVelocity> {
  const query = metric ? `?metric=${metric}` : "";
  return apiRequest(`/api/loans/${loanId}/velocity${query}`);
}

export async function calculateVelocity(
  loanId: string,
  data: {
    metric_name: string;
    historical_values: Array<{ date: string; value: number }>;
    threshold: number;
    covenant_type?: string;
  }
): Promise<RiskVelocity> {
  return apiRequest(`/api/loans/${loanId}/velocity/calculate`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ============================================
// ML Predictions
// ============================================

export async function fetchBreachPrediction(loanId: string): Promise<BreachPrediction> {
  return apiRequest(`/api/loans/${loanId}/predictions`);
}

export async function fetchPredictionExplanation(loanId: string): Promise<SHAPExplanation> {
  return apiRequest(`/api/loans/${loanId}/predictions/explain`);
}

// ============================================
// Cure Calculator
// ============================================

export async function calculateCure(
  loanId: string,
  data: {
    covenant_type: string;
    current_value: number;
    threshold: number;
    total_debt?: number;
    ebitda?: number;
  }
): Promise<CureResult> {
  return apiRequest(`/api/loans/${loanId}/cure/calculate`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchLoanCureOptions(loanId: string): Promise<{
  loan_id: string;
  at_risk_covenants: number;
  cure_analyses: Array<{
    covenant_type: string;
    current_value: number;
    threshold: number;
    is_breached: boolean;
    cure_deadline_days: number;
    recommended?: CureOption;
    options_count: number;
  }>;
}> {
  return apiRequest(`/api/loans/${loanId}/cure`);
}

// ============================================
// ESG
// ============================================

export async function fetchESG(loanId: string): Promise<{
  loan_id: string;
  overall_status: string;
  kpis: ESGKpi[];
  greenwashing_risk: string;
  spt_achieved: boolean;
}> {
  return apiRequest(`/api/esg/${loanId}`);
}

export async function fetchESGKpis(loanId: string): Promise<{
  success: boolean;
  loan_id: string;
  kpis: ESGKpi[];
}> {
  return apiRequest(`/api/esg/loans/${loanId}/kpis`);
}

export async function fetchSPTs(loanId: string): Promise<{
  success: boolean;
  loan_id: string;
  spts: SPT[];
  margin_adjustment?: number;
}> {
  return apiRequest(`/api/esg/loans/${loanId}/spts`);
}

// ============================================
// Greenwashing Detection (HERO FEATURE)
// ============================================

export async function detectGreenwashing(data: {
  borrower_name: string;
  claims: Array<{ text: string; category?: string }>;
}): Promise<GreenwashingResult> {
  return apiRequest("/api/esg/greenwashing/detect", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchLoanGreenwashing(loanId: string): Promise<{
  loan_id: string;
  borrower: string;
  analysis_date: string;
  overall_risk: string;
  overall_score: number;
  claims_analyzed: number;
  results: Array<{
    claim: string;
    verdict: string;
    risk_level: string;
    flags: string[];
  }>;
  recommendation: string;
  regulatory_context: Record<string, string>;
}> {
  return apiRequest(`/api/loans/${loanId}/greenwashing`);
}

// ============================================
// Carbon Emissions
// ============================================

export async function fetchCarbonStatus(): Promise<{
  service: string;
  api: string;
  available: boolean;
  capabilities: string[];
}> {
  return apiRequest("/api/esg/carbon/status");
}

export async function calculateCarbonEmissions(
  loanId: string,
  data: {
    electricity_kwh: number;
    fuel_liters: number;
    travel_km: number;
    country_code?: string;
  }
): Promise<{
  loan_id: string;
  total_co2e_kg: number;
  breakdown: Record<string, number>;
  calculated_at: string;
}> {
  return apiRequest(`/api/esg/loans/${loanId}/carbon/calculate`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function calculateElectricityEmissions(
  kwh: number,
  country?: string
): Promise<CarbonEmissions> {
  const query = new URLSearchParams({ kwh: kwh.toString() });
  if (country) query.set("country", country);
  return apiRequest(`/api/esg/carbon/calculate/electricity?${query}`);
}

// ============================================
// News Validation
// ============================================

export async function validateClaimWithNews(data: {
  company_name: string;
  claim_text: string;
  days_back?: number;
}): Promise<{
  success: boolean;
  company: string;
  claim: string;
  credibility: string;
  supporting_articles: number;
  contradicting_articles: number;
  sentiment_summary: Record<string, number>;
}> {
  return apiRequest("/api/esg/news/validate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchCompanyControversies(
  companyName: string,
  daysBack?: number
): Promise<{
  company: string;
  controversies_found: number;
  categories: Record<string, number>;
  articles: Array<{
    title: string;
    source: string;
    published_at: string;
    category: string;
  }>;
}> {
  const query = new URLSearchParams();
  if (daysBack) query.set("days_back", daysBack.toString());
  return apiRequest(`/api/esg/companies/${encodeURIComponent(companyName)}/controversies?${query}`);
}

// ============================================
// Alerts
// ============================================

export async function fetchAlerts(params?: {
  loan_id?: string;
  severity?: string;
  acknowledged?: boolean;
  limit?: number;
}): Promise<{ alerts: Alert[]; total_count: number }> {
  const searchParams = new URLSearchParams();
  if (params?.loan_id) searchParams.set("loan_id", params.loan_id);
  if (params?.severity) searchParams.set("severity", params.severity);
  if (params?.acknowledged !== undefined) {
    searchParams.set("acknowledged", params.acknowledged.toString());
  }
  if (params?.limit) searchParams.set("limit", params.limit.toString());
  
  const query = searchParams.toString();
  return apiRequest(`/api/alerts${query ? `?${query}` : ""}`);
}

export async function acknowledgeAlert(alertId: string): Promise<{
  alert_id: string;
  acknowledged: boolean;
  acknowledged_at: string;
}> {
  return apiRequest(`/api/alerts/${alertId}/acknowledge`, { method: "POST" });
}

export async function createAlert(data: {
  loan_id: string;
  alert_type: string;
  severity: string;
  message: string;
  details?: Record<string, unknown>;
}): Promise<{ success: boolean; alert: Alert }> {
  return apiRequest("/api/alerts/create", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ============================================
// Documents
// ============================================

export async function uploadDocument(
  loanId: string,
  file: File
): Promise<DocumentParseResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("loan_id", loanId);
  
  const res = await fetch(`${API_BASE_URL}/api/documents/upload?loan_id=${loanId}`, {
    method: "POST",
    body: formData,
  });
  
  if (!res.ok) {
    throw new Error(`Upload failed: ${res.status}`);
  }
  
  return res.json();
}

export async function fetchDocument(documentId: string): Promise<{
  document_id: string;
  status: string;
  extracted_covenants: Array<{
    name: string;
    threshold: string;
    type: string;
  }>;
  extracted_entities: Record<string, string>;
}> {
  return apiRequest(`/api/documents/${documentId}`);
}

// ============================================
// Chat (AI Agent)
// ============================================

export async function chatWithAgent(
  message: string,
  loanId?: string
): Promise<{
  response: string;
  suggestions: string[];
}> {
  const body: Record<string, string> = { message };
  if (loanId) body.loan_id = loanId;
  
  return apiRequest("/api/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ============================================
// PDF Report Generation
// ============================================

export async function downloadLoanPdfReport(loanId: string): Promise<Blob> {
  const url = `${API_BASE_URL}/api/loans/${loanId}/report/pdf`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to generate PDF: ${response.status}`);
  }
  
  return response.blob();
}

export async function downloadPortfolioPdfReport(): Promise<Blob> {
  const url = `${API_BASE_URL}/api/portfolio/report/pdf`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to generate PDF: ${response.status}`);
  }
  
  return response.blob();
}

export function triggerPdfDownload(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  a.remove();
}

// ============================================
// LGD / Recovery Rate (V9 - Basel III)
// ============================================

export interface LGDPrediction {
  loan_id: string;
  recovery_rate: number;
  recovery_rate_pct: string;
  lgd: number;
  lgd_pct: string;
  recovery_category: "HIGH_RECOVERY" | "MODERATE_RECOVERY" | "LOW_RECOVERY" | "MINIMAL_RECOVERY";
  model_version: string;
  success: boolean;
}

export interface LGDExplanation {
  loan_id: string;
  stage1_factors: Array<{
    feature: string;
    impact: number;
    value: number;
  }>;
  stage2_factors: Array<{
    feature: string;
    impact: number;
    value: number;
  }>;
  success: boolean;
}

export interface LGDModelInfo {
  success: boolean;
  model_type: string;
  version: string;
  stage1: {
    type: string;
    target: string;
    auc: number;
  };
  stage2: {
    type: string;
    target: string;
    mae: number;
  };
  combined_mae: number;
  training_data: string;
  formula: string;
}

export async function fetchLGD(loanId: string): Promise<LGDPrediction> {
  return apiRequest(`/api/loans/${loanId}/lgd`);
}

export async function predictLGD(
  loanId: string,
  loanData: {
    loan_amnt?: number;
    int_rate?: number;
    grade?: string;
    annual_inc?: number;
    dti?: number;
    fico_range_low?: number;
    fico_range_high?: number;
  }
): Promise<LGDPrediction> {
  return apiRequest(`/api/loans/${loanId}/lgd/predict`, {
    method: "POST",
    body: JSON.stringify(loanData),
  });
}

export async function fetchLGDExplanation(
  loanId: string,
  topN?: number
): Promise<LGDExplanation> {
  const query = topN ? `?top_n=${topN}` : "";
  return apiRequest(`/api/loans/${loanId}/lgd/explain${query}`);
}

export async function fetchLGDModelInfo(): Promise<LGDModelInfo> {
  return apiRequest("/api/ml/recovery-rate/importance");
}

// ============================================
// Health Check
// ============================================

export async function checkHealth(): Promise<{
  status: string;
  timestamp: string;
  services: Record<string, string>;
}> {
  return apiRequest("/health");
}

