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
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Leaf,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  AlertTriangle,
  CloudRain,
  Factory,
  Flame,
  Shield,
  Activity,
  ChevronDown,
  ChevronUp,
  Info,
  CheckCircle2,
} from "lucide-react";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// Types
interface RiskFactor {
  factor: string;
  severity: string;
  description: string;
  category: string;
}

interface ESGFinancialRiskResult {
  success: boolean;
  loan_id: string;
  borrower_name: string;
  sector: string;
  assessment_date: string;
  esg_financial_risk_score: number;
  transition_risk_score: number;
  physical_risk_score: number;
  reputational_risk_score: number;
  regulatory_risk_score: number;
  pd_adjustment: number;
  lgd_adjustment: number;
  ecl_impact_percent: number;
  risk_factors: RiskFactor[];
  recommendations: string[];
  evidence: string[];
  climate_scenario: string;
}

interface ClimateScenario {
  id: string;
  name: string;
  description: string;
  transition_multiplier: number;
  physical_multiplier: number;
}

interface Sector {
  sector_id: string;
  sector_name: string;
  transition_risk: number;
  physical_risk: number;
  material_issues_count: number;
}

// Fetch functions
async function fetchESGRisk(
  loanData: Record<string, unknown>,
  climateScenario: string
): Promise<ESGFinancialRiskResult> {
  const response = await fetch(`${API_BASE}/api/esg/financial-risk/assess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      loan_data: loanData,
      climate_scenario: climateScenario,
    }),
  });
  if (!response.ok) throw new Error("ESG risk assessment failed");
  return response.json();
}

async function fetchClimateScenarios(): Promise<{ scenarios: ClimateScenario[] }> {
  const response = await fetch(`${API_BASE}/api/esg/climate-scenarios`);
  if (!response.ok) throw new Error("Failed to fetch climate scenarios");
  return response.json();
}

async function fetchSectors(): Promise<{ sectors: Sector[] }> {
  const response = await fetch(`${API_BASE}/api/esg/sectors`);
  if (!response.ok) throw new Error("Failed to fetch sectors");
  return response.json();
}

// Component props
interface ESGFinancialRiskCardProps {
  loanId?: string;
  borrowerName?: string;
  sector?: string;
  loanAmount?: number;
}

export function ESGFinancialRiskCard({
  loanId = "DEMO-001",
  borrowerName = "Sample Corporation",
  sector = "energy",
  loanAmount = 10000000,
}: ESGFinancialRiskCardProps) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ESGFinancialRiskResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Climate scenarios and sectors
  const [scenarios, setScenarios] = useState<ClimateScenario[]>([]);
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [selectedScenario, setSelectedScenario] = useState("current_policies");
  const [selectedSector, setSelectedSector] = useState(sector);

  // Load scenarios and sectors on mount
  useEffect(() => {
    async function loadMetadata() {
      try {
        const [scenarioData, sectorData] = await Promise.all([
          fetchClimateScenarios(),
          fetchSectors(),
        ]);
        setScenarios(scenarioData.scenarios || []);
        setSectors(sectorData.sectors || []);
      } catch (err) {
        console.error("Failed to load metadata:", err);
      }
    }
    loadMetadata();
  }, []);

  // Run assessment
  async function handleAssess() {
    try {
      setLoading(true);
      setError(null);
      const loanData = {
        loan_id: loanId,
        borrower_name: borrowerName,
        sector: selectedSector,
        amount: loanAmount,
      };
      const data = await fetchESGRisk(loanData, selectedScenario);
      if (data.success) {
        setResult(data);
      } else {
        throw new Error("Assessment returned unsuccessful");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  // Get risk severity styling
  const getRiskSeverity = (score: number) => {
    if (score < 30) return { color: "text-emerald-600", bg: "bg-emerald-50", label: "Low Risk", icon: CheckCircle2 };
    if (score < 50) return { color: "text-amber-600", bg: "bg-amber-50", label: "Moderate", icon: Info };
    if (score < 70) return { color: "text-orange-600", bg: "bg-orange-50", label: "Elevated", icon: AlertTriangle };
    return { color: "text-red-600", bg: "bg-red-50", label: "High Risk", icon: AlertTriangle };
  };

  // Format percentage
  const formatPct = (value: number) => `${(value * 100).toFixed(1)}%`;

  // Format currency impact
  const formatCreditImpact = (pdAdj: number, lgdAdj: number) => {
    const pdChange = ((pdAdj - 1) * 100).toFixed(0);
    const lgdChange = (lgdAdj * 100).toFixed(0);
    return {
      pdLabel: pdAdj >= 1 ? `+${pdChange}%` : `${pdChange}%`,
      lgdLabel: lgdAdj >= 0 ? `+${lgdChange}%` : `${lgdChange}%`,
    };
  };

  return (
    <Card className="border-2 border-slate-200">
      <CardHeader className="bg-gradient-to-r from-emerald-50 to-teal-50">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Leaf className="h-5 w-5 text-emerald-600" />
            ESG Financial Risk
          </CardTitle>
          <Badge variant="outline" className="bg-emerald-100 text-emerald-800 border-emerald-300">
            EBA 2026
          </Badge>
        </div>
        <CardDescription>
          ESG as financial risk factor with credit impact per EBA guidelines
        </CardDescription>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {/* Sector and Climate Scenario Selection */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-lg">
          <div className="space-y-2">
            <Label className="text-xs font-medium text-slate-600">Sector</Label>
            <Select value={selectedSector} onValueChange={setSelectedSector}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select sector" />
              </SelectTrigger>
              <SelectContent>
                {sectors.map((s) => (
                  <SelectItem key={s.sector_id} value={s.sector_id}>
                    <div className="flex items-center gap-2">
                      <Factory className="h-3 w-3 text-slate-400" />
                      {s.sector_name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs font-medium text-slate-600">Climate Scenario (NGFS)</Label>
            <Select value={selectedScenario} onValueChange={setSelectedScenario}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select scenario" />
              </SelectTrigger>
              <SelectContent>
                {scenarios.map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    <div className="flex items-center gap-2">
                      <CloudRain className="h-3 w-3 text-slate-400" />
                      {s.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Run Assessment Button */}
        <Button onClick={handleAssess} disabled={loading} className="w-full bg-emerald-600 hover:bg-emerald-700">
          {loading ? (
            <RefreshCw className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Shield className="h-4 w-4 mr-2" />
          )}
          {loading ? "Assessing..." : "Assess ESG Financial Risk"}
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
            {/* Risk Score Summary */}
            <div className={`p-4 rounded-lg ${getRiskSeverity(result.esg_financial_risk_score).bg}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">ESG Financial Risk Score</span>
                  <Badge className={getRiskSeverity(result.esg_financial_risk_score).color}>
                    {getRiskSeverity(result.esg_financial_risk_score).label}
                  </Badge>
                </div>
                <span className={`text-3xl font-bold ${getRiskSeverity(result.esg_financial_risk_score).color}`}>
                  {result.esg_financial_risk_score.toFixed(0)}
                </span>
              </div>
              <Progress value={result.esg_financial_risk_score} className="h-3" />
            </div>

            {/* Credit Impact - Key Differentiator */}
            <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
              <p className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-blue-600" />
                Credit Risk Impact (EBA 2026 Compliant)
              </p>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-3 bg-white rounded-lg shadow-sm">
                  <p className="text-xs text-slate-500">PD Adjustment</p>
                  <p className={`text-xl font-bold ${result.pd_adjustment > 1 ? "text-red-600" : "text-emerald-600"}`}>
                    {formatCreditImpact(result.pd_adjustment, result.lgd_adjustment).pdLabel}
                  </p>
                </div>
                <div className="p-3 bg-white rounded-lg shadow-sm">
                  <p className="text-xs text-slate-500">LGD Adjustment</p>
                  <p className={`text-xl font-bold ${result.lgd_adjustment > 0 ? "text-red-600" : "text-emerald-600"}`}>
                    {formatCreditImpact(result.pd_adjustment, result.lgd_adjustment).lgdLabel}
                  </p>
                </div>
                <div className="p-3 bg-white rounded-lg shadow-sm">
                  <p className="text-xs text-slate-500">ECL Impact</p>
                  <p className={`text-xl font-bold ${result.ecl_impact_percent > 0 ? "text-red-600" : "text-emerald-600"}`}>
                    {result.ecl_impact_percent > 0 ? "+" : ""}{result.ecl_impact_percent.toFixed(0)}%
                  </p>
                </div>
              </div>
            </div>

            {/* Risk Component Breakdown */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-amber-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Flame className="h-4 w-4 text-amber-600" />
                  <span className="text-xs font-medium text-amber-800">Transition Risk</span>
                </div>
                <Progress value={result.transition_risk_score} className="h-2" />
                <p className="text-right text-xs mt-1 text-amber-700">{result.transition_risk_score.toFixed(0)}/100</p>
              </div>
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CloudRain className="h-4 w-4 text-blue-600" />
                  <span className="text-xs font-medium text-blue-800">Physical Risk</span>
                </div>
                <Progress value={result.physical_risk_score} className="h-2" />
                <p className="text-right text-xs mt-1 text-blue-700">{result.physical_risk_score.toFixed(0)}/100</p>
              </div>
            </div>

            {/* Toggle Details */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
              className="w-full"
            >
              {showDetails ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-2" />
                  Hide Details
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-2" />
                  Show Risk Factors & Recommendations
                </>
              )}
            </Button>

            {/* Expandable Details */}
            {showDetails && (
              <div className="space-y-4 pt-4 border-t">
                {/* Risk Factors */}
                {result.risk_factors && result.risk_factors.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-slate-700 mb-2">Key Risk Factors</h4>
                    <div className="space-y-2">
                      {result.risk_factors.map((factor, idx) => (
                        <div
                          key={idx}
                          className={`p-2 rounded flex items-center gap-2 ${
                            factor.severity === "high" ? "bg-red-50" : "bg-amber-50"
                          }`}
                        >
                          <AlertTriangle className={`h-4 w-4 ${
                            factor.severity === "high" ? "text-red-600" : "text-amber-600"
                          }`} />
                          <div className="flex-1">
                            <p className="text-sm font-medium">{factor.factor}</p>
                            <p className="text-xs text-slate-500">{factor.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {result.recommendations && result.recommendations.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-slate-700 mb-2">Recommendations</h4>
                    <ul className="space-y-1">
                      {result.recommendations.map((rec, idx) => (
                        <li key={idx} className="text-sm text-slate-600 flex items-start gap-2">
                          <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Evidence */}
                {result.evidence && result.evidence.length > 0 && (
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <h4 className="text-xs font-semibold text-slate-600 mb-2">Evidence Trail</h4>
                    <ul className="text-xs text-slate-500 space-y-1">
                      {result.evidence.map((ev, idx) => (
                        <li key={idx}>{ev}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Scenario Info */}
            <div className="flex items-center gap-2 p-2 bg-teal-50 border border-teal-200 rounded-lg">
              <Badge className="bg-teal-600 text-white">NGFS</Badge>
              <span className="text-xs text-teal-700">
                Scenario: {scenarios.find(s => s.id === result.climate_scenario)?.name || result.climate_scenario}
              </span>
            </div>
          </div>
        )}

        {/* Initial State */}
        {!result && !loading && !error && (
          <div className="text-center py-8 text-slate-500">
            <Activity className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">Select sector and climate scenario to assess</p>
            <p className="text-xs mt-1">ESG treated as financial risk per EBA 2026 guidelines</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
