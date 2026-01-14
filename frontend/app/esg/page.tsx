"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { StatusBadge } from "@/components/status-badge";
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
  Leaf,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Loader2,
  RefreshCw,
  ChevronRight,
  Flame,
  Search,
  XCircle,
} from "lucide-react";
import {
  fetchLoans,
  fetchESGKpis,
  fetchSPTs,
  fetchCarbonStatus,
  calculateCarbonEmissions,
  type Loan,
  type ESGKpi,
  type SPT,
} from "@/lib/api";

interface LoanESGData {
  loan: Loan;
  kpis: ESGKpi[];
  spts: SPT[];
  marginAdjustment?: number;
  greenwashingRisk?: string;
  loading: boolean;
  error?: string;
}

function getProgressColor(progress: number): string {
  if (progress >= 80) return "bg-emerald-500";
  if (progress >= 50) return "bg-amber-500";
  return "bg-red-500";
}

function getRiskBadgeClass(risk: string): string {
  switch (risk?.toUpperCase()) {
    case "LOW":
      return "bg-emerald-100 text-emerald-800 border-emerald-200";
    case "MEDIUM":
      return "bg-amber-100 text-amber-800 border-amber-200";
    case "HIGH":
      return "bg-red-100 text-red-800 border-red-200";
    default:
      return "bg-slate-100 text-slate-800 border-slate-200";
  }
}

