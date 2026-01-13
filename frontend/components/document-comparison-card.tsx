"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertTriangle,
  CheckCircle,
  FileText,
  GitCompare,
  Loader2,
  ShieldAlert,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from "lucide-react";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// Types
interface MaterialChange {
  category: string;
  original_text: string;
  new_text: string;
  materiality: string;
  impact_description: string;
  risk_score: number;
  recommendation: string;
}

interface ExtractedClause {
  clause_type: string;
  text: string;
  location: string | null;
  confidence: number;
}

interface ComparisonAnalysis {
  similarity_score: number;
  total_changes: number;
  material_changes: MaterialChange[];
  extracted_clauses_doc1: ExtractedClause[];
  extracted_clauses_doc2: ExtractedClause[];
  summary: string;
  risk_assessment: string;
  recommendations: string[];
}

interface ComparisonResult {
  success: boolean;
  analysis: ComparisonAnalysis;
  meta: {
    engine: string;
    version: string;
    has_ai_analysis: boolean;
  };
  error?: string;
}

// API call function
async function compareDocuments(
  text1: string,
  text2: string,
  context?: string
): Promise<ComparisonResult> {
  const response = await fetch(`${API_BASE}/api/documents/compare/semantic`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text1, text2, context }),
  });
  return response.json();
}

// Materiality badge styling
function getMaterialityBadge(materiality: string) {
  const styles: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; icon: React.ReactNode }> = {
    CRITICAL: { variant: "destructive", icon: <ShieldAlert className="w-3 h-3 mr-1" /> },
    HIGH: { variant: "destructive", icon: <AlertTriangle className="w-3 h-3 mr-1" /> },
    MEDIUM: { variant: "default", icon: <TrendingUp className="w-3 h-3 mr-1" /> },
    LOW: { variant: "secondary", icon: <TrendingDown className="w-3 h-3 mr-1" /> },
    INFORMATIONAL: { variant: "outline", icon: <Minus className="w-3 h-3 mr-1" /> },
  };
  const style = styles[materiality] || styles.MEDIUM;
  return (
    <Badge variant={style.variant} className="flex items-center">
      {style.icon}
      {materiality}
    </Badge>
  );
}

// Risk Assessment badge
function getRiskBadge(assessment: string) {
  if (assessment.includes("CRITICAL") || assessment.includes("HIGH")) {
    return <Badge variant="destructive" className="text-sm">{assessment}</Badge>;
  }
  if (assessment.includes("MEDIUM")) {
    return <Badge variant="default" className="text-sm">{assessment}</Badge>;
  }
  if (assessment.includes("LOW")) {
    return <Badge variant="secondary" className="text-sm">{assessment}</Badge>;
  }
  return <Badge variant="outline" className="text-sm">{assessment}</Badge>;
}

// Category icons mapping
function getCategoryIcon(category: string) {
  const icons: Record<string, string> = {
    FINANCIAL_TERMS: "💰",
    COVENANT: "📜",
    DEFAULT_PROVISION: "⚠️",
    INTEREST_RATE: "📈",
    COLLATERAL: "🏦",
    MATURITY: "📅",
    PREPAYMENT: "💵",
    LEGAL_ENTITY: "🏢",
    GOVERNANCE: "⚖️",
    OTHER: "📋",
  };
  return icons[category] || "📄";
}

