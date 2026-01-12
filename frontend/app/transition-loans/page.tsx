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
  generateTLPReport,
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

  async function handleGenerateReport(loanId: string) {
    try {
      const result = await generateTLPReport(loanId);
      if (result.success) {
        alert(`TLP Report generated for ${loanId}`);
      }
    } catch (err) {
      console.error("Report generation failed:", err);
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
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Transition Loans</h1>
            <p className="text-slate-500">
              LMA Transition Loan Principles (October 2025)
            </p>
          </div>
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
              LMA TLP Oct 2025
            </Badge>
            <ExportTlpPdfButton variant="outline" />
            <Button variant="outline" onClick={loadData}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <ArrowRightLeft className="h-5 w-5 text-amber-500" />
                <p className="text-sm text-slate-500">Transition Loans</p>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {summary?.total_loans || loans.length || 0}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-5 w-5 text-emerald-500" />
                <p className="text-sm text-slate-500">TLP Compliant</p>
              </div>
              <p className="text-2xl font-bold text-emerald-600">
                {summary?.compliant_count || 0}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Leaf className="h-5 w-5 text-emerald-500" />
                <p className="text-sm text-slate-500">Avg TLP Score</p>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {(summary?.avg_tlp_score || 0).toFixed(1)}%
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Flame className="h-5 w-5 text-red-500" />
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
          <TabsList>
            <TabsTrigger value="overview">Loan Portfolio</TabsTrigger>
            <TabsTrigger value="tlp">TLP Validation</TabsTrigger>
            <TabsTrigger value="carbon">Carbon Lock-in</TabsTrigger>
            <TabsTrigger value="dnsh">DNSH Screening</TabsTrigger>
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

                          {/* Generate Report */}
                          <Button
                            className="w-full bg-amber-600 hover:bg-amber-700"
                            onClick={() => handleGenerateReport(selectedLoan)}
                          >
                            <FileText className="h-4 w-4 mr-2" />
                            Generate TLP Report
                          </Button>
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
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Flame className="h-5 w-5 text-red-500" />
                  Carbon Lock-in Risk Assessment (LMA TLP Section 3.2.1 iv)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
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
                      return (
                        <div className="space-y-4">
                          <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                            <div>
                              <p className="font-medium">{details.loan.borrower_name}</p>
                              <p className="text-sm text-slate-500">{selectedLoan}</p>
                            </div>
                            <Badge className={getRiskColor(cl.risk_level)}>
                              {cl.risk_level} RISK
                            </Badge>
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            {Object.entries(cl.criteria_scores || {}).map(([key, value]) => (
                              <div key={key} className="p-3 border rounded-lg">
                                <p className="text-xs text-slate-500 capitalize">
                                  {key.replace(/_/g, " ")}
                                </p>
                                <div className="flex items-center gap-2 mt-1">
                                  <Progress value={value as number} className="flex-1 h-2" />
                                  <span className="font-medium">{value}%</span>
                                </div>
                              </div>
                            ))}
                          </div>

                          {cl.recommendations?.length > 0 && (
                            <div>
                              <h4 className="font-medium mb-2">Recommendations</h4>
                              <ul className="list-disc list-inside space-y-1 text-sm text-slate-600">
                                {cl.recommendations.map((rec, idx) => (
                                  <li key={idx}>{rec}</li>
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
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Leaf className="h-5 w-5 text-emerald-500" />
                  Do No Significant Harm (DNSH) Screening
                </CardTitle>
              </CardHeader>
              <CardContent>
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

                    return (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                          <div>
                            <p className="font-medium">{details.loan.borrower_name}</p>
                            <p className="text-sm text-slate-500">
                              6 EU Taxonomy Environmental Objectives
                            </p>
                          </div>
                          <Badge
                            className={
                              details.dnsh.overall_status === "PASS"
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-red-100 text-red-800"
                            }
                          >
                            {details.dnsh.overall_status}
                          </Badge>
                        </div>

                        <div className="space-y-3">
                          {details.dnsh.objectives?.map((obj) => (
                            <div
                              key={obj.objective}
                              className={`flex items-center justify-between p-3 rounded-lg border ${
                                obj.status === "PASS"
                                  ? "bg-emerald-50 border-emerald-200"
                                  : obj.status === "FAIL"
                                  ? "bg-red-50 border-red-200"
                                  : "bg-amber-50 border-amber-200"
                              }`}
                            >
                              <div className="flex items-center gap-2">
                                {getStatusIcon(obj.status)}
                                <span className="text-sm">{obj.objective}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <Progress value={obj.score} className="w-16 h-2" />
                                <span className="text-sm font-medium">{obj.score}%</span>
                              </div>
                            </div>
                          ))}
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
