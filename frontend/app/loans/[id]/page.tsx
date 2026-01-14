"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
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
  ArrowLeft,
  Shield,
  Leaf,
  Brain,
  Activity,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Loader2,
  Calculator,
  FileText,
  RefreshCw,
  DollarSign,
  Banknote,
  Clock,
  CheckCircle2,
} from "lucide-react";
import {
  fetchLoan,
  fetchCovenants,
  fetchESGKpis,
  fetchBreachPrediction,
  fetchPredictionExplanation,
  fetchLoanVelocity,
  fetchLoanCureOptions,
  calculateCure,
  downloadLoanPdfReport,
  triggerPdfDownload,
  fetchLGD,
  type Loan,
  type Covenant,
  type ESGKpi,
  type BreachPrediction,
  type SHAPExplanation,
  type RiskVelocity,
  type CureResult,
  type LGDPrediction,
} from "@/lib/api";
import { LGDCard } from "@/components/lgd-card";
import { PrepaymentCard } from "@/components/prepayment-card";
import { SHAPWaterfall } from "@/components/shap-waterfall";
import { ESGRiskCard } from "@/components/esg-risk-card";
import { StressTestCard } from "@/components/stress-test-card";
import { ClimateRiskCard } from "@/components/climate-risk-card";

function formatCurrency(amount: number, currency: string = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(amount);
}

