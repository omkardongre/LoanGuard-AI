"use client";

import * as React from "react";
import { TrendingUp, TrendingDown, Info, AlertCircle, CheckCircle2, Sparkles, ShieldCheck, BarChart3 } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { getSHAPExplanation, type SHAPFactor } from "@/lib/api";

interface SHAPWaterfallProps {
  loanId: string;
  className?: string;
}

/**
 * SHAP Waterfall Visualization Component - Premium 2026 Design
 * 
 * Production-level ML explainability visualization for banking judges.
 * Features:
 * - Gradient backgrounds and glassmorphism effects
 * - Animated progress bars with smooth transitions
 * - Modern typography and visual hierarchy
 * - EU AI Act compliance messaging
 */
export function SHAPWaterfall({ loanId, className }: SHAPWaterfallProps) {
  const [data, setData] = React.useState<{
    baseProbability: number;
    finalProbability: number;
    factors: SHAPFactor[];
  } | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadExplanation() {
      try {
        setLoading(true);
        setError(null);

        const result = await getSHAPExplanation(loanId, 10);

        if (!result.success) {
          throw new Error("Failed to load explanation");
        }

        setData({
          baseProbability: result.base_probability,
          finalProbability: result.final_probability,
          factors: result.top_factors,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    loadExplanation();
  }, [loanId]);

  if (loading) {
    return (
      <Card className={`${className} bg-gradient-to-br from-slate-50 to-blue-50 border-slate-200`}>
        <CardHeader className="pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-lg">AI Risk Explanation</CardTitle>
              <CardDescription>Loading intelligence...</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="h-12 w-full bg-gradient-to-r from-slate-200 to-slate-100 rounded-xl animate-pulse" />
          <div className="h-20 w-full bg-gradient-to-r from-slate-200 to-slate-100 rounded-xl animate-pulse" />
          <div className="h-20 w-full bg-gradient-to-r from-slate-200 to-slate-100 rounded-xl animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className={`${className} border-red-200 bg-red-50`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-700">
            <AlertCircle className="h-5 w-5" />
            Explanation Unavailable
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertDescription>{error || "Failed to load explanation data"}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const { baseProbability, finalProbability, factors } = data;
  const riskChange = ((finalProbability - baseProbability) / baseProbability) * 100;
  const isRiskIncreased = riskChange > 0;

  return (
    <Card className={`${className} overflow-hidden border-0 shadow-xl bg-gradient-to-br from-white via-slate-50 to-blue-50`}>
      {/* Premium Header with Gradient */}
      <CardHeader className="pb-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-blue-600 text-white">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm">
              <BarChart3 className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">
                AI Risk Intelligence
              </CardTitle>
              <CardDescription className="text-blue-100">
                Explainable ML driven by {factors.length} key factors
              </CardDescription>
            </div>
          </div>
          <Badge 
            className={`${isRiskIncreased 
              ? 'bg-red-500/90 hover:bg-red-500' 
              : 'bg-emerald-500/90 hover:bg-emerald-500'
            } text-white border-0 px-3 py-1`}
          >
            {isRiskIncreased ? "↑" : "↓"} {Math.abs(riskChange).toFixed(1)}% vs baseline
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-6 space-y-6">
        {/* Probability Cards - Premium Glass Effect */}
        <div className="grid grid-cols-2 gap-4">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-100 to-slate-50 p-5 border border-slate-200">
            <div className="absolute top-0 right-0 w-20 h-20 bg-blue-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="text-sm font-medium text-slate-500 mb-1">Base Probability</div>
            <div className="text-4xl font-bold text-slate-700 tracking-tight">
              {(baseProbability * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-slate-400 mt-1">Portfolio average</div>
          </div>
          
          <div className={`relative overflow-hidden rounded-2xl p-5 border ${
            finalProbability > 0.5 
              ? 'bg-gradient-to-br from-red-50 to-orange-50 border-red-200' 
              : finalProbability > 0.3 
                ? 'bg-gradient-to-br from-amber-50 to-yellow-50 border-amber-200'
                : 'bg-gradient-to-br from-emerald-50 to-green-50 border-emerald-200'
          }`}>
            <div className="absolute top-0 right-0 w-20 h-20 bg-current opacity-5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="text-sm font-medium text-slate-500 mb-1">Final Probability</div>
            <div className={`text-4xl font-bold tracking-tight ${
              finalProbability > 0.5 
                ? 'text-red-600' 
                : finalProbability > 0.3 
                  ? 'text-amber-600'
                  : 'text-emerald-600'
            }`}>
              {(finalProbability * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-slate-400 mt-1">This loan's risk</div>
          </div>
        </div>

        {/* EU AI Act Compliance - Premium Badge */}
        <div className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200">
          <div className="p-2 rounded-lg bg-emerald-500/10">
            <ShieldCheck className="h-5 w-5 text-emerald-600" />
          </div>
          <div className="flex-1">
            <div className="font-semibold text-emerald-800 text-sm">
              EU AI Act Compliant
            </div>
            <div className="text-xs text-emerald-600">
              Full transparency in automated risk assessment decisions
            </div>
          </div>
          <CheckCircle2 className="h-5 w-5 text-emerald-500" />
        </div>

        {/* Risk Factors - Premium Cards */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <Sparkles className="h-4 w-4 text-purple-500" />
            Key Risk Drivers
          </div>
          
          <div className="space-y-3">
            {factors.map((factor, index) => {
              const isPositive = factor.shap_value > 0;
              const percentage = Math.abs(factor.shap_value * 100);
              const barWidth = Math.min(percentage * 2.5, 100);

              return (
                <div 
                  key={index} 
                  className="group rounded-xl border border-slate-200 bg-white hover:shadow-md transition-all duration-300 overflow-hidden"
                >
                  {/* Factor Header */}
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                          isPositive 
                            ? 'bg-red-100 text-red-600' 
                            : 'bg-blue-100 text-blue-600'
                        }`}>
                          {isPositive ? (
                            <TrendingUp className="h-4 w-4" />
                          ) : (
                            <TrendingDown className="h-4 w-4" />
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-800 capitalize">
                            {factor.feature.replace(/_/g, " ")}
                          </div>
                          <div className="text-xs text-slate-400">
                            Value: {typeof factor.value === 'number' 
                              ? factor.value > 1000 
                                ? `$${(factor.value / 1000000).toFixed(1)}M`
                                : factor.value.toFixed(2)
                              : factor.value}
                          </div>
                        </div>
                      </div>
                      <Badge 
                        variant="outline" 
                        className={`font-bold ${
                          isPositive 
                            ? 'border-red-300 text-red-600 bg-red-50' 
                            : 'border-blue-300 text-blue-600 bg-blue-50'
                        }`}
                      >
                        {isPositive ? "+" : "-"}{percentage.toFixed(1)}%
                      </Badge>
                    </div>

                    {/* Animated Progress Bar */}
                    <div className="relative h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className={`absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out ${
                          isPositive 
                            ? 'bg-gradient-to-r from-red-400 to-red-500' 
                            : 'bg-gradient-to-r from-blue-400 to-blue-500'
                        }`}
                        style={{ 
                          width: `${barWidth}%`,
                          animation: 'growWidth 0.8s ease-out'
                        }}
                      />
                    </div>

                    {/* Explanation */}
                    <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                      {factor.explanation}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer - Model Info */}
        <div className="flex flex-wrap items-center gap-2 pt-4 border-t border-slate-200 text-xs text-slate-500">
          <Badge variant="secondary" className="bg-slate-100">
            720K+ loans trained
          </Badge>
          <Badge variant="secondary" className="bg-slate-100">
            Explainable AI
          </Badge>
          <Badge variant="secondary" className="bg-slate-100">
            EU AI Act Ready
          </Badge>
          <span className="ml-auto text-slate-400">
            {factors.length} factors analyzed
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
