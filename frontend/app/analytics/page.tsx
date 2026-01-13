"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Activity,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Shield,
  DollarSign,
  PieChart,
  BarChart3,
  Target,
  Zap,
  RefreshCw,
  Building2,
  Leaf,
  Brain,
  Calculator,
} from "lucide-react";
import { MonteCarloCard } from "@/components/monte-carlo-card";
import { ECLSummaryCard } from "@/components/ecl-summary-card";
import { WhatIfCard } from "@/components/what-if-card";
import { ESGFinancialRiskCard } from "@/components/esg-financial-risk-card";
import { RiskCommitteeCard } from "@/components/risk-committee-card";
import { ExportPptxButton } from "@/components/export-button";
import { SendEmailButton } from "@/components/send-email-button";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// Types
interface PortfolioSummary {
  total_loans: number;
  total_exposure: number;
  weighted_avg_pd: number;
  weighted_avg_lgd: number;
  expected_loss: number;
  var_95: number;
  var_99: number;
  cvar_99: number;
}

interface SectorExposure {
  sector: string;
  loan_count: number;
  total_ead: number;
  avg_pd: number;
  concentration_pct: number;
}

interface RiskDistribution {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

interface StressTestSummary {
  scenario: string;
  ecl_increase_pct: number;
  stressed_ecl: number;
}

// Fetch functions
async function fetchPortfolioAnalytics(): Promise<any> {
  const response = await fetch(`${API_BASE}/api/dashboard`);
  if (!response.ok) throw new Error("Failed to fetch analytics");
  return response.json();
}

async function fetchECLSummary(): Promise<any> {
  const response = await fetch(`${API_BASE}/api/ecl/portfolio/summary`);
  if (!response.ok) throw new Error("Failed to fetch ECL");
  return response.json();
}

async function fetchMacroData(): Promise<any> {
  const response = await fetch(`${API_BASE}/api/stress-test/macro-data`);
  if (!response.ok) throw new Error("Failed to fetch macro data");
  return response.json();
}

async function fetchConcentration(): Promise<any> {
  const response = await fetch(`${API_BASE}/api/portfolio/concentration`);
  if (!response.ok) throw new Error("Failed to fetch concentration");
  return response.json();
}

async function fetchMonteCarloVaR(): Promise<any> {
  const response = await fetch(`${API_BASE}/api/monte-carlo/production/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!response.ok) throw new Error("Failed to fetch VaR");
  return response.json();
}

async function fetchESGPortfolioRisk(scenario: string = 'current_policies'): Promise<any> {
  const response = await fetch(`${API_BASE}/api/esg/portfolio/risk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ climate_scenario: scenario }),
  });
  if (!response.ok) throw new Error("Failed to fetch ESG risk");
  return response.json();
}

// Format currency
function formatCurrency(value: number) {
  if (value >= 1000000000) return `$${(value / 1000000000).toFixed(1)}B`;
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

// Format percentage
function formatPct(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

// Honeycomb metric card - Modern 2025 design
function HoneycombCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
  trend,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: any;
  color: string;
  trend?: "up" | "down" | "neutral";
}) {
  const colorClasses = {
    blue: {
      container: "bg-gradient-to-br from-blue-50 to-white border-blue-200",
      icon: "bg-gradient-to-br from-blue-500 to-blue-600",
      text: "text-blue-700",
      value: "text-blue-900",
    },
    green: {
      container: "bg-gradient-to-br from-emerald-50 to-white border-emerald-200",
      icon: "bg-gradient-to-br from-emerald-500 to-emerald-600",
      text: "text-emerald-700",
      value: "text-emerald-900",
    },
    amber: {
      container: "bg-gradient-to-br from-amber-50 to-white border-amber-200",
      icon: "bg-gradient-to-br from-amber-500 to-orange-500",
      text: "text-amber-700",
      value: "text-amber-900",
    },
    red: {
      container: "bg-gradient-to-br from-red-50 to-white border-red-200",
      icon: "bg-gradient-to-br from-red-500 to-rose-600",
      text: "text-red-700",
      value: "text-red-900",
    },
    purple: {
      container: "bg-gradient-to-br from-purple-50 to-white border-purple-200",
      icon: "bg-gradient-to-br from-purple-500 to-violet-600",
      text: "text-purple-700",
      value: "text-purple-900",
    },
    slate: {
      container: "bg-gradient-to-br from-slate-50 to-white border-slate-200",
      icon: "bg-gradient-to-br from-slate-500 to-slate-600",
      text: "text-slate-700",
      value: "text-slate-900",
    },
  };

  const styles = colorClasses[color as keyof typeof colorClasses];

  return (
    <div className={`relative overflow-hidden p-5 rounded-2xl border-2 ${styles.container} transition-all duration-300 hover:shadow-xl hover:-translate-y-1 cursor-default group`}>
      {/* Decorative orb */}
      <div className="absolute -top-8 -right-8 w-24 h-24 rounded-full bg-gradient-to-br from-current/5 to-transparent blur-xl group-hover:scale-150 transition-transform duration-500" />
      
      <div className="relative">
        <div className="flex items-center justify-between mb-3">
          <div className={`p-2.5 rounded-xl ${styles.icon} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
          {trend && (
            <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
              trend === "up" ? "bg-emerald-100 text-emerald-700" :
              trend === "down" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-600"
            }`}>
              {trend === "up" ? <TrendingUp className="h-3 w-3" /> :
               trend === "down" ? <TrendingDown className="h-3 w-3" /> : null}
              {trend === "up" ? "+5%" : trend === "down" ? "-3%" : "—"}
            </div>
          )}
        </div>
        <p className={`text-3xl font-bold tracking-tight ${styles.value}`}>{value}</p>
        <p className={`text-sm font-semibold ${styles.text} mt-1`}>{title}</p>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

