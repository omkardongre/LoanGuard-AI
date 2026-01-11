"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Target,
  Loader2,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Gauge,
  FileCheck,
} from "lucide-react";
import {
  fetchLoans,
  fetchSLLKPIs,
  fetchSLLSPTs,
  validateSLLSPTs,
  calculateSLLMargin,
  fetchSLLPortfolioSummary,
  type Loan,
  type SLLKPI,
  type SLLSPT,
  type SLLMarginAdjustment,
} from "@/lib/api";

interface LoanSLLDetails {
  loan: Loan;
  kpis?: SLLKPI[];
  spts?: SLLSPT[];
  marginAdjustment?: SLLMarginAdjustment;
  loading: boolean;
}

const KPI_TYPES: Record<string, { color: string; label: string }> = {
  GHG: { color: "bg-emerald-100 text-emerald-800", label: "GHG Emissions" },
  Energy: { color: "bg-amber-100 text-amber-800", label: "Energy" },
  Water: { color: "bg-blue-100 text-blue-800", label: "Water" },
  Waste: { color: "bg-orange-100 text-orange-800", label: "Waste" },
  Biodiversity: { color: "bg-green-100 text-green-800", label: "Biodiversity" },
  Social: { color: "bg-purple-100 text-purple-800", label: "Social" },
  Governance: { color: "bg-slate-100 text-slate-800", label: "Governance" },
};

function getVerificationColor(status: string): string {
  switch (status?.toUpperCase()) {
    case "VERIFIED":
      return "bg-emerald-100 text-emerald-800";
    case "PENDING":
      return "bg-amber-100 text-amber-800";
    case "FAILED":
      return "bg-red-100 text-red-800";
    default:
      return "bg-slate-100 text-slate-800";
  }
}

function getSPTStatusColor(status: string): string {
  switch (status?.toUpperCase()) {
    case "ACHIEVED":
      return "bg-emerald-100 text-emerald-800";
    case "ACTIVE":
      return "bg-blue-100 text-blue-800";
    case "NOT_ACHIEVED":
      return "bg-red-100 text-red-800";
    case "EXPIRED":
      return "bg-slate-100 text-slate-800";
    default:
      return "bg-slate-100 text-slate-800";
  }
}

