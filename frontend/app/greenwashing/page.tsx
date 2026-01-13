"use client";

import { useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Search,
  Loader2,
  Leaf,
  ExternalLink,
  ShieldAlert,
  ChevronDown,
  Newspaper,
  Globe,
  Calendar,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

interface ClaimResult {
  claim: string;
  category: string;
  verification_score: number;
  verdict: string;
  language_flags: string[];
  greenwashing_risk: string;
  contradictions: Array<{
    title: string;
    source: string;
    snippet: string;
    severity: string;
  }>;
  supporting_evidence: Array<{
    title: string;
    source: string;
    snippet: string;
  }>;
}

interface GreenwashingResult {
  borrower: string;
  claims_analyzed: number;
  overall_score: number;
  overall_risk: string;
  results: ClaimResult[];
  recommendation: string;
}

export default function GreenwashingPage() {
  const [borrowerName, setBorrowerName] = useState("");
  const [claimsText, setClaimsText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GreenwashingResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    if (!borrowerName || !claimsText) {
      setError("Please enter borrower name and at least one ESG claim");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const claims = claimsText
        .split("\n")
        .filter((line) => line.trim())
        .map((text) => ({ text: text.trim(), category: "general" }));

      const response = await fetch(
        `${API_BASE_URL}/api/esg/greenwashing/detect`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            borrower_name: borrowerName,
            claims: claims,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to analyze claims");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError("Failed to analyze. Make sure the API is running.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function getRiskColor(risk: string) {
    switch (risk) {
      case "HIGH":
        return "bg-red-100 text-red-800 border-red-200";
      case "MEDIUM":
        return "bg-amber-100 text-amber-800 border-amber-200";
      case "LOW":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      default:
        return "bg-slate-100 text-slate-800 border-slate-200";
    }
  }

  function getVerdictIcon(verdict: string) {
    switch (verdict) {
      case "VERIFIED":
        return <CheckCircle className="h-5 w-5 text-emerald-600" />;
      case "CONTRADICTED":
        return <XCircle className="h-5 w-5 text-red-600" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-amber-600" />;
    }
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-orange-500 to-red-600 shadow-lg">
              <ShieldAlert className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">
                Greenwashing Detection
              </h1>
              <p className="text-slate-500">
                Verify ESG claims against external sources. Detect potential
                greenwashing before regulators do.
              </p>
            </div>
          </div>
        </div>

        {/* Input Section */}
        <Card className="mb-6 overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-slate-50 to-white border-b">
            <CardTitle className="text-lg flex items-center gap-2">
              <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600">
                <Search className="h-4 w-4 text-white" />
              </div>
              Analyze ESG Claims
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Borrower Name
              </label>
              <input
                type="text"
                value={borrowerName}
                onChange={(e) => setBorrowerName(e.target.value)}
                placeholder="e.g., Acme Corporation"
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                ESG Claims (one per line)
              </label>
              <textarea
                value={claimsText}
                onChange={(e) => setClaimsText(e.target.value)}
                placeholder="Carbon neutral by 2030&#10;100% renewable energy by 2025&#10;Zero waste to landfill"
                rows={4}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <Button
              onClick={handleAnalyze}
              disabled={loading}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Detect Greenwashing
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Results Section */}
        {result && (
          <div className="space-y-6">
            {/* Overall Result - Modern Hero Card */}
            <Card className="overflow-hidden border-0 shadow-xl">
              {/* Risk Level Hero */}
              <div className={`p-6 ${
                result.overall_risk === 'CRITICAL' || result.overall_risk === 'HIGH' 
                  ? 'bg-gradient-to-r from-red-600 via-red-500 to-orange-500'
                  : result.overall_risk === 'MEDIUM' 
                    ? 'bg-gradient-to-r from-amber-500 via-amber-400 to-yellow-400'
                    : 'bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-500'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white/80 text-sm font-medium uppercase tracking-wider">Overall Assessment</p>
                    <h3 className="text-2xl font-bold text-white mt-1">{result.borrower}</h3>
                  </div>
                  <div className="text-right">
                    <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-full px-4 py-2">
                      <ShieldAlert className="h-5 w-5 text-white" />
                      <span className="text-lg font-bold text-white">
                        {result.overall_risk} RISK
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Recommendation & Stats */}
              <CardContent className="p-6 bg-white">
                <div className="flex items-center gap-6">
                  {/* Risk Gauge */}
                  <div className="flex-shrink-0">
                    <div className="relative w-24 h-24">
                      <svg className="w-24 h-24 transform -rotate-90">
                        <circle cx="48" cy="48" r="40" stroke="#e5e7eb" strokeWidth="8" fill="none" />
                        <circle 
                          cx="48" cy="48" r="40" 
                          stroke={result.overall_risk === 'CRITICAL' || result.overall_risk === 'HIGH' ? '#ef4444' : result.overall_risk === 'MEDIUM' ? '#f59e0b' : '#10b981'}
                          strokeWidth="8" 
                          fill="none"
                          strokeLinecap="round"
                          strokeDasharray={`${(1 - (result.overall_score || 0)) * 251} 251`}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-xl font-bold text-slate-800">
                          {((1 - (result.overall_score || 0)) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <p className="text-center text-xs text-slate-500 mt-1">Risk Score</p>
                  </div>
                  
                  {/* Recommendation */}
                  <div className="flex-1 p-4 bg-slate-50 rounded-xl border border-slate-100">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className={`h-5 w-5 flex-shrink-0 ${
                        result.overall_risk === 'CRITICAL' || result.overall_risk === 'HIGH' 
                          ? 'text-red-500' 
                          : result.overall_risk === 'MEDIUM' ? 'text-amber-500' : 'text-emerald-500'
                      }`} />
                      <div>
                        <p className="text-sm font-medium text-slate-700">Recommendation</p>
                        <p className="text-slate-600 mt-1">{result.recommendation}</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Quick Stats */}
                <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-slate-800">{result.claims_analyzed}</p>
                    <p className="text-xs text-slate-500">Claims Analyzed</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-red-600">
                      {result.results.filter(r => r.verdict === 'CONTRADICTED').length}
                    </p>
                    <p className="text-xs text-slate-500">Contradicted</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-emerald-600">
                      {result.results.filter(r => r.verdict === 'VERIFIED').length}
                    </p>
                    <p className="text-xs text-slate-500">Verified</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Individual Claims - Modern Accordion Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
                    <Search className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-800">
                      Claim Analysis
                    </h3>
                    <p className="text-sm text-slate-500">{result.claims_analyzed} ESG claims verified against external sources</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Badge className="bg-red-100 text-red-700 border-0 px-3 py-1">
                    <XCircle className="h-3.5 w-3.5 mr-1" />
                    {result.results.filter(r => r.verdict === 'CONTRADICTED').length} Issues
                  </Badge>
                  <Badge className="bg-emerald-100 text-emerald-700 border-0 px-3 py-1">
                    <CheckCircle className="h-3.5 w-3.5 mr-1" />
                    {result.results.filter(r => r.verdict === 'VERIFIED').length} Verified
                  </Badge>
                </div>
              </div>

              {result.results.map((claim, index) => (
                <Collapsible key={index} defaultOpen={index === 0}>
                  <Card className={`overflow-hidden transition-all duration-300 hover:shadow-xl border-0 shadow-md ${
                    claim.verdict === 'CONTRADICTED' 
                      ? 'bg-gradient-to-br from-red-50 via-white to-orange-50/30' 
                      : claim.verdict === 'VERIFIED' 
                        ? 'bg-gradient-to-br from-emerald-50 via-white to-teal-50/30' 
                        : 'bg-gradient-to-br from-amber-50 via-white to-yellow-50/30'
                  }`}>
                    <CollapsibleTrigger asChild>
                      <CardHeader className="cursor-pointer group">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-4">
                            {/* Verdict Icon with Ring */}
                            <div className={`relative`}>
                              <div className={`p-3 rounded-2xl shadow-lg ${
                                claim.verdict === 'CONTRADICTED' 
                                  ? 'bg-gradient-to-br from-red-500 to-rose-600' 
                                  : claim.verdict === 'VERIFIED' 
                                    ? 'bg-gradient-to-br from-emerald-500 to-teal-600' 
                                    : 'bg-gradient-to-br from-amber-500 to-orange-600'
                              }`}>
                                {claim.verdict === 'CONTRADICTED' 
                                  ? <XCircle className="h-6 w-6 text-white" />
                                  : claim.verdict === 'VERIFIED'
                                    ? <CheckCircle className="h-6 w-6 text-white" />
                                    : <AlertTriangle className="h-6 w-6 text-white" />
                                }
                              </div>
                              {/* Pulse effect for contradicted */}
                              {claim.verdict === 'CONTRADICTED' && (
                                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                                </span>
                              )}
                            </div>
                            
                            <div className="flex-1">
                              <CardTitle className="text-lg font-semibold text-slate-800 group-hover:text-slate-900 transition-colors">
                                "{claim.claim}"
                              </CardTitle>
                              <div className="flex items-center gap-3 mt-2">
                                <Badge variant="outline" className={`${
                                  claim.verdict === 'CONTRADICTED' 
                                    ? 'border-red-300 text-red-700 bg-red-50' 
                                    : claim.verdict === 'VERIFIED'
                                      ? 'border-emerald-300 text-emerald-700 bg-emerald-50'
                                      : 'border-amber-300 text-amber-700 bg-amber-50'
                                }`}>
                                  {claim.verdict}
                                </Badge>
                                <span className="text-sm text-slate-500">
                                  {claim.contradictions?.length || 0} contradicting • {claim.supporting_evidence?.length || 0} supporting
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-3">
                            {/* Confidence Meter */}
                            <div className="text-right">
                              <p className="text-xs text-slate-400 uppercase tracking-wider">Confidence</p>
                              <div className="flex items-center gap-2 mt-1">
                                <div className="w-20 h-2 bg-slate-200 rounded-full overflow-hidden">
                                  <div 
                                    className={`h-full rounded-full transition-all duration-500 ${
                                      claim.verification_score < 0.3 ? 'bg-gradient-to-r from-red-500 to-rose-500' 
                                        : claim.verification_score < 0.7 ? 'bg-gradient-to-r from-amber-500 to-orange-500' 
                                        : 'bg-gradient-to-r from-emerald-500 to-teal-500'
                                    }`}
                                    style={{ width: `${Math.max(5, claim.verification_score * 100)}%` }}
                                  />
                                </div>
                                <span className="text-sm font-bold text-slate-700">
                                  {(claim.verification_score * 100).toFixed(0)}%
                                </span>
                              </div>
                            </div>
                            <ChevronDown className="h-5 w-5 text-slate-400 transition-transform duration-300 group-data-[state=open]:rotate-180" />
                          </div>
                        </div>
                      </CardHeader>
                    </CollapsibleTrigger>
                    
                    <CollapsibleContent>
                      <CardContent className="pt-0 pb-6 space-y-5">
                        {/* Language Flags */}
                        {claim.language_flags && claim.language_flags.length > 0 && (
                          <div className="flex flex-wrap gap-2 p-3 bg-amber-50/80 rounded-xl border border-amber-200/50">
                            <span className="text-xs font-medium text-amber-700 mr-2">⚠️ Language Concerns:</span>
                            {claim.language_flags.map((flag, i) => (
                              <Badge
                                key={i}
                                variant="outline"
                                className="text-amber-700 border-amber-300 bg-white text-xs"
                              >
                                {flag.replace(/_/g, " ")}
                              </Badge>
                            ))}
                          </div>
                        )}

                    {/* Contradictions - Modern Cards */}
                    {claim.contradictions && claim.contradictions.length > 0 && (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <div className="p-1.5 bg-gradient-to-br from-red-500 to-rose-600 rounded-lg">
                            <TrendingDown className="h-4 w-4 text-white" />
                          </div>
                          <p className="text-sm font-bold text-red-700">
                            Contradicting Evidence
                          </p>
                          <Badge className="bg-red-100 text-red-600 border-0 text-xs px-2">
                            {claim.contradictions.length}
                          </Badge>
                        </div>
                        <div className="grid gap-3">
                          {claim.contradictions.map((c, i) => (
                            <a
                              key={i}
                              href={c.source}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="group block p-4 bg-white rounded-xl border border-red-200/60 hover:border-red-400 hover:shadow-lg transition-all duration-200"
                            >
                              <div className="flex items-start gap-3">
                                <div className="p-2 bg-red-50 rounded-lg group-hover:bg-red-100 transition-colors">
                                  <Newspaper className="h-4 w-4 text-red-500" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium text-slate-800 group-hover:text-red-700 transition-colors line-clamp-2">
                                    {c.title}
                                  </p>
                                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                                    {c.snippet}
                                  </p>
                                </div>
                                <ExternalLink className="h-4 w-4 text-slate-300 group-hover:text-red-500 transition-colors flex-shrink-0" />
                              </div>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Supporting Evidence - Modern Cards */}
                    {claim.supporting_evidence && claim.supporting_evidence.length > 0 && (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <div className="p-1.5 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg">
                            <TrendingUp className="h-4 w-4 text-white" />
                          </div>
                          <p className="text-sm font-bold text-emerald-700">
                            Supporting Evidence
                          </p>
                          <Badge className="bg-emerald-100 text-emerald-600 border-0 text-xs px-2">
                            {claim.supporting_evidence.length}
                          </Badge>
                        </div>
                        <div className="grid gap-3">
                          {claim.supporting_evidence.map((s, i) => (
                            <a
                              key={i}
                              href={s.source}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="group block p-4 bg-white rounded-xl border border-emerald-200/60 hover:border-emerald-400 hover:shadow-lg transition-all duration-200"
                            >
                              <div className="flex items-start gap-3">
                                <div className="p-2 bg-emerald-50 rounded-lg group-hover:bg-emerald-100 transition-colors">
                                  <Globe className="h-4 w-4 text-emerald-500" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium text-slate-800 group-hover:text-emerald-700 transition-colors line-clamp-2">
                                    {s.title}
                                  </p>
                                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                                    {s.snippet}
                                  </p>
                                </div>
                                <ExternalLink className="h-4 w-4 text-slate-300 group-hover:text-emerald-500 transition-colors flex-shrink-0" />
                              </div>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                      </CardContent>
                    </CollapsibleContent>
                  </Card>
                </Collapsible>
              ))}
            </div>
          </div>
        )}

        {/* Demo Info */}
        {!result && !loading && (
          <Card className="bg-emerald-50 border-emerald-200">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <Leaf className="h-8 w-8 text-emerald-600 flex-shrink-0" />
                <div>
                  <h3 className="font-bold text-emerald-900">
                    Why Greenwashing Detection?
                  </h3>
                  <p className="text-emerald-700 mt-1">
                    DWS was fined <strong>€25 million</strong> for ESG
                    greenwashing. Our system cross-checks ESG claims against
                    external news sources to detect contradictions before
                    regulators do.
                  </p>
                  <p className="text-sm text-emerald-600 mt-2">
                    Try entering claims like &quot;Carbon neutral by 2030&quot;
                    or &quot;100% sustainable sourcing&quot;
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
