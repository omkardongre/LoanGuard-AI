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
  ArrowRightLeft,
  Loader2,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Leaf,
  FileText,
  Flame,
} from "lucide-react";
import { ExportTlpPdfButton } from "@/components/export-button";
import {
  fetchLoans,
  validateTransitionLoan,
  assessCarbonLockin,
  screenDNSH,
  fetchTransitionLoansSummary,
  type Loan,
  type TLPAssessment,
  type CarbonLockinAssessment,
  type DNSHScreening,
} from "@/lib/api";

interface LoanDetails {
  loan: Loan;
  tlp?: TLPAssessment;
  carbonLockin?: CarbonLockinAssessment;
  dnsh?: DNSHScreening;
  loading: boolean;
}

function getRiskColor(risk: string): string {
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

function getStatusIcon(status: string) {
  switch (status?.toUpperCase()) {
    case "PASS":
    case "COMPLIANT":
      return <CheckCircle className="h-4 w-4 text-emerald-600" />;
    case "FAIL":
    case "NON_COMPLIANT":
      return <XCircle className="h-4 w-4 text-red-600" />;
    default:
      return <AlertTriangle className="h-4 w-4 text-amber-600" />;
  }
}

// TLP Principles from LMA October 2025
const TLP_PRINCIPLES = [
  "Designation as Transition",
  "Strategy & Governance",
  "Financial Materiality",
  "Climate Science Alignment",
  "Transparency & Reporting",
];

export default function TransitionLoansPage() {
  const [loading, setLoading] = useState(true);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [selectedLoan, setSelectedLoan] = useState<string | null>(null);
  const [loanDetails, setLoanDetails] = useState<Map<string, LoanDetails>>(new Map());
  const [activeTab, setActiveTab] = useState("overview");
  const [summary, setSummary] = useState<{
    total_loans: number;
    compliant_count: number;
    avg_tlp_score: number;
    carbon_lockin_distribution: Record<string, number>;
  } | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [loansRes, summaryRes] = await Promise.allSettled([
        fetchLoans(),
        fetchTransitionLoansSummary(),
      ]);

      if (loansRes.status === "fulfilled") {
        setLoans(loansRes.value.loans || []);
      }

      if (summaryRes.status === "fulfilled" && summaryRes.value.success) {
        setSummary({
          total_loans: summaryRes.value.total_loans,
          compliant_count: summaryRes.value.compliant_count,
          avg_tlp_score: summaryRes.value.avg_tlp_score,
          carbon_lockin_distribution: summaryRes.value.carbon_lockin_distribution,
        });
      }
    } catch (err) {
      console.error("Failed to load transition loans:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadLoanDetails(loanId: string) {
    const existing = loanDetails.get(loanId);
    if (existing && !existing.loading && existing.tlp) return;

    const loan = loans.find((l) => l.loan_id === loanId);
    if (!loan) return;

    setLoanDetails((prev) => {
      const next = new Map(prev);
      next.set(loanId, { loan, loading: true });
      return next;
    });

    try {
      const [tlpRes, carbonRes, dnshRes] = await Promise.allSettled([
        validateTransitionLoan(loanId),
        assessCarbonLockin(loanId),
        screenDNSH(loanId),
      ]);

      setLoanDetails((prev) => {
        const next = new Map(prev);
        next.set(loanId, {
          loan,
          tlp: tlpRes.status === "fulfilled" && tlpRes.value.success
            ? tlpRes.value.assessment
            : undefined,
          carbonLockin: carbonRes.status === "fulfilled" && carbonRes.value.success
            ? carbonRes.value.assessment
            : undefined,
          dnsh: dnshRes.status === "fulfilled" && dnshRes.value.success
            ? dnshRes.value.screening
            : undefined,
          loading: false,
        });
        return next;
      });
    } catch (err) {
      console.error("Failed to load loan details:", err);
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
          <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
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
            <div className="p-3 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg">
              <ArrowRightLeft className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">Transition Loans</h1>
              <p className="text-slate-500">
                LMA Transition Loan Principles (October 2025)
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-gradient-to-r from-amber-50 to-orange-50 text-amber-700 border-amber-200">
              LMA TLP Oct 2025
            </Badge>
            <ExportTlpPdfButton variant="outline" />
            <Button variant="outline" onClick={loadData} className="hover:bg-blue-50 transition-colors">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-16 h-16 rounded-full bg-gradient-to-br from-amber-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500">
                  <ArrowRightLeft className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">Transition Loans</p>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {summary?.total_loans || loans.length || 0}
              </p>
            </CardContent>
          </Card>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-16 h-16 rounded-full bg-gradient-to-br from-emerald-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-500">
                  <CheckCircle className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">TLP Compliant</p>
              </div>
              <p className="text-2xl font-bold text-emerald-600">
                {summary?.compliant_count || 0}
              </p>
            </CardContent>
          </Card>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-16 h-16 rounded-full bg-gradient-to-br from-teal-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-gradient-to-br from-teal-400 to-teal-500">
                  <Leaf className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">Avg TLP Score</p>
              </div>
              <p className="text-2xl font-bold text-teal-600">
                {(summary?.avg_tlp_score || 0).toFixed(1)}%
              </p>
            </CardContent>
          </Card>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-16 h-16 rounded-full bg-gradient-to-br from-red-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-gradient-to-br from-red-400 to-red-500">
                  <Flame className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">High Carbon Lock-in</p>
              </div>
              <p className="text-2xl font-bold text-red-600">
                {summary?.carbon_lockin_distribution?.HIGH || 0}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-gradient-to-r from-slate-100 to-slate-50 p-1 rounded-xl">
            <TabsTrigger 
              value="overview"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-500 data-[state=active]:to-orange-600 data-[state=active]:text-white data-[state=active]:shadow-md rounded-lg transition-all"
            >
              <ArrowRightLeft className="h-4 w-4 mr-2" />
              Loan Portfolio
            </TabsTrigger>
            <TabsTrigger 
              value="tlp"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-500 data-[state=active]:to-teal-600 data-[state=active]:text-white data-[state=active]:shadow-md rounded-lg transition-all"
            >
              <FileText className="h-4 w-4 mr-2" />
              TLP Validation
            </TabsTrigger>
            <TabsTrigger 
              value="carbon"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-red-500 data-[state=active]:to-rose-600 data-[state=active]:text-white data-[state=active]:shadow-md rounded-lg transition-all"
            >
              <Flame className="h-4 w-4 mr-2" />
              Carbon Lock-in
            </TabsTrigger>
            <TabsTrigger 
              value="dnsh"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-teal-500 data-[state=active]:to-cyan-600 data-[state=active]:text-white data-[state=active]:shadow-md rounded-lg transition-all"
            >
              <Leaf className="h-4 w-4 mr-2" />
              DNSH Screening
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Transition Loan Portfolio</CardTitle>
              </CardHeader>
              <CardContent>
                {loans.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <ArrowRightLeft className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>No loans found. Data loaded from BigQuery.</p>
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
                      {loans.slice(0, 15).map((loan) => (
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
                            <Badge className={getRiskColor(loan.status)}>
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
                                setActiveTab("tlp");
                              }}
                            >
                              Assess
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

          {/* TLP Validation Tab */}
          <TabsContent value="tlp">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Loan List */}
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle className="text-base">Select Loan</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
                  {loans.slice(0, 20).map((loan) => (
                    <div
                      key={loan.loan_id}
                      onClick={() => {
                        setSelectedLoan(loan.loan_id);
                        loadLoanDetails(loan.loan_id);
                      }}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedLoan === loan.loan_id
                          ? "border-amber-500 bg-amber-50"
                          : "hover:bg-slate-50"
                      }`}
                    >
                      <p className="font-medium text-slate-900">{loan.borrower_name}</p>
                      <p className="text-xs text-slate-500">{loan.loan_id}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* TLP Details */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">
                    TLP Compliance Assessment
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
                        <div className="space-y-6">
                          {/* Overall Score */}
                          <div className="p-4 bg-slate-50 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium">Overall TLP Score</span>
                              <Badge
                                className={
                                  (details.tlp?.overall_score || 0) >= 70
                                    ? "bg-emerald-100 text-emerald-800"
                                    : "bg-amber-100 text-amber-800"
                                }
                              >
                                {details.tlp?.compliance_status || "PENDING"}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-3">
                              <Progress
                                value={details.tlp?.overall_score || 0}
                                className="flex-1 h-3"
                              />
                              <span className="text-xl font-bold">
                                {(details.tlp?.overall_score || 0).toFixed(1)}%
                              </span>
                            </div>
                          </div>

                          {/* 5 TLP Principles */}
                          <div>
                            <h4 className="font-medium mb-3">5 TLP Principles</h4>
                            <div className="space-y-3">
                              {TLP_PRINCIPLES.map((principle, idx) => {
                                const principleData = details.tlp?.principles?.find(
                                  (p) => p.principle === principle
                                );
                                return (
                                  <div
                                    key={principle}
                                    className="flex items-center justify-between p-3 border rounded-lg"
                                  >
                                    <div className="flex items-center gap-2">
                                      {getStatusIcon(principleData?.status || "PENDING")}
                                      <span className="text-sm">
                                        {idx + 1}. {principle}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <Progress
                                        value={principleData?.score || 0}
                                        className="w-20 h-2"
                                      />
                                      <span className="text-sm font-medium w-12 text-right">
                                        {(principleData?.score || 0).toFixed(0)}%
                                      </span>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>

                        </div>
                      );
                    })()
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <FileText className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>Select a loan to view TLP assessment</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Carbon Lock-in Tab */}
          <TabsContent value="carbon">
            <Card className="overflow-hidden border-0 shadow-lg">
              <CardHeader className="bg-gradient-to-r from-red-500 to-rose-600 text-white">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Flame className="h-5 w-5" />
                  Carbon Lock-in Risk Assessment (LMA TLP Section 3.2.1 iv)
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-6">
                  {selectedLoan ? (
                    (() => {
                      const details = loanDetails.get(selectedLoan);
                      if (!details?.carbonLockin) {
                        return (
                          <p className="text-slate-500 text-center py-8">
                            No carbon lock-in data. Load loan details first.
                          </p>
                        );
                      }

                      const cl = details.carbonLockin;
                      const riskGradient = cl.risk_level === "HIGH" 
                        ? "from-red-500 to-red-600" 
                        : cl.risk_level === "MEDIUM" 
                          ? "from-amber-500 to-orange-600"
                          : "from-emerald-500 to-teal-600";
                      
                      return (
                        <div className="space-y-6">
                          {/* Borrower Header with Risk Badge */}
                          <div className="flex items-center justify-between p-5 bg-gradient-to-r from-slate-50 to-slate-100 rounded-xl border">
                            <div>
                              <p className="font-semibold text-lg text-slate-900">{details.loan.borrower_name}</p>
                              <p className="text-sm text-slate-500">{selectedLoan}</p>
                            </div>
                            <Badge className={`bg-gradient-to-r ${riskGradient} text-white border-0 px-4 py-2 text-sm font-semibold shadow-md`}>
                              {cl.risk_level} RISK
                            </Badge>
                          </div>

                          {/* Criteria Scores Grid */}
                          <div className="grid grid-cols-2 gap-4">
                            {Object.entries(cl.criteria_scores || {}).map(([key, value]) => {
                              const score = value as number;
                              const scoreColor = score >= 80 ? "bg-emerald-500" : score >= 60 ? "bg-amber-500" : "bg-red-500";
                              return (
                                <div key={key} className="p-4 bg-white border rounded-xl shadow-sm hover:shadow-md transition-shadow">
                                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
                                    {key.replace(/_/g, " ")}
                                  </p>
                                  <div className="flex items-center gap-3">
                                    <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
                                      <div 
                                        className={`h-full ${scoreColor} rounded-full transition-all`}
                                        style={{ width: `${score}%` }}
                                      />
                                    </div>
                                    <span className="text-lg font-bold text-slate-900">{score}%</span>
                                  </div>
                                </div>
                              );
                            })}
                          </div>

                          {/* Recommendations */}
                          {cl.recommendations?.length > 0 && (
                            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
                              <h4 className="font-semibold text-amber-800 mb-3 flex items-center gap-2">
                                <AlertTriangle className="h-4 w-4" />
                                Recommendations
                              </h4>
                              <ul className="space-y-2">
                                {cl.recommendations.map((rec, idx) => (
                                  <li key={idx} className="flex items-start gap-2 text-sm text-amber-900">
                                    <span className="w-5 h-5 rounded-full bg-amber-200 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">{idx + 1}</span>
                                    {rec}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      );
                    })()
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <Flame className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>Select a loan from TLP Validation tab first</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* DNSH Tab */}
          <TabsContent value="dnsh">
            <Card className="overflow-hidden border-0 shadow-lg">
              <CardHeader className="bg-gradient-to-r from-teal-500 to-cyan-600 text-white">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Leaf className="h-5 w-5" />
                  Do No Significant Harm (DNSH) Screening
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                {selectedLoan ? (
                  (() => {
                    const details = loanDetails.get(selectedLoan);
                    if (!details?.dnsh) {
                      return (
                        <p className="text-slate-500 text-center py-8">
                          No DNSH data. Load loan details first.
                        </p>
                      );
                    }

                    const statusGradient = details.dnsh.overall_status === "PASS" 
                      ? "from-emerald-500 to-teal-600" 
                      : "from-red-500 to-rose-600";

                    return (
                      <div className="space-y-6">
                        {/* Borrower Header */}
                        <div className="flex items-center justify-between p-5 bg-gradient-to-r from-slate-50 to-slate-100 rounded-xl border">
                          <div>
                            <p className="font-semibold text-lg text-slate-900">{details.loan.borrower_name}</p>
                            <p className="text-sm text-slate-500">
                              6 EU Taxonomy Environmental Objectives
                            </p>
                          </div>
                          <Badge className={`bg-gradient-to-r ${statusGradient} text-white border-0 px-4 py-2 text-sm font-semibold shadow-md`}>
                            {details.dnsh.overall_status}
                          </Badge>
                        </div>

                        {/* Objectives Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {details.dnsh.objectives?.map((obj) => {
                            const scoreColor = obj.score >= 80 ? "bg-emerald-500" : obj.score >= 60 ? "bg-amber-500" : "bg-red-500";
                            const bgColor = obj.status === "PASS" 
                              ? "bg-emerald-50 border-emerald-200 hover:shadow-emerald-100" 
                              : obj.status === "FAIL" 
                                ? "bg-red-50 border-red-200 hover:shadow-red-100"
                                : "bg-amber-50 border-amber-200 hover:shadow-amber-100";
                            
                            return (
                              <div
                                key={obj.objective}
                                className={`p-4 rounded-xl border shadow-sm hover:shadow-md transition-all ${bgColor}`}
                              >
                                <div className="flex items-center justify-between mb-3">
                                  <div className="flex items-center gap-2">
                                    {getStatusIcon(obj.status)}
                                    <span className="font-medium text-slate-900">{obj.objective}</span>
                                  </div>
                                  <span className="text-lg font-bold">{obj.score}%</span>
                                </div>
                                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                                  <div 
                                    className={`h-full ${scoreColor} rounded-full transition-all`}
                                    style={{ width: `${obj.score}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })()
                ) : (
                  <div className="text-center py-12 text-slate-500">
                    <Leaf className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>Select a loan from TLP Validation tab first</p>
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
