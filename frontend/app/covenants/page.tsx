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
  Shield,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  Loader2,
  RefreshCw,
  ChevronRight,
  Brain,
  Activity,
} from "lucide-react";
import {
  fetchLoans,
  fetchCovenants,
  fetchBreachPrediction,
  type Loan,
  type Covenant,
  type BreachPrediction,
} from "@/lib/api";
import { SendEmailButton } from "@/components/send-email-button";
import { VoiceCallButton } from "@/components/voice-call-button";
import { SHAPWaterfall } from "@/components/shap-waterfall";

interface CovenantWithLoan extends Covenant {
  loan_id?: string;
  borrower_name?: string;
  trend?: "up" | "down" | "stable";
}

interface LoanCovenantData {
  loan: Loan;
  covenants: Covenant[];
  prediction?: BreachPrediction;
  loading: boolean;
  error?: string;
}

function getStatusFromBuffer(buffer: number | undefined): "GREEN" | "AMBER" | "RED" {
  if (buffer === undefined) return "AMBER";
  if (buffer < 0) return "RED";
  if (buffer < 10) return "AMBER";
  return "GREEN";
}

function formatThreshold(value: number | string | undefined | null, type?: string): string {
  // Handle null, undefined, empty string
  if (value === undefined || value === null || value === "") return "-";
  
  // Parse to number
  const numValue = typeof value === "string" ? parseFloat(value) : value;
  
  // Handle NaN (invalid number)
  if (isNaN(numValue)) return "-";
  
  // Format based on covenant type
  if (type?.includes("ratio") || type?.includes("coverage") || type?.includes("ebitda")) {
    return `${numValue.toFixed(2)}x`;
  }
  if (type?.includes("percent")) {
    return `${numValue.toFixed(1)}%`;
  }
  if (numValue >= 1000000) {
    return `$${(numValue / 1000000).toFixed(1)}M`;
  }
  if (numValue >= 1000) {
    return `$${(numValue / 1000).toFixed(0)}K`;
  }
  return numValue.toFixed(2);
}


