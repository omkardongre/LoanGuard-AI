"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DollarSign,
  TrendingDown,
  TrendingUp,
  Info,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  fetchLGD,
  fetchLGDExplanation,
  type LGDPrediction,
  type LGDExplanation,
} from "@/lib/api";

interface LGDCardProps {
  loanId: string;
  compact?: boolean;
}

export function LGDCard({ loanId, compact = false }: LGDCardProps) {
  const [lgd, setLgd] = useState<LGDPrediction | null>(null);
  const [explanation, setExplanation] = useState<LGDExplanation | null>(null);
  const [loading, setLoading] = useState(true);
  const [showExplanation, setShowExplanation] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  async function loadLGD() {
    try {
      setLoading(true);
      const data = await fetchLGD(loanId);
      setLgd(data);
    } catch (err) {
      console.error("Failed to fetch LGD:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadExplanation() {
    if (explanation) {
      setShowExplanation(!showExplanation);
      return;
    }
    try {
      const data = await fetchLGDExplanation(loanId, 5);
      setExplanation(data);
      setShowExplanation(true);
    } catch (err) {
      console.error("Failed to fetch explanation:", err);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    await loadLGD();
    setRefreshing(false);
  }

  useEffect(() => {
    loadLGD();
  }, [loanId]);

  // Get category styling
  function getCategoryStyle(category: string) {
    switch (category) {
      case "HIGH_RECOVERY":
        return {
          bg: "bg-emerald-50",
          text: "text-emerald-700",
          border: "border-emerald-200",
        };
      case "MODERATE_RECOVERY":
        return {
          bg: "bg-blue-50",
          text: "text-blue-700",
          border: "border-blue-200",
        };
      case "LOW_RECOVERY":
        return {
          bg: "bg-amber-50",
          text: "text-amber-700",
          border: "border-amber-200",
        };
      case "MINIMAL_RECOVERY":
        return {
          bg: "bg-red-50",
          text: "text-red-700",
          border: "border-red-200",
        };
      default:
        return {
          bg: "bg-slate-50",
          text: "text-slate-700",
          border: "border-slate-200",
        };
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-emerald-600" />
        </CardContent>
      </Card>
    );
  }

  if (!lgd) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-slate-500">
          <p>LGD prediction unavailable</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={loadLGD}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const categoryStyle = getCategoryStyle(lgd.recovery_category);
  const lgdPercent = lgd.lgd * 100;
  const recoveryPercent = lgd.recovery_rate * 100;

  if (compact) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="h-5 w-5 text-purple-500" />
            <p className="text-sm text-slate-500">LGD (Loss Given Default)</p>
          </div>
          <div className="flex items-baseline gap-2">
            <p className={`text-2xl font-bold ${lgdPercent > 70 ? "text-red-600" : lgdPercent > 50 ? "text-amber-600" : "text-emerald-600"}`}>
              {lgd.lgd_pct}
            </p>
            <span className="text-sm text-slate-500">
              Recovery: {recoveryPercent.toFixed(1)}%
            </span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-purple-600" />
            Loss Given Default (LGD)
          </CardTitle>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-4 w-4 text-slate-400" />
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="text-sm">
                    LGD = 1 - Recovery Rate. Used in Basel III ECL calculation:
                    ECL = PD × LGD × EAD
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw
                className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
              />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Main LGD Display */}
        <div className={`p-6 rounded-xl ${categoryStyle.bg} border ${categoryStyle.border}`}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-slate-600 mb-1">Loss Given Default</p>
              <p className={`text-4xl font-bold ${categoryStyle.text}`}>
                {lgd.lgd_pct}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-600 mb-1">Recovery Rate</p>
              <p className="text-2xl font-semibold text-emerald-600">
                {recoveryPercent.toFixed(1)}%
              </p>
            </div>
          </div>

          {/* Visual Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-slate-500">
              <span>Recovery</span>
              <span>Loss</span>
            </div>
            <div className="w-full h-4 bg-slate-200 rounded-full overflow-hidden flex">
              <div
                className="h-full bg-emerald-500 transition-all"
                style={{ width: `${recoveryPercent}%` }}
              />
              <div
                className="h-full bg-red-400 transition-all"
                style={{ width: `${lgdPercent}%` }}
              />
            </div>
            <div className="flex justify-between text-xs font-medium">
              <span className="text-emerald-600">{recoveryPercent.toFixed(1)}%</span>
              <span className="text-red-600">{lgdPercent.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Category Badge */}
        <div className="flex items-center justify-between">
          <Badge
            variant="outline"
            className={`${categoryStyle.bg} ${categoryStyle.text} border-0`}
          >
            {lgd.recovery_category.replace(/_/g, " ")}
          </Badge>
          <span className="text-xs text-slate-500">
            Model: {lgd.model_version}
          </span>
        </div>

        {/* ECL Formula */}
        <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
          <p className="text-sm font-medium text-purple-800 mb-1">
            Basel III ECL Calculation
          </p>
          <p className="text-xs text-purple-600 font-mono">
            ECL = PD × LGD × EAD = PD × {lgd.lgd.toFixed(4)} × EAD
          </p>
        </div>

        {/* SHAP Explanation Toggle */}
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={loadExplanation}
        >
          {showExplanation ? (
            <>
              <ChevronUp className="h-4 w-4 mr-1" />
              Hide Explanation
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4 mr-1" />
              Show SHAP Explanation
            </>
          )}
        </Button>

        {/* SHAP Explanation */}
        {showExplanation && explanation && (
          <div className="space-y-4 pt-4 border-t animate-in slide-in-from-top-2">
            <div>
              <h4 className="font-medium text-sm mb-3">
                Stage 1: Recovery Probability Factors
              </h4>
              <div className="space-y-2">
                {explanation.stage1_factors.map((factor, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 bg-slate-50 rounded"
                  >
                    <span className="text-sm">{factor.feature}</span>
                    <div className="flex items-center gap-2">
                      {factor.impact > 0 ? (
                        <TrendingUp className="h-3 w-3 text-emerald-500" />
                      ) : (
                        <TrendingDown className="h-3 w-3 text-red-500" />
                      )}
                      <span
                        className={`text-sm font-medium ${
                          factor.impact > 0 ? "text-emerald-600" : "text-red-600"
                        }`}
                      >
                        {factor.impact > 0 ? "+" : ""}
                        {(factor.impact * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="font-medium text-sm mb-3">
                Stage 2: Recovery Amount Factors
              </h4>
              <div className="space-y-2">
                {explanation.stage2_factors.map((factor, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 bg-slate-50 rounded"
                  >
                    <span className="text-sm">{factor.feature}</span>
                    <div className="flex items-center gap-2">
                      {factor.impact > 0 ? (
                        <TrendingUp className="h-3 w-3 text-emerald-500" />
                      ) : (
                        <TrendingDown className="h-3 w-3 text-red-500" />
                      )}
                      <span
                        className={`text-sm font-medium ${
                          factor.impact > 0 ? "text-emerald-600" : "text-red-600"
                        }`}
                      >
                        {factor.impact > 0 ? "+" : ""}
                        {(factor.impact * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
