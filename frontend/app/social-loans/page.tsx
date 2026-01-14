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
  Loader2,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Heart,
  Users,
  FileText,
  Home,
  Briefcase,
  GraduationCap,
  Utensils,
} from "lucide-react";
import {
  fetchLoans,
  fetchSocialPortfolioSummary,
  fetchSocialLoan,
  validateSocialLoan,
  fetchSocialLoanReport,
  fetchSLPCategories,
  type Loan,
  type SocialLoanClassification,
  type SocialLoanValidation,
} from "@/lib/api";

// SLP 2025 Categories with icons
const CATEGORY_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  AFFORDABLE_INFRASTRUCTURE: { icon: Home, color: "bg-blue-100 text-blue-800", label: "Infrastructure" },
  ESSENTIAL_SERVICES: { icon: GraduationCap, color: "bg-purple-100 text-purple-800", label: "Essential Services" },
  AFFORDABLE_HOUSING: { icon: Home, color: "bg-emerald-100 text-emerald-800", label: "Affordable Housing" },
  EMPLOYMENT_GENERATION: { icon: Briefcase, color: "bg-amber-100 text-amber-800", label: "Employment" },
  FOOD_SECURITY: { icon: Utensils, color: "bg-orange-100 text-orange-800", label: "Food Security" },
  SOCIOECONOMIC_ADVANCEMENT: { icon: Users, color: "bg-indigo-100 text-indigo-800", label: "Socioeconomic" },
  UNCLASSIFIED: { icon: AlertTriangle, color: "bg-slate-100 text-slate-800", label: "Unclassified" },
};

function getScoreColor(score: number): string {
  if (score >= 70) return "bg-emerald-100 text-emerald-800";
  if (score >= 50) return "bg-amber-100 text-amber-800";
  return "bg-red-100 text-red-800";
}

function getComplianceIcon(isCompliant: boolean) {
  return isCompliant 
    ? <CheckCircle className="h-4 w-4 text-emerald-600" />
    : <XCircle className="h-4 w-4 text-red-600" />;
}

// SLP 2025 - 4 Core Components
const SLP_COMPONENTS = [
  { key: "use_of_proceeds", label: "Use of Proceeds", weight: 35 },
  { key: "project_evaluation", label: "Project Evaluation", weight: 25 },
  { key: "proceeds_management", label: "Proceeds Management", weight: 20 },
  { key: "reporting", label: "Reporting (Mandatory)", weight: 20 },
];

interface LoanDetails {
  loan: Loan;
  validation?: SocialLoanValidation;
  classification?: SocialLoanClassification;
  loading: boolean;
}