// Risk gauge component
function RiskGauge({ value, label, color }: { value: number; label: string; color: string }) {
  const colorClasses = {
    green: "bg-emerald-500",
    amber: "bg-amber-500",
    red: "bg-red-500",
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium">{value.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClasses[color as keyof typeof colorClasses]} rounded-full transition-all`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  );
}

// Main analytics page
export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dashboard, setDashboard] = useState<any>(null);
  const [ecl, setEcl] = useState<any>(null);
  const [macro, setMacro] = useState<any>(null);
  const [concentration, setConcentration] = useState<any>(null);
  const [monteCarlo, setMonteCarlo] = useState<any>(null);
  const [esgPortfolio, setEsgPortfolio] = useState<any>(null);
  const [esgScenario, setEsgScenario] = useState<string>('current_policies');
  const [esgLoading, setEsgLoading] = useState<boolean>(false);

  async function loadData() {
    try {
      const [dashData, eclData, macroData, concData, mcData, esgData] = await Promise.allSettled([
        fetchPortfolioAnalytics(),
        fetchECLSummary(),
        fetchMacroData(),
        fetchConcentration(),
        fetchMonteCarloVaR(),
        fetchESGPortfolioRisk(esgScenario),
      ]);

      if (dashData.status === "fulfilled") setDashboard(dashData.value);
      if (eclData.status === "fulfilled" && eclData.value.success) setEcl(eclData.value);
      if (macroData.status === "fulfilled" && macroData.value.success) setMacro(macroData.value);
      if (concData.status === "fulfilled") setConcentration(concData.value);
      if (mcData.status === "fulfilled" && mcData.value.success) setMonteCarlo(mcData.value);
      if (esgData.status === "fulfilled" && esgData.value.success) setEsgPortfolio(esgData.value);
    } catch (err) {
      console.error("Failed to load analytics:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    await loadData();
  }

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-50">
          <Sidebar />
        <main className="flex-1 p-8">
          <div className="flex items-center justify-center h-full">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        </main>
      </div>
    );
  }

  // Calculate derived metrics from real ECL data (BigQuery source)
  const totalLoans = dashboard?.total_loans || 0;
  // Use ECL portfolio_summary for accurate exposure data (actual API structure)
  const portfolioSummary = ecl?.portfolio_summary || {};
  const totalExposure = portfolioSummary?.total_ead || 0;
  // Calculate weighted averages from loan results when available
  const loanResults = ecl?.loan_results || [];
  const avgPD = loanResults.length > 0 
    ? loanResults.reduce((sum: number, loan: any) => sum + (loan.parameters?.pd_12m || 0), 0) / loanResults.length
    : 0.08;
  const avgLGD = loanResults.length > 0
    ? loanResults.reduce((sum: number, loan: any) => sum + (loan.parameters?.lgd || 0), 0) / loanResults.length
    : 0.45;
  const totalECL = portfolioSummary?.total_ecl || 0;
  const coverageRatio = portfolioSummary?.ecl_coverage_ratio_pct || (totalExposure > 0 ? (totalECL / totalExposure * 100) : 0);

  // Calculate PD distribution from real loan data
  const pdDistribution = loanResults.length > 0 ? {
    low: Math.round((loanResults.filter((l: any) => (l.parameters?.pd_12m || 0) < 0.05).length / loanResults.length) * 100),
    medium: Math.round((loanResults.filter((l: any) => (l.parameters?.pd_12m || 0) >= 0.05 && (l.parameters?.pd_12m || 0) < 0.15).length / loanResults.length) * 100),
    high: Math.round((loanResults.filter((l: any) => (l.parameters?.pd_12m || 0) >= 0.15 && (l.parameters?.pd_12m || 0) < 0.30).length / loanResults.length) * 100),
    critical: Math.round((loanResults.filter((l: any) => (l.parameters?.pd_12m || 0) >= 0.30).length / loanResults.length) * 100),
  } : { low: 0, medium: 0, high: 0, critical: 0 };

  // Calculate LGD distribution from real loan data
  const lgdDistribution = loanResults.length > 0 ? {
    wellSecured: Math.round((loanResults.filter((l: any) => (l.parameters?.lgd || 0) < 0.30).length / loanResults.length) * 100),
    standard: Math.round((loanResults.filter((l: any) => (l.parameters?.lgd || 0) >= 0.30 && (l.parameters?.lgd || 0) <= 0.50).length / loanResults.length) * 100),
    unsecured: Math.round((loanResults.filter((l: any) => (l.parameters?.lgd || 0) > 0.50).length / loanResults.length) * 100),
  } : { wellSecured: 0, standard: 0, unsecured: 0 };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 min-w-0 overflow-x-hidden p-4 md:p-6 lg:p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg">
              <BarChart3 className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold gradient-text">Portfolio Analytics</h1>
              <p className="text-slate-500">Real-time risk monitoring and KPIs</p>
            </div>
          </div>
          <div className="flex gap-2">
            <SendEmailButton
              variant="portfolio-summary"
              period="weekly"
              size="default"
            />
            <ExportPptxButton variant="outline" />
            <Button onClick={handleRefresh} disabled={refreshing} variant="outline" className="hover:bg-blue-50 transition-colors">
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Honeycomb KPI Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          <HoneycombCard
            title="Total Loans"
            value={totalLoans.toString()}
            subtitle="Active facilities"
            icon={Building2}
            color="blue"
          />
          <HoneycombCard
            title="Total Exposure"
            value={formatCurrency(totalExposure)}
            subtitle="EAD"
            icon={DollarSign}
            color="green"
          />
          <HoneycombCard
            title="Avg Default Prob"
            value={formatPct(avgPD)}
            subtitle="Weighted PD"
            icon={Target}
            color={avgPD > 0.1 ? "red" : avgPD > 0.05 ? "amber" : "green"}
          />
          <HoneycombCard
            title="Avg LGD"
            value={formatPct(avgLGD)}
            subtitle="Loss Given Default"
            icon={Shield}
            color="purple"
          />
          <HoneycombCard
            title="Total ECL"
            value={formatCurrency(totalECL)}
            subtitle="Expected Credit Loss"
            icon={AlertTriangle}
            color="amber"
          />
          <HoneycombCard
            title="Coverage Ratio"
            value={`${coverageRatio.toFixed(2)}%`}
            subtitle="ECL / Exposure"
            icon={Calculator}
            color="slate"
          />
        </div>

        {/* Tabs for different views */}
        <Tabs defaultValue="overview" className="space-y-6">
          <div className="relative">
            <TabsList className="bg-white border border-slate-200 shadow-sm rounded-xl p-1.5 flex overflow-x-auto gap-1 w-full pb-2 scroll-smooth snap-x snap-mandatory hover:scrollbar-default scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
            <TabsTrigger value="overview" className="flex-shrink-0 snap-start flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
              <BarChart3 className="h-4 w-4" />
              <span>Overview</span>
            </TabsTrigger>
            <TabsTrigger value="advanced" className="flex-shrink-0 snap-start flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-500 data-[state=active]:to-violet-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
              <Calculator className="h-4 w-4" />
              <span>Analytics</span>
            </TabsTrigger>
            <TabsTrigger value="risk" className="flex-shrink-0 snap-start flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-500 data-[state=active]:to-orange-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
              <Shield className="h-4 w-4" />
              <span>Risk</span>
            </TabsTrigger>
            <TabsTrigger value="sector" className="flex-shrink-0 snap-start flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-500 data-[state=active]:to-teal-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
              <PieChart className="h-4 w-4" />
              <span>Sector</span>
            </TabsTrigger>
            <TabsTrigger value="macro" className="flex-shrink-0 snap-start flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-rose-500 data-[state=active]:to-pink-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
              <TrendingUp className="h-4 w-4" />
              <span>Macro</span>
            </TabsTrigger>
            <TabsTrigger value="esg" className="flex-shrink-0 snap-start flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-500 data-[state=active]:to-green-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
              <Leaf className="h-4 w-4" />
              <span>ESG</span>
            </TabsTrigger>
            <TabsTrigger value="committee" className="flex-shrink-0 snap-start flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap text-sm data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo-500 data-[state=active]:to-blue-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
              <Brain className="h-4 w-4" />
              <span>AI</span>
            </TabsTrigger>
            </TabsList>
          </div>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* ECL Staging */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-blue-600" />
                    IFRS 9 ECL Staging
                  </CardTitle>
                  <CardDescription>Expected Credit Loss by Stage</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {ecl?.stage_breakdown ? (
                    Object.entries(ecl.stage_breakdown).map(([stageNum, data]: [string, any]) => (
                      <div key={stageNum} className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="font-medium">{data.name || `Stage ${stageNum}`}</span>
                          <span>{data.loan_count} loans | {formatCurrency(data.total_ecl)}</span>
                        </div>
                        <Progress
                          value={data.pct_of_portfolio_ead || 0}
                          className="h-2"
                        />
                        <div className="text-xs text-slate-500 text-right">
                          {data.pct_of_portfolio_ead?.toFixed(1) || 0}% of portfolio
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="space-y-3">
                      <RiskGauge value={60} label="Stage 1 (12-month ECL)" color="green" />
                      <RiskGauge value={30} label="Stage 2 (Lifetime ECL)" color="amber" />
                      <RiskGauge value={10} label="Stage 3 (Credit Impaired)" color="red" />
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* VaR Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5 text-purple-600" />
                    Value at Risk (Monte Carlo)
                  </CardTitle>
                  <CardDescription>Tail risk metrics</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg text-center">
                      <p className="text-xs text-blue-600 mb-1">VaR 95%</p>
                      <p className="text-2xl font-bold text-blue-700">
                        {formatCurrency(monteCarlo?.var?.var_95?.var_amount || 0)}
                      </p>
                      <p className="text-xs text-blue-500 mt-1">
                        {monteCarlo?.var?.var_95?.var_pct_of_portfolio?.toFixed(1) || 0}% of portfolio
                      </p>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg text-center">
                      <p className="text-xs text-purple-600 mb-1">VaR 99%</p>
                      <p className="text-2xl font-bold text-purple-700">
                        {formatCurrency(monteCarlo?.var?.var_99?.var_amount || 0)}
                      </p>
                      <p className="text-xs text-purple-500 mt-1">
                        {monteCarlo?.var?.var_99?.var_pct_of_portfolio?.toFixed(1) || 0}% of portfolio
                      </p>
                    </div>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg text-center">
                    <p className="text-xs text-red-600 mb-1">CVaR 99% (Expected Shortfall)</p>
                    <p className="text-2xl font-bold text-red-700">
                      {formatCurrency(monteCarlo?.cvar?.cvar_99_amount || 0)}
                    </p>
                    <p className="text-xs text-red-500 mt-1">
                      Worst 1% scenario average loss ({monteCarlo?.cvar?.cvar_99_pct?.toFixed(1) || 0}%)
                    </p>
                  </div>
                  {monteCarlo?.simulation_info && (
                    <div className="text-xs text-slate-500 text-center pt-2 border-t">
                      {monteCarlo.simulation_info.n_simulations?.toLocaleString()} Monte Carlo simulations
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Risk Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChart className="h-5 w-5 text-amber-600" />
                    Risk Level Distribution
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {(() => {
                    // Calculate risk distribution from actual loan PD values
                    const riskCounts = loanResults.reduce((acc: any, loan: any) => {
                      const pd = loan.parameters?.pd_12m || 0;
                      if (pd < 0.05) acc.low++;
                      else if (pd < 0.15) acc.medium++;
                      else if (pd < 0.30) acc.high++;
                      else acc.critical++;
                      return acc;
                    }, { low: 0, medium: 0, high: 0, critical: 0 });
                    
                    return (
                      <div className="grid grid-cols-4 gap-3">
                        <div className="text-center p-3 bg-emerald-50 rounded-lg">
                          <p className="text-2xl font-bold text-emerald-700">{riskCounts.low}</p>
                          <p className="text-xs text-emerald-600">Low Risk</p>
                          <p className="text-[10px] text-emerald-500">PD &lt; 5%</p>
                        </div>
                        <div className="text-center p-3 bg-amber-50 rounded-lg">
                          <p className="text-2xl font-bold text-amber-700">{riskCounts.medium}</p>
                          <p className="text-xs text-amber-600">Medium</p>
                          <p className="text-[10px] text-amber-500">PD 5-15%</p>
                        </div>
                        <div className="text-center p-3 bg-orange-50 rounded-lg">
                          <p className="text-2xl font-bold text-orange-700">{riskCounts.high}</p>
                          <p className="text-xs text-orange-600">High</p>
                          <p className="text-[10px] text-orange-500">PD 15-30%</p>
                        </div>
                        <div className="text-center p-3 bg-red-50 rounded-lg">
                          <p className="text-2xl font-bold text-red-700">{riskCounts.critical}</p>
                          <p className="text-xs text-red-600">Critical</p>
                          <p className="text-[10px] text-red-500">PD &gt; 30%</p>
                        </div>
                      </div>
                    );
                  })()}
                </CardContent>
              </Card>

              {/* AI-Powered Risk Models */}
              <Card className="border-2 border-indigo-100">
                <CardHeader className="bg-gradient-to-r from-indigo-50 to-purple-50">
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5 text-indigo-600" />
                    AI-Powered Risk Analysis
                  </CardTitle>
                  <CardDescription>Real-time predictive models running on your portfolio</CardDescription>
                </CardHeader>
                <CardContent className="pt-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
                      <div>
                        <span className="text-sm font-medium text-slate-700">Default Probability Predictor</span>
                        <p className="text-xs text-slate-500">Predicts likelihood of borrower default</p>
                      </div>
                      <Badge className="bg-green-500 text-white">Active</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gradient-to-r from-purple-50 to-violet-50 rounded-lg border border-purple-100">
                      <div>
                        <span className="text-sm font-medium text-slate-700">Loss Severity Estimator</span>
                        <p className="text-xs text-slate-500">Calculates expected loss if default occurs</p>
                      </div>
                      <Badge className="bg-green-500 text-white">Active</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg border border-amber-100">
                      <div>
                        <span className="text-sm font-medium text-slate-700">Early Repayment Detector</span>
                        <p className="text-xs text-slate-500">Identifies prepayment risk patterns</p>
                      </div>
                      <Badge className="bg-green-500 text-white">Active</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gradient-to-r from-emerald-50 to-green-50 rounded-lg border border-emerald-100">
                      <div>
                        <span className="text-sm font-medium text-slate-700">ESG Risk Scorer</span>
                        <p className="text-xs text-slate-500">Evaluates climate and sustainability risks</p>
                      </div>
                      <Badge className="bg-green-500 text-white">Active</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gradient-to-r from-rose-50 to-pink-50 rounded-lg border border-rose-100">
                      <div>
                        <span className="text-sm font-medium text-slate-700">Tail Risk Simulator</span>
                        <p className="text-xs text-slate-500">10,000 Monte Carlo simulations for VaR</p>
                      </div>
                      <Badge className="bg-purple-500 text-white">Running</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Advanced Analytics Tab */}
          <TabsContent value="advanced">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 lg:gap-6">
              <MonteCarloCard />
              <ECLSummaryCard />
              <WhatIfCard />
            </div>
          </TabsContent>

          {/* Risk Distribution Tab */}
          <TabsContent value="risk">
            <div className="space-y-6">
              {/* Concentration Risk Alert Card */}
              <Card className={`border-l-4 ${
                Math.max(pdDistribution.low, pdDistribution.medium, pdDistribution.high, pdDistribution.critical) >= 80 
                  ? 'border-l-amber-500 bg-amber-50' 
                  : 'border-l-green-500 bg-green-50'
              }`}>
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-full ${
                      Math.max(pdDistribution.low, pdDistribution.medium, pdDistribution.high, pdDistribution.critical) >= 80
                        ? 'bg-amber-100'
                        : 'bg-green-100'
                    }`}>
                      <AlertTriangle className={`h-6 w-6 ${
                        Math.max(pdDistribution.low, pdDistribution.medium, pdDistribution.high, pdDistribution.critical) >= 80
                          ? 'text-amber-600'
                          : 'text-green-600'
                      }`} />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">
                        {Math.max(pdDistribution.low, pdDistribution.medium, pdDistribution.high, pdDistribution.critical) >= 80 
                          ? '⚠️ Concentration Risk Detected' 
                          : '✅ Portfolio Well Diversified'}
                      </h3>
                      <p className="text-sm text-slate-600 mt-1">
                        {Math.max(pdDistribution.low, pdDistribution.medium, pdDistribution.high, pdDistribution.critical) >= 80 
                          ? `${Math.max(pdDistribution.low, pdDistribution.medium, pdDistribution.high, pdDistribution.critical)}% of loans are concentrated in a single risk bucket. High concentration increases correlated default risk.`
                          : 'Your portfolio has healthy diversification across risk buckets.'}
                      </p>
                      {Math.max(pdDistribution.low, pdDistribution.medium, pdDistribution.high, pdDistribution.critical) >= 80 && (
                        <div className="mt-3 p-3 bg-white rounded-lg border border-amber-200">
                          <p className="text-sm font-medium text-amber-800">💡 Recommendation:</p>
                          <p className="text-sm text-amber-700 mt-1">
                            Consider diversifying with {pdDistribution.medium >= 80 ? 'lower-risk secured loans (PD < 5%)' : 'medium-risk loans'} to reduce portfolio correlation risk.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Risk Distribution Cards */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* PD Distribution Card */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Target className="h-5 w-5 text-blue-600" />
                      Default Probability Distribution
                      <Badge variant="outline" className="ml-auto text-xs bg-blue-50">Real Data</Badge>
                    </CardTitle>
                    <CardDescription>
                      {loanResults.length} loans analyzed • Dominant: {
                        pdDistribution.low >= Math.max(pdDistribution.medium, pdDistribution.high, pdDistribution.critical) ? 'Low Risk' :
                        pdDistribution.medium >= Math.max(pdDistribution.low, pdDistribution.high, pdDistribution.critical) ? 'Medium Risk' :
                        pdDistribution.high >= Math.max(pdDistribution.low, pdDistribution.medium, pdDistribution.critical) ? 'High Risk' : 'Critical Risk'
                      }
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <RiskGauge value={pdDistribution.low} label={`PD < 5% (Low) - ${Math.round(loanResults.length * pdDistribution.low / 100)} loans`} color="green" />
                    <RiskGauge value={pdDistribution.medium} label={`PD 5-15% (Medium) - ${Math.round(loanResults.length * pdDistribution.medium / 100)} loans`} color="amber" />
                    <RiskGauge value={pdDistribution.high} label={`PD 15-30% (High) - ${Math.round(loanResults.length * pdDistribution.high / 100)} loans`} color="red" />
                    <RiskGauge value={pdDistribution.critical} label={`PD > 30% (Critical) - ${Math.round(loanResults.length * pdDistribution.critical / 100)} loans`} color="red" />
                  </CardContent>
                </Card>

                {/* LGD Distribution Card */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Shield className="h-5 w-5 text-purple-600" />
                      Loss Given Default Distribution
                      <Badge variant="outline" className="ml-auto text-xs bg-purple-50">Real Data</Badge>
                    </CardTitle>
                    <CardDescription>
                      Collateral quality • Dominant: {
                        lgdDistribution.wellSecured >= Math.max(lgdDistribution.standard, lgdDistribution.unsecured) ? 'Well Secured' :
                        lgdDistribution.standard >= Math.max(lgdDistribution.wellSecured, lgdDistribution.unsecured) ? 'Standard' : 'Unsecured'
                      }
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <RiskGauge value={lgdDistribution.wellSecured} label={`LGD < 30% (Well Secured) - ${Math.round(loanResults.length * lgdDistribution.wellSecured / 100)} loans`} color="green" />
                    <RiskGauge value={lgdDistribution.standard} label={`LGD 30-50% (Standard) - ${Math.round(loanResults.length * lgdDistribution.standard / 100)} loans`} color="amber" />
                    <RiskGauge value={lgdDistribution.unsecured} label={`LGD > 50% (Unsecured) - ${Math.round(loanResults.length * lgdDistribution.unsecured / 100)} loans`} color="red" />
                  </CardContent>
                </Card>
              </div>

              {/* Portfolio Risk Summary */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Portfolio Risk Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 bg-slate-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{loanResults.length}</div>
                      <div className="text-xs text-slate-500">Total Loans</div>
                    </div>
                    <div className="text-center p-4 bg-slate-50 rounded-lg">
                      <div className="text-2xl font-bold text-amber-600">{formatPct(avgPD)}</div>
                      <div className="text-xs text-slate-500">Avg PD</div>
                    </div>
                    <div className="text-center p-4 bg-slate-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">{formatPct(avgLGD)}</div>
                      <div className="text-xs text-slate-500">Avg LGD</div>
                    </div>
                    <div className="text-center p-4 bg-slate-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {Math.max(pdDistribution.low, pdDistribution.medium, pdDistribution.high, pdDistribution.critical) < 50 ? '🟢' : 
                         Math.max(pdDistribution.low, pdDistribution.medium, pdDistribution.high, pdDistribution.critical) < 80 ? '🟡' : '🟠'}
                      </div>
                      <div className="text-xs text-slate-500">Diversification</div>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t text-xs text-slate-500">
                    Data source: ECL loan_results ({loanResults.length} loans) • BigQuery • Updated: {new Date().toLocaleDateString()}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Sector Analysis Tab */}
          <TabsContent value="sector">
            <div className="space-y-6">
              {/* Concentration Level Alert */}
              {concentration && (
                <Card className={`border-l-4 ${
                  concentration.concentration_level === 'HIGH' 
                    ? 'border-l-red-500 bg-red-50' 
                    : concentration.concentration_level === 'MODERATE'
                    ? 'border-l-amber-500 bg-amber-50'
                    : 'border-l-green-500 bg-green-50'
                }`}>
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <div className={`p-3 rounded-full ${
                        concentration.concentration_level === 'HIGH' 
                          ? 'bg-red-100' 
                          : concentration.concentration_level === 'MODERATE'
                          ? 'bg-amber-100'
                          : 'bg-green-100'
                      }`}>
                        <Building2 className={`h-6 w-6 ${
                          concentration.concentration_level === 'HIGH' 
                            ? 'text-red-600' 
                            : concentration.concentration_level === 'MODERATE'
                            ? 'text-amber-600'
                            : 'text-green-600'
                        }`} />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg">
                          {concentration.concentration_level === 'HIGH' 
                            ? '🔴 High Sector Concentration' 
                            : concentration.concentration_level === 'MODERATE'
                            ? '🟡 Moderate Sector Concentration'
                            : '🟢 Well Diversified Portfolio'}
                        </h3>
                        <p className="text-sm text-slate-600 mt-1">
                          HHI Index: {concentration.hhi_index?.toFixed(0) || 'N/A'} • 
                          {concentration.concentration_level === 'HIGH' 
                            ? ' Consider reducing exposure to top sectors to manage concentration risk.'
                            : concentration.concentration_level === 'MODERATE'
                            ? ' Portfolio has moderate sector diversification. Monitor top exposures.'
                            : ' Portfolio is well balanced across sectors.'}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold">{concentration.total_loans}</div>
                        <div className="text-xs text-slate-500">Total Loans</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Sector Distribution Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChart className="h-5 w-5 text-cyan-600" />
                    Sector Concentration
                    <Badge variant="outline" className="ml-auto text-xs bg-cyan-50">Real Data</Badge>
                  </CardTitle>
                  <CardDescription>
                    Exposure by industry sector • {concentration?.top_exposures?.length || 0} sectors • 
                    Total: {formatCurrency(concentration?.total_exposure || 0)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {concentration?.top_exposures && concentration.top_exposures.length > 0 ? (
                    <div className="space-y-3">
                      {concentration.top_exposures.slice(0, 10).map((sector: any, idx: number) => (
                        <div key={sector.category || idx} className="flex items-center gap-4">
                          <div className="w-8 text-center">
                            <Badge variant="outline" className={`text-xs ${
                              idx === 0 ? 'bg-cyan-100 text-cyan-700' :
                              idx === 1 ? 'bg-blue-100 text-blue-700' :
                              idx === 2 ? 'bg-purple-100 text-purple-700' :
                              'bg-slate-100 text-slate-600'
                            }`}>
                              #{idx + 1}
                            </Badge>
                          </div>
                          <div className="w-40 text-sm font-medium truncate">{sector.category || sector.value || 'Unknown'}</div>
                          <div className="flex-1">
                            <Progress 
                              value={sector.percentage || 0} 
                              className={`h-3 ${
                                sector.percentage > 25 ? '[&>div]:bg-red-500' :
                                sector.percentage > 15 ? '[&>div]:bg-amber-500' :
                                '[&>div]:bg-cyan-500'
                              }`} 
                            />
                          </div>
                          <div className="w-16 text-right text-sm font-medium">
                            {(sector.percentage || 0).toFixed(1)}%
                          </div>
                          <div className="w-24 text-right text-sm text-slate-500">
                            {formatCurrency(sector.exposure || 0)}
                          </div>
                          <div className="w-20 text-right text-xs text-slate-400">
                            {sector.loan_count} loan{sector.loan_count !== 1 ? 's' : ''}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <Building2 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>No sector data available</p>
                      <p className="text-xs mt-1">Refresh to load data from BigQuery</p>
                    </div>
                  )}
                  <div className="mt-4 pt-4 border-t text-xs text-slate-500">
                    Data source: BigQuery loans.industry • HHI Index: {concentration?.hhi_index?.toFixed(0) || 'N/A'} • Updated: {new Date().toLocaleDateString()}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Macro Conditions Tab */}
          <TabsContent value="macro">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-blue-600" />
                  Current Market Conditions
                </CardTitle>
                <CardDescription>
                  {macro?.data_source || "FRED API (Federal Reserve)"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl text-center">
                    <p className="text-sm text-blue-600 mb-2">30-Year Mortgage Rate</p>
                    <p className="text-4xl font-bold text-blue-700">
                      {macro?.mortgage_rate_30y?.toFixed(2) || "6.85"}%
                    </p>
                    <p className="text-xs text-blue-500 mt-2">Weekly update</p>
                  </div>
                  <div className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl text-center">
                    <p className="text-sm text-purple-600 mb-2">10-Year Treasury</p>
                    <p className="text-4xl font-bold text-purple-700">
                      {macro?.treasury_10y?.toFixed(2) || "4.25"}%
                    </p>
                    <p className="text-xs text-purple-500 mt-2">Daily update</p>
                  </div>
                  <div className="p-6 bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl text-center">
                    <p className="text-sm text-emerald-600 mb-2">Federal Funds Rate</p>
                    <p className="text-4xl font-bold text-emerald-700">
                      {macro?.fed_funds_rate?.toFixed(2) || "4.50"}%
                    </p>
                    <p className="text-xs text-emerald-500 mt-2">Monthly update</p>
                  </div>
                </div>
                <div className="mt-6 p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600">
                    <strong>Data Source:</strong> Federal Reserve Economic Data (FRED API)
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Last updated: {macro?.timestamp ? new Date(macro.timestamp).toLocaleString() : "Live"}
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ESG Climate Risk Tab */}
          <TabsContent value="esg">
            <div className="space-y-6">
              {/* Portfolio ESG Overview Card */}
              <Card className="border-l-4 border-l-emerald-500">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Leaf className="h-5 w-5 text-emerald-600" />
                        Portfolio ESG Climate Risk
                        <Badge variant="outline" className="bg-emerald-50 text-emerald-700 text-xs">EBA 2026</Badge>
                      </CardTitle>
                      <CardDescription>
                        ESG as financial risk factor • {loanResults.length} loans analyzed • NGFS climate scenarios
                      </CardDescription>
                    </div>
                    <Badge variant="outline" className="bg-blue-50">Real Data</Badge>
                  </div>
                </CardHeader>
                <CardContent className="relative">
                  {/* Climate Scenario Selector */}
                  <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Activity className={`h-4 w-4 text-blue-600 ${esgLoading ? 'animate-spin' : ''}`} />
                        <span className="font-medium text-sm">
                          Climate Scenario {esgLoading && <span className="text-blue-500 text-xs ml-2">Updating...</span>}
                        </span>
                      </div>
                      <select 
                        value={esgScenario} 
                        disabled={esgLoading}
                        onChange={(e) => {
                          setEsgScenario(e.target.value);
                          setEsgLoading(true);
                          fetchESGPortfolioRisk(e.target.value).then(data => {
                            if (data.success) setEsgPortfolio(data);
                          }).finally(() => setEsgLoading(false));
                        }}
                        className={`text-sm border border-slate-300 rounded-md px-3 py-2 bg-white cursor-pointer hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm min-w-[180px] ${esgLoading ? 'opacity-50' : ''}`}
                      >
                        <option value="current_policies">🌍 Current Policies</option>
                        <option value="net_zero_2050">🌱 Net Zero 2050</option>
                        <option value="delayed_transition">⏰ Delayed Transition</option>
                        <option value="fragmented_world">🌐 Fragmented World</option>
                      </select>
                    </div>
                    <p className="text-xs text-slate-600">
                      {esgScenario === 'current_policies' && 'Assumes existing climate measures continue without further action.'}
                      {esgScenario === 'net_zero_2050' && 'Aggressive transition to net zero emissions by 2050.'}
                      {esgScenario === 'delayed_transition' && 'Transition to clean energy is delayed, causing more abrupt changes.'}
                      {esgScenario === 'fragmented_world' && 'Fragmented global climate policy with high physical risks.'}
                    </p>
                  </div>
                  
                  {/* Loading Overlay - shows immediately on scenario change */}
                  {esgLoading && (
                    <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-10 rounded-lg">
                      <div className="flex flex-col items-center gap-3">
                        <div className="h-10 w-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                        <span className="text-sm font-medium text-blue-600">Analyzing climate scenario...</span>
                      </div>
                    </div>
                  )}
                  
                  {/* Risk Scores Grid - DYNAMIC from API */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="text-center p-4 bg-amber-50 rounded-lg border border-amber-200">
                      <div className="text-2xl font-bold text-amber-600">
                        {esgPortfolio?.risk_scores?.transition_risk?.toFixed(1) || '0.0'}%
                      </div>
                      <div className="text-xs text-amber-700">Transition Risk</div>
                    </div>
                    <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="text-2xl font-bold text-blue-600">
                        {esgPortfolio?.risk_scores?.physical_risk?.toFixed(1) || '0.0'}%
                      </div>
                      <div className="text-xs text-blue-700">Physical Risk</div>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg border border-purple-200">
                      <div className="text-2xl font-bold text-purple-600">
                        {esgPortfolio?.risk_scores?.overall_esg_risk?.toFixed(1) || '0.0'}%
                      </div>
                      <div className="text-xs text-purple-700">Overall ESG Risk</div>
                    </div>
                    <div className="text-center p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                      <div className="text-2xl font-bold text-emerald-600">
                        {esgPortfolio?.portfolio_summary?.sll_loans || 0}
                      </div>
                      <div className="text-xs text-emerald-700">
                        SLL Loans ({esgPortfolio?.portfolio_summary?.sll_percentage?.toFixed(0) || 0}%)
                      </div>
                    </div>
                  </div>
                  
                  {/* Credit Impact - DYNAMIC from API */}
                  <div className="p-4 bg-red-50 rounded-lg border border-red-200 mb-6">
                    <h4 className="font-medium text-red-800 mb-3 flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4" />
                      Credit Risk Impact (EBA 2026 Methodology)
                    </h4>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div className="p-3 bg-white rounded-lg">
                        <p className="text-xs text-slate-500">PD Adjustment</p>
                        <p className="text-lg font-bold text-red-600">
                          +{esgPortfolio?.credit_impact?.pd_adjustment_bps?.toFixed(0) || 0} bps
                        </p>
                      </div>
                      <div className="p-3 bg-white rounded-lg">
                        <p className="text-xs text-slate-500">LGD Adjustment</p>
                        <p className="text-lg font-bold text-amber-600">
                          +{esgPortfolio?.credit_impact?.lgd_adjustment_bps?.toFixed(0) || 0} bps
                        </p>
                      </div>
                      <div className="p-3 bg-white rounded-lg">
                        <p className="text-xs text-slate-500">ECL Impact</p>
                        <p className="text-lg font-bold text-purple-600">
                          +{esgPortfolio?.credit_impact?.ecl_impact_percent?.toFixed(2) || 0}%
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  {/* Top Sectors by ESG Risk - DYNAMIC from API */}
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <h4 className="font-medium text-slate-700 mb-3">
                      Top Sectors by Physical Risk ({esgPortfolio?.portfolio_summary?.sectors_analyzed || 0} analyzed)
                    </h4>
                    <div className="space-y-2">
                      {(esgPortfolio?.sector_breakdown || []).slice(0, 5).map((s: any, i: number) => (
                        <div key={i} className="flex items-center gap-3">
                          <Badge variant="outline" className={`text-xs ${
                            s.physical_risk * 100 > 60 ? 'bg-red-100 text-red-700' : 
                            s.physical_risk * 100 > 40 ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
                          }`}>
                            {(s.physical_risk * 100).toFixed(0)}%
                          </Badge>
                          <span className="flex-1 text-sm">{s.sector}</span>
                          <span className="text-xs text-slate-500">{formatCurrency(s.exposure)}</span>
                          {s.sll_count > 0 && <Badge className="bg-emerald-500 text-xs">{s.sll_count} SLL</Badge>}
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="mt-4 pt-4 border-t text-xs text-slate-400 flex items-center justify-between">
                    <span>Live portfolio data • EBA 2026 Methodology • {esgPortfolio?.portfolio_summary?.sectors_analyzed || 12} sectors</span>
                    <span>Last updated: {new Date().toLocaleDateString()}</span>
                  </div>
                </CardContent>
              </Card>
              
              {/* ESG Framework Info Card */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Shield className="h-5 w-5 text-emerald-600" />
                    ESG as Financial Risk (EBA 2026)
                  </CardTitle>
                  <CardDescription>
                    Regulatory context and credit risk integration
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-lg">
                    <h4 className="text-sm font-semibold text-emerald-800 mb-2">Key Features</h4>
                    <ul className="text-xs text-emerald-700 space-y-2">
                      <li className="flex items-start gap-2">
                        <Badge variant="outline" className="bg-emerald-100 text-emerald-800 text-[10px]">TNFD</Badge>
                        <span>12 sector materiality mappings aligned with TNFD/GRI frameworks</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Badge variant="outline" className="bg-blue-100 text-blue-800 text-[10px]">NGFS</Badge>
                        <span>4 climate scenarios: Net Zero 2050, Delayed, Current Policies, Fragmented</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Badge variant="outline" className="bg-purple-100 text-purple-800 text-[10px]">EBA</Badge>
                        <span>PD/LGD adjustments based on sector-level ESG risk per EBA 2026 guidelines</span>
                      </li>
                    </ul>
                  </div>
                  <div className="text-xs text-slate-500 p-3 bg-blue-50 rounded-lg">
                    <strong>Regulatory Timeline:</strong> EBA ESG Guidelines effective January 2026. 
                    Banks must integrate ESG factors into credit risk assessment and capital planning.
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* AI Committee Tab - Full Width Modern Layout */}
          <TabsContent value="committee">
            <div className="space-y-4">
              {/* Compact Header with Key Info */}
              <div className="flex items-center justify-between p-3 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg text-white">
                <div className="flex items-center gap-3">
                  <Brain className="h-6 w-6" />
                  <div>
                    <h3 className="font-semibold">AI Risk Committee</h3>
                    <p className="text-xs text-purple-100">5 specialized agents • Debate-style voting • Full audit trail</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Badge className="bg-white/20 text-white border-white/30">EU AI Act</Badge>
                  <Badge className="bg-white/20 text-white border-white/30">EBA 2026</Badge>
                  <Badge className="bg-white/20 text-white border-white/30">IFRS 9</Badge>
                </div>
              </div>
              {/* Full Width Risk Committee */}
              <RiskCommitteeCard />
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
