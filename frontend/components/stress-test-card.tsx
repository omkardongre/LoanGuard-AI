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
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Thermometer,
  Leaf,
  Building2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  BarChart3,
} from "lucide-react";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// Types
interface Scenario {
  id: string;
  name: string;
  type: string;
  description: string;
  pd_multiplier: number;
  lgd_multiplier: number;
  horizon_years: number;
}

interface ECLSummary {
  base_ecl_total: number;
  stressed_ecl_total: number;
  ecl_increase_total: number;
  ecl_increase_pct: number;
}

interface MacroConditions {
  mortgage_rate_30y: number;
  treasury_10y: number;
  fed_funds_rate: number;
  data_source: string;
  timestamp: string;
}

interface MLPredictions {
  model_versions: {
    pd: string;
    lgd: string;
  };
  avg_base_pd: number;
  avg_base_lgd: number;
  avg_stressed_pd: number;
}

interface LoanResult {
  loan_id: string;
  real_pd: number;
  real_lgd: number;
  ead: number;
  stressed_pd: number;
  stressed_lgd: number;
  base_ecl: number;
  stressed_ecl: number;
  ecl_increase_pct: number;
}

interface StressTestResult {
  success: boolean;
  production_level: boolean;
  scenario: {
    id: string;
    name: string;
    type: string;
    pd_multiplier: number;
    lgd_multiplier: number;
  };
  macro_conditions: MacroConditions;
  portfolio_summary: {
    loan_count: number;
    total_ead: number;
  };
  ml_predictions: MLPredictions;
  ecl_summary: ECLSummary;
  run_timestamp: string;
  loan_results: LoanResult[];
}

// Fetch functions
async function fetchScenarios(): Promise<Scenario[]> {
  const response = await fetch(`${API_BASE}/api/stress-test/scenarios`);
  if (!response.ok) throw new Error("Failed to fetch scenarios");
  const data = await response.json();
  return data.scenarios || [];
}

