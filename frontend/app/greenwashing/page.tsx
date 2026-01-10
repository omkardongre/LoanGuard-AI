"use client";

import { useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Search,
  Loader2,
  Leaf,
  ExternalLink,
  ShieldAlert,
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
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <ShieldAlert className="h-8 w-8 text-emerald-600" />
            <h1 className="text-2xl font-bold text-slate-900">
              Greenwashing Detection
            </h1>
          </div>
          <p className="text-slate-500">
            Verify ESG claims against external sources. Detect potential
            greenwashing before regulators do.
          </p>
        </div>

        {/* Input Section */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Search className="h-5 w-5" />
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
            {/* Overall Result */}
            <Card className={`border-2 ${getRiskColor(result.overall_risk)}`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold">Overall Assessment</h3>
                    <p className="text-slate-600">{result.borrower}</p>
                  </div>
                  <div className="text-right">
                    <Badge
                      className={`text-lg px-4 py-2 ${getRiskColor(
                        result.overall_risk
                      )}`}
                    >
                      {result.overall_risk} RISK
                    </Badge>
                    <p className="text-sm text-slate-500 mt-1">
                      Score: {(result.overall_score * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-white/50 rounded-lg">
                  <p className="font-medium">{result.recommendation}</p>
                </div>
              </CardContent>
            </Card>

            {/* Individual Claims */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold">
                Claim Analysis ({result.claims_analyzed} claims)
              </h3>

              {result.results.map((claim, index) => (
                <Card key={index}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        {getVerdictIcon(claim.verdict)}
                        <CardTitle className="text-base">
                          {claim.claim}
                        </CardTitle>
                      </div>
                      <Badge className={getRiskColor(claim.greenwashing_risk)}>
                        {claim.greenwashing_risk}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {/* Language Flags */}
                    {claim.language_flags && claim.language_flags.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-slate-700 mb-1">
                          Language Issues:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {claim.language_flags.map((flag, i) => (
                            <Badge
                              key={i}
                              variant="outline"
                              className="text-amber-700 border-amber-300"
                            >
                              {flag.replace(/_/g, " ")}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Contradictions */}
                    {claim.contradictions && claim.contradictions.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-red-700 mb-1">
                          ⚠️ Contradicting Evidence:
                        </p>
                        <div className="space-y-2">
                          {claim.contradictions.map((c, i) => (
                            <div
                              key={i}
                              className="p-2 bg-red-50 rounded border border-red-100"
                            >
                              <a
                                href={c.source}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-medium text-red-800 hover:underline flex items-center gap-1"
                              >
                                {c.title}
                                <ExternalLink className="h-3 w-3" />
                              </a>
                              <p className="text-xs text-red-600 mt-1">
                                {c.snippet}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Supporting Evidence */}
                    {claim.supporting_evidence && claim.supporting_evidence.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-emerald-700 mb-1">
                          ✓ Supporting Evidence:
                        </p>
                        <div className="space-y-2">
                          {claim.supporting_evidence.map((s, i) => (
                            <div
                              key={i}
                              className="p-2 bg-emerald-50 rounded border border-emerald-100"
                            >
                              <a
                                href={s.source}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-medium text-emerald-800 hover:underline flex items-center gap-1"
                              >
                                {s.title}
                                <ExternalLink className="h-3 w-3" />
                              </a>
                              <p className="text-xs text-emerald-600 mt-1">
                                {s.snippet}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-2 border-t">
                      <span className="text-sm text-slate-500">
                        Verdict: <strong>{claim.verdict}</strong>
                      </span>
                      <span className="text-sm text-slate-500">
                        Score: {(claim.verification_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </CardContent>
                </Card>
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