export default function ESGPage() {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [loanData, setLoanData] = useState<Map<string, LoanESGData>>(new Map());
  const [loading, setLoading] = useState(true);
  const [selectedLoan, setSelectedLoan] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [carbonAvailable, setCarbonAvailable] = useState(false);

  // Carbon calculator state
  const [carbonForm, setCarbonForm] = useState({
    electricity_kwh: 0,
    fuel_liters: 0,
    travel_km: 0,
    country_code: "US",
  });
  const [carbonResult, setCarbonResult] = useState<{
    total_co2e_kg: number;
    breakdown: Record<string, number>;
  } | null>(null);
  const [carbonLoading, setCarbonLoading] = useState(false);

  // Load SLL loans on mount
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [loansResponse, carbonStatus] = await Promise.all([
          fetchLoans(),
          fetchCarbonStatus().catch(() => ({ available: false })),
        ]);

        // Filter for SLL loans
        const sllLoans = loansResponse.loans.filter((l) => l.is_sll);
        setLoans(sllLoans.length > 0 ? sllLoans : loansResponse.loans.slice(0, 10));
        setCarbonAvailable(carbonStatus.available);

        // Load ESG data for first few loans
        for (const loan of sllLoans.slice(0, 5)) {
          loadLoanESG(loan);
        }
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  async function loadLoanESG(loan: Loan) {
    const currentData = loanData.get(loan.loan_id);
    if (currentData && currentData.kpis && currentData.kpis.length > 0) return;

    setLoanData((prev) => {
      const next = new Map(prev);
      next.set(loan.loan_id, { loan, kpis: [], spts: [], loading: true });
      return next;
    });

    try {
      const [kpisResponse, sptsResponse] = await Promise.allSettled([
        fetchESGKpis(loan.loan_id),
        fetchSPTs(loan.loan_id),
      ]);

      const kpis =
        kpisResponse.status === "fulfilled" ? kpisResponse.value.kpis || [] : [];
      const spts =
        sptsResponse.status === "fulfilled" ? sptsResponse.value.spts || [] : [];
      const marginAdjustment =
        sptsResponse.status === "fulfilled"
          ? sptsResponse.value.margin_adjustment
          : undefined;

      // Calculate greenwashing risk based on SPT achievement
      const achievedCount = spts.filter((s) => s.achieved).length;
      const greenwashingRisk =
        spts.length === 0
          ? "UNKNOWN"
          : achievedCount === spts.length
          ? "LOW"
          : achievedCount > spts.length / 2
          ? "MEDIUM"
          : "HIGH";

      setLoanData((prev) => {
        const next = new Map(prev);
        next.set(loan.loan_id, {
          loan,
          kpis,
          spts,
          marginAdjustment,
          greenwashingRisk,
          loading: false,
        });
        return next;
      });
    } catch {
      setLoanData((prev) => {
        const next = new Map(prev);
        next.set(loan.loan_id, {
          loan,
          kpis: [],
          spts: [],
          loading: false,
          error: "Failed to load ESG data",
        });
        return next;
      });
    }
  }

  async function handleCarbonCalculate() {
    if (!selectedLoan) return;
    setCarbonLoading(true);
    setCarbonResult(null);

    try {
      const result = await calculateCarbonEmissions(selectedLoan, carbonForm);
      setCarbonResult({
        total_co2e_kg: result.total_co2e_kg,
        breakdown: result.breakdown,
      });
    } catch (err) {
      console.error("Carbon calculation failed:", err);
    } finally {
      setCarbonLoading(false);
    }
  }

  // Aggregate stats
  const allKpis = Array.from(loanData.values()).flatMap((d) => d.kpis);
  const allSpts = Array.from(loanData.values()).flatMap((d) => d.spts);

  const stats = {
    sllLoans: loans.filter((l) => l.is_sll).length || loans.length,
    sptAchieved: allSpts.filter((s) => s.achieved).length,
    sptTotal: allSpts.length,
    onTrackKpis: allKpis.filter((k) => k.on_track || k.progress_pct >= 70).length,
    atRiskKpis: allKpis.filter((k) => !k.on_track && k.progress_pct < 70).length,
    avgProgress:
      allKpis.length > 0
        ? allKpis.reduce((sum, k) => sum + k.progress_pct, 0) / allKpis.length
        : 0,
  };

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
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg">
              <Leaf className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">ESG Compliance</h1>
              <p className="text-slate-500">
                Sustainability-linked loan monitoring
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="hover:bg-blue-50 transition-colors"
              onClick={() => {
                setLoanData(new Map());
                loans.slice(0, 5).forEach((loan) => loadLoanESG(loan));
              }}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button
              className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 shadow-lg"
              onClick={() => (window.location.href = "/greenwashing")}
            >
              <Search className="h-4 w-4 mr-2" />
              Greenwashing Detector
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-20 h-20 rounded-full bg-gradient-to-br from-emerald-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-500">
                  <Leaf className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">SLL Loans</p>
              </div>
              <p className="text-3xl font-bold text-slate-900">{stats.sllLoans}</p>
            </CardContent>
          </Card>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-20 h-20 rounded-full bg-gradient-to-br from-emerald-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600">
                  <CheckCircle className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">SPT Achieved</p>
              </div>
              <p className="text-3xl font-bold text-emerald-600">
                {stats.sptAchieved}
                <span className="text-lg text-slate-500 font-normal">
                  /{stats.sptTotal}
                </span>
              </p>
            </CardContent>
          </Card>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-20 h-20 rounded-full bg-gradient-to-br from-blue-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600">
                  <TrendingUp className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">Avg KPI Progress</p>
              </div>
              <p className="text-3xl font-bold text-blue-600">
                {stats.avgProgress.toFixed(0)}%
              </p>
            </CardContent>
          </Card>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-20 h-20 rounded-full bg-gradient-to-br from-amber-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500">
                  <AlertTriangle className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">At Risk KPIs</p>
              </div>
              <p className="text-3xl font-bold text-amber-600">{stats.atRiskKpis}</p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-gradient-to-r from-slate-100 to-slate-50 p-1.5 rounded-xl border border-slate-200 shadow-sm">
            <TabsTrigger 
              value="overview"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-500 data-[state=active]:to-teal-600 data-[state=active]:text-white data-[state=active]:shadow-md rounded-lg px-6 py-2.5 font-medium transition-all duration-300 hover:bg-slate-200/50"
            >
              🌍 Portfolio Overview
            </TabsTrigger>
            <TabsTrigger 
              value="by-loan"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-blue-600 data-[state=active]:text-white data-[state=active]:shadow-md rounded-lg px-6 py-2.5 font-medium transition-all duration-300 hover:bg-slate-200/50"
            >
              🏦 By Loan
            </TabsTrigger>
            <TabsTrigger 
              value="carbon"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-red-600 data-[state=active]:text-white data-[state=active]:shadow-md rounded-lg px-6 py-2.5 font-medium transition-all duration-300 hover:bg-slate-200/50"
            >
              🔥 Carbon Tracking
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="space-y-6">
              {Array.from(loanData.values()).map((data) => (
                <Card key={data.loan.loan_id}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">
                          {data.loan.borrower_name}
                        </CardTitle>
                        <p className="text-sm text-slate-500">{data.loan.loan_id}</p>
                      </div>
                      <div className="flex items-center gap-4">
                        {data.marginAdjustment !== undefined && (
                          <div className="text-right">
                            <p className="text-xs text-slate-500">Margin Adjustment</p>
                            <p
                              className={`font-semibold ${
                                data.marginAdjustment < 0
                                  ? "text-emerald-600"
                                  : data.marginAdjustment > 0
                                  ? "text-red-600"
                                  : "text-slate-600"
                              }`}
                            >
                              {data.marginAdjustment > 0 ? "+" : ""}
                              {data.marginAdjustment} bps
                            </p>
                          </div>
                        )}
                        <Badge className={getRiskBadgeClass(data.greenwashingRisk || "")}>
                          {data.greenwashingRisk} RISK
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {data.loading ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin" />
                      </div>
                    ) : data.kpis.length === 0 ? (
                      <p className="text-slate-500 py-4 text-center">
                        No ESG KPIs found for this loan
                      </p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {data.kpis.map((kpi, idx) => (
                          <div key={kpi.kpi_id || idx} className="p-4 bg-slate-50 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <p className="font-medium text-slate-900">
                                {kpi.name || kpi.kpi_name}
                              </p>
                              <StatusBadge
                                status={
                                  kpi.on_track || kpi.progress_pct >= 70
                                    ? "GREEN"
                                    : kpi.progress_pct >= 40
                                    ? "AMBER"
                                    : "RED"
                                }
                                size="sm"
                              />
                            </div>
                            <div className="mb-2">
                              <div className="flex justify-between text-xs text-slate-500 mb-1">
                                <span>Progress: {kpi.progress_pct.toFixed(0)}%</span>
                                <span>
                                  Target: {(kpi.target_value || kpi.target)?.toLocaleString()}
                                </span>
                              </div>
                              <div className="w-full bg-slate-200 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full ${getProgressColor(
                                    kpi.progress_pct
                                  )}`}
                                  style={{
                                    width: `${Math.min(kpi.progress_pct, 100)}%`,
                                  }}
                                />
                              </div>
                            </div>
                            <div className="flex justify-between text-xs text-slate-500">
                              <span>Baseline: {kpi.baseline?.toLocaleString()}</span>
                              <span>
                                Current:{" "}
                                {(kpi.current_value || kpi.current)?.toLocaleString()}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}

              {loanData.size === 0 && (
                <Card>
                  <CardContent className="py-12 text-center text-slate-500">
                    <Leaf className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>No ESG data loaded. Refresh to load from API.</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* By Loan Tab */}
          <TabsContent value="by-loan">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Loan List */}
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle className="text-base">SLL Loans</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
                  {loans.map((loan) => {
                    const data = loanData.get(loan.loan_id);
                    const isSelected = selectedLoan === loan.loan_id;

                    return (
                      <div
                        key={loan.loan_id}
                        onClick={() => {
                          setSelectedLoan(loan.loan_id);
                          loadLoanESG(loan);
                        }}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          isSelected
                            ? "border-emerald-500 bg-emerald-50"
                            : "hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-slate-900">
                              {loan.borrower_name}
                            </p>
                            <p className="text-xs text-slate-500">{loan.loan_id}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            {loan.is_sll && (
                              <Badge variant="outline" className="text-emerald-600">
                                SLL
                              </Badge>
                            )}
                            <ChevronRight className="h-4 w-4 text-slate-400" />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>

              {/* ESG Details */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">
                    {selectedLoan
                      ? `ESG Details - ${selectedLoan}`
                      : "Select a loan to view ESG details"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {selectedLoan ? (
                    (() => {
                      const data = loanData.get(selectedLoan);
                      if (!data) return <p>Loading...</p>;
                      if (data.loading)
                        return (
                          <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin" />
                          </div>
                        );

                      return (
                        <div className="space-y-6">
                          {/* SPTs Section */}
                          <div>
                            <h4 className="font-medium mb-3">
                              Sustainability Performance Targets
                            </h4>
                            {data.spts.length === 0 ? (
                              <p className="text-sm text-slate-500">No SPTs defined</p>
                            ) : (
                              <div className="space-y-3">
                                {data.spts.map((spt, idx) => (
                                  <div
                                    key={spt.spt_id || idx}
                                    className={`p-3 rounded-lg border ${
                                      spt.achieved
                                        ? "bg-emerald-50 border-emerald-200"
                                        : "bg-red-50 border-red-200"
                                    }`}
                                  >
                                    <div className="flex items-center justify-between">
                                      <div className="flex items-center gap-2">
                                        {spt.achieved ? (
                                          <CheckCircle className="h-4 w-4 text-emerald-600" />
                                        ) : (
                                          <XCircle className="h-4 w-4 text-red-600" />
                                        )}
                                        <span className="font-medium">{spt.name}</span>
                                      </div>
                                      <Badge
                                        variant={spt.achieved ? "outline" : "destructive"}
                                      >
                                        {spt.achieved ? "ACHIEVED" : "MISSED"}
                                      </Badge>
                                    </div>
                                    <div className="flex justify-between text-sm mt-2 text-slate-600">
                                      <span>Target: {spt.target_value}</span>
                                      {spt.actual_value !== undefined && (
                                        <span>Actual: {spt.actual_value}</span>
                                      )}
                                      {spt.variance_pct !== undefined && (
                                        <span
                                          className={
                                            spt.variance_pct < 0
                                              ? "text-red-600"
                                              : "text-emerald-600"
                                          }
                                        >
                                          {spt.variance_pct > 0 ? "+" : ""}
                                          {spt.variance_pct.toFixed(1)}%
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* KPIs Section */}
                          <div>
                            <h4 className="font-medium mb-3">ESG Key Performance Indicators</h4>
                            {data.kpis.length === 0 ? (
                              <p className="text-sm text-slate-500">No KPIs tracked</p>
                            ) : (
                              <Table>
                                <TableHeader>
                                  <TableRow>
                                    <TableHead>KPI</TableHead>
                                    <TableHead>Baseline</TableHead>
                                    <TableHead>Current</TableHead>
                                    <TableHead>Target</TableHead>
                                    <TableHead>Progress</TableHead>
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {data.kpis.map((kpi, idx) => (
                                    <TableRow key={kpi.kpi_id || idx}>
                                      <TableCell className="font-medium">
                                        {kpi.name || kpi.kpi_name}
                                      </TableCell>
                                      <TableCell>
                                        {kpi.baseline?.toLocaleString()}
                                        {kpi.unit && ` ${kpi.unit}`}
                                      </TableCell>
                                      <TableCell>
                                        {(kpi.current_value || kpi.current)?.toLocaleString()}
                                        {kpi.unit && ` ${kpi.unit}`}
                                      </TableCell>
                                      <TableCell>
                                        {(kpi.target_value || kpi.target)?.toLocaleString()}
                                        {kpi.unit && ` ${kpi.unit}`}
                                      </TableCell>
                                      <TableCell>
                                        <div className="flex items-center gap-2">
                                          <Progress
                                            value={Math.min(kpi.progress_pct, 100)}
                                            className="h-2 w-16"
                                          />
                                          <span className="text-sm">
                                            {kpi.progress_pct.toFixed(0)}%
                                          </span>
                                        </div>
                                      </TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            )}
                          </div>
                        </div>
                      );
                    })()
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Leaf className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>Select a loan from the list to view ESG details</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Carbon Tracking Tab */}
          <TabsContent value="carbon">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Flame className="h-5 w-5 text-orange-500" />
                    Carbon Emissions Calculator
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Select Loan
                    </label>
                    <select
                      value={selectedLoan || ""}
                      onChange={(e) => setSelectedLoan(e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    >
                      <option value="">Select a loan...</option>
                      {loans.map((loan) => (
                        <option key={loan.loan_id} value={loan.loan_id}>
                          {loan.borrower_name} ({loan.loan_id})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Electricity (kWh/year)
                      </label>
                      <input
                        type="number"
                        value={carbonForm.electricity_kwh}
                        onChange={(e) =>
                          setCarbonForm((p) => ({
                            ...p,
                            electricity_kwh: parseFloat(e.target.value) || 0,
                          }))
                        }
                        className="w-full px-3 py-2 border rounded-lg"
                        placeholder="e.g., 100000"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Fuel (liters/year)
                      </label>
                      <input
                        type="number"
                        value={carbonForm.fuel_liters}
                        onChange={(e) =>
                          setCarbonForm((p) => ({
                            ...p,
                            fuel_liters: parseFloat(e.target.value) || 0,
                          }))
                        }
                        className="w-full px-3 py-2 border rounded-lg"
                        placeholder="e.g., 5000"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Travel (km/year)
                      </label>
                      <input
                        type="number"
                        value={carbonForm.travel_km}
                        onChange={(e) =>
                          setCarbonForm((p) => ({
                            ...p,
                            travel_km: parseFloat(e.target.value) || 0,
                          }))
                        }
                        className="w-full px-3 py-2 border rounded-lg"
                        placeholder="e.g., 50000"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Country
                      </label>
                      <select
                        value={carbonForm.country_code}
                        onChange={(e) =>
                          setCarbonForm((p) => ({ ...p, country_code: e.target.value }))
                        }
                        className="w-full px-3 py-2 border rounded-lg"
                      >
                        <option value="US">United States</option>
                        <option value="GB">United Kingdom</option>
                        <option value="DE">Germany</option>
                        <option value="FR">France</option>
                        <option value="JP">Japan</option>
                        <option value="CN">China</option>
                        <option value="IN">India</option>
                      </select>
                    </div>
                  </div>

                  <Button
                    onClick={handleCarbonCalculate}
                    disabled={!selectedLoan || carbonLoading || !carbonAvailable}
                    className="w-full bg-orange-600 hover:bg-orange-700"
                  >
                    {carbonLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Calculating...
                      </>
                    ) : (
                      <>
                        <Flame className="h-4 w-4 mr-2" />
                        Calculate Emissions
                      </>
                    )}
                  </Button>

                  {!carbonAvailable && (
                    <p className="text-sm text-amber-600">
                      ⚠️ Climatiq API not configured. Set CLIMATIQ_API_KEY to enable.
                    </p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Results</CardTitle>
                </CardHeader>
                <CardContent>
                  {carbonResult ? (
                    <div className="space-y-4">
                      <div className="text-center py-6 bg-orange-50 rounded-lg">
                        <p className="text-sm text-orange-600 mb-1">Total CO₂ Equivalent</p>
                        <p className="text-4xl font-bold text-orange-700">
                          {(carbonResult.total_co2e_kg / 1000).toFixed(2)}
                        </p>
                        <p className="text-sm text-orange-600">tonnes/year</p>
                      </div>

                      {carbonResult.breakdown && (
                        <div className="space-y-2">
                          <h4 className="font-medium">Breakdown by Source</h4>
                          {Object.entries(carbonResult.breakdown).map(([source, value]) => (
                            <div
                              key={source}
                              className="flex justify-between p-2 bg-slate-50 rounded"
                            >
                              <span className="capitalize">{source.replace("_", " ")}</span>
                              <span className="font-medium">
                                {((value as number) / 1000).toFixed(2)} t
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Flame className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>Enter values and calculate to see emissions</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Climatiq Info */}
            <Card className="mt-6">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <Flame className="h-8 w-8 text-orange-500" />
                  <div>
                    <h3 className="font-semibold">Powered by Climatiq API</h3>
                    <p className="text-sm text-slate-500">
                      Accurate carbon emission factors from EPA, DEFRA, and other sources
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
