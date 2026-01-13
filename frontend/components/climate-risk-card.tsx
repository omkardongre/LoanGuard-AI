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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  AlertTriangle,
  Leaf,
  Thermometer,
  Wind,
  Droplets,
  Factory,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Globe,
  Zap,
} from "lucide-react";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// Climate scenario type
interface ClimateScenario {
  id: string;
  name: string;
  type: string;
  description: string;
  pd_multiplier: number;
  lgd_multiplier: number;
  carbon_price_2030?: number;
  temperature_increase_2050?: number;
  transition_risk_factor?: number;
  physical_risk_factor?: number;
}

// Climate stress result
interface ClimateStressResult {
  success: boolean;
  scenario: {
    id: string;
    name: string;
    type: string;
  };
  ecl_summary: {
    base_ecl_total: number;
    stressed_ecl_total: number;
    ecl_increase_pct: number;
  };
  sector_impacts: Record<string, {
    loan_count: number;
    total_ead: number;
    base_ecl: number;
    stressed_ecl: number;
    ecl_increase_pct: number;
  }>;
}

// NGFS scenario definitions (static data)
const NGFS_SCENARIOS: ClimateScenario[] = [
  {
    id: "climate_disorderly",
    name: "Disorderly Transition",
    type: "climate_transition",
    description: "Delayed policy action leads to abrupt, disorderly transition. High transition risk.",
    pd_multiplier: 1.5,
    lgd_multiplier: 1.15,
    carbon_price_2030: 250,
    temperature_increase_2050: 1.8,
    transition_risk_factor: 1.4,
    physical_risk_factor: 1.1,
  },
  {
    id: "climate_hot_house",
    name: "Hot House World",
    type: "climate_physical",
    description: "No climate policy, severe physical risks from unmitigated climate change.",
    pd_multiplier: 1.6,
    lgd_multiplier: 1.3,
    carbon_price_2030: 0,
    temperature_increase_2050: 3.5,
    transition_risk_factor: 1.0,
    physical_risk_factor: 1.8,
  },
  {
    id: "climate_nz50",
    name: "Net Zero 2050",
    type: "climate_transition",
    description: "Orderly transition to net zero by 2050. Moderate transition costs.",
    pd_multiplier: 1.1,
    lgd_multiplier: 1.05,
    carbon_price_2030: 140,
    temperature_increase_2050: 1.5,
    transition_risk_factor: 1.15,
    physical_risk_factor: 1.05,
  },
];

// High carbon intensity sectors
const HIGH_CARBON_SECTORS = [
  "oil_gas",
  "utilities",
  "mining",
  "transportation",
  "manufacturing",
  "agriculture",
];

