"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
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
  Bell,
  Activity,
  Loader2,
} from "lucide-react";
import {
  fetchDashboard,
  fetchLoans,
  fetchAlerts,
  type DashboardSummary,
  type Loan,
  type Alert,
} from "@/lib/api";

// Fallback data if API fails
const fallbackLoans = [
  {
    loan_id: "LOAN-0001",
    borrower_name: "Acme Corp",
    facility_amount: 150000000,
    currency: "USD",
    status: "GREEN" as const,
    is_sll: true,
  },
  {
    loan_id: "LOAN-0002",
    borrower_name: "Global Industries",
    facility_amount: 200000000,
    currency: "USD",
    status: "AMBER" as const,
    is_sll: false,
  },
  {
    loan_id: "LOAN-0003",
    borrower_name: "TechStart Inc",
    facility_amount: 75000000,
    currency: "USD",
    status: "RED" as const,
    is_sll: true,
  },
];

const fallbackAlerts = [
  {
    alert_id: "ALT-001",
    loan_id: "LOAN-0003",
    message: "Debt/EBITDA breach detected",
    severity: "HIGH" as const,
    type: "breach",
    created_at: new Date().toISOString(),
    acknowledged: false,
  },
  {
    alert_id: "ALT-002",
    loan_id: "LOAN-0002",
    message: "Interest Coverage approaching threshold",
    severity: "MEDIUM" as const,
    type: "warning",
    created_at: new Date().toISOString(),
    acknowledged: false,
  },
];

function formatCurrency(amount: number, currency: string = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 0,
  }).format(amount);
}

export default function Home() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [dashboardData, loansData, alertsData] = await Promise.all([
          fetchDashboard().catch(() => null),
          fetchLoans().catch(() => ({ loans: fallbackLoans, total: 3 })),
          fetchAlerts().catch(() => ({
            alerts: fallbackAlerts,
            total_count: 2,
          })),
        ]);

        setDashboard(
          dashboardData || {
            total_loans: 50,
            loans_compliant: 35,
            loans_warning: 10,
            loans_breach: 5,
            active_alerts: 12,
            esg_average_score: 72.5,
          }
        );
        setLoans(loansData.loans.slice(0, 5));
        setAlerts(alertsData.alerts.slice(0, 3));
      } catch (err) {
        setError("Failed to load data");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);
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

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-500">
            Monitor your loan portfolio compliance
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            title="Total Loans"
            value={dashboard?.total_loans || 0}
            icon={FileText}
            trend={{ value: 5, isPositive: true }}
          />
          <StatCard
            title="Compliant"
            value={dashboard?.loans_compliant || 0}
            icon={CheckCircle}
            className="border-l-4 border-l-emerald-500"
          />
          <StatCard
            title="Warning"
            value={dashboard?.loans_warning || 0}
            icon={AlertTriangle}
            className="border-l-4 border-l-amber-500"
          />
          <StatCard
            title="Breach"
            value={dashboard?.loans_breach || 0}
            icon={XCircle}
            className="border-l-4 border-l-red-500"
          />
        </div>

        {/* Secondary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <StatCard
            title="Active Alerts"
            value={dashboard?.active_alerts || 0}
            icon={Bell}
          />
          <StatCard
            title="ESG Score (Avg)"
            value={dashboard?.esg_average_score?.toFixed(1) || "0"}
            icon={Leaf}
          />
          <StatCard title="Breach Probability" value="8.2%" icon={TrendingUp} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Loans - Using Card and Table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">Recent Loans</CardTitle>
              <a
                href="/loans"
                className="text-sm text-emerald-600 hover:underline"
              >
                View all →
              </a>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Borrower</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loans.map((loan) => (
                    <TableRow key={loan.loan_id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{loan.borrower_name}</p>
                          <p className="text-xs text-slate-500">
                            {loan.loan_id}
                          </p>
                        </div>
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
            </CardContent>
          </Card>

          {/* Active Alerts - Using Card and Badge */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">Active Alerts</CardTitle>
              <a
                href="/alerts"
                className="text-sm text-emerald-600 hover:underline"
              >
                View all →
              </a>
            </CardHeader>
            <CardContent className="space-y-3">
              {alerts.map((alert) => (
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
                    <p className="font-medium text-slate-900">
                      {alert.message}
                    </p>
                    <p className="text-sm text-slate-500">{alert.loan_id}</p>
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
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Compliance Progress Section */}
        <div className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Portfolio Compliance Progress
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Financial Covenants</span>
                  <span className="text-emerald-600">85% Compliant</span>
                </div>
                <Progress value={85} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>ESG Targets</span>
                  <span className="text-amber-600">72% On Track</span>
                </div>
                <Progress value={72} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Reporting Compliance</span>
                  <span className="text-emerald-600">92% Complete</span>
                </div>
                <Progress value={92} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