// Component
export default function DocumentComparisonCard() {
  const [document1, setDocument1] = useState("");
  const [document2, setDocument2] = useState("");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [expandedChanges, setExpandedChanges] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState("summary");

  // Run comparison
  const handleCompare = async () => {
    if (!document1.trim() || !document2.trim()) return;
    
    setLoading(true);
    try {
      const data = await compareDocuments(document1, document2, context || undefined);
      setResult(data);
      if (data.success) setActiveTab("summary");
    } catch (error) {
      setResult({
        success: false,
        error: "Failed to connect to comparison service",
        analysis: {} as ComparisonAnalysis,
        meta: { engine: "error", version: "0", has_ai_analysis: false },
      });
    } finally {
      setLoading(false);
    }
  };

  // Toggle change expansion
  const toggleChange = (index: number) => {
    const newExpanded = new Set(expandedChanges);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedChanges(newExpanded);
  };

  // Load sample documents for testing
  const loadSample = () => {
    setDocument1(`CREDIT AGREEMENT

This Credit Agreement ("Agreement") is entered into as of January 1, 2024.

SECTION 1. INTEREST RATE
The applicable interest rate shall be 5.5% per annum.

SECTION 2. MATURITY
The loan shall mature on December 31, 2029.

SECTION 3. COVENANTS
Borrower shall maintain:
- Debt-to-EBITDA ratio not exceeding 3.5x
- Interest Coverage Ratio of at least 3.0x
- Current Ratio of at least 1.2x

SECTION 4. EVENTS OF DEFAULT
An Event of Default occurs upon:
- Failure to make any payment within 5 business days
- Breach of any covenant not cured within 30 days
- Material adverse change in financial condition`);
    
    setDocument2(`CREDIT AGREEMENT (AMENDED)

This Credit Agreement ("Agreement") is entered into as of January 1, 2024.

SECTION 1. INTEREST RATE
The applicable interest rate shall be 6.25% per annum.

SECTION 2. MATURITY
The loan shall mature on June 30, 2028.

SECTION 3. COVENANTS
Borrower shall maintain:
- Debt-to-EBITDA ratio not exceeding 4.0x
- Interest Coverage Ratio of at least 2.5x
- Current Ratio of at least 1.0x
- NEW: ESG Compliance Score above 60

SECTION 4. EVENTS OF DEFAULT
An Event of Default occurs upon:
- Failure to make any payment within 3 business days
- Breach of any covenant not cured within 15 days
- Material adverse change in financial condition
- NEW: ESG Score falling below 40`);
    
    setContext("Commercial real estate loan amendment");
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitCompare className="w-6 h-6 text-blue-600" />
            <CardTitle>Document Comparison</CardTitle>
            <Badge variant="outline" className="ml-2">
              <Sparkles className="w-3 h-3 mr-1" />
              AI-Powered
            </Badge>
          </div>
          <Button variant="outline" size="sm" onClick={loadSample}>
            Load Sample
          </Button>
        </div>
        <CardDescription>
          Compare loan documents using semantic AI analysis to identify material changes
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Input Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="doc1" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Original Document
            </Label>
            <Textarea
              id="doc1"
              placeholder="Paste original document content..."
              className="min-h-[200px] font-mono text-sm"
              value={document1}
              onChange={(e) => setDocument1(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="doc2" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Amended/New Document
            </Label>
            <Textarea
              id="doc2"
              placeholder="Paste amended document content..."
              className="min-h-[200px] font-mono text-sm"
              value={document2}
              onChange={(e) => setDocument2(e.target.value)}
            />
          </div>
        </div>

        {/* Context Input */}
        <div className="space-y-2">
          <Label htmlFor="context">Context (Optional)</Label>
          <Input
            id="context"
            placeholder="e.g., Commercial real estate loan, SBA 7(a), etc."
            value={context}
            onChange={(e) => setContext(e.target.value)}
          />
        </div>

        {/* Compare Button */}
        <Button
          onClick={handleCompare}
          disabled={loading || !document1.trim() || !document2.trim()}
          className="w-full"
          size="lg"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Analyzing Documents...
            </>
          ) : (
            <>
              <GitCompare className="w-4 h-4 mr-2" />
              Compare Documents
            </>
          )}
        </Button>

        {/* Results Section */}
        {result && (
          <div className="space-y-4 pt-4 border-t">
            {result.success ? (
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="summary">Summary</TabsTrigger>
                  <TabsTrigger value="changes">
                    Changes ({result.analysis.material_changes?.length || 0})
                  </TabsTrigger>
                  <TabsTrigger value="clauses">Clauses</TabsTrigger>
                  <TabsTrigger value="recommendations">Actions</TabsTrigger>
                </TabsList>

                {/* Summary Tab */}
                <TabsContent value="summary" className="space-y-4">
                  {/* Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">Similarity</div>
                      <div className="text-2xl font-bold">
                        {result.analysis.similarity_score?.toFixed(1)}%
                      </div>
                      <Progress
                        value={result.analysis.similarity_score}
                        className="mt-2"
                      />
                    </Card>
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">Total Changes</div>
                      <div className="text-2xl font-bold">
                        {result.analysis.total_changes}
                      </div>
                    </Card>
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">Material Changes</div>
                      <div className="text-2xl font-bold text-orange-600">
                        {result.analysis.material_changes?.length || 0}
                      </div>
                    </Card>
                    <Card className="p-4">
                      <div className="text-sm text-muted-foreground">Risk Level</div>
                      <div className="mt-1">
                        {getRiskBadge(result.analysis.risk_assessment || "UNKNOWN")}
                      </div>
                    </Card>
                  </div>

                  {/* AI Summary */}
                  <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="w-4 h-4 text-blue-600" />
                      <span className="font-semibold">AI Analysis Summary</span>
                      {result.meta.has_ai_analysis && (
                        <Badge variant="outline" className="ml-auto">
                          <CheckCircle className="w-3 h-3 mr-1 text-green-600" />
                          Gemini Enhanced
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm">{result.analysis.summary}</p>
                  </Card>
                </TabsContent>

                {/* Changes Tab */}
                <TabsContent value="changes" className="space-y-3">
                  {result.analysis.material_changes?.length > 0 ? (
                    result.analysis.material_changes.map((change, idx) => (
                      <Card
                        key={idx}
                        className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
                        onClick={() => toggleChange(idx)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-xl">{getCategoryIcon(change.category)}</span>
                            <div>
                              <div className="font-medium">{change.category.replace(/_/g, " ")}</div>
                              <div className="text-sm text-muted-foreground">
                                Risk Score: {(change.risk_score * 100).toFixed(0)}%
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {getMaterialityBadge(change.materiality)}
                            {expandedChanges.has(idx) ? (
                              <ChevronUp className="w-4 h-4" />
                            ) : (
                              <ChevronDown className="w-4 h-4" />
                            )}
                          </div>
                        </div>

                        {expandedChanges.has(idx) && (
                          <div className="mt-4 space-y-3 pt-3 border-t">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              <div>
                                <div className="text-xs font-semibold text-red-600 mb-1">Original:</div>
                                <div className="text-sm bg-red-50 dark:bg-red-950 p-2 rounded border border-red-200">
                                  {change.original_text || "N/A"}
                                </div>
                              </div>
                              <div>
                                <div className="text-xs font-semibold text-green-600 mb-1">New:</div>
                                <div className="text-sm bg-green-50 dark:bg-green-950 p-2 rounded border border-green-200">
                                  {change.new_text || "N/A"}
                                </div>
                              </div>
                            </div>
                            <div>
                              <div className="text-xs font-semibold mb-1">Impact:</div>
                              <div className="text-sm">{change.impact_description}</div>
                            </div>
                            <div>
                              <div className="text-xs font-semibold mb-1">Recommendation:</div>
                              <div className="text-sm text-blue-600">{change.recommendation}</div>
                            </div>
                          </div>
                        )}
                      </Card>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-600" />
                      <p>No material changes detected</p>
                    </div>
                  )}
                </TabsContent>

                {/* Clauses Tab */}
                <TabsContent value="clauses" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card className="p-4">
                      <h4 className="font-semibold mb-3">Original Document Clauses</h4>
                      <div className="space-y-2">
                        {result.analysis.extracted_clauses_doc1?.map((clause, idx) => (
                          <div key={idx} className="text-sm p-2 bg-muted rounded">
                            <div className="flex items-center justify-between">
                              <Badge variant="outline">{clause.clause_type}</Badge>
                              <span className="text-xs text-muted-foreground">
                                {(clause.confidence * 100).toFixed(0)}% conf
                              </span>
                            </div>
                            <div className="mt-1 text-xs truncate">{clause.text}</div>
                          </div>
                        )) || <p className="text-sm text-muted-foreground">No clauses extracted</p>}
                      </div>
                    </Card>
                    <Card className="p-4">
                      <h4 className="font-semibold mb-3">Amended Document Clauses</h4>
                      <div className="space-y-2">
                        {result.analysis.extracted_clauses_doc2?.map((clause, idx) => (
                          <div key={idx} className="text-sm p-2 bg-muted rounded">
                            <div className="flex items-center justify-between">
                              <Badge variant="outline">{clause.clause_type}</Badge>
                              <span className="text-xs text-muted-foreground">
                                {(clause.confidence * 100).toFixed(0)}% conf
                              </span>
                            </div>
                            <div className="mt-1 text-xs truncate">{clause.text}</div>
                          </div>
                        )) || <p className="text-sm text-muted-foreground">No clauses extracted</p>}
                      </div>
                    </Card>
                  </div>
                </TabsContent>

                {/* Recommendations Tab */}
                <TabsContent value="recommendations" className="space-y-3">
                  {result.analysis.recommendations?.length > 0 ? (
                    <div className="space-y-2">
                      {result.analysis.recommendations.map((rec, idx) => (
                        <Card key={idx} className="p-3 flex items-start gap-3">
                          <div className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-sm font-bold text-blue-600">
                            {idx + 1}
                          </div>
                          <div className="text-sm">{rec}</div>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-600" />
                      <p>No specific actions required</p>
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            ) : (
              <Card className="p-4 bg-red-50 dark:bg-red-950 border-red-200">
                <div className="flex items-center gap-2 text-red-600">
                  <AlertTriangle className="w-5 h-5" />
                  <span className="font-semibold">Comparison Failed</span>
                </div>
                <p className="text-sm mt-2">{result.error}</p>
              </Card>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