export default function SocialLoansPage() {
  const [loading, setLoading] = useState(true);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [selectedLoan, setSelectedLoan] = useState<string | null>(null);
  const [loanDetails, setLoanDetails] = useState<Map<string, LoanDetails>>(new Map());
  const [activeTab, setActiveTab] = useState("overview");
  const [summary, setSummary] = useState<{
    total_social_loans: number;
    by_category: Array<{
      category: string;
      loan_count: number;
      avg_score: number;
      beneficiaries: number;
    }>;
  } | null>(null);
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [loansRes, summaryRes, categoriesRes] = await Promise.allSettled([
        fetchLoans(),
        fetchSocialPortfolioSummary(),
        fetchSLPCategories(),
      ]);

      if (loansRes.status === "fulfilled") {
        setLoans(loansRes.value.loans || []);
      }

      if (summaryRes.status === "fulfilled" && summaryRes.value.success) {
        setSummary({
          total_social_loans: summaryRes.value.total_social_loans,
          by_category: summaryRes.value.by_category || [],
        });
      }

      if (categoriesRes.status === "fulfilled") {
        setCategories(categoriesRes.value.categories || []);
      }
    } catch (err) {
      console.error("Failed to load social loans:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadLoanDetails(loanId: string, loanPurpose?: string) {
    const existing = loanDetails.get(loanId);
    if (existing && !existing.loading && existing.validation) return;

    const loan = loans.find((l) => l.loan_id === loanId);
    if (!loan) return;

    setLoanDetails((prev) => {
      const next = new Map(prev);
      next.set(loanId, { loan, loading: true });
      return next;
    });

    try {
      // Use loan_type as purpose if available
      const purpose = loanPurpose || loan.loan_type || "";
      
      const [validationRes, classificationRes] = await Promise.allSettled([
        validateSocialLoan(loanId, purpose),
        fetchSocialLoan(loanId),
      ]);

      setLoanDetails((prev) => {
        const next = new Map(prev);
        next.set(loanId, {
          loan,
          validation: validationRes.status === "fulfilled" && validationRes.value.success
            ? validationRes.value
            : undefined,
          classification: classificationRes.status === "fulfilled" && classificationRes.value.success
            ? classificationRes.value
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
      const result = await fetchSocialLoanReport(loanId);
      if (result.success) {
        alert(`Social Impact Report generated for ${loanId}`);
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
          <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
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
            <div className="p-3 rounded-2xl bg-gradient-to-br from-pink-500 to-purple-600 shadow-lg">
              <Heart className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">Social Loans</h1>
              <p className="text-slate-500">
                LMA Social Loan Principles (SLP March 2025)
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-gradient-to-r from-purple-50 to-pink-50 text-purple-700 border-purple-200">
              SLP March 2025
            </Badge>
            <Button variant="outline" onClick={loadData} className="hover:bg-purple-50 transition-colors">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-16 h-16 rounded-full bg-gradient-to-br from-purple-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-gradient-to-br from-purple-400 to-purple-500">
                  <Heart className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">Social Loans</p>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {summary?.total_social_loans || 0}
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
                <p className="text-sm text-slate-500">SLP Compliant</p>
              </div>
              <p className="text-2xl font-bold text-emerald-600">
                {summary?.by_category?.filter(c => c.avg_score >= 70).length || 0}
              </p>
            </CardContent>
          </Card>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-16 h-16 rounded-full bg-gradient-to-br from-blue-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-gradient-to-br from-blue-400 to-blue-500">
                  <Users className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">Beneficiaries</p>
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {(summary?.by_category?.reduce((sum, c) => sum + (c.beneficiaries || 0), 0) || 0).toLocaleString()}
              </p>
            </CardContent>
          </Card>
          <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
            <CardContent className="pt-6 relative">
              <div className="absolute -top-4 -right-4 w-16 h-16 rounded-full bg-gradient-to-br from-amber-100 to-transparent opacity-50 group-hover:scale-150 transition-transform" />
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500">
                  <Briefcase className="h-4 w-4 text-white" />
                </div>
                <p className="text-sm text-slate-500">Categories</p>
              </div>
              <p className="text-2xl font-bold text-amber-600">
                {summary?.by_category?.length || 0} / 6
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-3 gap-2 bg-transparent p-1 h-auto">
            <TabsTrigger 
              value="overview" 
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-500 data-[state=active]:to-pink-600 data-[state=active]:text-white data-[state=active]:shadow-lg px-4 py-2.5 rounded-xl transition-all duration-200 flex items-center gap-2"
            >
              <Heart className="h-4 w-4" />
              Loan Portfolio
            </TabsTrigger>
            <TabsTrigger 
              value="validation"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-500 data-[state=active]:to-teal-600 data-[state=active]:text-white data-[state=active]:shadow-lg px-4 py-2.5 rounded-xl transition-all duration-200 flex items-center gap-2"
            >
              <FileText className="h-4 w-4" />
              SLP Validation
            </TabsTrigger>
            <TabsTrigger 
              value="categories"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-amber-500 data-[state=active]:to-orange-600 data-[state=active]:text-white data-[state=active]:shadow-lg px-4 py-2.5 rounded-xl transition-all duration-200 flex items-center gap-2"
            >
              <Briefcase className="h-4 w-4" />
              SLP Categories
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Social Loan Portfolio</CardTitle>
              </CardHeader>
              <CardContent>
                {loans.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <Heart className="h-12 w-12 mx-auto mb-4 text-slate-300" />
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
                            <Badge className={loan.status === "GREEN" ? "bg-emerald-100 text-emerald-800" : loan.status === "AMBER" ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"}>
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
                                setActiveTab("validation");
                              }}
                            >
                              Assess SLP
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

          {/* SLP Validation Tab */}
          <TabsContent value="validation">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Loan List */}
              <Card className="lg:col-span-1 overflow-hidden border-0 shadow-lg">
                <CardHeader className="bg-gradient-to-r from-purple-500 to-pink-600 text-white">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Heart className="h-4 w-4" />
                    Select Loan
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 max-h-[500px] overflow-y-auto p-4">
                  {loans.slice(0, 20).map((loan) => (
                    <div
                      key={loan.loan_id}
                      onClick={() => {
                        setSelectedLoan(loan.loan_id);
                        loadLoanDetails(loan.loan_id);
                      }}
                      className={`p-4 rounded-xl border cursor-pointer transition-all hover:shadow-md ${
                        selectedLoan === loan.loan_id
                          ? "border-purple-500 bg-gradient-to-r from-purple-50 to-pink-50 shadow-md"
                          : "hover:bg-slate-50 border-slate-200"
                      }`}
                    >
                      <p className="font-semibold text-slate-900">{loan.borrower_name}</p>
                      <p className="text-xs text-slate-500 mt-1">{loan.loan_id}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* SLP Details */}
              <Card className="lg:col-span-2 overflow-hidden border-0 shadow-lg">
                <CardHeader className="bg-gradient-to-r from-emerald-500 to-teal-600 text-white">
                  <CardTitle className="text-base flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    SLP Compliance Assessment
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
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

                      const validation = details.validation;
                      if (!validation) {
                        return (
                          <div className="text-center py-8 text-slate-500">
                            <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-amber-400" />
                            <p>No SLP assessment available.</p>
                            <p className="text-sm">Click Assess SLP to validate this loan.</p>
                          </div>
                        );
                      }

                      return (
                        <div className="space-y-6">
                          {/* Overall Score */}
                          <div className="p-5 bg-gradient-to-r from-slate-50 to-slate-100 rounded-xl border">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-lg">Overall SLP Score</span>
                                {getComplianceIcon(validation.is_slp_compliant)}
                              </div>
                              <Badge className={`${validation.is_slp_compliant ? 'bg-gradient-to-r from-emerald-500 to-teal-600' : 'bg-gradient-to-r from-red-500 to-rose-600'} text-white border-0 px-4 py-2 text-sm font-semibold shadow-md`}>
                                {validation.is_slp_compliant ? "COMPLIANT" : "NON-COMPLIANT"}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="flex-1 h-4 bg-slate-200 rounded-full overflow-hidden">
                                <div 
                                  className={`h-full rounded-full transition-all ${validation.scores.overall >= 70 ? 'bg-gradient-to-r from-emerald-400 to-teal-500' : 'bg-gradient-to-r from-amber-400 to-orange-500'}`}
                                  style={{ width: `${validation.scores.overall}%` }}
                                />
                              </div>
                              <span className="text-2xl font-bold text-slate-900">
                                {validation.scores.overall.toFixed(1)}%
                              </span>
                            </div>
                          </div>

                          {/* Social Category */}
                          <div className="p-4 border rounded-lg">
                            <p className="text-sm text-slate-500 mb-2">Social Category (SLP Appendix 1)</p>
                            <Badge className={CATEGORY_CONFIG[validation.social_category]?.color || "bg-slate-100"}>
                              {CATEGORY_CONFIG[validation.social_category]?.label || validation.social_category}
                            </Badge>
                          </div>

                          {/* Target Populations */}
                          {validation.target_populations.length > 0 && (
                            <div className="p-4 border rounded-lg">
                              <p className="text-sm text-slate-500 mb-2">Target Populations (SLP Appendix 2)</p>
                              <div className="flex flex-wrap gap-2">
                                {validation.target_populations.map((pop) => (
                                  <Badge key={pop} variant="outline">
                                    {pop.replace(/_/g, " ")}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* 4 SLP Components */}
                          <div>
                            <h4 className="font-medium mb-3">4 SLP Core Components</h4>
                            <div className="space-y-3">
                              {SLP_COMPONENTS.map((component) => {
                                const score = validation.scores[component.key as keyof typeof validation.scores] || 0;
                                return (
                                  <div
                                    key={component.key}
                                    className="flex items-center justify-between p-3 border rounded-lg"
                                  >
                                    <div className="flex items-center gap-2">
                                      {score >= 70 ? (
                                        <CheckCircle className="h-4 w-4 text-emerald-600" />
                                      ) : score >= 50 ? (
                                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                                      ) : (
                                        <XCircle className="h-4 w-4 text-red-600" />
                                      )}
                                      <span className="text-sm">
                                        {component.label}
                                      </span>
                                      <span className="text-xs text-slate-400">
                                        ({component.weight}%)
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <Progress
                                        value={score}
                                        className="w-20 h-2"
                                      />
                                      <span className="text-sm font-medium w-12 text-right">
                                        {score.toFixed(0)}%
                                      </span>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>

                          {/* Recommendations */}
                          {validation.recommendations?.length > 0 && (
                            <div>
                              <h4 className="font-medium mb-2">Recommendations</h4>
                              <ul className="list-disc list-inside space-y-1 text-sm text-slate-600">
                                {validation.recommendations.slice(0, 3).map((rec, idx) => (
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
                      <FileText className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                      <p>Select a loan to view SLP assessment</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Categories Tab */}
          <TabsContent value="categories">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Heart className="h-5 w-5 text-purple-500" />
                  SLP Eligible Social Project Categories (March 2025)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(CATEGORY_CONFIG).filter(([key]) => key !== "UNCLASSIFIED").map(([key, config]) => {
                    const Icon = config.icon;
                    const categoryData = summary?.by_category?.find(c => c.category === key);
                    return (
                      <Card key={key} className="border">
                        <CardContent className="pt-6">
                          <div className="flex items-center gap-3 mb-3">
                            <div className={`p-2 rounded-lg ${config.color}`}>
                              <Icon className="h-5 w-5" />
                            </div>
                            <div>
                              <p className="font-medium text-sm">{config.label}</p>
                              <p className="text-xs text-slate-500">{key}</p>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-4 mt-4">
                            <div>
                              <p className="text-xs text-slate-500">Loans</p>
                              <p className="text-lg font-bold">{categoryData?.loan_count || 0}</p>
                            </div>
                            <div>
                              <p className="text-xs text-slate-500">Avg Score</p>
                              <p className="text-lg font-bold">{(categoryData?.avg_score || 0).toFixed(0)}%</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

        </Tabs>
      </main>
    </div>
  );
}
