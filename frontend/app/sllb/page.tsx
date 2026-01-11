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
  Building2,
  Loader2,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Clock,
  Globe,
  Landmark,
  FileCheck,
} from "lucide-react";
import {
  fetchLoans,
  fetchSLLBPortfolios,
  evaluateSLLEligibility,
  fetchZARONIASummary,
  assessZARONIATransition,
  fetchSFDRSummary,
  classifySFDR,
  type Loan,
  type SLLBPortfolio,
  type SLLBEligibility,
  type ZARONIATransition,
  type SFDRClassification,
} from "@/lib/api";

// SFDR 2.0 Categories (November 2025)
const SFDR_CATEGORIES = {
  ARTICLE_7_TRANSITION: { name: "Transition", color: "bg-amber-100 text-amber-800" },
  ARTICLE_8_ESG_BASICS: { name: "ESG Basics", color: "bg-green-100 text-green-800" },
  ARTICLE_9_SUSTAINABLE: { name: "Sustainable", color: "bg-emerald-100 text-emerald-800" },
  UNCATEGORIZED: { name: "Uncategorized", color: "bg-slate-100 text-slate-800" },
};

function getUrgencyColor(urgency: string): string {
  switch (urgency?.toUpperCase()) {
    case "CRITICAL":
      return "bg-red-100 text-red-800 border-red-200";
    case "HIGH":
      return "bg-orange-100 text-orange-800 border-orange-200";
    case "MEDIUM":
      return "bg-amber-100 text-amber-800 border-amber-200";
    case "LOW":
      return "bg-emerald-100 text-emerald-800 border-emerald-200";
    default:
      return "bg-slate-100 text-slate-800 border-slate-200";
  }
}

