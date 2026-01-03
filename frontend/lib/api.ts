const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export interface Loan {
  loan_id: string;
  borrower_name: string;
  facility_amount: number;
  currency: string;
  maturity_date: string;
  status: "GREEN" | "AMBER" | "RED";
  is_sll: boolean;
  loan_type?: string;
  covenant_count?: number;
  borrower_industry?: string;
  agent_bank?: string;
}

export interface Covenant {
  covenant_id: string;
  name: string;
  threshold: number;
  actual: number;
  status: "GREEN" | "AMBER" | "RED";
  buffer_pct: number;
}

export interface ESGKpi {
  kpi_id: string;
  name: string;
  baseline: number;
  target: number;
  current: number;
  progress_pct: number;
  status: string;
}

export interface Alert {
  alert_id: string;
  loan_id: string;
  type: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  message: string;
  created_at: string;
  acknowledged: boolean;
}

export interface DashboardSummary {
  total_loans: number;
  loans_compliant: number;
  loans_warning: number;
  loans_breach: number;
  active_alerts: number;
  esg_average_score: number;
}

export async function fetchDashboard(): Promise<DashboardSummary> {
  const res = await fetch(`${API_BASE_URL}/api/dashboard`);
  if (!res.ok) throw new Error("Failed to fetch dashboard");
  return res.json();
}

export async function fetchLoans(): Promise<{ loans: Loan[]; total: number }> {
  const res = await fetch(`${API_BASE_URL}/api/loans`);
  if (!res.ok) throw new Error("Failed to fetch loans");
  return res.json();
}

export async function fetchLoan(loanId: string): Promise<Loan> {
  const res = await fetch(`${API_BASE_URL}/api/loans/${loanId}`);
  if (!res.ok) throw new Error("Failed to fetch loan");
  return res.json();
}

export async function fetchCovenants(
  loanId: string
): Promise<{ covenants: Covenant[] }> {
  const res = await fetch(`${API_BASE_URL}/api/covenants/${loanId}`);
  if (!res.ok) throw new Error("Failed to fetch covenants");
  return res.json();
}

export async function fetchESG(loanId: string): Promise<{ kpis: ESGKpi[] }> {
  const res = await fetch(`${API_BASE_URL}/api/esg/${loanId}`);
  if (!res.ok) throw new Error("Failed to fetch ESG");
  return res.json();
}

export async function fetchAlerts(): Promise<{
  alerts: Alert[];
  total_count: number;
}> {
  const res = await fetch(`${API_BASE_URL}/api/alerts`);
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
}

export async function acknowledgeAlert(alertId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/alerts/${alertId}/acknowledge`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to acknowledge alert");
}
