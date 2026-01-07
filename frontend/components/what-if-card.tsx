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
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Wand2,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Building2,
  Activity,
} from "lucide-react";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types
interface LoanResult {
  loan_id: string;
  base_ecl: number;
  stressed_ecl: number;
  ecl_increase_pct: number;
}

interface ECLSummary {
  base_ecl_total: number;
  stressed_ecl_total: number;
  ecl_increase_pct: number;
}

interface WhatIfResult {
  success: boolean;
  custom_scenario: boolean;
  scenario: {
    id: string;
    name: string;
    pd_multiplier: number;
    lgd_multiplier: number;
    sector_adjustments: Record<string, number>;
  };
  portfolio_summary: {
    loan_count: number;
    total_ead: number;
  };
  ecl_summary: ECLSummary;
  loan_results: LoanResult[];
}

// Sector options
const SECTORS = [
  { id: "real_estate", label: "Real Estate" },
  { id: "technology", label: "Technology" },
  { id: "healthcare", label: "Healthcare" },
  { id: "manufacturing", label: "Manufacturing" },
  { id: "retail", label: "Retail" },
  { id: "energy", label: "Energy" },
];

// Fetch function
async function runWhatIfScenario(params: {
  name: string;
  pd_multiplier: number;
  lgd_multiplier: number;
  sector_adjustments: Record<string, number>;
  gdp_shock: number;
  unemployment_shock: number;
}): Promise<WhatIfResult> {
  const response = await fetch(`${API_BASE}/api/stress-test/what-if`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!response.ok) throw new Error("What-If scenario failed");
  return response.json();
}