export default function SLLBPage() {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("sllb");
  const [loans, setLoans] = useState<Loan[]>([]);
  const [portfolios, setPortfolios] = useState<SLLBPortfolio[]>([]);
  const [selectedLoan, setSelectedLoan] = useState<string | null>(null);

  // SLLB Eligibility
  const [eligibilityCache, setEligibilityCache] = useState<Map<string, SLLBEligibility>>(new Map());
  const [eligibilityLoading, setEligibilityLoading] = useState<string | null>(null);

  // ZARONIA
  const [zaroniaSummary, setZaroniaSummary] = useState<{
    deadline: string;
    days_remaining: number;
    total_transitions: number;
    by_status: Record<string, number>;
    completion_rate: number;
  } | null>(null);
  const [zaroniaCache, setZaroniaCache] = useState<Map<string, ZARONIATransition>>(new Map());

  // SFDR
  const [sfdrSummary, setSfdrSummary] = useState<{
    total_products: number;
    by_category: Record<string, number>;
    avg_taxonomy_alignment: number;
  } | null>(null);
  const [sfdrCache, setSfdrCache] = useState<Map<string, SFDRClassification>>(new Map());

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [loansRes, portfoliosRes, zaroniaRes, sfdrRes] = await Promise.allSettled([
        fetchLoans(),
        fetchSLLBPortfolios(),
        fetchZARONIASummary(),
        fetchSFDRSummary(),
      ]);

      if (loansRes.status === "fulfilled") {
        setLoans(loansRes.value.loans || []);
      }

      if (portfoliosRes.status === "fulfilled" && portfoliosRes.value.success) {
        setPortfolios(portfoliosRes.value.portfolios || []);
      }

      if (zaroniaRes.status === "fulfilled" && zaroniaRes.value.success) {
        setZaroniaSummary({
          deadline: zaroniaRes.value.deadline,
          days_remaining: zaroniaRes.value.days_remaining,
          total_transitions: zaroniaRes.value.total_transitions,
          by_status: zaroniaRes.value.by_status,
          completion_rate: zaroniaRes.value.completion_rate,
        });
      }

      if (sfdrRes.status === "fulfilled" && sfdrRes.value.success) {
        setSfdrSummary({
          total_products: sfdrRes.value.total_products,
          by_category: sfdrRes.value.by_category,
          avg_taxonomy_alignment: sfdrRes.value.avg_taxonomy_alignment,
        });
      }
    } catch (err) {
      console.error("Failed to load SLLB data:", err);
    } finally {
      setLoading(false);
    }
  }

  async function checkEligibility(loanId: string) {
    if (eligibilityCache.has(loanId)) return;
    setEligibilityLoading(loanId);
    try {
      const res = await evaluateSLLEligibility(loanId);
      if (res.success) {
        setEligibilityCache((prev) => {
          const next = new Map(prev);
          next.set(loanId, res.eligibility);
          return next;
        });
      }
    } catch (err) {
      console.error("Eligibility check failed:", err);
    } finally {
      setEligibilityLoading(null);
    }
  }

  async function checkZARONIA(loanId: string) {
    if (zaroniaCache.has(loanId)) return;
    try {
      const res = await assessZARONIATransition(loanId);
      if (res.success) {
        setZaroniaCache((prev) => {
          const next = new Map(prev);
          next.set(loanId, res.assessment);
          return next;
        });
      }
    } catch (err) {
      console.error("ZARONIA check failed:", err);
    }
  }

  async function checkSFDR(productId: string) {
    if (sfdrCache.has(productId)) return;
    try {
      const res = await classifySFDR(productId);
      if (res.success) {
        setSfdrCache((prev) => {
          const next = new Map(prev);
          next.set(productId, res.classification);
          return next;
        });
      }
    } catch (err) {
      console.error("SFDR classification failed:", err);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 p-8 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
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
            <h1 className="text-2xl font-bold text-slate-900">SLLB & Regional</h1>
            <p className="text-slate-500">
              ICMA SLLBG, SARB ZARONIA, EU SFDR 2.0
            </p>
          </div>
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
              ICMA June 2024
            </Badge>
            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
              SFDR 2.0 Nov 2025
            </Badge>
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
                <Building2 className="h-5 w-5 text-purple-500" />
                <p className="text-sm text-slate-500">SLLB Portfolios</p>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {portfolios.length}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-5 w-5 text-amber-500" />
                <p className="text-sm text-slate-500">JIBAR Deadline</p>
              </div>
              <p className="text-2xl font-bold text-amber-600">
                {zaroniaSummary?.days_remaining || "–"} days
              </p>
              <p className="text-xs text-slate-500">Dec 31, 2026</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <Globe className="h-5 w-5 text-emerald-500" />
                <p className="text-sm text-slate-500">ZARONIA Transitions</p>
              </div>
              <p className="text-2xl font-bold text-emerald-600">
                {zaroniaSummary?.completion_rate?.toFixed(1) || 0}%
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <FileCheck className="h-5 w-5 text-blue-500" />
                <p className="text-sm text-slate-500">SFDR Products</p>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {sfdrSummary?.total_products || 0}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList>
            <TabsTrigger value="sllb">SLLB Portfolios</TabsTrigger>
            <TabsTrigger value="eligibility">SLL Eligibility</TabsTrigger>
            <TabsTrigger value="zaronia">ZARONIA Transition</TabsTrigger>
            <TabsTrigger value="sfdr">SFDR 2.0</TabsTrigger>
          </TabsList>

          {/* SLLB Portfolios Tab */}
          <TabsContent value="sllb">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Landmark className="h-5 w-5 text-purple-500" />
                  SLL Financing Bonds (ICMA SLLBG)
                </CardTitle>
              </CardHeader>
              <CardContent>
                {portfolios.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <Building2 className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>No SLLB portfolios found. Data loaded from BigQuery.</p>
                    <p className="text-sm mt-2">Create portfolios to manage SLL-backed bonds.</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Bond Name</TableHead>
                        <TableHead>Issuer</TableHead>
                        <TableHead>Amount</TableHead>
                        <TableHead>SLLs</TableHead>
                        <TableHead>Coverage</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {portfolios.map((portfolio) => (
                        <TableRow key={portfolio.portfolio_id}>
                          <TableCell className="font-medium">
                            {portfolio.bond_name}
                          </TableCell>
                          <TableCell>{portfolio.issuer_name}</TableCell>
                          <TableCell>
                            {portfolio.currency} {(portfolio.bond_amount / 1e6).toFixed(1)}M
                          </TableCell>
                          <TableCell>{portfolio.eligible_sll_count}</TableCell>
                          <TableCell>
                            <Progress
                              value={
                                portfolio.bond_amount > 0
                                  ? (portfolio.total_sll_amount / portfolio.bond_amount) * 100
                                  : 0
                              }
                              className="h-2 w-20"
                            />
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{portfolio.status}</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* SLL Eligibility Tab */}
          <TabsContent value="eligibility">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">SLL Eligibility for SLLB Inclusion</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {loans.filter((l) => l.is_sll).slice(0, 10).map((loan) => {
                    const eligibility = eligibilityCache.get(loan.loan_id);
                    const isLoading = eligibilityLoading === loan.loan_id;

                    return (
                      <div
                        key={loan.loan_id}
                        className="p-4 border rounded-lg hover:bg-slate-50"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{loan.borrower_name}</p>
                            <p className="text-xs text-slate-500">{loan.loan_id}</p>
                          </div>
                          {eligibility ? (
                            <div className="flex items-center gap-3">
                              <div className="text-right">
                                <p className="text-xs text-slate-500">Eligibility Score</p>
                                <p className="font-bold">
                                  {eligibility.eligibility_score.toFixed(1)}%
                                </p>
                              </div>
                              <Badge
                                className={
                                  eligibility.eligible
                                    ? "bg-emerald-100 text-emerald-800"
                                    : "bg-red-100 text-red-800"
                                }
                              >
                                {eligibility.eligible ? "Eligible" : "Not Eligible"}
                              </Badge>
                            </div>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => checkEligibility(loan.loan_id)}
                              disabled={isLoading}
                            >
                              {isLoading ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                "Check Eligibility"
                              )}
                            </Button>
                          )}
                        </div>
                        {eligibility && (
                          <div className="mt-3 grid grid-cols-4 gap-2">
                            {Object.entries(eligibility.component_scores || {}).map(([key, value]) => (
                              <div key={key} className="text-center p-2 bg-slate-50 rounded">
                                <p className="text-xs text-slate-500 capitalize">
                                  {key.replace(/_/g, " ")}
                                </p>
                                <p className="font-medium">{value}%</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {loans.filter((l) => l.is_sll).length === 0 && (
                    <div className="text-center py-12 text-slate-500">
                      <CheckCircle className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>No SLL loans found. Data loaded from BigQuery.</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ZARONIA Transition Tab */}
          <TabsContent value="zaronia">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Globe className="h-5 w-5 text-blue-500" />
                  JIBAR to ZARONIA Transition (SARB)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Deadline warning */}
                  <div
                    className={`p-4 rounded-lg border ${
                      (zaroniaSummary?.days_remaining || 999) < 180
                        ? "bg-red-50 border-red-200"
                        : "bg-amber-50 border-amber-200"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle
                        className={`h-5 w-5 ${
                          (zaroniaSummary?.days_remaining || 999) < 180
                            ? "text-red-600"
                            : "text-amber-600"
                        }`}
                      />
                      <span className="font-medium">JIBAR Discontinuation Deadline</span>
                    </div>
                    <p className="text-2xl font-bold">December 31, 2026</p>
                    <p className="text-sm text-slate-600">
                      {zaroniaSummary?.days_remaining || "–"} days remaining
                    </p>
                  </div>

                  {/* Status breakdown */}
                  {zaroniaSummary?.by_status && (
                    <div className="grid grid-cols-5 gap-4">
                      {Object.entries(zaroniaSummary.by_status).map(([status, count]) => (
                        <div key={status} className="p-3 bg-slate-50 rounded-lg text-center">
                          <p className="text-xs text-slate-500 capitalize">
                            {status.replace(/_/g, " ")}
                          </p>
                          <p className="text-xl font-bold">{count}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Loan assessment */}
                  <div className="space-y-3">
                    <h4 className="font-medium">Check Loan Transition Status</h4>
                    {loans.slice(0, 8).map((loan) => {
                      const transition = zaroniaCache.get(loan.loan_id);
                      return (
                        <div
                          key={loan.loan_id}
                          className="flex items-center justify-between p-3 border rounded-lg"
                        >
                          <div>
                            <p className="font-medium">{loan.borrower_name}</p>
                            <p className="text-xs text-slate-500">{loan.loan_id}</p>
                          </div>
                          {transition ? (
                            <Badge className={getUrgencyColor(transition.urgency)}>
                              {transition.transition_status}
                            </Badge>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => checkZARONIA(loan.loan_id)}
                            >
                              Assess
                            </Button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* SFDR 2.0 Tab */}
          <TabsContent value="sfdr">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <FileCheck className="h-5 w-5 text-emerald-500" />
                  SFDR 2.0 Classification (November 2025)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Category distribution */}
                  {sfdrSummary?.by_category && (
                    <div className="grid grid-cols-4 gap-4">
                      {Object.entries(SFDR_CATEGORIES).map(([key, cat]) => (
                        <div
                          key={key}
                          className={`p-4 rounded-lg ${cat.color}`}
                        >
                          <p className="text-sm font-medium">{cat.name}</p>
                          <p className="text-3xl font-bold">
                            {sfdrSummary.by_category[key] || 0}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Taxonomy alignment */}
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Average Taxonomy Alignment</span>
                      <span className="text-sm text-slate-500">
                        15% = meets 70% threshold
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Progress
                        value={sfdrSummary?.avg_taxonomy_alignment || 0}
                        className="flex-1 h-3"
                      />
                      <span className="text-xl font-bold">
                        {(sfdrSummary?.avg_taxonomy_alignment || 0).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Product classification */}
                  <div className="space-y-3">
                    <h4 className="font-medium">Classify Products</h4>
                    {loans.slice(0, 6).map((loan) => {
                      const classification = sfdrCache.get(loan.loan_id);
                      return (
                        <div
                          key={loan.loan_id}
                          className="flex items-center justify-between p-3 border rounded-lg"
                        >
                          <div>
                            <p className="font-medium">{loan.borrower_name}</p>
                            <p className="text-xs text-slate-500">{loan.loan_id}</p>
                          </div>
                          {classification ? (
                            <div className="flex items-center gap-2">
                              <Badge
                                className={
                                  SFDR_CATEGORIES[
                                    classification.new_classification as keyof typeof SFDR_CATEGORIES
                                  ]?.color || "bg-slate-100"
                                }
                              >
                                {classification.category_details.name}
                              </Badge>
                            </div>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => checkSFDR(loan.loan_id)}
                            >
                              Classify
                            </Button>
                          )}
                        </div>
                      );
                    })}
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