// Fetch climate stress test
async function runClimateStressTest(scenarioId: string): Promise<ClimateStressResult> {
  const response = await fetch(`${API_BASE}/api/stress-test/production/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario_id: scenarioId }),
  });
  if (!response.ok) throw new Error("Failed to run climate stress test");
  return response.json();
}

// Component
export function ClimateRiskCard() {
  const [selectedScenario, setSelectedScenario] = useState<ClimateScenario>(NGFS_SCENARIOS[0]);
  const [result, setResult] = useState<ClimateStressResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Run climate stress test
  async function handleRunTest() {
    try {
      setLoading(true);
      setError(null);
      const data = await runClimateStressTest(selectedScenario.id);
      if (data.success) {
        setResult(data);
      } else {
        throw new Error("Climate stress test failed");
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

  // Get scenario icon
  const getScenarioIcon = (type: string) => {
    switch (type) {
      case "climate_transition":
        return <Zap className="h-5 w-5 text-amber-500" />;
      case "climate_physical":
        return <Thermometer className="h-5 w-5 text-red-500" />;
      default:
        return <Leaf className="h-5 w-5 text-green-500" />;
    }
  };

  // Get risk color
  const getRiskColor = (factor: number) => {
    if (factor < 1.2) return "text-green-600";
    if (factor < 1.5) return "text-amber-600";
    return "text-red-600";
  };

  return (
    <Card className="border-2 border-green-200">
      <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Leaf className="h-5 w-5 text-green-600" />
            Climate Risk Analysis
          </CardTitle>
          <Badge variant="outline" className="bg-green-100 text-green-800 border-green-300">
            NGFS v5
          </Badge>
        </div>
        <CardDescription>
          EU 2025 mandated climate stress testing with NGFS scenarios
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4 space-y-4">
        {/* Scenario Tabs */}
        <Tabs
          value={selectedScenario.id}
          onValueChange={(id) => {
            const scenario = NGFS_SCENARIOS.find((s) => s.id === id);
            if (scenario) setSelectedScenario(scenario);
          }}
        >
          <TabsList className="grid w-full grid-cols-3">
            {NGFS_SCENARIOS.map((scenario) => (
              <TabsTrigger key={scenario.id} value={scenario.id} className="text-xs">
                {getScenarioIcon(scenario.type)}
                <span className="ml-1 hidden sm:inline">{scenario.name.split(" ")[0]}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          {NGFS_SCENARIOS.map((scenario) => (
            <TabsContent key={scenario.id} value={scenario.id} className="mt-4">
              <div className="p-4 bg-slate-50 rounded-lg space-y-3">
                <div className="flex items-start gap-2">
                  {getScenarioIcon(scenario.type)}
                  <div>
                    <p className="font-medium text-sm">{scenario.name}</p>
                    <p className="text-xs text-slate-500">{scenario.description}</p>
                  </div>
                </div>

                {/* Scenario Parameters */}
                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="p-2 bg-white rounded border">
                    <div className="flex items-center gap-1 text-xs text-slate-500">
                      <Factory className="h-3 w-3" /> Carbon Price 2030
                    </div>
                    <p className="font-medium">
                      ${scenario.carbon_price_2030}/tCO₂
                    </p>
                  </div>
                  <div className="p-2 bg-white rounded border">
                    <div className="flex items-center gap-1 text-xs text-slate-500">
                      <Thermometer className="h-3 w-3" /> Temp Rise 2050
                    </div>
                    <p className={`font-medium ${scenario.temperature_increase_2050 && scenario.temperature_increase_2050 > 2 ? 'text-red-600' : 'text-green-600'}`}>
                      +{scenario.temperature_increase_2050}°C
                    </p>
                  </div>
                  <div className="p-2 bg-white rounded border">
                    <div className="flex items-center gap-1 text-xs text-slate-500">
                      <Zap className="h-3 w-3" /> Transition Risk
                    </div>
                    <p className={`font-medium ${getRiskColor(scenario.transition_risk_factor || 1)}`}>
                      {scenario.transition_risk_factor}x
                    </p>
                  </div>
                  <div className="p-2 bg-white rounded border">
                    <div className="flex items-center gap-1 text-xs text-slate-500">
                      <Droplets className="h-3 w-3" /> Physical Risk
                    </div>
                    <p className={`font-medium ${getRiskColor(scenario.physical_risk_factor || 1)}`}>
                      {scenario.physical_risk_factor}x
                    </p>
                  </div>
                </div>
              </div>
            </TabsContent>
          ))}
        </Tabs>

        {/* Run Test Button */}
        <Button onClick={handleRunTest} disabled={loading} className="w-full bg-green-600 hover:bg-green-700">
          {loading ? (
            <RefreshCw className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Globe className="h-4 w-4 mr-2" />
          )}
          Run Climate Stress Test
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
            {/* ECL Impact */}
            <div className="p-4 bg-gradient-to-r from-green-50 to-amber-50 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium flex items-center gap-1">
                  {getScenarioIcon(result.scenario.type)}
                  {result.scenario.name}
                </span>
                <Badge className={result.ecl_summary.ecl_increase_pct > 100 ? "bg-red-600" : "bg-amber-500"}>
                  +{result.ecl_summary.ecl_increase_pct.toFixed(1)}% ECL
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <p className="text-xs text-slate-500">Base ECL</p>
                  <p className="text-xl font-bold text-slate-700">
                    {formatCurrency(result.ecl_summary.base_ecl_total)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Climate-Stressed ECL</p>
                  <p className="text-xl font-bold text-red-600">
                    {formatCurrency(result.ecl_summary.stressed_ecl_total)}
                  </p>
                </div>
              </div>

              {/* Visual bar */}
              <div className="mt-3">
                <div className="flex justify-between text-xs text-slate-500 mb-1">
                  <span>ECL Impact</span>
                  <span>{result.ecl_summary.ecl_increase_pct.toFixed(0)}%</span>
                </div>
                <Progress 
                  value={Math.min(100, result.ecl_summary.ecl_increase_pct)} 
                  className="h-2"
                />
              </div>
            </div>

            {/* Sector Impacts */}
            {result.sector_impacts && Object.keys(result.sector_impacts).length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium">Sector Exposure</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowDetails(!showDetails)}
                  >
                    {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </Button>
                </div>

                {showDetails && (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {Object.entries(result.sector_impacts)
                      .sort(([, a], [, b]) => b.ecl_increase_pct - a.ecl_increase_pct)
                      .slice(0, 8)
                      .map(([sector, data]) => (
                        <div
                          key={sector}
                          className={`flex items-center justify-between p-2 rounded text-xs ${
                            HIGH_CARBON_SECTORS.includes(sector) ? "bg-amber-50" : "bg-slate-50"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            {HIGH_CARBON_SECTORS.includes(sector) && (
                              <Factory className="h-3 w-3 text-amber-600" />
                            )}
                            <span className="font-medium capitalize">
                              {sector.replace(/_/g, " ")}
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-slate-500">
                              {data.loan_count} loans
                            </span>
                            <Badge
                              variant="outline"
                              className={data.ecl_increase_pct > 100 ? "text-red-600" : "text-amber-600"}
                            >
                              +{data.ecl_increase_pct.toFixed(0)}%
                            </Badge>
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            )}

            {/* NGFS Badge */}
            <div className="text-center p-2 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-600">
                Powered by NGFS Climate Scenarios v5 (November 2024)
              </p>
              <p className="text-xs text-slate-500">
                Same methodology used by ECB, Fed, BoE
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