// Component
export function WhatIfCard() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WhatIfResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showSectorAdjust, setShowSectorAdjust] = useState(false);
  const [showLoanDetails, setShowLoanDetails] = useState(false);

  // Scenario Parameters
  const [scenarioName, setScenarioName] = useState("Custom Recession");
  const [pdMultiplier, setPdMultiplier] = useState(1.5);
  const [lgdMultiplier, setLgdMultiplier] = useState(1.2);
  const [gdpShock, setGdpShock] = useState(-0.03);
  const [unemploymentShock, setUnemploymentShock] = useState(0.05);
  const [sectorAdjustments, setSectorAdjustments] = useState<Record<string, number>>({
    real_estate: 1.3,
    technology: 0.9,
    healthcare: 1.0,
    manufacturing: 1.2,
    retail: 1.4,
    energy: 1.1,
  });

  // Run scenario
  async function handleRunScenario() {
    try {
      setLoading(true);
      setError(null);
      const data = await runWhatIfScenario({
        name: scenarioName,
        pd_multiplier: pdMultiplier,
        lgd_multiplier: lgdMultiplier,
        sector_adjustments: sectorAdjustments,
        gdp_shock: gdpShock,
        unemployment_shock: unemploymentShock,
      });
      if (data.success) {
        setResult(data);
      } else {
        throw new Error("Scenario returned unsuccessful");
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

  // Get ECL severity
  const getECLSeverity = (pct: number) => {
    if (pct < 50) return { color: "text-yellow-600", bg: "bg-yellow-50", label: "Moderate" };
    if (pct < 100) return { color: "text-orange-600", bg: "bg-orange-50", label: "Significant" };
    if (pct < 200) return { color: "text-red-600", bg: "bg-red-50", label: "Severe" };
    return { color: "text-red-800", bg: "bg-red-100", label: "Critical" };
  };

  // Preset scenarios
  const presets = [
    { name: "Mild Recession", pd: 1.3, lgd: 1.1, gdp: -0.01, unemp: 0.02 },
    { name: "Moderate Recession", pd: 1.8, lgd: 1.3, gdp: -0.04, unemp: 0.06 },
    { name: "Severe Recession", pd: 2.5, lgd: 1.5, gdp: -0.08, unemp: 0.12 },
  ];

  return (
    <Card className="border-2 border-slate-200">
      <CardHeader className="bg-gradient-to-r from-indigo-50 to-violet-50">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Wand2 className="h-5 w-5 text-indigo-600" />
            What-If Scenario Builder
          </CardTitle>
          <Badge variant="outline" className="bg-indigo-100 text-indigo-800 border-indigo-300">
            Custom Analysis
          </Badge>
        </div>
        <CardDescription>
          Build custom stress scenarios with adjustable parameters
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4 space-y-4">
        {/* Scenario Name */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Scenario Name</Label>
          <Input
            value={scenarioName}
            onChange={(e) => setScenarioName(e.target.value)}
            placeholder="Enter scenario name..."
            className="w-full"
          />
        </div>

        {/* Preset Buttons */}
        <div className="flex gap-2 flex-wrap">
          {presets.map((preset) => (
            <Button
              key={preset.name}
              variant="outline"
              size="sm"
              onClick={() => {
                setScenarioName(preset.name);
                setPdMultiplier(preset.pd);
                setLgdMultiplier(preset.lgd);
                setGdpShock(preset.gdp);
                setUnemploymentShock(preset.unemp);
              }}
            >
              <Sparkles className="h-3 w-3 mr-1" />
              {preset.name}
            </Button>
          ))}
        </div>

        {/* Main Parameters */}
        <div className="p-4 bg-slate-50 rounded-lg space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">PD Multiplier</Label>
                <span className="text-sm font-bold text-indigo-600">{pdMultiplier.toFixed(1)}x</span>
              </div>
              <Slider
                value={[pdMultiplier * 10]}
                onValueChange={([v]) => setPdMultiplier(v / 10)}
                min={10}
                max={30}
                step={1}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">LGD Multiplier</Label>
                <span className="text-sm font-bold text-indigo-600">{lgdMultiplier.toFixed(1)}x</span>
              </div>
              <Slider
                value={[lgdMultiplier * 10]}
                onValueChange={([v]) => setLgdMultiplier(v / 10)}
                min={10}
                max={20}
                step={1}
                className="w-full"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">GDP Shock</Label>
                <span className="text-sm font-bold text-red-600">{(gdpShock * 100).toFixed(1)}%</span>
              </div>
              <Slider
                value={[Math.abs(gdpShock) * 100]}
                onValueChange={([v]) => setGdpShock(-v / 100)}
                min={0}
                max={15}
                step={0.5}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">Unemployment Shock</Label>
                <span className="text-sm font-bold text-amber-600">+{(unemploymentShock * 100).toFixed(1)}%</span>
              </div>
              <Slider
                value={[unemploymentShock * 100]}
                onValueChange={([v]) => setUnemploymentShock(v / 100)}
                min={0}
                max={20}
                step={0.5}
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* Sector Adjustments Collapsible */}
        <Collapsible open={showSectorAdjust} onOpenChange={setShowSectorAdjust}>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between">
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                Sector-Specific Adjustments
              </div>
              {showSectorAdjust ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="p-4 bg-slate-50 rounded-lg space-y-3">
            {SECTORS.map((sector) => (
              <div key={sector.id} className="flex items-center gap-4">
                <span className="text-sm w-32">{sector.label}</span>
                <Slider
                  value={[(sectorAdjustments[sector.id] || 1) * 10]}
                  onValueChange={([v]) =>
                    setSectorAdjustments((prev) => ({ ...prev, [sector.id]: v / 10 }))
                  }
                  min={5}
                  max={20}
                  step={1}
                  className="flex-1"
                />
                <span className="text-sm font-medium w-12 text-right">
                  {(sectorAdjustments[sector.id] || 1).toFixed(1)}x
                </span>
              </div>
            ))}
          </CollapsibleContent>
        </Collapsible>

        {/* Run Button */}
        <Button onClick={handleRunScenario} disabled={loading} className="w-full" size="lg">
          {loading ? (
            <RefreshCw className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Wand2 className="h-4 w-4 mr-2" />
          )}
          {loading ? "Running Analysis..." : "Run What-If Analysis"}
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

        {/* Results */}
        {result && (
          <div className="space-y-4">
            {/* ECL Impact Summary */}
            <div className={`p-4 rounded-lg ${getECLSeverity(result.ecl_summary.ecl_increase_pct).bg}`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium">{result.scenario.name}</span>
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
                  <div className="flex items-center justify-center gap-1">
                    <TrendingUp className={`h-4 w-4 ${getECLSeverity(result.ecl_summary.ecl_increase_pct).color}`} />
                    <p className={`text-lg font-bold ${getECLSeverity(result.ecl_summary.ecl_increase_pct).color}`}>
                      +{result.ecl_summary.ecl_increase_pct.toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Portfolio Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500">Loans Analyzed</p>
                <p className="text-sm font-medium">{result.portfolio_summary.loan_count}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500">Total EAD</p>
                <p className="text-sm font-medium">{formatCurrency(result.portfolio_summary.total_ead)}</p>
              </div>
            </div>

            {/* Loan Details Collapsible */}
            {result.loan_results && result.loan_results.length > 0 && (
              <Collapsible open={showLoanDetails} onOpenChange={setShowLoanDetails}>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" className="w-full justify-between">
                    <span className="text-sm">Top Impacted Loans</span>
                    {showLoanDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent className="space-y-2 pt-2">
                  {result.loan_results
                    .sort((a, b) => b.ecl_increase_pct - a.ecl_increase_pct)
                    .slice(0, 5)
                    .map((loan) => (
                      <div
                        key={loan.loan_id}
                        className="flex items-center justify-between p-2 bg-slate-50 rounded text-sm"
                      >
                        <span className="font-medium">{loan.loan_id}</span>
                        <div className="flex items-center gap-3">
                          <span className="text-slate-500">
                            {formatCurrency(loan.base_ecl)} → {formatCurrency(loan.stressed_ecl)}
                          </span>
                          <Badge variant="outline" className={getECLSeverity(loan.ecl_increase_pct).color}>
                            +{loan.ecl_increase_pct.toFixed(0)}%
                          </Badge>
                        </div>
                      </div>
                    ))}
                </CollapsibleContent>
              </Collapsible>
            )}

            {/* Scenario Badge */}
            <div className="flex items-center gap-2 p-2 bg-indigo-50 border border-indigo-200 rounded-lg">
              <Badge className="bg-indigo-600 text-white">Custom Scenario</Badge>
              <span className="text-xs text-indigo-700">
                PD: {result.scenario.pd_multiplier}x | LGD: {result.scenario.lgd_multiplier}x
              </span>
            </div>
          </div>
        )}

        {/* Initial State */}
        {!result && !loading && !error && (
          <div className="text-center py-6 text-slate-500">
            <Activity className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p className="text-sm">Configure your custom scenario parameters</p>
            <p className="text-xs mt-1">Adjust multipliers and run analysis</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
