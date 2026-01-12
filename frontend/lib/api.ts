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

export interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export async function chatWithAgent(
  message: string,
  loanId?: string,
  history?: ChatHistoryMessage[]
): Promise<{
  response: string;
  suggestions: string[];
}> {
  const body: Record<string, unknown> = { message };
  if (loanId) body.loan_id = loanId;
  if (history && history.length > 0) body.history = history;

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

// ============================================
// Prepayment Risk V2 (V9 - FRED Integration)
// ============================================

export interface PrepaymentPredictionV2 {
  loan_id: string;
  base_prepay_probability: number;
  adjusted_prepay_probability: number;
  prepay_probability_pct: string;
  will_prepay: boolean;
  risk_category: "HIGH_PREPAY" | "MODERATE_PREPAY" | "LOW_PREPAY";
  loan_rate: number;
  market_rate: number;
  refinancing_spread: number;
  refinancing_incentive: "STRONG_INCENTIVE" | "MODERATE_INCENTIVE" | "WEAK_INCENTIVE" | "NO_INCENTIVE" | "DISINCENTIVE";
  months_since_origination: number;
  seasoning_stage: "RAMP_UP" | "MATURE" | "BURNOUT";
  seasoning_factor: number;
  CPR: number;  // Conditional Prepayment Rate
  SMM: number;  // Single Monthly Mortality
  model_version: string;
  data_source: string;
  as_of: string;
  success: boolean;
}

export interface PrepaymentScenario {
  rate_change: string;
  market_rate: number;
  spread: number;
  spread_bps: number;
  prepay_probability: number;
  risk_category: string;
}

export interface PrepaymentScenarioAnalysis {
  loan_id: string;
  loan_rate: number;
  current_market_rate: number;
  current_spread: number;
  base_prepay_probability: number;
  scenarios: PrepaymentScenario[];
  analysis_date: string;
  success: boolean;
}

export interface FREDRates {
  mortgage_30y: number;
  mortgage_15y: number;
  treasury_10y: number;
  fed_funds: number;
  as_of: string;
  source: string;
}

export interface FREDRatesResponse {
  success: boolean;
  rates: FREDRates;
  service_info: {
    name: string;
    provider: string;
    cost: string;
    production_level: boolean;
  };
}

export async function fetchPrepaymentV2(
  loanId: string,
  monthsSinceOrigination?: number
): Promise<PrepaymentPredictionV2> {
  const query = monthsSinceOrigination ? `?months_since_origination=${monthsSinceOrigination}` : "";
  return apiRequest(`/api/loans/${loanId}/prepayment/v2${query}`);
}

export async function fetchPrepaymentScenario(
  loanId: string
): Promise<PrepaymentScenarioAnalysis> {
  return apiRequest(`/api/loans/${loanId}/prepayment/v2/scenario`);
}

export async function fetchFREDRates(): Promise<FREDRatesResponse> {
  return apiRequest("/api/ml/fred/rates");
}

export async function fetchPrepaymentV2ModelInfo(): Promise<{
  success: boolean;
  version: string;
  enhancements: string[];
  external_data: {
    source: string;
    cost: string;
    reliability: string;
  };
  current_rates: FREDRates;
}> {
  return apiRequest("/api/ml/prepayment/v2/model-info");
}

// ============================================
// Fund Finance Module (WINNING_STRATEGY L145-153)
// ============================================

export interface NAVFacility {
  facility_id: string;
  fund_name: string;
  fund_type: string;
  nav_value: number;
  facility_amount: number;
  drawn_amount: number;
  ltv_ratio: number;
  buffer_percentage: number;
  valuation_date: string;
  ilpa_compliant: boolean;
}

export interface LPPosition {
  lp_id: string;
  lp_name: string;
  commitment_amount: number;
  funded_amount: number;
  unfunded_commitment: number;
  concentration_pct: number;
}

export async function fetchNAVFacilities(): Promise<{
  success: boolean;
  facilities: NAVFacility[];
  total: number;
  source: string;
}> {
  return apiRequest("/api/fund-finance/nav/portfolio");
}

export async function fetchNAVFacility(facilityId: string): Promise<{
  success: boolean;
  facility: NAVFacility;
  source: string;
}> {
  return apiRequest(`/api/fund-finance/nav/${facilityId}`);
}

export async function fetchLTV(facilityId: string): Promise<{
  success: boolean;
  facility_id: string;
  current_ltv: number;
  max_ltv: number;
  buffer: number;
  status: string;
  source: string;
}> {
  return apiRequest(`/api/fund-finance/ltv/${facilityId}`);
}

export async function fetchBufferAnalysis(facilityId: string): Promise<{
  success: boolean;
  facility_id: string;
  current_buffer: number;
  required_buffer: number;
  additional_borrowing_capacity: number;
  source: string;
}> {
  return apiRequest(`/api/fund-finance/buffer/${facilityId}`);
}

export async function checkILPACompliance(fundId: string): Promise<{
  success: boolean;
  fund_id: string;
  compliant: boolean;
  compliance_score: number;
  requirements_met: string[];
  requirements_failed: string[];
  source: string;
}> {
  return apiRequest(`/api/fund-finance/ilpa/${fundId}/check`);
}

export async function fetchLPTransparency(fundId: string): Promise<{
  success: boolean;
  fund_id: string;
  lp_positions: LPPosition[];
  total_commitment: number;
  concentration_risk: string;
  source: string;
}> {
  return apiRequest(`/api/fund-finance/lp/${fundId}/transparency`);
}

export async function fetchFundFinanceSummary(): Promise<{
  success: boolean;
  total_facilities: number;
  total_nav: number;
  avg_ltv: number;
  ilpa_compliant_count: number;
  source: string;
}> {
  return apiRequest("/api/fund-finance/summary");
}

// ============================================
// Transition Loans Module (WINNING_STRATEGY L157-164)
// ============================================

export interface TLPAssessment {
  loan_id: string;
  overall_score: number;
  compliance_status: string;
  principles: Array<{
    principle: string;
    score: number;
    status: string;
  }>;
}

export interface CarbonLockinAssessment {
  loan_id: string;
  risk_level: string;
  assessment_score: number;
  criteria_scores: Record<string, number>;
  recommendations: string[];
}

export interface DNSHScreening {
  loan_id: string;
  overall_status: string;
  objectives: Array<{
    objective: string;
    status: string;
    score: number;
  }>;
}

export async function validateTransitionLoan(loanId: string): Promise<{
  success: boolean;
  assessment: TLPAssessment;
  source: string;
}> {
  return apiRequest(`/api/transition/validate/${loanId}`);
}

export async function fetchTLPScore(loanId: string): Promise<{
  success: boolean;
  loan_id: string;
  tlp_score: number;
  status: string;
  source: string;
}> {
  return apiRequest(`/api/transition/tlp-score/${loanId}`);
}

export async function assessCarbonLockin(loanId: string): Promise<{
  success: boolean;
  assessment: CarbonLockinAssessment;
  source: string;
}> {
  return apiRequest(`/api/transition/carbon-lockin/${loanId}`);
}

export async function screenDNSH(loanId: string): Promise<{
  success: boolean;
  screening: DNSHScreening;
  source: string;
}> {
  return apiRequest(`/api/transition/dnsh/${loanId}`);
}

export async function fetchTransitionLoansSummary(): Promise<{
  success: boolean;
  total_loans: number;
  compliant_count: number;
  avg_tlp_score: number;
  carbon_lockin_distribution: Record<string, number>;
  source: string;
}> {
  return apiRequest("/api/transition/summary");
}

export async function generateTLPReport(loanId: string): Promise<{
  success: boolean;
  report: {
    loan_id: string;
    generated_at: string;
    sections: Record<string, unknown>;
  };
  source: string;
}> {
  return apiRequest(`/api/transition/report/${loanId}`);
}

// ============================================
// SLLB & Regional Module (WINNING_STRATEGY L166-174)
// ============================================

export interface SLLBPortfolio {
  portfolio_id: string;
  bond_name: string;
  issuer_name: string;
  bond_amount: number;
  currency: string;
  total_sll_amount: number;
  eligible_sll_count: number;
  status: string;
}

export interface SLLBEligibility {
  loan_id: string;
  eligible: boolean;
  eligibility_score: number;
  component_scores: Record<string, number>;
  recommendation: string;
}

export interface ZARONIATransition {
  loan_id: string;
  requires_transition: boolean;
  transition_status: string;
  deadline: string;
  days_remaining: number;
  urgency: string;
}

export interface SFDRClassification {
  product_id: string;
  current_classification: string;
  new_classification: string;
  category_details: {
    name: string;
    description: string;
    threshold: number;
  };
  component_scores: Record<string, number>;
}

export async function fetchSLLBPortfolios(): Promise<{
  success: boolean;
  portfolios: SLLBPortfolio[];
  total: number;
  source: string;
}> {
  return apiRequest("/api/sllb/summary");
}

export async function fetchSLLBPortfolio(portfolioId: string): Promise<{
  success: boolean;
  portfolio: SLLBPortfolio;
  eligible_slls: Array<{
    loan_id: string;
    borrower_sector: string;
    loan_amount: number;
    kpi_type: string;
  }>;
  source: string;
}> {
  return apiRequest(`/api/sllb/portfolio/${portfolioId}`);
}

export async function evaluateSLLEligibility(loanId: string): Promise<{
  success: boolean;
  eligibility: SLLBEligibility;
  source: string;
}> {
  return apiRequest(`/api/sllb/eligibility/${loanId}`);
}

export async function assessZARONIATransition(loanId: string): Promise<{
  success: boolean;
  assessment: ZARONIATransition;
  source: string;
}> {
  return apiRequest(`/api/zaronia/assess/${loanId}`);
}

export async function fetchZARONIASummary(): Promise<{
  success: boolean;
  deadline: string;
  days_remaining: number;
  total_transitions: number;
  by_status: Record<string, number>;
  completion_rate: number;
  source: string;
}> {
  return apiRequest("/api/zaronia/summary");
}

export async function classifySFDR(productId: string): Promise<{
  success: boolean;
  classification: SFDRClassification;
  source: string;
}> {
  return apiRequest(`/api/sfdr/classify/${productId}`);
}

export async function fetchSFDRSummary(): Promise<{
  success: boolean;
  total_products: number;
  by_category: Record<string, number>;
  avg_taxonomy_alignment: number;
  source: string;
}> {
  return apiRequest("/api/sfdr/summary");
}


// ============================================
// SLL Monitoring Module API Functions
// Based on LMA SLLP (Sustainability-Linked Loan Principles)
// ============================================

export interface SLLKPI {
  kpi_id: string;
  loan_id: string;
  kpi_type: string;
  kpi_name: string;
  baseline_value: number;
  target_value: number;
  current_value: number;
  unit: string;
  target_year: number;
  measurement_frequency: string;
  verification_status: "PENDING" | "VERIFIED" | "FAILED";
  achievement_probability: number;
  last_measurement_date: string;
}

export interface SLLSPT {
  spt_id: string;
  loan_id: string;
  kpi_id?: string;
  target_description: string;
  target_value: number;
  current_progress: number;
  achievement_probability: number;
  margin_impact_bps: number;
  verification_required: boolean;
  verifier_name?: string;
  status: "ACTIVE" | "ACHIEVED" | "NOT_ACHIEVED" | "EXPIRED";
}

export interface SLLMarginAdjustment {
  loan_id: string;
  calculation_date: string;
  spts_achieved: number;
  spts_not_achieved: number;
  total_spts: number;
  adjustment_direction: "step-down" | "step-up" | "no_change";
  adjustment_bps: number;
  two_way_pricing: boolean;
  new_margin_bps: number;
  previous_margin_bps: number;
}

export async function fetchSLLKPIs(loanId: string): Promise<{
  success: boolean;
  loan_id: string;
  kpis: SLLKPI[];
  source: string;
}> {
  return apiRequest(`/api/sll/loan/${loanId}/kpis`);
}

export async function fetchSLLSPTs(loanId: string): Promise<{
  success: boolean;
  loan_id: string;
  spts: SLLSPT[];
  source: string;
}> {
  return apiRequest(`/api/sll/loan/${loanId}/spts`);
}

export async function validateSLLSPTs(loanId: string): Promise<{
  success: boolean;
  loan_id: string;
  validation_results: Array<{
    spt_id: string;
    achieved: boolean;
    variance_pct: number;
  }>;
  source: string;
}> {
  return apiRequest(`/api/sll/loan/${loanId}/spts/validate`);
}

export async function calculateSLLMargin(loanId: string): Promise<{
  success: boolean;
  loan_id: string;
  margin_adjustment: SLLMarginAdjustment;
  source: string;
}> {
  return apiRequest(`/api/sll/loan/${loanId}/margin`);
}

export async function fetchSLLPortfolioSummary(): Promise<{
  success: boolean;
  sll_loan_count: number;
  total_kpis: number;
  verified_kpis: number;
  verification_rate: number;
  avg_achievement_probability: number;
  total_spts: number;
  achieved_spts: number;
  spt_achievement_rate: number;
  avg_margin_impact_bps: number;
  source: string;
}> {
  return apiRequest("/api/sll/portfolio/summary");
}


// ============================================
// Social Loans Module API Functions
// Based on LMA Social Loan Principles (SLP March 2025)
// ============================================

export interface SocialLoanValidation {
  success: boolean;
  loan_id: string;
  is_social_loan: boolean;
  is_slp_compliant: boolean;
  social_category: string;
  target_populations: string[];
  scores: {
    overall: number;
    use_of_proceeds: number;
    project_evaluation: number;
    proceeds_management: number;
    reporting: number;
  };
  compliance_threshold: number;
  recommendations: string[];
  assessment_date: string;
  slp_version: string;
}

export interface SocialLoanClassification {
  success: boolean;
  loan_id: string;
  social_category: string;
  target_populations: string[];
  is_slp_compliant: boolean;
  scores: {
    overall: number;
    use_of_proceeds: number;
    project_evaluation: number;
    proceeds_management: number;
    reporting: number;
  };
  verification_status: string;
  assessment_date: string;
}

export interface SocialImpactMetrics {
  success: boolean;
  loan_id: string;
  social_category: string;
  expected_beneficiaries: number;
  actual_beneficiaries: number;
  impact_kpis: Record<string, number>;
  geographic_area: string;
  measurement_date: string;
}

export interface SocialLoanReport {
  success: boolean;
  loan_id: string;
  report_type: string;
  social_category: string;
  target_populations: string[];
  beneficiary_data: {
    expected: number;
    actual: number;
    achievement_rate: number;
  };
  impact_summary: string;
  slp_compliance: boolean;
  recommendations: string[];
  generated_at: string;
}

export interface SocialPortfolioSummary {
  success: boolean;
  total_social_loans: number;
  by_category: Array<{
    category: string;
    loan_count: number;
    avg_score: number;
    beneficiaries: number;
  }>;
  slp_version: string;
}

export interface SLPCategories {
  categories: string[];
  target_populations: string[];
  slp_version: string;
}

export async function validateSocialLoan(
  loanId: string,
  loanPurpose: string
): Promise<SocialLoanValidation> {
  return apiRequest("/api/esg/social/validate", {
    method: "POST",
    body: JSON.stringify({ loan_id: loanId, loan_purpose: loanPurpose }),
  });
}

export async function fetchSocialLoan(loanId: string): Promise<SocialLoanClassification> {
  return apiRequest(`/api/esg/social/loan/${loanId}`);
}

export async function fetchSocialImpact(loanId: string): Promise<SocialImpactMetrics> {
  return apiRequest(`/api/esg/social/impact/${loanId}`);
}

export async function updateSocialImpact(
  loanId: string,
  data: {
    expected_beneficiaries?: number;
    actual_beneficiaries?: number;
    geographic_area?: string;
  }
): Promise<{ success: boolean; loan_id: string; updated: boolean }> {
  return apiRequest(`/api/esg/social/impact/${loanId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function fetchSocialLoanReport(loanId: string): Promise<SocialLoanReport> {
  return apiRequest(`/api/esg/social/report/${loanId}`);
}

export async function fetchSocialPortfolioSummary(): Promise<SocialPortfolioSummary> {
  return apiRequest("/api/esg/social/summary");
}

export async function fetchSocialPortfolioImpact(): Promise<{
  success: boolean;
  total_social_loans: number;
  total_expected_beneficiaries: number;
  total_actual_beneficiaries: number;
  overall_achievement_rate: number;
  by_category: Array<{
    category: string;
    expected: number;
    actual: number;
  }>;
}> {
  return apiRequest("/api/esg/social/portfolio-impact");
}

export async function fetchSLPCategories(): Promise<SLPCategories> {
  return apiRequest("/api/esg/social/categories");
}

// ============================================
// Report Export Functions (V10.1)
// ============================================

/**
 * Export loan-level Risk Committee PowerPoint presentation.
 */
export async function exportLoanPptx(loanId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/esg/reports/pptx/loan/${loanId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) throw new Error(`PPTX export failed: ${response.status}`);
  return response.blob();
}

/**
 * Export portfolio-level Risk Committee PowerPoint presentation.
 */
export async function exportPortfolioPptx(): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/esg/reports/pptx/portfolio`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) throw new Error(`Portfolio PPTX export failed: ${response.status}`);
  return response.blob();
}

/**
 * Export TLP PDF report for a transition loan.
 * LMA TLP Principle 5 compliant.
 */
export async function exportTlpPdf(loanId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/esg/reports/tlp/${loanId}/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) throw new Error(`TLP PDF export failed: ${response.status}`);
  return response.blob();
}

/**
 * Export portfolio-level TLP PDF report.
 */
export async function exportTlpPortfolioPdf(): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/esg/reports/tlp/portfolio/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) throw new Error(`TLP Portfolio PDF export failed: ${response.status}`);
  return response.blob();
}


