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
import { Progress } from "@/components/ui/progress";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Zap,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  AlertTriangle,
  Activity,
  BarChart3,
} from "lucide-react";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// Types
interface VaRResult {
  var_95: number;
  var_99: number;
  cvar_99: number;
  mean_loss: number;
  std_loss: number;
  max_loss: number;
  min_loss: number;
  portfolio_ead: number;
  n_simulations: number;
  percentiles: Record<string, number>;
}

interface MonteCarloResult {
  success: boolean;
  var_result: VaRResult;
  loss_distribution_summary: {
    skewness: number;
    kurtosis: number;
    percentile_5: number;
    percentile_25: number;
    median: number;
    percentile_75: number;
    percentile_95: number;
  };
  stressed?: boolean;
  run_timestamp: string;
}

// Fetch function - Using production API
async function runMonteCarlo(params: {
  n_simulations: number;
  correlation: number;
  stressed: boolean;
  pd_multiplier: number;
  lgd_multiplier: number;
}): Promise<any> {
  const response = await fetch(`${API_BASE}/api/monte-carlo/production/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      n_simulations: params.n_simulations,
      correlation: params.correlation,
      // Include stress parameters if stressed mode
      ...(params.stressed && {
        pd_multiplier: params.pd_multiplier,
        lgd_multiplier: params.lgd_multiplier,
      }),
    }),
  });
  if (!response.ok) throw new Error("Monte Carlo simulation failed");
  return response.json();
}

// Component
export function MonteCarloCard() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Parameters
  const [nSimulations, setNSimulations] = useState(10000);
  const [correlation, setCorrelation] = useState(0.2);
  const [stressed, setStressed] = useState(false);
  const [pdMultiplier, setPdMultiplier] = useState(1.5);
  const [lgdMultiplier, setLgdMultiplier] = useState(1.2);

  // Run simulation
  async function handleRunSimulation() {
    try {
      setLoading(true);
      setError(null);
      const data = await runMonteCarlo({
        n_simulations: nSimulations,
        correlation,
        stressed,
        pd_multiplier: stressed ? pdMultiplier : 1.0,
        lgd_multiplier: stressed ? lgdMultiplier : 1.0,
      });
      if (data.success) {
        setResult(data);
      } else {
        throw new Error("Simulation returned unsuccessful");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
    return `$${value.toFixed(0)}`;
  };

  // Format percentage
  const formatPct = (value: number) => `${(value * 100).toFixed(2)}%`;

  // Get risk severity for VaR
  const getVaRSeverity = (var99: number, portfolioEad: number) => {
    const ratio = var99 / portfolioEad;
    if (ratio < 0.15) return { color: "text-emerald-600", bg: "bg-emerald-50", label: "Low Risk" };
    if (ratio < 0.25) return { color: "text-amber-600", bg: "bg-amber-50", label: "Moderate" };
    if (ratio < 0.35) return { color: "text-orange-600", bg: "bg-orange-50", label: "Elevated" };
    return { color: "text-red-600", bg: "bg-red-50", label: "High Risk" };
  };

  return (
    <Card className="border-2 border-slate-200">
      <CardHeader className="bg-gradient-to-r from-purple-50 to-indigo-50">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-purple-600" />
            Monte Carlo VaR
          </CardTitle>
          <Badge variant="outline" className="bg-purple-100 text-purple-800 border-purple-300">
            {(nSimulations / 1000).toFixed(0)}K Simulations
          </Badge>
        </div>
        <CardDescription>
          Portfolio risk analysis with correlated default modeling
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4 space-y-4">
        {/* Parameters */}
        <div className="space-y-4 p-4 bg-slate-50 rounded-lg">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium">Simulations</Label>
            <span className="text-sm text-slate-600">{nSimulations.toLocaleString()}</span>
          </div>
          <Slider
            value={[nSimulations]}
            onValueChange={([v]) => setNSimulations(v)}
            min={1000}
            max={50000}
            step={1000}
            className="w-full"
          />

          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium">Correlation</Label>
            <span className="text-sm text-slate-600">{correlation.toFixed(2)}</span>
          </div>
          <Slider
            value={[correlation * 100]}
            onValueChange={([v]) => setCorrelation(v / 100)}
            min={0}
            max={50}
            step={5}
            className="w-full"
          />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Switch checked={stressed} onCheckedChange={setStressed} />
              <Label className="text-sm font-medium">Stressed Scenario</Label>
            </div>
          </div>

          {stressed && (
            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-200">
              <div>
                <Label className="text-xs text-slate-500">PD Multiplier</Label>
                <div className="flex items-center gap-2">
                  <Slider
                    value={[pdMultiplier * 10]}
                    onValueChange={([v]) => setPdMultiplier(v / 10)}
                    min={10}
                    max={30}
                    step={1}
                    className="flex-1"
                  />
                  <span className="text-sm font-medium w-10">{pdMultiplier}x</span>
                </div>
              </div>
              <div>
                <Label className="text-xs text-slate-500">LGD Multiplier</Label>
                <div className="flex items-center gap-2">
                  <Slider
                    value={[lgdMultiplier * 10]}
                    onValueChange={([v]) => setLgdMultiplier(v / 10)}
                    min={10}
                    max={20}
                    step={1}
                    className="flex-1"
                  />
                  <span className="text-sm font-medium w-10">{lgdMultiplier}x</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Run Button */}
        <Button onClick={handleRunSimulation} disabled={loading} className="w-full">
          {loading ? (
            <RefreshCw className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <BarChart3 className="h-4 w-4 mr-2" />
          )}
          {loading ? "Simulating..." : "Run Simulation"}
        </Button>

        {/* Error */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </p>
          </div>
        )}

        {/* Results - Updated to match production API response */}
        {result && result.var && (
          <div className="space-y-4">
            {/* VaR Summary */}
            <div className={`p-4 rounded-lg ${getVaRSeverity(result.var.var_99?.var_amount || 0, result.portfolio?.total_ead || 1).bg}`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium">
                  {stressed ? "Stressed" : "Base"} Scenario
                </span>
                <Badge className={getVaRSeverity(result.var.var_99?.var_amount || 0, result.portfolio?.total_ead || 1).color}>
                  {getVaRSeverity(result.var.var_99?.var_amount || 0, result.portfolio?.total_ead || 1).label}
                </Badge>
              </div>

              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-xs text-slate-500">VaR 95%</p>
                  <p className="text-lg font-bold text-blue-700">
                    {formatCurrency(result.var.var_95?.var_amount || 0)}
                  </p>
                  <p className="text-xs text-slate-400">
                    {result.var.var_95?.var_pct_of_portfolio?.toFixed(1) || 0}% of portfolio
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">VaR 99%</p>
                  <p className="text-lg font-bold text-purple-700">
                    {formatCurrency(result.var.var_99?.var_amount || 0)}
                  </p>
                  <p className="text-xs text-slate-400">
                    {result.var.var_99?.var_pct_of_portfolio?.toFixed(1) || 0}% of portfolio
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">CVaR 99%</p>
                  <p className="text-lg font-bold text-red-700">
                    {formatCurrency(result.cvar?.cvar_99_amount || 0)}
                  </p>
                  <p className="text-xs text-slate-400">Expected Shortfall</p>
                </div>
              </div>
            </div>

            {/* Loss Distribution Percentiles */}
            {result.percentiles && (
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-sm font-medium text-slate-700 mb-3">Loss Distribution Percentiles</p>
                <div className="grid grid-cols-5 gap-2 text-center text-xs">
                  <div className="p-2 bg-emerald-50 rounded">
                    <p className="text-slate-500">50th %ile</p>
                    <p className="font-medium">{formatCurrency(result.percentiles.p50 || 0)}</p>
                  </div>
                  <div className="p-2 bg-green-50 rounded">
                    <p className="text-slate-500">75th %ile</p>
                    <p className="font-medium">{formatCurrency(result.percentiles.p75 || 0)}</p>
                  </div>
                  <div className="p-2 bg-blue-50 rounded">
                    <p className="text-slate-500">90th %ile</p>
                    <p className="font-medium">{formatCurrency(result.percentiles.p90 || 0)}</p>
                  </div>
                  <div className="p-2 bg-amber-50 rounded">
                    <p className="text-slate-500">95th %ile</p>
                    <p className="font-medium">{formatCurrency(result.percentiles.p95 || 0)}</p>
                  </div>
                  <div className="p-2 bg-red-50 rounded">
                    <p className="text-slate-500">99th %ile</p>
                    <p className="font-medium">{formatCurrency(result.percentiles.p99 || 0)}</p>
                  </div>
                </div>

                {/* Loss Distribution Stats */}
                {result.loss_distribution && (
                  <div className="grid grid-cols-3 gap-4 mt-4 text-xs">
                    <div className="flex items-center justify-between p-2 bg-white rounded">
                      <span className="text-slate-500">Mean Loss</span>
                      <span className="font-medium">{formatCurrency(result.loss_distribution.mean || 0)}</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-white rounded">
                      <span className="text-slate-500">Volatility</span>
                      <span className="font-medium">{formatCurrency(result.loss_distribution.std || 0)}</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-white rounded">
                      <span className="text-slate-500">Max Loss</span>
                      <span className="font-medium">{formatCurrency(result.loss_distribution.max || 0)}</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Portfolio Summary */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500">Portfolio EAD</p>
                <p className="text-sm font-medium">{formatCurrency(result.portfolio?.total_ead || 0)}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500">Loans Analyzed</p>
                <p className="text-sm font-medium">{result.portfolio?.loan_count || 0} loans</p>
              </div>
            </div>

            {/* Simulation Info */}
            <div className="flex items-center gap-2 p-2 bg-purple-50 border border-purple-200 rounded-lg">
              <Badge className="bg-purple-600 text-white">Correlated Defaults</Badge>
              <span className="text-xs text-purple-700">
                {result.simulation_info?.n_simulations?.toLocaleString() || 0} scenarios
              </span>
              <span className="text-xs text-slate-500 ml-auto">
                Run ID: {result.simulation_info?.id || 'N/A'}
              </span>
            </div>
          </div>
        )}

        {/* Initial State */}
        {!result && !loading && !error && (
          <div className="text-center py-8 text-slate-500">
            <Activity className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">Configure parameters and run simulation</p>
            <p className="text-xs mt-1">Models how defaults spread across your portfolio</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
