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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
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
  Percent,
  ExternalLink,
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
          bg: "bg-amber-50",
          text: "text-amber-700",
          border: "border-amber-200",
          icon: <TrendingUp className="h-4 w-4" />,
        };
      case "MODERATE_PREPAY":
        return {
          bg: "bg-blue-50",
          text: "text-blue-700",
          border: "border-blue-200",
          icon: <BarChart3 className="h-4 w-4" />,
        };
      case "LOW_PREPAY":
        return {
          bg: "bg-emerald-50",
          text: "text-emerald-700",
          border: "border-emerald-200",
          icon: <TrendingDown className="h-4 w-4" />,
        };
      default:
        return {
          bg: "bg-slate-50",
          text: "text-slate-700",
          border: "border-slate-200",
          icon: null,
        };
    }
  }

  // Get incentive styling
  function getIncentiveStyle(incentive: string) {
    switch (incentive) {
      case "STRONG_INCENTIVE":
        return { color: "text-red-600", label: "Strong" };
      case "MODERATE_INCENTIVE":
        return { color: "text-amber-600", label: "Moderate" };
      case "WEAK_INCENTIVE":
        return { color: "text-yellow-600", label: "Weak" };
      case "NO_INCENTIVE":
        return { color: "text-slate-600", label: "None" };
      case "DISINCENTIVE":
        return { color: "text-emerald-600", label: "Disincentive" };
      default:
        return { color: "text-slate-600", label: incentive };
    }
  }

  // Get seasoning styling
  function getSeasoningStyle(stage: string) {
    switch (stage) {
      case "RAMP_UP":
        return { color: "text-blue-600", label: "Ramp-Up (< 30 mo)" };
      case "MATURE":
        return { color: "text-emerald-600", label: "Mature (30-60 mo)" };
      case "BURNOUT":
        return { color: "text-amber-600", label: "Burnout (> 60 mo)" };
      default:
        return { color: "text-slate-600", label: stage };
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-amber-600" />
        </CardContent>
      </Card>
    );
  }

  if (!prepayment) {
    return (
      <Card>
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
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 mb-2">
            <Banknote className="h-5 w-5 text-amber-500" />
            <p className="text-sm text-slate-500">Prepayment Risk</p>
          </div>
          <div className="flex items-baseline gap-2">
            <p className={`text-2xl font-bold ${adjustedPercent > 70 ? "text-red-600" : adjustedPercent > 40 ? "text-amber-600" : "text-emerald-600"}`}>
              {prepayment.prepay_probability_pct}
            </p>
            <span className="text-sm text-slate-500">
              CPR: {prepayment.CPR.toFixed(1)}%
            </span>
          </div>
          <div className="mt-2 flex items-center gap-2 text-xs">
            <span className="text-slate-500">Market:</span>
            <span className="font-medium">{prepayment.market_rate}%</span>
            <span className={`${incentiveStyle.color}`}>
              ({prepayment.refinancing_spread > 0 ? "+" : ""}{prepayment.refinancing_spread.toFixed(2)}%)
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
            <Banknote className="h-5 w-5 text-amber-600" />
            Prepayment Risk Analysis
          </CardTitle>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-4 w-4 text-slate-400" />
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="text-sm">
                    V2 Model with live FRED data. Refinancing incentive = loan rate - market rate.
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-xs">
              <ExternalLink className="h-3 w-3 mr-1" />
              FRED Live
            </Badge>
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
        {/* Main Prepayment Display */}
        <div className={`p-6 rounded-xl ${categoryStyle.bg} border ${categoryStyle.border}`}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-slate-600 mb-1">Prepayment Probability</p>
              <p className={`text-4xl font-bold ${categoryStyle.text}`}>
                {prepayment.prepay_probability_pct}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Base: {(prepayment.base_prepay_probability * 100).toFixed(1)}% → Adjusted
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-600 mb-1">Refinancing Spread</p>
              <p className={`text-2xl font-semibold ${incentiveStyle.color}`}>
                {prepayment.refinancing_spread > 0 ? "+" : ""}{prepayment.refinancing_spread.toFixed(2)}%
              </p>
              <p className={`text-xs ${incentiveStyle.color}`}>
                {incentiveStyle.label} Incentive
              </p>
            </div>
          </div>

          {/* Visual Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-slate-500">
              <span>Low Risk</span>
              <span>High Risk</span>
            </div>
            <Progress value={adjustedPercent} className="h-3" />
            <div className="flex justify-between text-xs">
              <span className="text-emerald-600">0%</span>
              <span className={categoryStyle.text}>{adjustedPercent.toFixed(1)}%</span>
              <span className="text-red-600">100%</span>
            </div>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Loan Rate */}
          <div className="p-3 bg-slate-50 rounded-lg">
            <p className="text-xs text-slate-500 mb-1">Loan Rate</p>
            <p className="text-lg font-semibold">{prepayment.loan_rate}%</p>
          </div>
          
          {/* Market Rate (FRED) */}
          <div className="p-3 bg-blue-50 rounded-lg">
            <p className="text-xs text-blue-600 mb-1 flex items-center gap-1">
              Market Rate
              <Badge variant="outline" className="text-[10px] px-1 py-0 border-blue-300">FRED</Badge>
            </p>
            <p className="text-lg font-semibold text-blue-700">{prepayment.market_rate}%</p>
          </div>

          {/* CPR */}
          <div className="p-3 bg-purple-50 rounded-lg">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger className="w-full text-left">
                  <p className="text-xs text-purple-600 mb-1">CPR (Annual)</p>
                  <p className="text-lg font-semibold text-purple-700">{prepayment.CPR.toFixed(2)}%</p>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-sm">Conditional Prepayment Rate - Annualized</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          {/* SMM */}
          <div className="p-3 bg-indigo-50 rounded-lg">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger className="w-full text-left">
                  <p className="text-xs text-indigo-600 mb-1">SMM (Monthly)</p>
                  <p className="text-lg font-semibold text-indigo-700">{prepayment.SMM.toFixed(4)}%</p>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-sm">Single Monthly Mortality - Monthly Rate</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>

        {/* Seasoning Info */}
        <div className="flex items-center justify-between p-3 bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-amber-600" />
            <span className="text-sm text-slate-600">Loan Age:</span>
            <span className="font-medium">{prepayment.months_since_origination} months</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600">Stage:</span>
            <Badge variant="outline" className={`${seasoningStyle.color}`}>
              {seasoningStyle.label}
            </Badge>
            <span className="text-xs text-slate-500">
              (Factor: {prepayment.seasoning_factor.toFixed(3)})
            </span>
          </div>
        </div>

        {/* Category and Model Info */}
        <div className="flex items-center justify-between">
          <Badge
            variant="outline"
            className={`${categoryStyle.bg} ${categoryStyle.text} border-0`}
          >
            {categoryStyle.icon}
            <span className="ml-1">{prepayment.risk_category.replace(/_/g, " ")}</span>
          </Badge>
          <span className="text-xs text-slate-500">
            {prepayment.data_source} | v{prepayment.model_version}
          </span>
        </div>

        {/* Scenario Analysis Toggle */}
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={loadScenario}
          disabled={scenarioLoading}
        >
          {scenarioLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              Loading Scenarios...
            </>
          ) : showScenario ? (
            <>
              <ChevronUp className="h-4 w-4 mr-1" />
              Hide Rate Scenarios
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4 mr-1" />
              Show What-If Rate Scenarios
            </>
          )}
        </Button>

        {/* Scenario Analysis Table */}
        {showScenario && scenario && (
          <div className="space-y-3 pt-4 border-t animate-in slide-in-from-top-2">
            <h4 className="font-medium text-sm flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-blue-600" />
              Interest Rate Scenario Analysis
            </h4>
            <p className="text-xs text-slate-500">
              How prepayment probability changes with market rate movements
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b">
                    <th className="pb-2">Rate Change</th>
                    <th className="pb-2">Market Rate</th>
                    <th className="pb-2">Spread</th>
                    <th className="pb-2">Prepay Prob</th>
                    <th className="pb-2">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {scenario.scenarios.map((s, idx) => (
                    <tr 
                      key={idx} 
                      className={`border-b last:border-0 ${s.rate_change === "+0.0%" ? "bg-blue-50 font-medium" : ""}`}
                    >
                      <td className="py-2">{s.rate_change}</td>
                      <td className="py-2">{s.market_rate}%</td>
                      <td className={`py-2 ${s.spread > 0 ? "text-red-600" : "text-emerald-600"}`}>
                        {s.spread > 0 ? "+" : ""}{s.spread.toFixed(2)}%
                      </td>
                      <td className="py-2">{s.prepay_probability}%</td>
                      <td className="py-2">
                        <Badge 
                          variant="outline" 
                          className={
                            s.risk_category === "HIGH" ? "bg-red-50 text-red-700" :
                            s.risk_category === "MODERATE" ? "bg-amber-50 text-amber-700" :
                            "bg-emerald-50 text-emerald-700"
                          }
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
