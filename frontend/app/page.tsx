"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
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

      <main className="flex-1 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
            <p className="text-slate-500">
              Monitor your loan portfolio compliance
            </p>
          </div>
          <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            title="Total Loans"
            value={stats.total_loans}
            icon={FileText}
            trend={{ value: 5, isPositive: true }}
          />
          <StatCard
            title="Compliant"
            value={stats.loans_compliant}
            icon={CheckCircle}
            className="border-l-4 border-l-emerald-500"
          />
          <StatCard
            title="Warning"
            value={stats.loans_warning}
            icon={AlertTriangle}
            className="border-l-4 border-l-amber-500"
          />
          <StatCard
            title="Breach"
            value={stats.loans_breach}
            icon={XCircle}
            className="border-l-4 border-l-red-500"
          />
        </div>

        {/* Secondary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <StatCard title="Active Alerts" value={stats.active_alerts} icon={Bell} />
          <StatCard
            title="ESG Score (Avg)"
            value={stats.esg_average_score?.toFixed(1) || "-"}
            icon={Leaf}
          />
          <StatCard
            title="ML Predictions"
            value={velocity?.total_loans_analyzed || 0}
            icon={Brain}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Recent Loans */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">Recent Loans</CardTitle>
              <a href="/loans" className="text-sm text-emerald-600 hover:underline">
                View all →
              </a>
            </CardHeader>
            <CardContent>
              {loans.length === 0 ? (
                <p className="text-slate-500 text-center py-4">
                  No loans found. Connect to API to load data.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Borrower</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {loans.slice(0, 5).map((loan) => (
                      <TableRow key={loan.loan_id}>
                        <TableCell>
                          <a href={`/loans/${loan.loan_id}`} className="hover:underline">
                            <p className="font-medium">{loan.borrower_name}</p>
                            <p className="text-xs text-slate-500">{loan.loan_id}</p>
                          </a>
                        </TableCell>
                        <TableCell>
                          {formatCurrency(loan.facility_amount, loan.currency)}
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={loan.status} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* Active Alerts */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">Active Alerts</CardTitle>
              <a href="/alerts" className="text-sm text-emerald-600 hover:underline">
                View all →
              </a>
            </CardHeader>
            <CardContent className="space-y-3">
              {alerts.length === 0 ? (
                <p className="text-slate-500 text-center py-4">
                  No active alerts
                </p>
              ) : (
                alerts.slice(0, 4).map((alert) => (
                  <div
                    key={alert.alert_id}
                    className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg"
                  >
                    <div
                      className={`p-2 rounded-full ${
                        alert.severity === "HIGH" || alert.severity === "CRITICAL"
                          ? "bg-red-100 text-red-600"
                          : "bg-amber-100 text-amber-600"
                      }`}
                    >
                      <AlertTriangle className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-slate-900">{alert.message}</p>
                      <a
                        href={`/loans/${alert.loan_id}`}
                        className="text-sm text-emerald-600 hover:underline"
                      >
                        {alert.loan_id}
                      </a>
                    </div>
                    <Badge
                      variant={
                        alert.severity === "HIGH" || alert.severity === "CRITICAL"
                          ? "destructive"
                          : "secondary"
                      }
                    >
                      {alert.severity}
                    </Badge>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Portfolio Velocity */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-600" />
                Risk Velocity
              </CardTitle>
            </CardHeader>
            <CardContent>
              {velocity ? (
                <div className="space-y-4">
                  <p className="text-sm text-slate-600">{velocity.summary}</p>

                  {/* Risk Distribution */}
                  {velocity.risk_distribution && (
                    <div className="grid grid-cols-4 gap-2 text-center">
                      {Object.entries(velocity.risk_distribution).map(([level, count]) => (
                        <div
                          key={level}
                          className={`p-2 rounded-lg ${
                            level === "CRITICAL"
                              ? "bg-red-100"
                              : level === "HIGH"
                              ? "bg-red-50"
                              : level === "MEDIUM"
                              ? "bg-amber-50"
                              : "bg-emerald-50"
                          }`}
                        >
                          <p className="text-lg font-bold">{count}</p>
                          <p className="text-xs text-slate-600">{level}</p>
                        </div>
                      ))}
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
                              <span className="text-sm text-red-600">
                                {loan.nearest_breach} periods to breach
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
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5 text-purple-600" />
                Portfolio Concentration
              </CardTitle>
            </CardHeader>
            <CardContent>
              {concentration ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">HHI Index</p>
                      <p className="text-2xl font-bold">
                        {concentration.hhi_index?.toFixed(0)}
                      </p>
                    </div>
                    <Badge
                      variant={
                        concentration.concentration_level === "HIGH"
                          ? "destructive"
                          : concentration.concentration_level === "MODERATE"
                          ? "secondary"
                          : "outline"
                      }
                    >
                      {concentration.concentration_level} CONCENTRATION
                    </Badge>
                  </div>

                  <div className="text-sm text-slate-600">
                    <p>Total Exposure: {formatCurrency(concentration.total_exposure)}</p>
                    <p>Loans: {concentration.total_loans}</p>
                  </div>

                  {/* Top Exposures */}
                  {concentration.top_exposures?.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">Top Exposures</p>
                      <div className="space-y-2">
                        {concentration.top_exposures.slice(0, 5).map((exp, idx) => (
                          <div key={idx} className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span>{exp.value || exp.category}</span>
                              <span className="font-medium">
                                {exp.percentage?.toFixed(1)}%
                              </span>
                            </div>
                            <Progress value={exp.percentage} className="h-1" />
                          </div>
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

        {/* Compliance Progress Section */}
        <div className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Portfolio Compliance Progress
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Financial Covenants</span>
                  <span className="text-emerald-600">
                    {stats.total_loans > 0
                      ? ((stats.loans_compliant / stats.total_loans) * 100).toFixed(0)
                      : 0}
                    % Compliant
                  </span>
                </div>
                <Progress
                  value={
                    stats.total_loans > 0
                      ? (stats.loans_compliant / stats.total_loans) * 100
                      : 0
                  }
                  className="h-2"
                />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>ESG Targets</span>
                  <span className="text-amber-600">
                    {stats.esg_average_score?.toFixed(0) || 0}% On Track
                  </span>
                </div>
                <Progress value={stats.esg_average_score || 0} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Alert Resolution</span>
                  <span className="text-emerald-600">
                    {stats.active_alerts > 0 ? "In Progress" : "100% Resolved"}
                  </span>
                </div>
                <Progress
                  value={stats.active_alerts > 0 ? 75 : 100}
                  className="h-2"
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
