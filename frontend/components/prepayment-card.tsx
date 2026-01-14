"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Banknote,
  TrendingDown,
  TrendingUp,
  Info,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  BarChart3,
  Clock,
  Sparkles,
  ShieldCheck,
  Zap,
  Target,
} from "lucide-react";
import {
  fetchPrepaymentV2,
  fetchPrepaymentScenario,
  type PrepaymentPredictionV2,
  type PrepaymentScenarioAnalysis,
} from "@/lib/api";

interface PrepaymentCardProps {
  loanId: string;
  compact?: boolean;
}

/**
 * Prepayment Risk Analysis Card - Premium 2026 Design
 * 
 * Features:
 * - Gradient header with Federal Reserve badge
 * - Glassmorphism metric cards
 * - Animated progress bars
 * - Modern typography and spacing
 */
export function PrepaymentCard({ loanId, compact = false }: PrepaymentCardProps) {
  const [prepayment, setPrepayment] = useState<PrepaymentPredictionV2 | null>(null);
  const [scenario, setScenario] = useState<PrepaymentScenarioAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [showScenario, setShowScenario] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  async function loadPrepayment() {
    try {
      setLoading(true);
      const data = await fetchPrepaymentV2(loanId);
      setPrepayment(data);
    } catch (err) {
      console.error("Failed to fetch prepayment:", err);
    } finally {
      setLoading(false);
    }
  }

  async function loadScenario() {
    if (scenario) {
      setShowScenario(!showScenario);
      return;
    }
    try {
      setScenarioLoading(true);
      const data = await fetchPrepaymentScenario(loanId);
      setScenario(data);
      setShowScenario(true);
    } catch (err) {
      console.error("Failed to fetch scenario analysis:", err);
    } finally {
      setScenarioLoading(false);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    await loadPrepayment();
    setRefreshing(false);
  }

  useEffect(() => {
    loadPrepayment();
  }, [loanId]);

  // Get category styling
  function getCategoryStyle(category: string) {
    switch (category) {
      case "HIGH_PREPAY":
        return {
          bg: "bg-gradient-to-br from-red-50 to-orange-50",
          text: "text-red-700",
          border: "border-red-200",
          icon: <TrendingUp className="h-4 w-4" />,
          gradient: "from-red-500 to-orange-500",
        };
      case "MODERATE_PREPAY":
        return {
          bg: "bg-gradient-to-br from-amber-50 to-yellow-50",
          text: "text-amber-700",
          border: "border-amber-200",
          icon: <BarChart3 className="h-4 w-4" />,
          gradient: "from-amber-500 to-yellow-500",
        };
      case "LOW_PREPAY":
        return {
          bg: "bg-gradient-to-br from-emerald-50 to-green-50",
          text: "text-emerald-700",
          border: "border-emerald-200",
          icon: <TrendingDown className="h-4 w-4" />,
          gradient: "from-emerald-500 to-green-500",
        };
      default:
        return {
          bg: "bg-gradient-to-br from-slate-50 to-gray-50",
          text: "text-slate-700",
          border: "border-slate-200",
          icon: null,
          gradient: "from-slate-500 to-gray-500",
        };
    }
  }

  // Get incentive styling
  function getIncentiveStyle(incentive: string) {
    switch (incentive) {
      case "STRONG_INCENTIVE":
        return { color: "text-red-600", bgColor: "bg-red-100", label: "Strong" };
      case "MODERATE_INCENTIVE":
        return { color: "text-amber-600", bgColor: "bg-amber-100", label: "Moderate" };
      case "WEAK_INCENTIVE":
        return { color: "text-yellow-600", bgColor: "bg-yellow-100", label: "Weak" };
      case "NO_INCENTIVE":
        return { color: "text-slate-600", bgColor: "bg-slate-100", label: "None" };
      case "DISINCENTIVE":
        return { color: "text-emerald-600", bgColor: "bg-emerald-100", label: "Disincentive" };
      default:
        return { color: "text-slate-600", bgColor: "bg-slate-100", label: incentive };
    }
  }

  // Get seasoning styling
  function getSeasoningStyle(stage: string) {
    switch (stage) {
      case "RAMP_UP":
        return { color: "text-blue-600", bgColor: "bg-blue-100", label: "Ramp-Up" };
      case "MATURE":
        return { color: "text-emerald-600", bgColor: "bg-emerald-100", label: "Mature" };
      case "BURNOUT":
        return { color: "text-amber-600", bgColor: "bg-amber-100", label: "Burnout" };
      default:
        return { color: "text-slate-600", bgColor: "bg-slate-100", label: stage };
    }
  }

  if (loading) {
    return (
      <Card className="overflow-hidden border-0 shadow-xl bg-gradient-to-br from-white to-orange-50">
        <CardHeader className="pb-4 bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-500 text-white">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm">
              <Banknote className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">Prepayment Risk</CardTitle>
              <p className="text-sm text-orange-100">Loading analysis...</p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6 space-y-4">
          <div className="h-24 w-full bg-gradient-to-r from-slate-200 to-slate-100 rounded-2xl animate-pulse" />
          <div className="grid grid-cols-4 gap-4">
            <div className="h-20 bg-gradient-to-r from-slate-200 to-slate-100 rounded-xl animate-pulse" />
            <div className="h-20 bg-gradient-to-r from-slate-200 to-slate-100 rounded-xl animate-pulse" />
            <div className="h-20 bg-gradient-to-r from-slate-200 to-slate-100 rounded-xl animate-pulse" />
            <div className="h-20 bg-gradient-to-r from-slate-200 to-slate-100 rounded-xl animate-pulse" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!prepayment) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="py-8 text-center text-slate-500">
          <p>Prepayment prediction unavailable</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={loadPrepayment}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const categoryStyle = getCategoryStyle(prepayment.risk_category);
  const incentiveStyle = getIncentiveStyle(prepayment.refinancing_incentive);
  const seasoningStyle = getSeasoningStyle(prepayment.seasoning_stage);
  const adjustedPercent = prepayment.adjusted_prepay_probability * 100;

  if (compact) {
    return (
      <Card className="overflow-hidden border-0 shadow-lg bg-gradient-to-br from-white to-orange-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-orange-500 to-amber-500">
              <Banknote className="h-4 w-4 text-white" />
            </div>
            <p className="text-sm font-medium text-slate-600">Prepayment Risk</p>
          </div>
          <div className="flex items-baseline gap-2">
            <p className={`text-3xl font-bold ${categoryStyle.text}`}>{prepayment.prepay_probability_pct}</p>
            <span className="text-sm text-slate-500">CPR: {prepayment.CPR.toFixed(1)}%</span>
          </div>
          <div className="mt-2 flex items-center gap-2 text-xs">
            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
              FRED Live
            </Badge>
            <span className="font-medium">{prepayment.market_rate}%</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden border-0 shadow-xl bg-gradient-to-br from-white via-slate-50 to-orange-50">
      {/* Premium Header with Gradient */}
      <CardHeader className="pb-4 bg-gradient-to-r from-orange-600 via-amber-500 to-yellow-500 text-white">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm">
              <Banknote className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-white">Prepayment Risk Analysis</CardTitle>
              <p className="text-sm text-orange-100">Refinancing incentive monitoring</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge className="bg-white/20 text-white border-0 backdrop-blur-sm">
              <Zap className="h-3 w-3 mr-1" />
              FRED Live
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
              className="text-white hover:bg-white/10"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-6 space-y-6">
        {/* Main Probability Display - Glassmorphism */}
        <div className={`relative overflow-hidden rounded-2xl p-6 ${categoryStyle.bg} border ${categoryStyle.border}`}>
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${categoryStyle.gradient} opacity-10 rounded-full -translate-y-1/2 translate-x-1/2" />
          
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Prepayment Probability</p>
              <p className={`text-5xl font-bold tracking-tight ${categoryStyle.text}`}>
                {prepayment.prepay_probability_pct}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Base: {(prepayment.base_prepay_probability * 100).toFixed(1)}% → Adjusted
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-slate-500 mb-1">Refinancing Spread</p>
              <p className={`text-3xl font-bold ${incentiveStyle.color}`}>
                {(prepayment.refinancing_spread ?? 0) > 0 ? "+" : ""}{(prepayment.refinancing_spread ?? 0).toFixed(2)}%
              </p>
              <Badge className={`mt-1 ${incentiveStyle.bgColor} ${incentiveStyle.color} border-0`}>
                {incentiveStyle.label} Incentive
              </Badge>
            </div>
          </div>

          {/* Animated Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <ShieldCheck className="h-3 w-3 text-emerald-500" />
                Low Risk
              </span>
              <span className="flex items-center gap-1">
                High Risk
                <Target className="h-3 w-3 text-red-500" />
              </span>
            </div>
            <div className="relative h-4 bg-slate-200 rounded-full overflow-hidden">
              <div 
                className={`absolute inset-y-0 left-0 rounded-full bg-gradient-to-r ${categoryStyle.gradient} transition-all duration-1000 ease-out`}
                style={{ 
                  width: `${adjustedPercent}%`,
                  animation: 'growWidth 1s ease-out'
                }}
              />
              <div 
                className="absolute inset-y-0 flex items-center justify-center w-full text-xs font-bold"
                style={{ mixBlendMode: 'difference' }}
              >
                <span className="text-white">{adjustedPercent.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Key Metrics Grid - Modern Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Loan Rate */}
          <div className="relative overflow-hidden p-4 bg-gradient-to-br from-slate-50 to-gray-50 rounded-xl border border-slate-200 hover:shadow-md transition-shadow">
            <div className="absolute top-0 right-0 w-16 h-16 bg-slate-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <p className="text-xs font-medium text-slate-500 mb-1">Loan Rate</p>
            <p className="text-2xl font-bold text-slate-800">{prepayment.loan_rate}%</p>
            <p className="text-[10px] text-slate-400 mt-1">Current interest rate</p>
          </div>
          
          {/* Market Rate (FRED) */}
          <div className="relative overflow-hidden p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 hover:shadow-md transition-shadow">
            <div className="absolute top-0 right-0 w-16 h-16 bg-blue-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="flex items-center gap-1 mb-1">
              <p className="text-xs font-medium text-blue-600">Market Rate</p>
              <Badge variant="outline" className="text-[8px] px-1 py-0 border-blue-300 text-blue-600">FRED</Badge>
            </div>
            <p className="text-2xl font-bold text-blue-700">{prepayment.market_rate}%</p>
            <p className="text-[10px] text-blue-400 mt-1">Federal Reserve data</p>
          </div>

          {/* CPR */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="relative overflow-hidden p-4 bg-gradient-to-br from-purple-50 to-violet-50 rounded-xl border border-purple-200 hover:shadow-md transition-shadow cursor-help">
                  <div className="absolute top-0 right-0 w-16 h-16 bg-purple-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
                  <p className="text-xs font-medium text-purple-600 mb-1">CPR (Annual)</p>
                  <p className="text-2xl font-bold text-purple-700">{prepayment.CPR.toFixed(2)}%</p>
                  <p className="text-[10px] text-purple-400 mt-1">Annualized rate</p>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p className="text-sm">Conditional Prepayment Rate - Annualized</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {/* SMM */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="relative overflow-hidden p-4 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl border border-indigo-200 hover:shadow-md transition-shadow cursor-help">
                  <div className="absolute top-0 right-0 w-16 h-16 bg-indigo-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
                  <p className="text-xs font-medium text-indigo-600 mb-1">SMM (Monthly)</p>
                  <p className="text-2xl font-bold text-indigo-700">{prepayment.SMM.toFixed(4)}%</p>
                  <p className="text-[10px] text-indigo-400 mt-1">Monthly mortality</p>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p className="text-sm">Single Monthly Mortality - Monthly Rate</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        {/* Seasoning Info - Premium Badge */}
        <div className="flex items-center justify-between p-4 bg-gradient-to-r from-amber-50 via-orange-50 to-yellow-50 rounded-xl border border-amber-200">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-100">
              <Clock className="h-4 w-4 text-amber-600" />
            </div>
            <div>
              <span className="text-sm font-medium text-slate-700">Loan Age: </span>
              <span className="font-bold text-slate-900">{prepayment.months_since_origination} months</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600">Stage:</span>
            <Badge className={`${seasoningStyle.bgColor} ${seasoningStyle.color} border-0`}>
              {seasoningStyle.label}
            </Badge>
            <span className="text-xs text-slate-400">(Factor: {prepayment.seasoning_factor.toFixed(3)})</span>
          </div>
        </div>

        {/* Category Badge and Model Info */}
        <div className="flex items-center justify-between">
          <Badge className={`${categoryStyle.bg} ${categoryStyle.text} border-0 px-3 py-1`}>
            {categoryStyle.icon}
            <span className="ml-1 font-semibold">{prepayment.risk_category.replace(/_/g, " ")}</span>
          </Badge>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Sparkles className="h-3 w-3 text-purple-500" />
            {prepayment.data_source} | v{prepayment.model_version}
          </div>
        </div>

        {/* Scenario Analysis Toggle */}
        <Button
          variant="outline"
          size="sm"
          className="w-full bg-gradient-to-r from-slate-50 to-gray-50 hover:from-slate-100 hover:to-gray-100 border-slate-200"
          onClick={loadScenario}
          disabled={scenarioLoading}
        >
          {scenarioLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Loading Scenarios...
            </>
          ) : showScenario ? (
            <>
              <ChevronUp className="h-4 w-4 mr-2" />
              Hide Rate Scenarios
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4 mr-2" />
              Show What-If Rate Scenarios
            </>
          )}
        </Button>

        {/* Scenario Analysis Table - Premium Style */}
        {showScenario && scenario && (
          <div className="space-y-4 pt-4 border-t border-slate-200 animate-in slide-in-from-top-2">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-blue-100">
                <BarChart3 className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <h4 className="font-semibold text-slate-800">Interest Rate Scenario Analysis</h4>
                <p className="text-xs text-slate-500">How prepayment probability changes with market rate movements</p>
              </div>
            </div>
            
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-sm">
                <thead className="bg-gradient-to-r from-slate-100 to-gray-100">
                  <tr className="text-left text-slate-600">
                    <th className="px-4 py-3 font-semibold">Rate Change</th>
                    <th className="px-4 py-3 font-semibold">Market Rate</th>
                    <th className="px-4 py-3 font-semibold">Spread</th>
                    <th className="px-4 py-3 font-semibold">Prepay Prob</th>
                    <th className="px-4 py-3 font-semibold">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {scenario.scenarios.map((s, idx) => (
                    <tr 
                      key={idx} 
                      className={`border-t border-slate-100 hover:bg-slate-50 transition-colors ${
                        s.rate_change === "+0.0%" ? "bg-blue-50" : ""
                      }`}
                    >
                      <td className="px-4 py-3 font-medium">{s.rate_change}</td>
                      <td className="px-4 py-3">{s.market_rate}%</td>
                      <td className={`px-4 py-3 font-medium ${s.spread > 0 ? "text-red-600" : "text-emerald-600"}`}>
                        {s.spread > 0 ? "+" : ""}{s.spread.toFixed(2)}%
                      </td>
                      <td className="px-4 py-3 font-bold">{s.prepay_probability}%</td>
                      <td className="px-4 py-3">
                        <Badge 
                          className={`border-0 ${
                            s.risk_category === "HIGH" ? "bg-red-100 text-red-700" :
                            s.risk_category === "MODERATE" ? "bg-amber-100 text-amber-700" :
                            "bg-emerald-100 text-emerald-700"
                          }`}
                        >
                          {s.risk_category}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <p className="text-xs text-slate-400 text-right">
              Analysis date: {new Date(scenario.analysis_date).toLocaleString()}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
