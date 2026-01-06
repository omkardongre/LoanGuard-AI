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

        if (loanData.status === "fulfilled") setLoan(loanData.value);
        if (covenantData.status === "fulfilled")
          setCovenants(covenantData.value.covenants || []);
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
        <main className="flex-1 p-8 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
        </main>
      </div>
    );
  }

  if (!loan) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 p-8">
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

      <main className="flex-1 p-8">
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

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="covenants">Covenants</TabsTrigger>
            <TabsTrigger value="predictions">ML Predictions</TabsTrigger>
            <TabsTrigger value="lgd">LGD Analysis</TabsTrigger>
            <TabsTrigger value="velocity">Risk Velocity</TabsTrigger>
            <TabsTrigger value="cure">Cure Calculator</TabsTrigger>
            {loan.is_sll && <TabsTrigger value="esg">ESG</TabsTrigger>}
          </TabsList>

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
                          {cov.buffer_pct !== undefined ? (
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
                        Model: {prediction.model_version || "LightGBM v1.0"}
                      </p>
                    </div>
                  ) : (
                    <p className="text-slate-500">No prediction available</p>
                  )}
                </CardContent>
              </Card>

              {/* SHAP Explanation Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-blue-600" />
                    SHAP Feature Contributions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {explanation ? (
                    <div className="space-y-4">
                      <p className="text-sm text-slate-600">{explanation.summary}</p>

                      <div className="space-y-2">
                        {explanation.feature_contributions
                          ?.slice(0, 8)
                          .map((feat, idx) => (
                            <div key={idx} className="space-y-1">
                              <div className="flex justify-between text-sm">
                                <span>{feat.feature}</span>
                                <span
                                  className={
                                    feat.contribution > 0
                                      ? "text-red-600"
                                      : "text-emerald-600"
                                  }
                                >
                                  {feat.contribution > 0 ? "+" : ""}
                                  {(feat.contribution * 100).toFixed(2)}%
                                </span>
                              </div>
                              <div className="w-full bg-slate-100 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full ${
                                    feat.contribution > 0 ? "bg-red-500" : "bg-emerald-500"
                                  }`}
                                  style={{
                                    width: `${Math.min(
                                      Math.abs(feat.contribution) * 100 * 2,
                                      100
                                    )}%`,
                                  }}
                                />
                              </div>
                            </div>
                          ))}
                      </div>

                      <div className="pt-4 border-t text-sm text-slate-500">
                        <p>Base value: {explanation.base_value?.toFixed(3)}</p>
                        <p>Final prediction: {explanation.prediction?.toFixed(3)}</p>
                      </div>
                    </div>
                  ) : (
                    <p className="text-slate-500">
                      SHAP explanation not available. Run prediction first.
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Model Info */}
            <Card className="mt-6">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <Brain className="h-8 w-8 text-purple-600" />
                  <div>
                    <h3 className="font-semibold">LightGBM Breach Predictor</h3>
                    <p className="text-sm text-slate-500">
                      Trained on 720,966 real Lending Club loans (2007-2018) • ROC AUC:
                      0.7299 • SHAP TreeExplainer
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
                    <p><strong>Model:</strong> Two-Stage LGD V2 (XGBoost + LightGBM Ensemble)</p>
                    <p><strong>Training Data:</strong> 148K Lending Club charged-off loans</p>
                    <p><strong>Combined MAE:</strong> 6.45%</p>
                  </div>
                </CardContent>
              </Card>
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
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calculator className="h-5 w-5 text-emerald-600" />
                    Cure Calculator
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Covenant Type
                    </label>
                    <select
                      value={cureForm.covenant_type}
                      onChange={(e) =>
                        setCureForm((p) => ({ ...p, covenant_type: e.target.value }))
                      }
                      className="w-full px-3 py-2 border rounded-lg"
                    >
                      <option value="debt_to_ebitda">Debt/EBITDA</option>
                      <option value="interest_coverage">Interest Coverage</option>
                      <option value="current_ratio">Current Ratio</option>
                      <option value="net_worth">Net Worth</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Current Value
                      </label>
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
                        className="w-full px-3 py-2 border rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Threshold
                      </label>
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
                        className="w-full px-3 py-2 border rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
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
                        className="w-full px-3 py-2 border rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
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
                        className="w-full px-3 py-2 border rounded-lg"
                      />
                    </div>
                  </div>

                  <Button
                    onClick={handleCalculateCure}
                    disabled={cureLoading}
                    className="w-full bg-emerald-600 hover:bg-emerald-700"
                  >
                    {cureLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Calculating...
                      </>
                    ) : (
                      <>
                        <Calculator className="h-4 w-4 mr-2" />
                        Calculate Cure Options
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Cure Options</CardTitle>
                </CardHeader>
                <CardContent>
                  {cureOptions ? (
                    <div className="space-y-4">
                      {cureOptions.is_breached && (
                        <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                          <div className="flex items-center gap-2 text-red-700">
                            <AlertTriangle className="h-4 w-4" />
                            <span className="font-medium">Covenant Breached</span>
                          </div>
                          <p className="text-sm text-red-600 mt-1">
                            Cure deadline: {cureOptions.cure_deadline_days} days
                          </p>
                        </div>
                      )}

                      {cureOptions.recommended && (
                        <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                          <p className="text-sm text-emerald-600 font-medium mb-1">
                            Recommended Option
                          </p>
                          <p className="font-medium">{cureOptions.recommended.method}</p>
                          <p className="text-sm text-slate-600">
                            {cureOptions.recommended.description}
                          </p>
                          {cureOptions.recommended.amount && (
                            <p className="text-lg font-bold text-emerald-700 mt-2">
                              {formatCurrency(cureOptions.recommended.amount)}
                            </p>
                          )}
                        </div>
                      )}

                      <div className="space-y-2">
                        <p className="font-medium">All Options ({cureOptions.options_count})</p>
                        {cureOptions.options?.map((opt, idx) => (
                          <div key={idx} className="p-3 bg-slate-50 rounded-lg">
                            <div className="flex justify-between items-start">
                              <div>
                                <p className="font-medium">{opt.method}</p>
                                <p className="text-sm text-slate-600">{opt.description}</p>
                              </div>
                              <Badge
                                variant={
                                  opt.feasibility === "HIGH"
                                    ? "outline"
                                    : opt.feasibility === "LOW"
                                    ? "destructive"
                                    : "secondary"
                                }
                              >
                                {opt.feasibility}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>

                      <p className="text-sm text-slate-500">{cureOptions.summary}</p>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Calculator className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>Enter values and calculate to see cure options</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ESG Tab (for SLL loans) */}
          {loan.is_sll && (
            <TabsContent value="esg" className="mt-6">
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
        </Tabs>
      </main>
    </div>
  );
}