export default function SLLMonitoringPage() {
  const [loading, setLoading] = useState(true);
  const [sllLoans, setSllLoans] = useState<Loan[]>([]);
  const [selectedLoan, setSelectedLoan] = useState<string | null>(null);
  const [loanDetails, setLoanDetails] = useState<Map<string, LoanSLLDetails>>(new Map());
  const [activeTab, setActiveTab] = useState("overview");
  const [summary, setSummary] = useState<{
    sll_loan_count: number;
    total_kpis: number;
    verified_kpis: number;
    verification_rate: number;
    avg_achievement_probability: number;
    total_spts: number;
    achieved_spts: number;
    spt_achievement_rate: number;
    avg_margin_impact_bps: number;
  } | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [loansRes, summaryRes] = await Promise.allSettled([
        fetchLoans(),
        fetchSLLPortfolioSummary(),
      ]);

      if (loansRes.status === "fulfilled") {
        // Filter only SLL loans
        const allLoans = loansRes.value.loans || [];
        setSllLoans(allLoans.filter((l) => l.is_sll));
      }

      if (summaryRes.status === "fulfilled" && summaryRes.value.success) {
        setSummary({
          sll_loan_count: summaryRes.value.sll_loan_count,
          total_kpis: summaryRes.value.total_kpis,
          verified_kpis: summaryRes.value.verified_kpis,
          verification_rate: summaryRes.value.verification_rate,
          avg_achievement_probability: summaryRes.value.avg_achievement_probability,
          total_spts: summaryRes.value.total_spts,
          achieved_spts: summaryRes.value.achieved_spts,
          spt_achievement_rate: summaryRes.value.spt_achievement_rate,
          avg_margin_impact_bps: summaryRes.value.avg_margin_impact_bps,
        });
      }
    } catch (err) {
      console.error("Failed to load SLL data:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadLoanDetails(loanId: string) {
    const existing = loanDetails.get(loanId);
    if (existing && !existing.loading && existing.kpis) return;

    const loan = sllLoans.find((l) => l.loan_id === loanId);
    if (!loan) return;

    setLoanDetails((prev) => {
      const next = new Map(prev);
      next.set(loanId, { loan, loading: true });
      return next;
    });

    try {
      const [kpisRes, sptsRes, marginRes] = await Promise.allSettled([
        fetchSLLKPIs(loanId),
        fetchSLLSPTs(loanId),
        calculateSLLMargin(loanId),
      ]);

      setLoanDetails((prev) => {
        const next = new Map(prev);
        next.set(loanId, {
          loan,
          kpis: kpisRes.status === "fulfilled" && kpisRes.value.success
            ? kpisRes.value.kpis
            : [],
          spts: sptsRes.status === "fulfilled" && sptsRes.value.success
            ? sptsRes.value.spts
            : [],
          marginAdjustment: marginRes.status === "fulfilled" && marginRes.value.success
            ? marginRes.value.margin_adjustment
            : undefined,
          loading: false,
        });
        return next;
      });
    } catch (err) {
      console.error("Failed to load loan SLL details:", err);
      setLoanDetails((prev) => {
        const next = new Map(prev);
        next.set(loanId, { loan, loading: false });
        return next;
      });
    }
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

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">SLL Monitoring</h1>
            <p className="text-slate-500">
              KPIs, SPTs & Margin Adjustments per LMA SLLP
            </p>
          </div>
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
              LMA SLLP 2024
            </Badge>
            <Button variant="outline" onClick={loadData}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-5 w-5 text-emerald-500" />
                <p className="text-sm text-slate-500">SLL Loans</p>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {summary?.sll_loan_count || sllLoans.length || 0}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Gauge className="h-5 w-5 text-blue-500" />
                <p className="text-sm text-slate-500">KPIs Tracked</p>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {summary?.total_kpis || 0}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <FileCheck className="h-5 w-5 text-emerald-500" />
                <p className="text-sm text-slate-500">Verification Rate</p>
              </div>
              <p className="text-2xl font-bold text-emerald-600">
                {summary?.verification_rate || 0}%
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-5 w-5 text-blue-500" />
                <p className="text-sm text-slate-500">SPT Achievement</p>
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {summary?.spt_achievement_rate || 0}%
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <TrendingDown className="h-5 w-5 text-amber-500" />
                <p className="text-sm text-slate-500">Avg Margin Impact</p>
              </div>
              <p className="text-2xl font-bold text-amber-600">
                {summary?.avg_margin_impact_bps || 0} bps
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">SLL Portfolio</TabsTrigger>
            <TabsTrigger value="kpis">KPI Tracking</TabsTrigger>
            <TabsTrigger value="spts">SPT Performance</TabsTrigger>
            <TabsTrigger value="margin">Margin Adjustments</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Sustainability-Linked Loans</CardTitle>
              </CardHeader>
              <CardContent>
                {sllLoans.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <Target className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>No SLL loans found. Data loaded from BigQuery.</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Borrower</TableHead>
                        <TableHead>Industry</TableHead>
                        <TableHead>Amount</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sllLoans.map((loan) => (
                        <TableRow key={loan.loan_id}>
                          <TableCell className="font-medium">
                            {loan.borrower_name}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">
                              {loan.borrower_industry || "General"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {loan.currency} {(loan.facility_amount / 1e6).toFixed(1)}M
                          </TableCell>
                          <TableCell>
                            <Badge
                              className={
                                loan.status === "GREEN"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : loan.status === "AMBER"
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-red-100 text-red-800"
                              }
                            >
                              {loan.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedLoan(loan.loan_id);
                                loadLoanDetails(loan.loan_id);
                                setActiveTab("kpis");
                              }}
                            >
                              View KPIs
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* KPIs Tab */}
          <TabsContent value="kpis">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Loan List */}
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle className="text-base">Select SLL Loan</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
                  {sllLoans.map((loan) => (
                    <div
                      key={loan.loan_id}
                      onClick={() => {
                        setSelectedLoan(loan.loan_id);
                        loadLoanDetails(loan.loan_id);
                      }}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedLoan === loan.loan_id
                          ? "border-emerald-500 bg-emerald-50"
                          : "hover:bg-slate-50"
                      }`}
                    >
                      <p className="font-medium text-slate-900">{loan.borrower_name}</p>
                      <p className="text-xs text-slate-500">{loan.loan_id}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* KPI Details */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">
                    {selectedLoan ? "KPI Performance" : "Select a loan to view KPIs"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {selectedLoan ? (
                    (() => {
                      const details = loanDetails.get(selectedLoan);
                      if (!details) return <p>Loading...</p>;
                      if (details.loading) {
                        return (
                          <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin" />
                          </div>
                        );
                      }

                      return (
                        <div className="space-y-4">
                          {details.kpis && details.kpis.length > 0 ? (
                            details.kpis.map((kpi) => {
                              const progress = kpi.target_value > 0
                                ? ((kpi.baseline_value - kpi.current_value) /
                                    (kpi.baseline_value - kpi.target_value)) *
                                  100
                                : 0;
                              const typeInfo = KPI_TYPES[kpi.kpi_type] || {
                                color: "bg-slate-100 text-slate-800",
                                label: kpi.kpi_type,
                              };

                              return (
                                <div
                                  key={kpi.kpi_id}
                                  className="p-4 border rounded-lg"
                                >
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                      <Badge className={typeInfo.color}>
                                        {typeInfo.label}
                                      </Badge>
                                      <span className="font-medium">{kpi.kpi_name}</span>
                                    </div>
                                    <Badge className={getVerificationColor(kpi.verification_status)}>
                                      {kpi.verification_status}
                                    </Badge>
                                  </div>

                                  <div className="grid grid-cols-4 gap-2 text-sm mb-3">
                                    <div>
                                      <p className="text-slate-500">Baseline</p>
                                      <p className="font-medium">
                                        {kpi.baseline_value} {kpi.unit}
                                      </p>
                                    </div>
                                    <div>
                                      <p className="text-slate-500">Current</p>
                                      <p className="font-medium">
                                        {kpi.current_value} {kpi.unit}
                                      </p>
                                    </div>
                                    <div>
                                      <p className="text-slate-500">Target</p>
                                      <p className="font-medium">
                                        {kpi.target_value} {kpi.unit}
                                      </p>
                                    </div>
                                    <div>
                                      <p className="text-slate-500">Target Year</p>
                                      <p className="font-medium">{kpi.target_year}</p>
                                    </div>
                                  </div>

                                  <div className="flex items-center gap-2">
                                    <Progress
                                      value={Math.min(Math.max(progress, 0), 100)}
                                      className="flex-1 h-2"
                                    />
                                    <span className="text-sm font-medium w-16 text-right">
                                      {progress.toFixed(0)}% done
                                    </span>
                                  </div>

                                  {kpi.achievement_probability > 0 && (
                                    <div className="mt-2 flex items-center gap-2 text-sm">
                                      {kpi.achievement_probability >= 70 ? (
                                        <TrendingUp className="h-4 w-4 text-emerald-600" />
                                      ) : (
                                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                                      )}
                                      <span className="text-slate-600">
                                        {(kpi.achievement_probability * 100).toFixed(0)}% achievement probability
                                      </span>
                                    </div>
                                  )}
                                </div>
                              );
                            })
                          ) : (
                            <div className="text-center py-8 text-slate-500">
                              <Gauge className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                              <p>No KPIs found for this loan. Data from BigQuery.</p>
                            </div>
                          )}
                        </div>
                      );
                    })()
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Gauge className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>Select a loan from the list to view KPIs</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* SPTs Tab */}
          <TabsContent value="spts">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <CheckCircle className="h-5 w-5 text-emerald-500" />
                  Sustainability Performance Targets
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedLoan ? (
                  (() => {
                    const details = loanDetails.get(selectedLoan);
                    if (!details?.spts || details.spts.length === 0) {
                      return (
                        <div className="text-center py-8 text-slate-500">
                          <p>No SPTs found. Select a loan with SPT data.</p>
                        </div>
                      );
                    }

                    return (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Target</TableHead>
                            <TableHead>Target Value</TableHead>
                            <TableHead>Progress</TableHead>
                            <TableHead>Probability</TableHead>
                            <TableHead>Margin Impact</TableHead>
                            <TableHead>Status</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {details.spts.map((spt) => (
                            <TableRow key={spt.spt_id}>
                              <TableCell className="font-medium max-w-[200px] truncate">
                                {spt.target_description}
                              </TableCell>
                              <TableCell>{spt.target_value}</TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <Progress
                                    value={spt.current_progress}
                                    className="w-20 h-2"
                                  />
                                  <span className="text-sm">
                                    {spt.current_progress.toFixed(0)}%
                                  </span>
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge
                                  className={
                                    spt.achievement_probability >= 0.7
                                      ? "bg-emerald-100 text-emerald-800"
                                      : "bg-amber-100 text-amber-800"
                                  }
                                >
                                  {(spt.achievement_probability * 100).toFixed(0)}%
                                </Badge>
                              </TableCell>
                              <TableCell>
                                {spt.margin_impact_bps > 0
                                  ? `+${spt.margin_impact_bps}`
                                  : spt.margin_impact_bps}{" "}
                                bps
                              </TableCell>
                              <TableCell>
                                <Badge className={getSPTStatusColor(spt.status)}>
                                  {spt.status}
                                </Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    );
                  })()
                ) : (
                  <div className="text-center py-12 text-slate-500">
                    <CheckCircle className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>Select a loan from Overview or KPI tab first</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Margin Tab */}
          <TabsContent value="margin">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <TrendingDown className="h-5 w-5 text-amber-500" />
                  Two-Way Margin Adjustments (per LMA SLLP)
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedLoan ? (
                  (() => {
                    const details = loanDetails.get(selectedLoan);
                    if (!details?.marginAdjustment) {
                      return (
                        <div className="text-center py-8 text-slate-500">
                          <p>No margin adjustment data. Select a loan with SPTs.</p>
                        </div>
                      );
                    }

                    const ma = details.marginAdjustment;
                    return (
                      <div className="space-y-6">
                        <div
                          className={`p-6 rounded-lg border ${
                            ma.adjustment_direction === "step-down"
                              ? "bg-emerald-50 border-emerald-200"
                              : ma.adjustment_direction === "step-up"
                              ? "bg-red-50 border-red-200"
                              : "bg-slate-50 border-slate-200"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-4">
                            <div>
                              <p className="text-sm text-slate-600">Margin Adjustment</p>
                              <p className="text-3xl font-bold">
                                {ma.adjustment_bps > 0 ? "+" : ""}
                                {ma.adjustment_bps} bps
                              </p>
                            </div>
                            <Badge
                              className={
                                ma.adjustment_direction === "step-down"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : ma.adjustment_direction === "step-up"
                                  ? "bg-red-100 text-red-800"
                                  : "bg-slate-100 text-slate-800"
                              }
                            >
                              {ma.adjustment_direction.replace("-", " ").toUpperCase()}
                            </Badge>
                          </div>

                          <div className="grid grid-cols-4 gap-4">
                            <div>
                              <p className="text-sm text-slate-500">SPTs Achieved</p>
                              <p className="text-xl font-bold text-emerald-600">
                                {ma.spts_achieved}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-slate-500">SPTs Not Achieved</p>
                              <p className="text-xl font-bold text-red-600">
                                {ma.spts_not_achieved}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-slate-500">Previous Margin</p>
                              <p className="text-xl font-bold">
                                {ma.previous_margin_bps} bps
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-slate-500">New Margin</p>
                              <p className="text-xl font-bold">
                                {ma.new_margin_bps} bps
                              </p>
                            </div>
                          </div>

                          {ma.two_way_pricing && (
                            <div className="mt-4 flex items-center gap-2">
                              <Badge variant="outline">Two-Way Pricing</Badge>
                              <span className="text-sm text-slate-600">
                                Step-up on miss, step-down on achievement
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })()
                ) : (
                  <div className="text-center py-12 text-slate-500">
                    <TrendingDown className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>Select a loan to view margin adjustment</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
