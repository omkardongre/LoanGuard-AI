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

function formatThreshold(value: number | string | undefined, type?: string): string {
  if (value === undefined) return "-";
  const numValue = typeof value === "string" ? parseFloat(value) : value;
  
  if (type?.includes("ratio") || type?.includes("coverage")) {
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
  return numValue.toString();
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
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              Covenant Monitoring
            </h1>
            <p className="text-slate-500">
              Track covenant compliance across portfolio
            </p>
          </div>
          <Button
            variant="outline"
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
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">Total Covenants</p>
              <p className="text-2xl font-bold text-slate-900">
                {allCovenants.length}
              </p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-emerald-500">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">Compliant</p>
              <p className="text-2xl font-bold text-emerald-600">
                {statusCounts.GREEN}
              </p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-amber-500">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">Warning</p>
              <p className="text-2xl font-bold text-amber-600">
                {statusCounts.AMBER}
              </p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-red-500">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">Breach</p>
              <p className="text-2xl font-bold text-red-600">
                {statusCounts.RED}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs for Overview vs By Loan */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">Portfolio Overview</TabsTrigger>
            <TabsTrigger value="by-loan">By Loan</TabsTrigger>
            <TabsTrigger value="predictions">ML Predictions</TabsTrigger>
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
                            {cov.buffer_pct !== undefined ? (
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

                    return (
                      <div
                        key={loan.loan_id}
                        onClick={() => {
                          setSelectedLoan(loan.loan_id);
                          loadLoanCovenants(loan);
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
                            <StatusBadge status={loan.status} size="sm" />
                            <ChevronRight className="h-4 w-4 text-slate-400" />
                          </div>
                        </div>
                        {data && (
                          <p className="text-xs text-slate-500 mt-1">
                            {data.loading
                              ? "Loading..."
                              : `${data.covenants.length} covenants`}
                          </p>
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
                              className="p-4 border rounded-lg"
                            >
                              <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                  <Shield className="h-4 w-4 text-slate-400" />
                                  <span className="font-medium">
                                    {cov.name || cov.covenant_name || cov.covenant_type}
                                  </span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <StatusBadge
                                    status={cov.status || getStatusFromBuffer(cov.buffer_pct)}
                                  />
                                  {isBreached && (
                                    <>
                                      <SendEmailButton
                                        variant="covenant-breach"
                                        loanId={selectedLoan!}
                                        breachType={cov.name || cov.covenant_name || cov.covenant_type || "Unknown"}
                                        threshold={formatThreshold(cov.threshold, cov.covenant_type)}
                                        actualValue={formatThreshold(cov.actual, cov.covenant_type)}
                                        severity={severity}
                                        size="sm"
                                      />
                                      <VoiceCallButton
                                        variant="covenant-breach"
                                        loanId={selectedLoan!}
                                        breachType={cov.name || cov.covenant_name || cov.covenant_type || "Unknown"}
                                        threshold={formatThreshold(cov.threshold, cov.covenant_type)}
                                        actualValue={formatThreshold(cov.actual, cov.covenant_type)}
                                        severity={severity}
                                        size="sm"
                                      />
                                    </>
                                  )}
                                </div>
                              </div>
                              <div className="grid grid-cols-3 gap-4 text-sm">
                                <div>
                                  <p className="text-slate-500">Threshold</p>
                                  <p className="font-medium">
                                    {formatThreshold(cov.threshold, cov.covenant_type)}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-slate-500">Actual</p>
                                  <p className="font-medium">
                                    {formatThreshold(cov.actual, cov.covenant_type)}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-slate-500">Buffer</p>
                                  <p
                                    className={`font-medium ${
                                      (cov.buffer_pct || 0) < 0
                                        ? "text-red-600"
                                        : (cov.buffer_pct || 0) < 10
                                        ? "text-amber-600"
                                        : "text-emerald-600"
                                    }`}
                                  >
                                    {cov.buffer_pct !== undefined
                                      ? `${cov.buffer_pct > 0 ? "+" : ""}${cov.buffer_pct.toFixed(1)}%`
                                      : "-"}
                                  </p>
                                </div>
                              </div>
                              {cov.buffer_pct !== undefined && (
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

          {/* ML Predictions Tab */}
          <TabsContent value="predictions">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-purple-600" />
                  ML Breach Predictions
                </CardTitle>
              </CardHeader>
              <CardContent>
                {predictions.length === 0 ? (
                  <p className="text-slate-500 text-center py-8">
                    Loading predictions... Select loans in the "By Loan" tab to load prediction data.
                  </p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {predictions.map((pred) => (
                      <div
                        key={pred.loan_id}
                        className={`p-4 rounded-lg border ${
                          pred.probability > 0.5
                            ? "bg-red-50 border-red-200"
                            : pred.probability > 0.25
                            ? "bg-amber-50 border-amber-200"
                            : "bg-emerald-50 border-emerald-200"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <a
                            href={`/loans/${pred.loan_id}`}
                            className={`font-medium hover:underline ${
                              pred.probability > 0.5
                                ? "text-red-800"
                                : pred.probability > 0.25
                                ? "text-amber-800"
                                : "text-emerald-800"
                            }`}
                          >
                            {pred.loan_id}
                          </a>
                          <Badge
                            variant={
                              pred.risk_level === "HIGH"
                                ? "destructive"
                                : pred.risk_level === "MEDIUM"
                                ? "secondary"
                                : "outline"
                            }
                          >
                            {pred.risk_level}
                          </Badge>
                        </div>
                        <p
                          className={`text-2xl font-bold ${
                            pred.probability > 0.5
                              ? "text-red-700"
                              : pred.probability > 0.25
                              ? "text-amber-700"
                              : "text-emerald-700"
                          }`}
                        >
                          {(pred.probability * 100).toFixed(0)}%
                        </p>
                        <p
                          className={`text-xs ${
                            pred.probability > 0.5
                              ? "text-red-600"
                              : pred.probability > 0.25
                              ? "text-amber-600"
                              : "text-emerald-600"
                          }`}
                        >
                          Breach probability (90 days)
                        </p>
                        <p className="text-xs text-slate-500 mt-1">{pred.borrower}</p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Model Info */}
            <Card className="mt-6">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <Activity className="h-8 w-8 text-purple-600" />
                  <div>
                    <h3 className="font-semibold">LightGBM Breach Predictor</h3>
                    <p className="text-sm text-slate-500">
                      Trained on 720,966 real Lending Club loans • SHAP Explainability
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