export default function CovenantsPage() {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [loanData, setLoanData] = useState<Map<string, LoanCovenantData>>(new Map());
  const [loading, setLoading] = useState(true);
  const [selectedLoan, setSelectedLoan] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("overview");

  // Load all loans on mount
  useEffect(() => {
    async function loadLoans() {
      try {
        setLoading(true);
        const response = await fetchLoans();
        setLoans(response.loans || []);
        
        // Load covenants for first few loans
        const initialLoads = response.loans.slice(0, 5);
        for (const loan of initialLoads) {
          loadLoanCovenants(loan);
        }
      } catch (err) {
        console.error("Failed to load loans:", err);
      } finally {
        setLoading(false);
      }
    }
    loadLoans();
  }, []);

  async function loadLoanCovenants(loan: Loan) {
    const currentData = loanData.get(loan.loan_id);
    if (currentData && currentData.covenants && currentData.covenants.length > 0) return; // Already loaded

    setLoanData((prev) => {
      const next = new Map(prev);
      next.set(loan.loan_id, { loan, covenants: [], loading: true });
      return next;
    });

    try {
      const [covenantResponse, predictionResponse] = await Promise.allSettled([
        fetchCovenants(loan.loan_id),
        fetchBreachPrediction(loan.loan_id),
      ]);

      const covenants =
        covenantResponse.status === "fulfilled"
          ? covenantResponse.value.covenants || []
          : [];
      const prediction =
        predictionResponse.status === "fulfilled"
          ? predictionResponse.value
          : undefined;

      setLoanData((prev) => {
        const next = new Map(prev);
        next.set(loan.loan_id, {
          loan,
          covenants,
          prediction,
          loading: false,
        });
        return next;
      });
    } catch (err) {
      setLoanData((prev) => {
        const next = new Map(prev);
        next.set(loan.loan_id, {
          loan,
          covenants: [],
          loading: false,
          error: "Failed to load covenants",
        });
        return next;
      });
    }
  }

  // Aggregate all covenants for overview
  const allCovenants: CovenantWithLoan[] = Array.from(loanData.values()).flatMap(
    (data) =>
      data.covenants.map((cov) => ({
        ...cov,
        loan_id: data.loan.loan_id,
        borrower_name: data.loan.borrower_name,
      }))
  );

  const statusCounts = {
    GREEN: allCovenants.filter((c) => c.status === "GREEN" || (c.buffer_pct !== undefined && c.buffer_pct >= 10)).length,
    AMBER: allCovenants.filter((c) => c.status === "AMBER" || (c.buffer_pct !== undefined && c.buffer_pct >= 0 && c.buffer_pct < 10)).length,
    RED: allCovenants.filter((c) => c.status === "RED" || (c.buffer_pct !== undefined && c.buffer_pct < 0)).length,
  };

  // Get predictions for breach prediction cards
  const predictions = Array.from(loanData.values())
    .filter((d) => d.prediction)
    .map((d) => ({
      loan_id: d.loan.loan_id,
      borrower: d.loan.borrower_name,
      probability: d.prediction!.breach_probability,
      risk_level: d.prediction!.risk_level,
    }))
    .sort((a, b) => b.probability - a.probability);

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
            <div className="p-3 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg">
              <Shield className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">
                Covenant Monitoring
              </h1>
              <p className="text-slate-500">
                Track covenant compliance across portfolio
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            className="hover:bg-blue-50 transition-colors"
            onClick={() => {
              setLoanData(new Map());
              loans.slice(0, 5).forEach((loan) => loadLoanCovenants(loan));
            }}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-20 h-20 rounded-full bg-gradient-to-br from-slate-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-slate-400 to-slate-500">
                  <Shield className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">Total Covenants</p>
              </div>
              <p className="text-3xl font-bold text-slate-900">
                {allCovenants.length}
              </p>
            </CardContent>
          </Card>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group border-l-4 border-l-emerald-500">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-20 h-20 rounded-full bg-gradient-to-br from-emerald-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-500">
                  <Shield className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">Compliant</p>
              </div>
              <p className="text-3xl font-bold text-emerald-600">
                {statusCounts.GREEN}
              </p>
            </CardContent>
          </Card>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group border-l-4 border-l-amber-500">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-20 h-20 rounded-full bg-gradient-to-br from-amber-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500">
                  <AlertTriangle className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">Warning</p>
              </div>
              <p className="text-3xl font-bold text-amber-600">
                {statusCounts.AMBER}
              </p>
            </CardContent>
          </Card>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group border-l-4 border-l-red-500">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-20 h-20 rounded-full bg-gradient-to-br from-red-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-red-500 to-rose-600">
                  <AlertTriangle className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">Breach</p>
              </div>
              <p className="text-3xl font-bold text-red-600">
                {statusCounts.RED}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs for Overview vs By Loan */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-gradient-to-r from-slate-100 to-slate-50 p-1.5 rounded-xl border border-slate-200 shadow-sm">
            <TabsTrigger 
              value="overview" 
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-500 data-[state=active]:to-emerald-600 data-[state=active]:text-white data-[state=active]:shadow-md rounded-lg px-6 py-2.5 font-medium transition-all duration-300 hover:bg-slate-200/50"
            >
              📊 Portfolio Overview
            </TabsTrigger>
            <TabsTrigger 
              value="by-loan"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-blue-600 data-[state=active]:text-white data-[state=active]:shadow-md rounded-lg px-6 py-2.5 font-medium transition-all duration-300 hover:bg-slate-200/50"
            >
              🏦 By Loan
            </TabsTrigger>
          </TabsList>

          {/* Portfolio Overview Tab */}
          <TabsContent value="overview">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  All Covenants
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Covenant</TableHead>
                      <TableHead>Loan</TableHead>
                      <TableHead>Threshold</TableHead>
                      <TableHead>Actual</TableHead>
                      <TableHead>Buffer</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {allCovenants.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-slate-500 py-8">
                          {Array.from(loanData.values()).some((d) => d.loading)
                            ? "Loading covenants..."
                            : "No covenants found. Connect to API to load data."}
                        </TableCell>
                      </TableRow>
                    ) : (
                      allCovenants.map((cov, idx) => (
                        <TableRow key={`${cov.covenant_id}-${idx}`}>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Shield className="h-4 w-4 text-slate-400" />
                              <span className="font-medium">
                                {cov.name || cov.covenant_name || cov.covenant_type || "Unknown"}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <a
                              href={`/loans/${cov.loan_id}`}
                              className="text-emerald-600 hover:underline"
                            >
                              {cov.loan_id}
                            </a>
                            {cov.borrower_name && (
                              <p className="text-xs text-slate-500">{cov.borrower_name}</p>
                            )}
                          </TableCell>
                          <TableCell>{formatThreshold(cov.threshold, cov.covenant_type)}</TableCell>
                          <TableCell className="font-medium">
                            {formatThreshold(cov.actual, cov.covenant_type)}
                          </TableCell>
                          <TableCell>
                            {cov.buffer_pct != null ? (
                              <span
                                className={`font-medium ${
                                  cov.buffer_pct < 0
                                    ? "text-red-600"
                                    : cov.buffer_pct < 10
                                    ? "text-amber-600"
                                    : "text-emerald-600"
                                }`}
                              >
                                {cov.buffer_pct > 0 ? "+" : ""}
                                {cov.buffer_pct.toFixed(1)}%
                              </span>
                            ) : (
                              "-"
                            )}
                          </TableCell>
                          <TableCell>
                            <StatusBadge
                              status={cov.status || getStatusFromBuffer(cov.buffer_pct)}
                              size="sm"
                            />
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* By Loan Tab */}
          <TabsContent value="by-loan">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Loan List */}
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle className="text-base">Select Loan</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
                    {loans.map((loan) => {
                      const data = loanData.get(loan.loan_id);
                      const isSelected = selectedLoan === loan.loan_id;
                      const isRed = loan.status === "RED";

                      return (
                        <div
                          key={loan.loan_id}
                          onClick={() => {
                            setSelectedLoan(loan.loan_id);
                            loadLoanCovenants(loan);
                          }}
                          className={`relative p-4 rounded-xl border-2 cursor-pointer transition-all duration-300 group overflow-hidden ${
                            isSelected
                              ? "border-emerald-400 bg-gradient-to-br from-emerald-50 to-white shadow-lg shadow-emerald-100/50 scale-[1.02]"
                              : isRed
                                ? "border-red-200 bg-gradient-to-br from-red-50/30 to-white hover:border-red-300 hover:shadow-md hover:shadow-red-100/50"
                                : "border-slate-200 hover:border-slate-300 hover:shadow-md hover:bg-slate-50/50"
                          }`}
                        >
                          {/* Status glow indicator */}
                          <div className={`absolute top-0 right-0 w-16 h-16 rounded-full opacity-30 blur-2xl transition-opacity ${
                            isRed ? "bg-red-400" : loan.status === "AMBER" ? "bg-amber-400" : "bg-emerald-400"
                          } ${isSelected ? "opacity-50" : "opacity-0 group-hover:opacity-30"}`} />
                          
                          <div className="flex items-center justify-between relative z-10">
                            <div className="flex-1 min-w-0">
                              <p className="font-semibold text-slate-800 truncate">
                                {loan.borrower_name}
                              </p>
                              <p className="text-xs text-slate-500 font-mono">{loan.loan_id}</p>
                            </div>
                            <div className="flex items-center gap-3">
                              <StatusBadge status={loan.status} size="sm" />
                              <ChevronRight className={`h-4 w-4 transition-transform ${
                                isSelected ? "text-emerald-500 translate-x-1" : "text-slate-400 group-hover:translate-x-1"
                              }`} />
                            </div>
                          </div>
                          {data && (
                            <div className="mt-2 flex items-center gap-2">
                              <div className={`h-1.5 flex-1 rounded-full overflow-hidden bg-slate-100`}>
                                <div 
                                  className={`h-full transition-all duration-500 ${
                                    isRed ? "bg-gradient-to-r from-red-400 to-red-500" 
                                    : loan.status === "AMBER" ? "bg-gradient-to-r from-amber-400 to-orange-500"
                                    : "bg-gradient-to-r from-emerald-400 to-emerald-500"
                                  }`}
                                  style={{ width: data.loading ? '30%' : '100%' }}
                                />
                              </div>
                              <span className="text-xs text-slate-500 whitespace-nowrap">
                                {data.loading ? "Loading..." : `${data.covenants.length} covenants`}
                              </span>
                            </div>
                          )}
                        </div>
                      );
                    })}
                </CardContent>
              </Card>

              {/* Covenant Details */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">
                    {selectedLoan
                      ? `Covenants for ${selectedLoan}`
                      : "Select a loan to view covenants"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {selectedLoan ? (
                    (() => {
                      const data = loanData.get(selectedLoan);
                      if (!data) return <p>Select a loan</p>;
                      if (data.loading)
                        return (
                          <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin text-emerald-600" />
                          </div>
                        );
                      if (data.covenants.length === 0)
                        return (
                          <p className="text-slate-500 py-8 text-center">
                            No covenants found for this loan
                          </p>
                        );

                      return (
                        <div className="space-y-4">
                          {data.covenants.map((cov, idx) => {
                            const isBreached = (cov.buffer_pct !== undefined && cov.buffer_pct < 0) || cov.status === "RED";
                            const severity = (cov.buffer_pct || 0) < -10 ? "HIGH" : (cov.buffer_pct || 0) < 0 ? "MEDIUM" : "LOW";
                            
                            return (
                            <div
                              key={cov.covenant_id || idx}
                              className={`relative p-5 rounded-xl border-2 transition-all duration-300 group overflow-hidden ${
                                isBreached 
                                  ? "border-red-200 bg-gradient-to-br from-red-50 via-white to-red-50/30 shadow-lg shadow-red-100/50 hover:shadow-xl hover:shadow-red-200/50" 
                                  : cov.status === "AMBER" 
                                    ? "border-amber-200 bg-gradient-to-br from-amber-50/50 via-white to-amber-50/30 hover:shadow-lg hover:shadow-amber-100/50"
                                    : "border-emerald-200 bg-gradient-to-br from-emerald-50/30 via-white to-emerald-50/30 hover:shadow-lg hover:shadow-emerald-100/50"
                              }`}
                            >
                              {/* Animated pulse ring for breached covenants */}
                              {isBreached && (
                                <div className="absolute -top-4 -right-4 w-24 h-24">
                                  <div className="absolute inset-0 rounded-full bg-red-400/20 animate-ping" />
                                  <div className="absolute inset-2 rounded-full bg-red-400/30 animate-pulse" />
                                </div>
                              )}
                              
                              {/* Decorative gradient overlay */}
                              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-slate-100/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-full -translate-y-1/2 translate-x-1/2" />
                              
                              <div className="flex items-center justify-between mb-4 relative z-10">
                                <div className="flex items-center gap-3">
                                  <div className={`p-2.5 rounded-xl ${
                                    isBreached 
                                      ? "bg-gradient-to-br from-red-500 to-red-600 shadow-md shadow-red-200" 
                                      : cov.status === "AMBER"
                                        ? "bg-gradient-to-br from-amber-400 to-orange-500 shadow-md shadow-amber-200"
                                        : "bg-gradient-to-br from-emerald-400 to-emerald-500 shadow-md shadow-emerald-200"
                                  }`}>
                                    <Shield className="h-5 w-5 text-white" />
                                  </div>
                                  <div>
                                    <span className="font-semibold text-slate-800 text-lg">
                                      {cov.name || cov.covenant_name || cov.covenant_type}
                                    </span>
                                    {isBreached && (
                                      <p className="text-xs text-red-500 font-medium animate-pulse">
                                        ⚠️ Requires Immediate Attention
                                      </p>
                                    )}
                                  </div>
                                </div>
                                <div className="flex items-center gap-3">
                                  <StatusBadge
                                    status={cov.status || getStatusFromBuffer(cov.buffer_pct)}
                                  />
                                  {isBreached && (
                                    <div className="flex gap-2">
                                      <SendEmailButton
                                        variant="covenant-breach"
                                        loanId={selectedLoan!}
                                        breachType={cov.name || cov.covenant_name || cov.covenant_type || "Unknown"}
                                        threshold={formatThreshold(cov.threshold, cov.covenant_type)}
                                        actualValue={formatThreshold(cov.actual, cov.covenant_type)}
                                        severity={severity}
                                        size="sm"
                                        className="bg-gradient-to-r from-rose-500 to-red-600 text-white border-0 hover:from-rose-600 hover:to-red-700 shadow-md hover:shadow-lg transition-all"
                                      />
                                      <VoiceCallButton
                                        variant="covenant-breach"
                                        loanId={selectedLoan!}
                                        breachType={cov.name || cov.covenant_name || cov.covenant_type || "Unknown"}
                                        threshold={formatThreshold(cov.threshold, cov.covenant_type)}
                                        actualValue={formatThreshold(cov.actual, cov.covenant_type)}
                                        severity={severity}
                                        size="sm"
                                        className="bg-gradient-to-r from-slate-700 to-slate-800 text-white border-0 hover:from-slate-800 hover:to-slate-900 shadow-md hover:shadow-lg transition-all"
                                      />
                                    </div>
                                  )}
                                </div>
                              </div>
                              
                              {/* Metrics Grid with enhanced styling */}
                              <div className="grid grid-cols-3 gap-4 relative z-10">
                                <div className="p-3 rounded-lg bg-white/80 backdrop-blur-sm border border-slate-100 shadow-sm">
                                  <p className="text-xs text-slate-500 font-medium mb-1">Threshold</p>
                                  <p className="font-bold text-slate-800 text-lg">
                                    {formatThreshold(cov.threshold, cov.covenant_type)}
                                  </p>
                                </div>
                                <div className="p-3 rounded-lg bg-white/80 backdrop-blur-sm border border-slate-100 shadow-sm">
                                  <p className="text-xs text-slate-500 font-medium mb-1">Actual</p>
                                  <p className={`font-bold text-lg ${isBreached ? "text-red-600" : "text-slate-800"}`}>
                                    {formatThreshold(cov.actual, cov.covenant_type)}
                                  </p>
                                </div>
                                <div className="p-3 rounded-lg bg-white/80 backdrop-blur-sm border border-slate-100 shadow-sm">
                                  <p className="text-xs text-slate-500 font-medium mb-1">Buffer</p>
                                  <p
                                    className={`font-medium ${
                                      (cov.buffer_pct || 0) < 0
                                        ? "text-red-600"
                                        : (cov.buffer_pct || 0) < 10
                                        ? "text-amber-600"
                                        : "text-emerald-600"
                                    }`}
                                  >
                                    {cov.buffer_pct != null
                                      ? `${cov.buffer_pct > 0 ? "+" : ""}${cov.buffer_pct.toFixed(1)}%`
                                      : "-"}
                                  </p>
                                </div>
                              </div>
                              {cov.buffer_pct != null && (
                                <div className="mt-3">
                                  <Progress
                                    value={Math.min(Math.max(cov.buffer_pct + 50, 0), 100)}
                                    className="h-2"
                                  />
                                </div>
                              )}
                            </div>
                          );})}

                          {/* ML Prediction for this loan */}
                          {data.prediction && (
                            <div className="mt-6 p-4 bg-slate-50 rounded-lg border">
                              <div className="flex items-center gap-2 mb-3">
                                <Brain className="h-5 w-5 text-purple-600" />
                                <span className="font-medium">ML Breach Prediction</span>
                              </div>
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <p className="text-sm text-slate-500">90-Day Probability</p>
                                  <p
                                    className={`text-2xl font-bold ${
                                      data.prediction.breach_probability > 50
                                        ? "text-red-600"
                                        : data.prediction.breach_probability > 25
                                        ? "text-amber-600"
                                        : "text-emerald-600"
                                    }`}
                                  >
                                    {(data.prediction.breach_probability * 100).toFixed(0)}%
                                  </p>
                                </div>
                                <div>
                                  <p className="text-sm text-slate-500">Risk Level</p>
                                  <Badge
                                    variant={
                                      data.prediction.risk_level === "HIGH"
                                        ? "destructive"
                                        : data.prediction.risk_level === "MEDIUM"
                                        ? "secondary"
                                        : "outline"
                                    }
                                  >
                                    {data.prediction.risk_level}
                                   </Badge>
                                </div>
                              </div>
                              {data.prediction.top_risk_factors && (
                                <div className="mt-3">
                                  <p className="text-xs text-slate-500 mb-1">Top Risk Factors:</p>
                                  <div className="flex flex-wrap gap-1">
                                    {data.prediction.top_risk_factors.slice(0, 3).map((f, i) => (
                                      <Badge key={i} variant="outline" className="text-xs">
                                        {f.factor}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          {/* SHAP Explanation - AI Explainability */}
                          {data.prediction && selectedLoan && (
                            <SHAPWaterfall 
                              loanId={selectedLoan}
                              className="mt-6"
                            />
                          )}
                        </div>
                      );
                    })()
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Shield className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>Select a loan from the list to view covenant details</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
