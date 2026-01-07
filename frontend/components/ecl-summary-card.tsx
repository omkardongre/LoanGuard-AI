"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Calculator,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Shield,
  Target,
  BarChart3,
} from "lucide-react";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types
interface StageBreakdown {
  stage_1: { count: number; ecl: number; percentage: number };
  stage_2: { count: number; ecl: number; percentage: number };
  stage_3: { count: number; ecl: number; percentage: number };
}

interface ECLSummary {
  total_ecl: number;
  total_ead: number;
  weighted_avg_pd: number;
  weighted_avg_lgd: number;
  loan_count: number;
  stage_breakdown: StageBreakdown;
  coverage_ratio: number;
}

interface SectorBreakdown {
  sector: string;
  ecl: number;
  loan_count: number;
  avg_pd: number;
}

interface ECLResponse {
  success: boolean;
  summary: ECLSummary;
  sector_breakdown?: SectorBreakdown[];
  run_timestamp?: string;
}

// Fetch function
async function fetchECLSummary(): Promise<ECLResponse> {
  const response = await fetch(`${API_BASE}/api/ecl/portfolio/summary`);
  if (!response.ok) throw new Error("Failed to fetch ECL summary");
  return response.json();
}

// Component
export function ECLSummaryCard() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [result, setResult] = useState<ECLResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setError(null);
      const data = await fetchECLSummary();
      if (data.success) {
        setResult(data);
      } else {
        throw new Error("ECL calculation returned unsuccessful");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    await loadData();
  }

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
    return `$${value.toFixed(0)}`;
  };

  // Format percentage
  const formatPct = (value: number) => `${(value * 100).toFixed(2)}%`;

  // Get stage severity
  const getStageSeverity = (stage: string) => {
    switch (stage) {
      case "stage_1":
        return { color: "text-emerald-600", bg: "bg-emerald-100", label: "Stage 1", desc: "12-month ECL" };
      case "stage_2":
        return { color: "text-amber-600", bg: "bg-amber-100", label: "Stage 2", desc: "Lifetime ECL" };
      case "stage_3":
        return { color: "text-red-600", bg: "bg-red-100", label: "Stage 3", desc: "Credit Impaired" };
      default:
        return { color: "text-slate-600", bg: "bg-slate-100", label: stage, desc: "" };
    }
  };

  // Get coverage health
  const getCoverageHealth = (ratio: number) => {
    if (ratio < 0.02) return { color: "text-amber-600", label: "Low Coverage" };
    if (ratio < 0.05) return { color: "text-emerald-600", label: "Adequate" };
    return { color: "text-blue-600", label: "Conservative" };
  };

  return (
    <Card className="border-2 border-slate-200">
      <CardHeader className="bg-gradient-to-r from-emerald-50 to-teal-50">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5 text-emerald-600" />
            ECL Summary
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-emerald-100 text-emerald-800 border-emerald-300">
              IFRS 9
            </Badge>
            <Button variant="ghost" size="sm" onClick={handleRefresh} disabled={refreshing}>
              <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>
        <CardDescription>
          Expected Credit Loss by IFRS 9 staging
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4 space-y-4">
        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin text-emerald-600" />
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </p>
            <Button variant="outline" size="sm" onClick={handleRefresh} className="mt-2">
              Retry
            </Button>
          </div>
        )}

        {/* Results */}
        {result && result.summary && !loading && (
          <div className="space-y-4">
            {/* Total ECL Summary */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl text-center">
                <p className="text-xs text-emerald-600 mb-1">Total ECL</p>
                <p className="text-2xl font-bold text-emerald-800">
                  {formatCurrency(result.summary.total_ecl)}
                </p>
                <p className="text-xs text-emerald-600 mt-1">
                  {result.summary.loan_count} loans
                </p>
              </div>
              <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl text-center">
                <p className="text-xs text-blue-600 mb-1">Coverage Ratio</p>
                <p className={`text-2xl font-bold ${getCoverageHealth(result.summary.coverage_ratio).color}`}>
                  {(result.summary.coverage_ratio * 100).toFixed(2)}%
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  {getCoverageHealth(result.summary.coverage_ratio).label}
                </p>
              </div>
            </div>

            {/* Stage Breakdown */}
            <div className="p-4 bg-slate-50 rounded-lg">
              <p className="text-sm font-medium text-slate-700 mb-4 flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Stage Breakdown (IFRS 9)
              </p>

              {result.summary.stage_breakdown ? (
                <div className="space-y-4">
                  {(["stage_1", "stage_2", "stage_3"] as const).map((stage) => {
                    const data = result.summary.stage_breakdown[stage];
                    const severity = getStageSeverity(stage);
                    const eclPct = (data.ecl / result.summary.total_ecl) * 100 || 0;

                    return (
                      <div key={stage} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge className={severity.bg + " " + severity.color}>
                              {severity.label}
                            </Badge>
                            <span className="text-xs text-slate-500">{severity.desc}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-sm font-medium">{formatCurrency(data.ecl)}</span>
                            <span className="text-xs text-slate-500 ml-2">
                              ({data.count} loans)
                            </span>
                          </div>
                        </div>
                        <Progress value={eclPct} className="h-2" />
                        <p className="text-xs text-slate-400 text-right">
                          {eclPct.toFixed(1)}% of total ECL
                        </p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-2 bg-emerald-50 rounded">
                    <span className="text-sm font-medium text-emerald-700">Stage 1</span>
                    <span className="text-sm">12-month ECL</span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-amber-50 rounded">
                    <span className="text-sm font-medium text-amber-700">Stage 2</span>
                    <span className="text-sm">Lifetime ECL</span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-red-50 rounded">
                    <span className="text-sm font-medium text-red-700">Stage 3</span>
                    <span className="text-sm">Credit Impaired</span>
                  </div>
                </div>
              )}
            </div>

            {/* Risk Parameters */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Target className="h-4 w-4 text-slate-500" />
                  <p className="text-xs text-slate-500">Weighted Avg PD</p>
                </div>
                <p className="text-lg font-bold text-slate-700">
                  {formatPct(result.summary.weighted_avg_pd)}
                </p>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Shield className="h-4 w-4 text-slate-500" />
                  <p className="text-xs text-slate-500">Weighted Avg LGD</p>
                </div>
                <p className="text-lg font-bold text-slate-700">
                  {formatPct(result.summary.weighted_avg_lgd)}
                </p>
              </div>
            </div>

            {/* Portfolio Info */}
            <div className="flex items-center gap-2 p-2 bg-emerald-50 border border-emerald-200 rounded-lg">
              <Badge className="bg-emerald-600 text-white">IFRS 9 Compliant</Badge>
              <span className="text-xs text-emerald-700">
                Total EAD: {formatCurrency(result.summary.total_ead)}
              </span>
            </div>

            {/* Sector Breakdown */}
            {result.sector_breakdown && result.sector_breakdown.length > 0 && (
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-sm font-medium text-slate-700 mb-3">ECL by Sector</p>
                <div className="space-y-2">
                  {result.sector_breakdown.slice(0, 5).map((sector) => (
                    <div key={sector.sector} className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">{sector.sector}</span>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{formatCurrency(sector.ecl)}</span>
                        <span className="text-xs text-slate-400">
                          ({sector.loan_count} loans)
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
