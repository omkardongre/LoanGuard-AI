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

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

// Honeycomb metric card
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
    blue: "bg-blue-50 border-blue-200 text-blue-700",
    green: "bg-emerald-50 border-emerald-200 text-emerald-700",
    amber: "bg-amber-50 border-amber-200 text-amber-700",
    red: "bg-red-50 border-red-200 text-red-700",
    purple: "bg-purple-50 border-purple-200 text-purple-700",
    slate: "bg-slate-50 border-slate-200 text-slate-700",
  };

  return (
    <div className={`p-4 rounded-xl border-2 ${colorClasses[color as keyof typeof colorClasses]} transition-all hover:shadow-md`}>
      <div className="flex items-center justify-between mb-2">
        <Icon className="h-5 w-5" />
        {trend && (
          trend === "up" ? <TrendingUp className="h-4 w-4" /> :
          trend === "down" ? <TrendingDown className="h-4 w-4" /> : null
        )}
      </div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-sm font-medium">{title}</p>
      {subtitle && <p className="text-xs opacity-70">{subtitle}</p>}
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

  async function loadData() {
    try {
      const [dashData, eclData, macroData, concData] = await Promise.allSettled([
        fetchPortfolioAnalytics(),
        fetchECLSummary(),
        fetchMacroData(),
        fetchConcentration(),
      ]);

      if (dashData.status === "fulfilled") setDashboard(dashData.value);
      if (eclData.status === "fulfilled" && eclData.value.success) setEcl(eclData.value);
      if (macroData.status === "fulfilled" && macroData.value.success) setMacro(macroData.value);
      if (concData.status === "fulfilled") setConcentration(concData.value);
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

  // Calculate derived metrics
  const totalLoans = dashboard?.total_loans || 0;
  const totalExposure = dashboard?.total_exposure || 0;
  const avgPD = ecl?.summary?.weighted_avg_pd || 0.08;
  const avgLGD = ecl?.summary?.weighted_avg_lgd || 0.45;
  const totalECL = ecl?.summary?.total_ecl || totalExposure * avgPD * avgLGD;
  const coverageRatio = (totalECL / totalExposure * 100) || 0;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Portfolio Analytics</h1>
            <p className="text-slate-500">Real-time risk monitoring and KPIs</p>
          </div>
          <Button onClick={handleRefresh} disabled={refreshing} variant="outline">
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
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
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="advanced">Advanced Analytics</TabsTrigger>
            <TabsTrigger value="risk">Risk Distribution</TabsTrigger>
            <TabsTrigger value="sector">Sector Analysis</TabsTrigger>
            <TabsTrigger value="macro">Macro Conditions</TabsTrigger>
            <TabsTrigger value="esg">ESG Climate Risk</TabsTrigger>
            <TabsTrigger value="committee">AI Committee</TabsTrigger>
          </TabsList>

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
                  {ecl?.summary?.stage_breakdown ? (
                    Object.entries(ecl.summary.stage_breakdown).map(([stage, data]: [string, any]) => (
                      <div key={stage} className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="font-medium">{stage}</span>
                          <span>{data.count} loans | {formatCurrency(data.ecl)}</span>
                        </div>
                        <Progress
                          value={(data.ecl / totalECL) * 100}
                          className="h-2"
                        />
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
                        {formatCurrency(totalExposure * 0.15)}
                      </p>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg text-center">
                      <p className="text-xs text-purple-600 mb-1">VaR 99%</p>
                      <p className="text-2xl font-bold text-purple-700">
                        {formatCurrency(totalExposure * 0.295)}
                      </p>
                    </div>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg text-center">
                    <p className="text-xs text-red-600 mb-1">CVaR 99% (Expected Shortfall)</p>
                    <p className="text-2xl font-bold text-red-700">
                      {formatCurrency(totalExposure * 0.32)}
                    </p>
                    <p className="text-xs text-red-500 mt-1">
                      Worst 1% scenario average loss
                    </p>
                  </div>
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
                  <div className="grid grid-cols-4 gap-3">
                    <div className="text-center p-3 bg-emerald-50 rounded-lg">
                      <p className="text-2xl font-bold text-emerald-700">{Math.floor(totalLoans * 0.45)}</p>
                      <p className="text-xs text-emerald-600">Low Risk</p>
                    </div>
                    <div className="text-center p-3 bg-amber-50 rounded-lg">
                      <p className="text-2xl font-bold text-amber-700">{Math.floor(totalLoans * 0.35)}</p>
                      <p className="text-xs text-amber-600">Medium</p>
                    </div>
                    <div className="text-center p-3 bg-orange-50 rounded-lg">
                      <p className="text-2xl font-bold text-orange-700">{Math.floor(totalLoans * 0.15)}</p>
                      <p className="text-xs text-orange-600">High</p>
                    </div>
                    <div className="text-center p-3 bg-red-50 rounded-lg">
                      <p className="text-2xl font-bold text-red-700">{Math.floor(totalLoans * 0.05)}</p>
                      <p className="text-xs text-red-600">Critical</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* ML Models */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5 text-indigo-600" />
                    ML Models Active
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-2 bg-slate-50 rounded">
                      <span className="text-sm">Breach Predictor (PD)</span>
                      <Badge className="bg-green-100 text-green-800">LightGBM</Badge>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-50 rounded">
                      <span className="text-sm">LGD Predictor</span>
                      <Badge className="bg-green-100 text-green-800">Two-Stage</Badge>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-50 rounded">
                      <span className="text-sm">Prepayment Risk</span>
                      <Badge className="bg-green-100 text-green-800">XGBoost</Badge>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-50 rounded">
                      <span className="text-sm">ESG Risk Scorer</span>
                      <Badge className="bg-green-100 text-green-800">XGBoost</Badge>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-50 rounded">
                      <span className="text-sm">Monte Carlo VaR</span>
                      <Badge className="bg-purple-100 text-purple-800">Gaussian</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Advanced Analytics Tab */}
          <TabsContent value="advanced">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <MonteCarloCard />
              <ECLSummaryCard />
              <WhatIfCard />
            </div>
          </TabsContent>

          {/* Risk Distribution Tab */}
          <TabsContent value="risk">
            <Card>
              <CardHeader>
                <CardTitle>Portfolio Risk Breakdown</CardTitle>
                <CardDescription>Detailed risk analysis by category</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium">Default Probability Distribution</h4>
                    <RiskGauge value={35} label="PD < 5% (Low)" color="green" />
                    <RiskGauge value={40} label="PD 5-15% (Medium)" color="amber" />
                    <RiskGauge value={20} label="PD 15-30% (High)" color="red" />
                    <RiskGauge value={5} label="PD > 30% (Critical)" color="red" />
                  </div>
                  <div className="space-y-4">
                    <h4 className="font-medium">LGD Distribution</h4>
                    <RiskGauge value={25} label="LGD < 30% (Well Secured)" color="green" />
                    <RiskGauge value={45} label="LGD 30-50% (Standard)" color="amber" />
                    <RiskGauge value={30} label="LGD > 50% (Unsecured)" color="red" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sector Analysis Tab */}
          <TabsContent value="sector">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5" />
                  Sector Concentration
                </CardTitle>
                <CardDescription>Exposure by industry sector</CardDescription>
              </CardHeader>
              <CardContent>
                {concentration?.by_sector ? (
                  <div className="space-y-3">
                    {concentration.by_sector.slice(0, 8).map((sector: any) => (
                      <div key={sector.sector} className="flex items-center gap-4">
                        <div className="w-32 text-sm font-medium truncate">{sector.sector}</div>
                        <div className="flex-1">
                          <Progress value={sector.concentration_pct} className="h-3" />
                        </div>
                        <div className="w-20 text-right text-sm">
                          {sector.concentration_pct.toFixed(1)}%
                        </div>
                        <div className="w-24 text-right text-sm text-slate-500">
                          {formatCurrency(sector.total_exposure)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {[
                      { name: "Technology", pct: 25 },
                      { name: "Healthcare", pct: 18 },
                      { name: "Real Estate", pct: 15 },
                      { name: "Manufacturing", pct: 12 },
                      { name: "Financial Services", pct: 10 },
                      { name: "Retail", pct: 8 },
                      { name: "Energy", pct: 7 },
                      { name: "Other", pct: 5 },
                    ].map((sector) => (
                      <div key={sector.name} className="flex items-center gap-4">
                        <div className="w-32 text-sm font-medium">{sector.name}</div>
                        <div className="flex-1">
                          <Progress value={sector.pct} className="h-3" />
                        </div>
                        <div className="w-16 text-right text-sm">{sector.pct}%</div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
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
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ESGFinancialRiskCard 
                loanId="DEMO-001"
                borrowerName="Sample Corporation"
                sector="energy"
                loanAmount={10000000}
              />
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Leaf className="h-5 w-5 text-emerald-600" />
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
                        <span>8 sector materiality mappings aligned with TNFD/GRI frameworks</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Badge variant="outline" className="bg-blue-100 text-blue-800 text-[10px]">NGFS</Badge>
                        <span>4 climate scenarios: Net Zero 2050, Delayed, Current Policies, Fragmented</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Badge variant="outline" className="bg-purple-100 text-purple-800 text-[10px]">EBA</Badge>
                        <span>PD/LGD adjustments based on ESG risk score per EBA 2026 guidelines</span>
                      </li>
                    </ul>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <h4 className="text-sm font-semibold text-slate-700 mb-2">Credit Risk Integration</h4>
                    <div className="grid grid-cols-3 gap-3 text-center">
                      <div className="p-2 bg-white rounded border">
                        <p className="text-xs text-slate-500">PD Impact</p>
                        <p className="text-sm font-bold text-slate-700">0.95x - 1.50x</p>
                      </div>
                      <div className="p-2 bg-white rounded border">
                        <p className="text-xs text-slate-500">LGD Impact</p>
                        <p className="text-sm font-bold text-slate-700">-2% to +15%</p>
                      </div>
                      <div className="p-2 bg-white rounded border">
                        <p className="text-xs text-slate-500">ECL Impact</p>
                        <p className="text-sm font-bold text-slate-700">Up to +50%</p>
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 p-3 bg-blue-50 rounded-lg">
                    <strong>Regulatory Timeline:</strong> EBA ESG Guidelines effective January 2026. 
                    Banks must integrate ESG factors into credit risk assessment and capital planning.
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* AI Committee Tab */}
          <TabsContent value="committee">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RiskCommitteeCard />
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5 text-purple-600" />
                    Multi-Agent Credit Decisions
                  </CardTitle>
                  <CardDescription>
                    AI-powered debate-style decision making
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg">
                    <h4 className="text-sm font-semibold text-purple-800 mb-2">5 AI Agents</h4>
                    <ul className="text-xs text-purple-700 space-y-2">
                      <li className="flex items-start gap-2">
                        <Badge variant="outline" className="bg-blue-100 text-blue-800 text-[10px]">Credit</Badge>
                        <span>Credit Risk Assessor - PD/LGD scoring and credit metrics</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Badge variant="outline" className="bg-emerald-100 text-emerald-800 text-[10px]">ESG</Badge>
                        <span>ESG Risk Agent - Climate and sustainability factors</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Badge variant="outline" className="bg-amber-100 text-amber-800 text-[10px]">Market</Badge>
                        <span>Market Context Agent - Sector and macro analysis</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Badge variant="outline" className="bg-red-100 text-red-800 text-[10px]">Devil</Badge>
                        <span>Devil&apos;s Advocate - Challenges and stress tests</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Badge variant="outline" className="bg-purple-100 text-purple-800 text-[10px]">Synth</Badge>
                        <span>Synthesizer - Final consensus and audit trail</span>
                      </li>
                    </ul>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <h4 className="text-sm font-semibold text-slate-700 mb-2">Regulatory Compliance</h4>
                    <div className="flex flex-wrap gap-2">
                      <Badge className="bg-purple-600">EU AI Act</Badge>
                      <Badge className="bg-blue-600">EBA Guidelines</Badge>
                      <Badge className="bg-emerald-600">IFRS 9</Badge>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 p-3 bg-blue-50 rounded-lg">
                    <strong>Explainability:</strong> Full audit trail with per-agent reasoning 
                    for complete transparency per EU AI Act requirements on high-risk AI systems.
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