async function runStressTest(scenarioId: string): Promise<StressTestResult> {
  const response = await fetch(`${API_BASE}/api/stress-test/production/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario_id: scenarioId }),
  });
  if (!response.ok) throw new Error("Failed to run stress test");
  return response.json();
}

// Component
export function StressTestCard() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>("eco_moderate");
  const [result, setResult] = useState<StressTestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingScenarios, setLoadingScenarios] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Load scenarios on mount
  useEffect(() => {
    async function loadScenarios() {
      try {
        const data = await fetchScenarios();
        setScenarios(data);
      } catch (err) {
        console.error("Failed to load scenarios:", err);
      } finally {
        setLoadingScenarios(false);
      }
    }
    loadScenarios();
  }, []);

  // Run stress test
  async function handleRunTest() {
    try {
      setLoading(true);
      setError(null);
      const data = await runStressTest(selectedScenario);
      if (data.success) {
        setResult(data);
      } else {
        throw new Error("Stress test failed");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(2)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  // Get scenario type icon
  const getScenarioIcon = (type: string) => {
    switch (type) {
      case "economic":
        return <TrendingDown className="h-4 w-4 text-amber-600" />;
      case "climate_transition":
      case "climate_physical":
        return <Leaf className="h-4 w-4 text-green-600" />;
      case "combined":
        return <Thermometer className="h-4 w-4 text-red-600" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  // Get ECL increase severity
  const getECLSeverity = (pct: number) => {
    if (pct < 50) return { color: "text-yellow-600", bg: "bg-yellow-50", label: "Moderate" };
    if (pct < 100) return { color: "text-orange-600", bg: "bg-orange-50", label: "Significant" };
    if (pct < 200) return { color: "text-red-600", bg: "bg-red-50", label: "Severe" };
    return { color: "text-red-800", bg: "bg-red-100", label: "Critical" };
  };

  return (
    <Card className="border-2 border-slate-200">
      <CardHeader className="bg-gradient-to-r from-slate-50 to-blue-50">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-600" />
            Stress Testing
          </CardTitle>
          <Badge variant="outline" className="bg-blue-100 text-blue-800 border-blue-300">
            Basel III / IFRS 9
          </Badge>
        </div>
        <CardDescription>
          Production-level stress testing with real ML predictions
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4 space-y-4">
        {/* Scenario Selector */}
        <div className="flex gap-2">
          <Select
            value={selectedScenario}
            onValueChange={setSelectedScenario}
            disabled={loadingScenarios}
          >
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="Select scenario..." />
            </SelectTrigger>
            <SelectContent>
              {scenarios.map((scenario) => (
                <SelectItem key={scenario.id} value={scenario.id}>
                  <div className="flex items-center gap-2">
                    {getScenarioIcon(scenario.type)}
                    <span>{scenario.name}</span>
                    <span className="text-xs text-slate-500">({scenario.pd_multiplier}x PD)</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={handleRunTest} disabled={loading}>
            {loading ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <BarChart3 className="h-4 w-4 mr-1" />
                Run Test
              </>
            )}
          </Button>
        </div>

        {/* Error State */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-4">
            {/* ECL Summary */}
            <div className={`p-4 rounded-lg ${getECLSeverity(result.ecl_summary.ecl_increase_pct).bg}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">
                  {result.scenario.name}
                </span>
                <Badge className={getECLSeverity(result.ecl_summary.ecl_increase_pct).color}>
                  {getECLSeverity(result.ecl_summary.ecl_increase_pct).label}
                </Badge>
              </div>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-xs text-slate-500">Base ECL</p>
                  <p className="text-lg font-bold text-slate-700">
                    {formatCurrency(result.ecl_summary.base_ecl_total)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Stressed ECL</p>
                  <p className={`text-lg font-bold ${getECLSeverity(result.ecl_summary.ecl_increase_pct).color}`}>
                    {formatCurrency(result.ecl_summary.stressed_ecl_total)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">ECL Increase</p>
                  <p className={`text-lg font-bold ${getECLSeverity(result.ecl_summary.ecl_increase_pct).color}`}>
                    +{result.ecl_summary.ecl_increase_pct.toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>

            {/* Portfolio Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500">Portfolio</p>
                <p className="text-sm font-medium">
                  {result.portfolio_summary.loan_count} loans
                </p>
                <p className="text-xs text-slate-400">
                  {formatCurrency(result.portfolio_summary.total_ead)} EAD
                </p>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500">Multipliers</p>
                <p className="text-sm font-medium">
                  PD: {result.scenario.pd_multiplier}x
                </p>
                <p className="text-xs text-slate-400">
                  LGD: {result.scenario.lgd_multiplier}x
                </p>
              </div>
            </div>

            {/* Production Badge */}
            {result.production_level && (
              <div className="flex items-center gap-2 p-2 bg-green-50 border border-green-200 rounded-lg">
                <Badge className="bg-green-600 text-white">Production</Badge>
                <span className="text-xs text-green-700">
                  Real ML: {result.ml_predictions.model_versions.pd.split("(")[0]}
                </span>
              </div>
            )}

            {/* Details Toggle */}
            <Button
              variant="ghost"
              className="w-full"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-1" />
                  Hide Details
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-1" />
                  Show Details
                </>
              )}
            </Button>

            {/* Detailed View */}
            {showDetails && (
              <div className="space-y-3 pt-2 border-t">
                {/* Macro Conditions */}
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs font-medium text-blue-700 mb-2">
                    Current Macro Conditions (FRED API)
                  </p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <span className="text-slate-500">30Y Mortgage</span>
                      <p className="font-medium">{result.macro_conditions.mortgage_rate_30y}%</p>
                    </div>
                    <div>
                      <span className="text-slate-500">10Y Treasury</span>
                      <p className="font-medium">{result.macro_conditions.treasury_10y}%</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Fed Funds</span>
                      <p className="font-medium">{result.macro_conditions.fed_funds_rate}%</p>
                    </div>
                  </div>
                </div>

                {/* ML Predictions */}
                <div className="p-3 bg-purple-50 rounded-lg">
                  <p className="text-xs font-medium text-purple-700 mb-2">
                    ML Predictions
                  </p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <span className="text-slate-500">Avg Base PD</span>
                      <p className="font-medium">{(result.ml_predictions.avg_base_pd * 100).toFixed(2)}%</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Avg Base LGD</span>
                      <p className="font-medium">{(result.ml_predictions.avg_base_lgd * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Avg Stressed PD</span>
                      <p className="font-medium text-red-600">
                        {(result.ml_predictions.avg_stressed_pd * 100).toFixed(2)}%
                      </p>
                    </div>
                  </div>
                </div>

                {/* Top Impacted Loans */}
                {result.loan_results && result.loan_results.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-slate-700 mb-2">
                      Top Impacted Loans
                    </p>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {result.loan_results
                        .sort((a, b) => b.ecl_increase_pct - a.ecl_increase_pct)
                        .slice(0, 5)
                        .map((loan) => (
                          <div
                            key={loan.loan_id}
                            className="flex items-center justify-between p-2 bg-slate-50 rounded text-xs"
                          >
                            <span className="font-medium">{loan.loan_id}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-slate-500">
                                {formatCurrency(loan.ead)}
                              </span>
                              <Badge
                                variant="outline"
                                className={getECLSeverity(loan.ecl_increase_pct).color}
                              >
                                +{loan.ecl_increase_pct.toFixed(0)}%
                              </Badge>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                <p className="text-xs text-slate-400 text-center">
                  Run at: {new Date(result.run_timestamp).toLocaleString()}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Initial State */}
        {!result && !loading && !error && (
          <div className="text-center py-8 text-slate-500">
            <Activity className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">Select a scenario and click Run Test</p>
            <p className="text-xs mt-1">
              Uses real ML predictions from trained models
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
