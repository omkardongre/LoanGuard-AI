"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import { 
  CircularGauge, 
  AnimatedProgressBar, 
  RiskMetricCard, 
  ExposureBar 
} from "@/components/dashboard-visuals";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Leaf,
  TrendingUp,
  TrendingDown,
  Bell,
  Activity,
  Loader2,
  RefreshCw,
  Brain,
  PieChart,
} from "lucide-react";
import {
  fetchDashboard,
  fetchLoans,
  fetchAlerts,
  fetchPortfolioVelocity,
  fetchPortfolioConcentration,
  downloadPortfolioPdfReport,
  triggerPdfDownload,
  type DashboardSummary,
  type Loan,
  type Alert,
  type PortfolioConcentration,
} from "@/lib/api";

function formatCurrency(amount: number, currency: string = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(amount);
}

interface VelocityData {
  total_loans_analyzed: number;
  risk_distribution: Record<string, number>;
  worsening_loans: Array<{
    loan_id: string;
    risk_level: string;
    nearest_breach: number;
  }>;
  summary: string;
}

export default function Home() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [velocity, setVelocity] = useState<VelocityData | null>(null);
  const [concentration, setConcentration] = useState<PortfolioConcentration | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);

  async function loadData() {
    try {
      const [dashboardData, loansData, alertsData, velocityData, concentrationData] =
        await Promise.allSettled([
          fetchDashboard(),
          fetchLoans({ limit: 10 }),
          fetchAlerts({ limit: 5, acknowledged: false }),
          fetchPortfolioVelocity(),
          fetchPortfolioConcentration(),
        ]);

      if (dashboardData.status === "fulfilled") {
        setDashboard(dashboardData.value);
      }
      if (loansData.status === "fulfilled") {
        setLoans(loansData.value.loans || []);
      }
      if (alertsData.status === "fulfilled") {
        setAlerts(alertsData.value.alerts || []);
      }
      if (velocityData.status === "fulfilled") {
        setVelocity(velocityData.value);
      }
      if (concentrationData.status === "fulfilled") {
        setConcentration(concentrationData.value);
      }
    } catch (err) {
      console.error("Failed to load data:", err);
    }
  }

  useEffect(() => {
    async function init() {
      setLoading(true);
      await loadData();
      setLoading(false);
    }
    init();
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  }

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 p-8 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
        </main>
      </div>
    );
  }

  // Calculate stats from actual data if dashboard API fails
  const stats = dashboard || {
    total_loans: loans.length,
    loans_compliant: loans.filter((l) => l.status === "GREEN").length,
    loans_warning: loans.filter((l) => l.status === "AMBER").length,
    loans_breach: loans.filter((l) => l.status === "RED").length,
    active_alerts: alerts.length,
    esg_average_score: 0,
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 p-6 lg:p-8 fade-in-section overflow-y-auto">
        {/* Hero Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 gradient-text">Dashboard</h1>
            <p className="text-slate-500 mt-1">Real-time loan portfolio compliance monitoring</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={async () => {
                setPdfLoading(true);
                try {
                  const blob = await downloadPortfolioPdfReport();
                  triggerPdfDownload(blob, "portfolio_compliance_report.pdf");
                } catch (err) {
                  console.error("PDF download failed:", err);
                } finally {
                  setPdfLoading(false);
                }
              }}
              disabled={pdfLoading}
            >
              <FileText className="h-4 w-4 mr-2" />
              {pdfLoading ? "Generating..." : "Download Report"}
            </Button>
            <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Primary Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard
            title="Total Loans"
            value={stats.total_loans}
            icon={FileText}
            variant="info"
          />
          <StatCard
            title="Compliant"
            value={stats.loans_compliant}
            icon={CheckCircle}
            variant="success"
          />
          <StatCard
            title="Warning"
            value={stats.loans_warning}
            icon={AlertTriangle}
            variant="warning"
          />
          <StatCard
            title="Breach"
            value={stats.loans_breach}
            icon={XCircle}
            variant="danger"
          />
        </div>

        {/* Secondary Metrics Bar */}
        <div className="flex flex-wrap items-center gap-6 mb-8 p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-red-100 to-red-50">
              <Bell className="h-4 w-4 text-red-600" />
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wide">Alerts</p>
              <p className={`text-lg font-bold ${stats.active_alerts > 20 ? 'text-red-600' : stats.active_alerts > 10 ? 'text-amber-600' : 'text-slate-700'}`}>
                {stats.active_alerts}
              </p>
            </div>
          </div>
          
          <div className="w-px h-10 bg-slate-200" />
          
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-100 to-emerald-50">
              <Leaf className="h-4 w-4 text-emerald-600" />
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wide">ESG Score</p>
              <p className="text-lg font-bold text-emerald-600">{stats.esg_average_score?.toFixed(1) || "-"}%</p>
            </div>
          </div>
          
          <div className="w-px h-10 bg-slate-200" />
          
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-100 to-blue-50">
              <Brain className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wide">AI Analyzed</p>
              <p className="text-lg font-bold text-blue-600">{velocity?.total_loans_analyzed || "-"}</p>
            </div>
          </div>
        </div>

        {/* Section: Portfolio Activity */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <span className="w-1.5 h-6 bg-gradient-to-b from-blue-500 to-indigo-600 rounded-full" />
              Portfolio Activity
            </h2>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Recent Loans */}
            <Card className="overflow-hidden hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between py-4 px-5 bg-gradient-to-r from-slate-50 to-white border-b">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-gradient-to-br from-slate-600 to-slate-800 shadow-md">
                    <FileText className="h-4 w-4 text-white" />
                  </div>
                  <CardTitle className="text-base font-semibold">Recent Loans</CardTitle>
                </div>
                <a href="/loans" className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors group">
                  View all 
                  <span className="group-hover:translate-x-0.5 transition-transform">→</span>
                </a>
              </CardHeader>
              <CardContent className="p-0">
              {loans.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 mx-auto text-slate-200 mb-2" />
                  <p className="text-slate-500">No loans found</p>
                </div>
              ) : (
                <div className="divide-y">
                  {loans.slice(0, 5).map((loan, idx) => (
                    <a
                      key={loan.loan_id}
                      href={`/loans/${loan.loan_id}`}
                      className={`flex items-center justify-between p-4 hover:bg-gradient-to-r hover:from-blue-50 hover:to-transparent transition-all group ${
                        idx === 0 ? '' : ''
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-1 h-12 rounded-full ${
                          loan.status === "GREEN" ? "bg-emerald-500" :
                          loan.status === "AMBER" ? "bg-amber-500" : "bg-red-500"
                        }`} />
                        <div>
                          <p className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                            {loan.borrower_name}
                          </p>
                          <p className="text-xs text-slate-400">{loan.loan_id}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="font-bold text-slate-700">
                            {formatCurrency(loan.facility_amount, loan.currency)}
                          </p>
                        </div>
                        <StatusBadge status={loan.status} size="sm" />
                      </div>
                    </a>
                  ))}
                </div>
              )}
              </CardContent>
            </Card>

            {/* Active Alerts */}
            <Card className="overflow-hidden hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between py-4 px-5 bg-gradient-to-r from-red-50 to-white border-b">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-gradient-to-br from-red-500 to-rose-600 shadow-md pulse-alert">
                    <Bell className="h-4 w-4 text-white" />
                  </div>
                  <CardTitle className="text-base font-semibold">Active Alerts</CardTitle>
                  {alerts.length > 0 && (
                    <span className="px-2.5 py-1 text-xs font-bold bg-red-100 text-red-700 rounded-full animate-pulse">
                      {alerts.length}
                    </span>
                  )}
                </div>
                <a href="/alerts" className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors group">
                  Manage 
                  <span className="group-hover:translate-x-0.5 transition-transform">→</span>
                </a>
              </CardHeader>
              <CardContent className="p-0">
              {alerts.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 mx-auto text-emerald-200 mb-2" />
                  <p className="text-slate-500">No active alerts</p>
                  <p className="text-xs text-slate-400">Your portfolio is healthy!</p>
                </div>
              ) : (
                <div className="divide-y">
                  {alerts.slice(0, 4).map((alert) => (
                    <a
                      key={alert.alert_id}
                      href={`/loans/${alert.loan_id}`}
                      className={`flex items-center gap-4 p-4 hover:bg-gradient-to-r transition-all group ${
                        alert.severity === "HIGH" || alert.severity === "CRITICAL"
                          ? "hover:from-red-50 hover:to-transparent border-l-4 border-l-red-500"
                          : "hover:from-amber-50 hover:to-transparent border-l-4 border-l-amber-500"
                      }`}
                    >
                      <div
                        className={`p-3 rounded-xl shadow-md ${
                          alert.severity === "HIGH" || alert.severity === "CRITICAL"
                            ? "bg-gradient-to-br from-red-500 to-rose-600"
                            : "bg-gradient-to-br from-amber-400 to-orange-500"
                        }`}
                      >
                        <AlertTriangle className="h-5 w-5 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors truncate">
                          {alert.message}
                        </p>
                        <p className="text-sm text-slate-500 flex items-center gap-2">
                          <span className="font-mono text-xs bg-slate-100 px-2 py-0.5 rounded">
                            {alert.loan_id}
                          </span>
                        </p>
                      </div>
                      <Badge
                        variant={
                          alert.severity === "HIGH" || alert.severity === "CRITICAL"
                            ? "destructive"
                            : "secondary"
                        }
                        className="shrink-0"
                      >
                        {alert.severity}
                      </Badge>
                    </a>
                  ))}
                </div>
              )}
            </CardContent>
            </Card>
          </div>
        </div>

        {/* Section: Risk Analytics */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <span className="w-1.5 h-6 bg-gradient-to-b from-purple-500 to-violet-600 rounded-full" />
              Risk Analytics
            </h2>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Portfolio Velocity */}
            <Card className="overflow-hidden hover:shadow-lg transition-shadow">
              <CardHeader className="py-4 px-5 bg-gradient-to-r from-blue-50 to-white border-b">
                <CardTitle className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-md">
                    <Activity className="h-5 w-5 text-white" />
                  </div>
                  <span className="text-base font-semibold">Risk Velocity</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-5 pb-5">
              {velocity ? (
                <div className="space-y-6">
                  <p className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg border-l-4 border-blue-500">
                    {velocity.summary}
                  </p>

                  {/* Risk Distribution - Using new RiskMetricCard */}
                  {velocity.risk_distribution && (
                    <div className="grid grid-cols-2 gap-4">
                      {velocity.risk_distribution.CRITICAL > 0 && (
                        <RiskMetricCard 
                          value={velocity.risk_distribution.CRITICAL} 
                          label="Critical" 
                          variant="critical" 
                        />
                      )}
                      {velocity.risk_distribution.HIGH > 0 && (
                        <RiskMetricCard 
                          value={velocity.risk_distribution.HIGH} 
                          label="High" 
                          variant="high" 
                        />
                      )}
                      {velocity.risk_distribution.MEDIUM > 0 && (
                        <RiskMetricCard 
                          value={velocity.risk_distribution.MEDIUM} 
                          label="Medium" 
                          variant="medium" 
                        />
                      )}
                      {velocity.risk_distribution.LOW > 0 && (
                        <RiskMetricCard 
                          value={velocity.risk_distribution.LOW} 
                          label="Low" 
                          variant="low" 
                        />
                      )}
                    </div>
                  )}

                  {/* Worsening Loans */}
                  {velocity.worsening_loans?.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-red-600 mb-2">
                        ⚠️ Worsening Loans
                      </p>
                      <div className="space-y-2">
                        {velocity.worsening_loans.slice(0, 3).map((loan) => (
                          <div
                            key={loan.loan_id}
                            className="flex items-center justify-between p-2 bg-red-50 rounded"
                          >
                            <a
                              href={`/loans/${loan.loan_id}`}
                              className="text-sm font-medium text-red-800 hover:underline"
                            >
                              {loan.loan_id}
                            </a>
                            <div className="flex items-center gap-2">
                              <TrendingDown className="h-4 w-4 text-red-600" />
                              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ${
                                loan.risk_level === "CRITICAL" 
                                  ? "risk-critical pulse-alert" 
                                  : "risk-high"
                              }`}>
                                {loan.risk_level}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-6 text-slate-500">
                  <Activity className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                  <p>Velocity data not available</p>
                </div>
              )}
              </CardContent>
            </Card>

            {/* Portfolio Concentration */}
            <Card className="overflow-hidden hover:shadow-lg transition-shadow">
              <CardHeader className="py-4 px-5 bg-gradient-to-r from-purple-50 to-white border-b">
                <CardTitle className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-gradient-to-br from-purple-500 to-violet-600 shadow-md">
                    <PieChart className="h-5 w-5 text-white" />
                  </div>
                  <span className="text-base font-semibold">Portfolio Concentration</span>
                </CardTitle>
              </CardHeader>
            <CardContent className="pt-6">
              {concentration ? (
                <div className="space-y-6">
                  {/* HHI Gauge */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <CircularGauge
                        value={concentration.hhi_index || 0}
                        max={10000}
                        size={100}
                        strokeWidth={10}
                        label={concentration.hhi_index?.toFixed(0) || "0"}
                        sublabel="HHI"
                        variant={
                          concentration.concentration_level === "HIGH"
                            ? "danger"
                            : concentration.concentration_level === "MODERATE"
                            ? "warning"
                            : "success"
                        }
                      />
                      <div className="space-y-1">
                        <Badge
                          variant={
                            concentration.concentration_level === "HIGH"
                              ? "destructive"
                              : concentration.concentration_level === "MODERATE"
                              ? "secondary"
                              : "outline"
                          }
                          className="text-sm"
                        >
                          {concentration.concentration_level}
                        </Badge>
                        <p className="text-xs text-slate-500">Concentration Level</p>
                      </div>
                    </div>
                    <div className="text-right space-y-1">
                      <p className="text-lg font-bold text-slate-900">
                        {formatCurrency(concentration.total_exposure)}
                      </p>
                      <p className="text-xs text-slate-500">Total Exposure</p>
                      <p className="text-sm font-medium text-slate-600">
                        {concentration.total_loans} Loans
                      </p>
                    </div>
                  </div>

                  {/* Top Exposures with colorful bars */}
                  {concentration.top_exposures?.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-gradient-to-r from-violet-500 to-purple-500" />
                        Top Industry Exposures
                      </p>
                      <div className="space-y-3">
                        {concentration.top_exposures.slice(0, 5).map((exp, idx) => (
                          <ExposureBar
                            key={idx}
                            name={exp.value || exp.category}
                            percentage={exp.percentage || 0}
                            index={idx}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-6 text-slate-500">
                  <PieChart className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                  <p>Concentration data not available</p>
                </div>
              )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Section: Compliance Progress */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <span className="w-1.5 h-6 bg-gradient-to-b from-emerald-500 to-teal-600 rounded-full" />
              Compliance Progress
            </h2>
          </div>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow">
            <CardHeader className="py-4 px-5 bg-gradient-to-r from-emerald-50 to-white border-b">
              <CardTitle className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-md">
                  <TrendingUp className="h-5 w-5 text-white" />
                </div>
                <span className="text-base font-semibold">Portfolio Compliance Progress</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <AnimatedProgressBar
                value={
                  stats.total_loans > 0
                    ? (stats.loans_compliant / stats.total_loans) * 100
                    : 0
                }
                label="Financial Covenants"
                sublabel={`${stats.loans_compliant} of ${stats.total_loans} loans`}
                variant={
                  stats.total_loans > 0 && (stats.loans_compliant / stats.total_loans) >= 0.8
                    ? "success"
                    : stats.total_loans > 0 && (stats.loans_compliant / stats.total_loans) >= 0.5
                    ? "warning"
                    : "danger"
                }
              />
              <AnimatedProgressBar
                value={stats.esg_average_score || 0}
                label="ESG Targets"
                sublabel="Portfolio average score"
                variant={
                  (stats.esg_average_score || 0) >= 80
                    ? "success"
                    : (stats.esg_average_score || 0) >= 50
                    ? "warning"
                    : "danger"
                }
              />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