export default function LoanDetailPage() {
  const params = useParams();
  const loanId = params.id as string;

  const [loan, setLoan] = useState<Loan | null>(null);
  const [covenants, setCovenants] = useState<Covenant[]>([]);
  const [kpis, setKpis] = useState<ESGKpi[]>([]);
  const [prediction, setPrediction] = useState<BreachPrediction | null>(null);
  const [explanation, setExplanation] = useState<SHAPExplanation | null>(null);
  const [velocity, setVelocity] = useState<RiskVelocity | null>(null);
  const [cureOptions, setCureOptions] = useState<CureResult | null>(null);
  const [lgdData, setLgdData] = useState<LGDPrediction | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  // Cure calculator state
  const [cureForm, setCureForm] = useState({
    covenant_type: "debt_to_ebitda",
    current_value: 4.5,
    threshold: 4.0,
    total_debt: 100000000,
    ebitda: 25000000,
  });
  const [cureLoading, setCureLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);

  useEffect(() => {
    async function loadLoanData() {
      if (!loanId) return;

      try {
        setLoading(true);

        // Load all data in parallel
        const [
          loanData,
          covenantData,
          kpiData,
          predictionData,
          velocityData,
          lgdResult,
        ] = await Promise.allSettled([
          fetchLoan(loanId),
          fetchCovenants(loanId),
          fetchESGKpis(loanId),
          fetchBreachPrediction(loanId),
          fetchLoanVelocity(loanId),
          fetchLGD(loanId),
        ]);

        if (loanData.status === "fulfilled") {
          setLoan(loanData.value);
          // Use covenants from loan response (which works), fallback to fetchCovenants
          // API may return covenants embedded in loan response
          const loanWithCovenants = loanData.value as { covenants?: Covenant[] };
          if (loanWithCovenants.covenants && loanWithCovenants.covenants.length > 0) {
            setCovenants(loanWithCovenants.covenants);
          }
        }

        // Only use fetchCovenants if loan didn't have covenants embedded
        if (covenantData.status === "fulfilled" && covenants.length === 0) {
          setCovenants(covenantData.value.covenants || []);
        }
        if (kpiData.status === "fulfilled") setKpis(kpiData.value.kpis || []);
        if (predictionData.status === "fulfilled")
          setPrediction(predictionData.value);
        if (velocityData.status === "fulfilled") setVelocity(velocityData.value);
        if (lgdResult.status === "fulfilled") setLgdData(lgdResult.value);

        // Load SHAP explanation separately if prediction available
        if (predictionData.status === "fulfilled") {
          const shapData = await fetchPredictionExplanation(loanId).catch(() => null);
          if (shapData) setExplanation(shapData);
        }
      } catch (err) {
        console.error("Failed to load loan data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadLoanData();
  }, [loanId]);

  async function handleCalculateCure() {
    setCureLoading(true);
    try {
      const result = await calculateCure(loanId, cureForm);
      setCureOptions(result);
    } catch (err) {
      console.error("Cure calculation failed:", err);
    } finally {
      setCureLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 min-w-0 overflow-x-hidden p-8 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
        </main>
      </div>
    );
  }

  if (!loan) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 min-w-0 overflow-x-hidden p-4 md:p-6 lg:p-8">
          <div className="text-center py-12">
            <p className="text-slate-500">Loan not found</p>
            <Button variant="outline" onClick={() => window.history.back()}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 min-w-0 overflow-x-hidden p-4 md:p-6 lg:p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => window.history.back()}
              className="mb-2"
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
            <h1 className="text-2xl font-bold text-slate-900">
              {loan.borrower_name}
            </h1>
            <div className="flex items-center gap-3 mt-1">
              <p className="text-slate-500">{loan.loan_id}</p>
              <StatusBadge status={loan.status} />
              {loan.is_sll && (
                <Badge variant="outline" className="text-emerald-600">
                  SLL
                </Badge>
              )}
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-slate-500">Facility Amount</p>
            <p className="text-2xl font-bold text-slate-900">
              {formatCurrency(loan.facility_amount, loan.currency)}
            </p>
            <p className="text-sm text-slate-500 mb-2">Matures: {loan.maturity_date}</p>
            <Button
              variant="outline"
              size="sm"
              disabled={pdfLoading}
              onClick={async () => {
                setPdfLoading(true);
                try {
                  const blob = await downloadLoanPdfReport(loanId);
                  triggerPdfDownload(blob, `loan_report_${loanId}.pdf`);
                } catch (err) {
                  console.error("PDF download failed:", err);
                } finally {
                  setPdfLoading(false);
                }
              }}
            >
              <FileText className="h-4 w-4 mr-1" />
              {pdfLoading ? "Generating..." : "Download PDF"}
            </Button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="h-5 w-5 text-slate-500" />
                <p className="text-sm text-slate-500">Covenants</p>
              </div>
              <p className="text-2xl font-bold">{covenants.length}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="h-5 w-5 text-purple-500" />
                <p className="text-sm text-slate-500">Breach Probability</p>
              </div>
              <p
                className={`text-2xl font-bold ${
                  (prediction?.breach_probability || 0) > 0.5
                    ? "text-red-600"
                    : (prediction?.breach_probability || 0) > 0.25
                    ? "text-amber-600"
                    : "text-emerald-600"
                }`}
              >
                {prediction
                  ? `${(prediction.breach_probability * 100).toFixed(0)}%`
                  : "-"}
              </p>
            </CardContent>
          </Card>
          {/* LGD Stat Card - NEW */}
          <Card className="bg-gradient-to-br from-purple-50 to-blue-50 border-purple-100">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="h-5 w-5 text-purple-500" />
                <p className="text-sm text-slate-500">LGD (Basel III)</p>
              </div>
              <p
                className={`text-2xl font-bold ${
                  (lgdData?.lgd || 0) > 0.7
                    ? "text-red-600"
                    : (lgdData?.lgd || 0) > 0.5
                    ? "text-amber-600"
                    : "text-emerald-600"
                }`}
              >
                {lgdData ? lgdData.lgd_pct : "-"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="h-5 w-5 text-blue-500" />
                <p className="text-sm text-slate-500">Risk Velocity</p>
              </div>
              <div className="flex items-center gap-2">
                {velocity?.trajectory === "WORSENING" ? (
                  <TrendingDown className="h-5 w-5 text-red-500" />
                ) : velocity?.trajectory === "IMPROVING" ? (
                  <TrendingUp className="h-5 w-5 text-emerald-500" />
                ) : (
                  <span className="text-slate-400">—</span>
                )}
                <span
                  className={`text-xl font-bold ${
                    velocity?.trajectory === "WORSENING"
                      ? "text-red-600"
                      : velocity?.trajectory === "IMPROVING"
                      ? "text-emerald-600"
                      : "text-slate-600"
                  }`}
                >
                  {velocity?.trajectory || "STABLE"}
                </span>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Leaf className="h-5 w-5 text-emerald-500" />
                <p className="text-sm text-slate-500">ESG KPIs</p>
              </div>
              <p className="text-2xl font-bold">
                {kpis.filter((k) => k.on_track || k.progress_pct >= 70).length}/
                {kpis.length}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Modern Responsive Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <div className="relative">
            <TabsList className="bg-white border border-slate-200 shadow-sm rounded-xl p-1.5 flex overflow-x-auto gap-1 w-full pb-2 scroll-smooth snap-x snap-mandatory hover:scrollbar-default scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
              <TabsTrigger value="overview" className="flex-shrink-0 snap-start flex items-center gap-2 px-4 py-2.5 rounded-lg whitespace-nowrap text-sm font-medium data-[state=active]:bg-gradient-to-r data-[state=active]:from-slate-700 data-[state=active]:to-slate-900 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
                <FileText className="h-4 w-4" />
                <span className="hidden sm:inline">Overview</span>
              </TabsTrigger>
              <TabsTrigger value="covenants" className="flex-shrink-0 snap-start flex items-center gap-2 px-4 py-2.5 rounded-lg whitespace-nowrap text-sm font-medium data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
                <Shield className="h-4 w-4" />
                <span className="hidden sm:inline">Covenants</span>
              </TabsTrigger>
              <TabsTrigger value="predictions" className="flex-shrink-0 snap-start flex items-center gap-2 px-4 py-2.5 rounded-lg whitespace-nowrap text-sm font-medium data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-500 data-[state=active]:to-violet-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
                <Brain className="h-4 w-4" />
                <span className="hidden sm:inline">ML Predictions</span>
              </TabsTrigger>
              <TabsTrigger value="lgd" className="flex-shrink-0 snap-start flex items-center gap-2 px-4 py-2.5 rounded-lg whitespace-nowrap text-sm font-medium data-[state=active]:bg-gradient-to-r data-[state=active]:from-cyan-500 data-[state=active]:to-teal-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
                <DollarSign className="h-4 w-4" />
                <span className="hidden sm:inline">LGD Analysis</span>
              </TabsTrigger>
              <TabsTrigger value="prepayment" className="flex-shrink-0 snap-start flex items-center gap-2 px-4 py-2.5 rounded-lg whitespace-nowrap text-sm font-medium data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-500 data-[state=active]:to-orange-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
                <AlertTriangle className="h-4 w-4" />
                <span className="hidden sm:inline">Prepayment Risk</span>
              </TabsTrigger>
              <TabsTrigger value="velocity" className="flex-shrink-0 snap-start flex items-center gap-2 px-4 py-2.5 rounded-lg whitespace-nowrap text-sm font-medium data-[state=active]:bg-gradient-to-r data-[state=active]:from-rose-500 data-[state=active]:to-pink-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
                <Activity className="h-4 w-4" />
                <span className="hidden sm:inline">Risk Velocity</span>
              </TabsTrigger>
              <TabsTrigger value="cure" className="flex-shrink-0 snap-start flex items-center gap-2 px-4 py-2.5 rounded-lg whitespace-nowrap text-sm font-medium data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-500 data-[state=active]:to-green-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
                <Calculator className="h-4 w-4" />
                <span className="hidden sm:inline">Cure Calculator</span>
              </TabsTrigger>
              <TabsTrigger value="stress" className="flex-shrink-0 snap-start flex items-center gap-2 px-4 py-2.5 rounded-lg whitespace-nowrap text-sm font-medium data-[state=active]:bg-gradient-to-r data-[state=active]:from-red-500 data-[state=active]:to-rose-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
                <TrendingDown className="h-4 w-4" />
                <span className="hidden sm:inline">Stress Testing</span>
              </TabsTrigger>
              {loan.is_sll && (
                <TabsTrigger value="esg" className="flex-shrink-0 snap-start flex items-center gap-2 px-4 py-2.5 rounded-lg whitespace-nowrap text-sm font-medium data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-500 data-[state=active]:to-teal-600 data-[state=active]:text-white data-[state=active]:shadow-md hover:bg-slate-50 transition-all">
                  <Leaf className="h-4 w-4" />
                  <span className="hidden sm:inline">ESG</span>
                </TabsTrigger>
              )}
            </TabsList>
          </div>

          {/* Overview Tab */}
          <TabsContent value="overview" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Loan Details */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Loan Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-slate-500">Borrower</span>
                    <span className="font-medium">{loan.borrower_name}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-slate-500">Industry</span>
                    <span className="font-medium">
                      {loan.borrower_industry || "N/A"}
                    </span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-slate-500">Loan Type</span>
                    <span className="font-medium">{loan.loan_type || "Term Loan"}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-slate-500">Agent Bank</span>
                    <span className="font-medium">{loan.agent_bank || "N/A"}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-500">Sustainability Linked</span>
                    <Badge variant={loan.is_sll ? "default" : "outline"}>
                      {loan.is_sll ? "Yes" : "No"}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Covenant Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    Covenant Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {covenants.length === 0 ? (
                    <p className="text-slate-500">No covenants found</p>
                  ) : (
                    <div className="space-y-3">
                      {covenants.slice(0, 4).map((cov, idx) => (
                        <div
                          key={cov.covenant_id || idx}
                          className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                        >
                          <div>
                            <p className="font-medium">
                              {cov.name || cov.covenant_name || cov.covenant_type}
                            </p>
                            <p className="text-sm text-slate-500">
                              Actual: {cov.actual} | Threshold: {cov.threshold}
                            </p>
                          </div>
                          <StatusBadge status={cov.status} size="sm" />
                        </div>
                      ))}
                      {covenants.length > 4 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setActiveTab("covenants")}
                        >
                          View all {covenants.length} covenants →
                        </Button>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Covenants Tab */}
          <TabsContent value="covenants" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>All Covenants</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Covenant</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Threshold</TableHead>
                      <TableHead>Actual</TableHead>
                      <TableHead>Buffer</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {covenants.map((cov, idx) => (
                      <TableRow key={cov.covenant_id || idx}>
                        <TableCell className="font-medium">
                          {cov.name || cov.covenant_name}
                        </TableCell>
                        <TableCell>{cov.covenant_type || "-"}</TableCell>
                        <TableCell>{cov.threshold}</TableCell>
                        <TableCell>{cov.actual}</TableCell>
                        <TableCell>
                          {cov.buffer_pct != null ? (
                            <span
                              className={
                                cov.buffer_pct < 0
                                  ? "text-red-600"
                                  : cov.buffer_pct < 10
                                  ? "text-amber-600"
                                  : "text-emerald-600"
                              }
                            >
                              {cov.buffer_pct > 0 ? "+" : ""}
                              {cov.buffer_pct.toFixed(1)}%
                            </span>
                          ) : (
                            "-"
                          )}
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={cov.status} size="sm" />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ML Predictions Tab */}
          <TabsContent value="predictions" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Prediction Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5 text-purple-600" />
                    Breach Prediction
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {prediction ? (
                    <div className="space-y-4">
                      <div
                        className={`text-center py-6 rounded-lg ${
                          prediction.breach_probability > 0.5
                            ? "bg-red-50"
                            : prediction.breach_probability > 0.25
                            ? "bg-amber-50"
                            : "bg-emerald-50"
                        }`}
                      >
                        <p className="text-sm text-slate-600 mb-1">
                          {prediction.prediction_horizon || "90-Day"} Breach Probability
                        </p>
                        <p
                          className={`text-5xl font-bold ${
                            prediction.breach_probability > 0.5
                              ? "text-red-600"
                              : prediction.breach_probability > 0.25
                              ? "text-amber-600"
                              : "text-emerald-600"
                          }`}
                        >
                          {(prediction.breach_probability * 100).toFixed(0)}%
                        </p>
                        <Badge
                          variant={
                            prediction.risk_level === "HIGH"
                              ? "destructive"
                              : prediction.risk_level === "MEDIUM"
                              ? "secondary"
                              : "outline"
                          }
                          className="mt-2"
                        >
                          {prediction.risk_level} RISK
                        </Badge>
                      </div>

                      {prediction.top_risk_factors && (
                        <div>
                          <h4 className="font-medium mb-2">Top Risk Factors</h4>
                          <div className="space-y-2">
                            {prediction.top_risk_factors.map((factor, idx) => (
                              <div
                                key={idx}
                                className="flex items-center justify-between p-2 bg-slate-50 rounded"
                              >
                                <span>{factor.factor}</span>
                                <span
                                  className={`font-medium ${
                                    factor.impact > 0 ? "text-red-600" : "text-emerald-600"
                                  }`}
                                >
                                  {factor.impact > 0 ? "+" : ""}
                                  {(factor.impact * 100).toFixed(1)}%
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <p className="text-xs text-slate-500">
                        Model: {prediction.model_version || "AI Risk v2.0"}
                      </p>
                    </div>
                  ) : (
                    <p className="text-slate-500">No prediction available</p>
                  )}
                </CardContent>
              </Card>

              {/* SHAP Explanation Card - Use new component */}
              <div className="lg:col-span-2">
                <SHAPWaterfall loanId={loanId} />
              </div>
            </div>

            {/* Model Info */}
            <Card className="mt-6 bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <Brain className="h-8 w-8 text-purple-600" />
                  <div>
                    <h3 className="font-semibold">AI Risk Intelligence Engine</h3>
                    <p className="text-sm text-slate-600">
                      73% predictive accuracy • Trained on 720K+ historical loans • EU AI Act compliant explainable AI
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* LGD Analysis Tab - NEW */}
          <TabsContent value="lgd" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <LGDCard loanId={loanId} />
              
              {/* ECL Calculator Preview */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calculator className="h-5 w-5 text-blue-600" />
                    ECL Calculation (Basel III)
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-slate-600">
                    Expected Credit Loss calculation using the Two-Stage LGD model.
                  </p>
                  
                  <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg space-y-3">
                    <p className="font-mono text-sm font-medium text-blue-800">
                      ECL = PD × LGD × EAD
                    </p>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <p className="text-xs text-slate-500">PD</p>
                        <p className="text-lg font-bold text-purple-600">
                          {prediction
                            ? `${(prediction.breach_probability * 100).toFixed(1)}%`
                            : "--"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">LGD</p>
                        <p className="text-lg font-bold text-purple-600">
                          {lgdData ? lgdData.lgd_pct : "--"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">EAD</p>
                        <p className="text-lg font-bold text-purple-600">
                          {formatCurrency(loan.facility_amount, loan.currency)}
                        </p>
                      </div>
                    </div>
                    
                    {prediction && lgdData && (
                      <div className="pt-3 border-t border-blue-200">
                        <p className="text-xs text-slate-500 text-center">Expected Credit Loss</p>
                        <p className="text-2xl font-bold text-center text-red-600">
                          {formatCurrency(
                            prediction.breach_probability * lgdData.lgd * loan.facility_amount,
                            loan.currency
                          )}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  <div className="text-xs text-slate-500">
                    <p><strong>Model:</strong> AI Loss Model v2 (Ensemble Architecture)</p>
                    <p><strong>Training Data:</strong> 148K Lending Club charged-off loans</p>
                    <p><strong>Combined MAE:</strong> 6.45%</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Prepayment Risk Tab - V9 NEW */}
          <TabsContent value="prepayment" className="mt-6">
            <div className="grid grid-cols-1 gap-6">
              <PrepaymentCard loanId={loanId} />
            </div>
          </TabsContent>

          {/* Risk Velocity Tab */}
          <TabsContent value="velocity" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-blue-600" />
                  Risk Velocity Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                {velocity ? (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div
                        className={`p-4 rounded-lg ${
                          velocity.trajectory === "WORSENING"
                            ? "bg-red-50"
                            : velocity.trajectory === "IMPROVING"
                            ? "bg-emerald-50"
                            : "bg-slate-50"
                        }`}
                      >
                        <p className="text-sm text-slate-600">Trajectory</p>
                        <div className="flex items-center gap-2 mt-1">
                          {velocity.trajectory === "WORSENING" ? (
                            <TrendingDown className="h-5 w-5 text-red-600" />
                          ) : velocity.trajectory === "IMPROVING" ? (
                            <TrendingUp className="h-5 w-5 text-emerald-600" />
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                          <span className="text-xl font-bold">{velocity.trajectory}</span>
                        </div>
                      </div>
                      <div className="p-4 bg-slate-50 rounded-lg">
                        <p className="text-sm text-slate-600">Current Velocity</p>
                        <p className="text-xl font-bold mt-1">
                          {velocity.velocity?.current?.toFixed(2)} {velocity.velocity?.unit}
                        </p>
                      </div>
                      <div className="p-4 bg-slate-50 rounded-lg">
                        <p className="text-sm text-slate-600">Periods to Breach</p>
                        <p
                          className={`text-xl font-bold mt-1 ${
                            velocity.periods_to_breach !== null &&
                            velocity.periods_to_breach < 3
                              ? "text-red-600"
                              : ""
                          }`}
                        >
                          {velocity.periods_to_breach !== null
                            ? `${velocity.periods_to_breach} periods`
                            : "N/A"}
                        </p>
                      </div>
                    </div>

                    <div className="p-4 bg-blue-50 rounded-lg">
                      <p className="text-blue-800">{velocity.summary}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-slate-500">Current Value</p>
                        <p className="text-lg font-medium">{velocity.current_value}</p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-500">Threshold</p>
                        <p className="text-lg font-medium">{velocity.threshold}</p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-500">Headroom</p>
                        <p
                          className={`text-lg font-medium ${
                            velocity.headroom_percent < 0
                              ? "text-red-600"
                              : velocity.headroom_percent < 10
                              ? "text-amber-600"
                              : "text-emerald-600"
                          }`}
                        >
                          {velocity.headroom_percent > 0 ? "+" : ""}
                          {velocity.headroom_percent?.toFixed(1)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-500">Risk Level</p>
                        <Badge
                          variant={
                            velocity.risk_level === "HIGH" ||
                            velocity.risk_level === "CRITICAL"
                              ? "destructive"
                              : velocity.risk_level === "MEDIUM"
                              ? "secondary"
                              : "outline"
                          }
                        >
                          {velocity.risk_level}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-500 py-8 text-center">
                    No velocity data available for this loan
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Cure Calculator Tab */}
          <TabsContent value="cure" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Calculator Input Card - Premium Design */}
              <Card className="overflow-hidden border-0 shadow-xl bg-gradient-to-br from-white to-emerald-50">
                <CardHeader className="pb-4 bg-gradient-to-r from-emerald-600 via-green-500 to-teal-500 text-white">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm">
                      <Calculator className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <CardTitle className="text-xl font-bold text-white">Cure Calculator</CardTitle>
                      <p className="text-sm text-emerald-100">Covenant remediation analysis</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-6 space-y-5">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      Covenant Type
                    </label>
                    <select
                      value={cureForm.covenant_type}
                      onChange={(e) =>
                        setCureForm((p) => ({ ...p, covenant_type: e.target.value }))
                      }
                      className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl bg-white hover:border-emerald-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all font-medium"
                    >
                      <option value="debt_to_ebitda">Debt/EBITDA</option>
                      <option value="interest_coverage">Interest Coverage</option>
                      <option value="current_ratio">Current Ratio</option>
                      <option value="net_worth">Net Worth</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="relative">
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Current Value
                      </label>
                      <div className="relative">
                        <input
                          type="number"
                          step="0.1"
                          value={cureForm.current_value}
                          onChange={(e) =>
                            setCureForm((p) => ({
                              ...p,
                              current_value: parseFloat(e.target.value) || 0,
                            }))
                          }
                          className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl bg-white hover:border-emerald-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all font-bold text-lg"
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 font-medium">x</span>
                      </div>
                    </div>
                    <div className="relative">
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Threshold
                      </label>
                      <div className="relative">
                        <input
                          type="number"
                          step="0.1"
                          value={cureForm.threshold}
                          onChange={(e) =>
                            setCureForm((p) => ({
                              ...p,
                              threshold: parseFloat(e.target.value) || 0,
                            }))
                          }
                          className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl bg-white hover:border-emerald-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all font-bold text-lg"
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 font-medium">x</span>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        Total Debt ($)
                      </label>
                      <input
                        type="number"
                        value={cureForm.total_debt}
                        onChange={(e) =>
                          setCureForm((p) => ({
                            ...p,
                            total_debt: parseFloat(e.target.value) || 0,
                          }))
                        }
                        className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl bg-white hover:border-emerald-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all font-medium"
                        placeholder="100,000,000"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        EBITDA ($)
                      </label>
                      <input
                        type="number"
                        value={cureForm.ebitda}
                        onChange={(e) =>
                          setCureForm((p) => ({
                            ...p,
                            ebitda: parseFloat(e.target.value) || 0,
                          }))
                        }
                        className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl bg-white hover:border-emerald-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition-all font-medium"
                        placeholder="25,000,000"
                      />
                    </div>
                  </div>

                  <Button
                    onClick={handleCalculateCure}
                    disabled={cureLoading}
                    className="w-full py-6 text-lg font-bold bg-gradient-to-r from-emerald-600 to-green-500 hover:from-emerald-700 hover:to-green-600 shadow-lg hover:shadow-xl transition-all"
                  >
                    {cureLoading ? (
                      <>
                        <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                        Analyzing Options...
                      </>
                    ) : (
                      <>
                        <Calculator className="h-5 w-5 mr-2" />
                        Calculate Cure Options
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Results Card - Premium Design */}
              <Card className="overflow-hidden border-0 shadow-xl bg-gradient-to-br from-white to-slate-50">
                <CardHeader className="pb-4 bg-gradient-to-r from-slate-700 via-slate-600 to-slate-500 text-white">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm">
                      <Banknote className="h-6 w-6 text-white" />
                    </div>
                    <CardTitle className="text-xl font-bold text-white">Cure Options</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  {cureOptions ? (
                    <div className="space-y-5">
                      {/* Breach Alert */}
                      {cureOptions.is_breached && (
                        <div className="p-4 bg-gradient-to-r from-red-50 to-orange-50 rounded-xl border border-red-200">
                          <div className="flex items-center gap-2 text-red-700">
                            <AlertTriangle className="h-5 w-5" />
                            <span className="font-bold text-lg">Covenant Breached</span>
                          </div>
                          <div className="flex items-center gap-2 mt-2">
                            <Clock className="h-4 w-4 text-red-500" />
                            <p className="text-sm font-medium text-red-600">
                              Cure deadline: <span className="font-bold">{cureOptions.cure_deadline_days} days</span>
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Recommended Option - Hero Card */}
                      {cureOptions.recommended && (
                        <div className="relative overflow-hidden p-5 bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl border-2 border-emerald-300">
                          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full -translate-y-1/2 translate-x-1/2" />
                          <div className="flex items-center gap-2 mb-3">
                            <div className="p-1.5 rounded-lg bg-emerald-500">
                              <CheckCircle2 className="h-4 w-4 text-white" />
                            </div>
                            <p className="text-sm font-bold text-emerald-700 uppercase tracking-wide">
                              Recommended Option
                            </p>
                          </div>
                          <p className="text-xl font-bold text-slate-800">{cureOptions.recommended.method.replace(/_/g, " ")}</p>
                          <p className="text-sm text-slate-600 mt-1">
                            {cureOptions.recommended.description}
                          </p>
                          {(cureOptions.recommended.amount ?? 0) > 0 && (
                            <p className="text-3xl font-bold text-emerald-600 mt-3">
                              {formatCurrency(cureOptions.recommended.amount ?? 0)}
                            </p>
                          )}
                        </div>
                      )}

                      {/* All Options List */}
                      <div className="space-y-3">
                        <p className="font-bold text-slate-700 flex items-center gap-2">
                          <span>All Options</span>
                          <Badge variant="outline" className="text-slate-600">{cureOptions.options_count}</Badge>
                        </p>
                        {cureOptions.options?.map((opt, idx) => (
                          <div 
                            key={idx} 
                            className="p-4 bg-gradient-to-r from-slate-50 to-gray-50 rounded-xl border border-slate-200 hover:shadow-md hover:border-slate-300 transition-all"
                          >
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <p className="font-bold text-slate-800">{opt.method.replace(/_/g, " ")}</p>
                                <p className="text-sm text-slate-600 mt-1">{opt.description}</p>
                                {(opt.amount ?? 0) > 0 && (
                                  <p className="text-lg font-bold text-slate-700 mt-2">
                                    {formatCurrency(opt.amount ?? 0)}
                                  </p>
                                )}
                              </div>
                              <Badge
                                className={`ml-3 ${
                                  opt.feasibility === "HIGH"
                                    ? "bg-emerald-100 text-emerald-700 border-emerald-300"
                                    : opt.feasibility === "LOW"
                                    ? "bg-red-100 text-red-700 border-red-300"
                                    : "bg-amber-100 text-amber-700 border-amber-300"
                                } border-0 font-bold`}
                              >
                                {opt.feasibility}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Summary Footer */}
                      <div className="p-3 bg-slate-100 rounded-lg">
                        <p className="text-sm text-slate-600">{cureOptions.summary}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-16 text-slate-500">
                      <div className="p-4 rounded-2xl bg-slate-100 inline-block mb-4">
                        <Calculator className="h-12 w-12 text-slate-300" />
                      </div>
                      <p className="font-medium">Enter values and calculate to see cure options</p>
                      <p className="text-sm text-slate-400 mt-1">Analyze remediation paths for covenant breaches</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ESG Tab (for SLL loans) */}
          {loan.is_sll && (
            <TabsContent value="esg" className="mt-6">
              {/* ESG Risk ML Assessment */}
              <div className="mb-6">
                <ESGRiskCard loanId={loanId} />
              </div>

              {/* ESG KPIs */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Leaf className="h-5 w-5 text-emerald-600" />
                    ESG Key Performance Indicators
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {kpis.length === 0 ? (
                    <p className="text-slate-500 py-8 text-center">
                      No ESG KPIs tracked for this loan
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {kpis.map((kpi, idx) => (
                        <div key={kpi.kpi_id || idx} className="p-4 bg-slate-50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <p className="font-medium">{kpi.name || kpi.kpi_name}</p>
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
                            <Progress
                              value={Math.min(kpi.progress_pct, 100)}
                              className="h-2"
                            />
                          </div>
                          <div className="flex justify-between text-xs text-slate-500">
                            <span>Baseline: {kpi.baseline?.toLocaleString()}</span>
                            <span>
                              Current: {(kpi.current_value || kpi.current)?.toLocaleString()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          )}

          {/* Stress Testing Tab */}
          <TabsContent value="stress" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <StressTestCard />
              <ClimateRiskCard />
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
