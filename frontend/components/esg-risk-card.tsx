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
  Leaf,
  Users,
  Building2,
  AlertTriangle,
  CheckCircle2,
  Info,
  ChevronDown,
  ChevronUp,
  Zap,
  Droplets,
  Factory,
} from "lucide-react";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// Types
interface ESGComponents {
  environmental: number;
  social: number;
  governance: number;
}

interface ESGRiskPrediction {
  success: boolean;
  loan_id: string;
  borrower: string;
  is_sll: boolean;
  risk_level: string;
  risk_level_display: string;
  confidence: number;
  confidence_pct: string;
  composite_score: number;
  esg_components: ESGComponents;
  description: string;
  color: string;
  industry: string;
  region: string;
  probabilities: {
    LOW_RISK: number;
    MEDIUM_RISK: number;
    HIGH_RISK: number;
  };
}

interface TopFactor {
  feature: string;
  importance: number;
  importance_pct: string;
  value: string | number;
}

interface ESGExplanation {
  success: boolean;
  prediction: ESGRiskPrediction;
  top_factors: TopFactor[];
  interpretation: string;
}

// Fetch functions
async function fetchESGRisk(loanId: string): Promise<ESGRiskPrediction> {
  const response = await fetch(`${API_BASE}/api/loans/${loanId}/esg-risk`);
  if (!response.ok) throw new Error("Failed to fetch ESG risk");
  return response.json();
}

async function fetchESGExplanation(loanId: string): Promise<ESGExplanation> {
  const response = await fetch(`${API_BASE}/api/ml/esg-risk/explain/${loanId}`);
  if (!response.ok) throw new Error("Failed to fetch ESG explanation");
  return response.json();
}

// Component props
interface ESGRiskCardProps {
  loanId: string;
}

export function ESGRiskCard({ loanId }: ESGRiskCardProps) {
  const [data, setData] = useState<ESGRiskPrediction | null>(null);
  const [explanation, setExplanation] = useState<ESGExplanation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        const [riskData, explainData] = await Promise.allSettled([
          fetchESGRisk(loanId),
          fetchESGExplanation(loanId),
        ]);

        if (riskData.status === "fulfilled" && riskData.value.success) {
          setData(riskData.value);
        } else {
          throw new Error("Failed to load ESG risk data");
        }

        if (explainData.status === "fulfilled" && explainData.value.success) {
          setExplanation(explainData.value);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [loanId]);

  if (loading) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Leaf className="h-5 w-5 text-emerald-600" />
            ESG Risk Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 bg-slate-100 rounded-lg" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className="border-red-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            ESG Risk Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-600">{error || "Failed to load data"}</p>
        </CardContent>
      </Card>
    );
  }

  // Risk level styling
  const riskStyles = {
    LOW_RISK: {
      bg: "bg-emerald-50",
      border: "border-emerald-200",
      text: "text-emerald-700",
      badge: "bg-emerald-100 text-emerald-800",
      icon: CheckCircle2,
    },
    MEDIUM_RISK: {
      bg: "bg-amber-50",
      border: "border-amber-200",
      text: "text-amber-700",
      badge: "bg-amber-100 text-amber-800",
      icon: Info,
    },
    HIGH_RISK: {
      bg: "bg-red-50",
      border: "border-red-200",
      text: "text-red-700",
      badge: "bg-red-100 text-red-800",
      icon: AlertTriangle,
    },
  };

  const style = riskStyles[data.risk_level as keyof typeof riskStyles] || riskStyles.MEDIUM_RISK;
  const RiskIcon = style.icon;

  return (
    <Card className={`${style.border} border-2`}>
      <CardHeader className={style.bg}>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Leaf className="h-5 w-5 text-emerald-600" />
            ESG Risk Assessment
          </CardTitle>
          {data.is_sll && (
            <Badge variant="outline" className="bg-green-100 text-green-800 border-green-300">
              SLL Loan
            </Badge>
          )}
        </div>
        <CardDescription>
          ML-powered ESG analysis for {data.borrower}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6 pt-6">
        {/* Risk Level Display */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-full ${style.bg}`}>
              <RiskIcon className={`h-6 w-6 ${style.text}`} />
            </div>
            <div>
              <p className="text-sm text-slate-500">Risk Level</p>
              <p className={`text-2xl font-bold ${style.text}`}>
                {data.risk_level_display}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-slate-500">Confidence</p>
            <p className="text-2xl font-bold text-slate-800">
              {data.confidence_pct}
            </p>
          </div>
        </div>

        {/* Composite Score */}
        <div className="p-4 bg-gradient-to-r from-emerald-50 to-blue-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-600">Composite ESG Score</span>
            <span className="text-xl font-bold text-emerald-700">
              {data.composite_score}/100
            </span>
          </div>
          <Progress value={data.composite_score} className="h-3" />
        </div>

        {/* E/S/G Component Scores */}
        <div className="grid grid-cols-3 gap-4">
          {/* Environmental */}
          <div className="text-center p-3 bg-emerald-50 rounded-lg">
            <Leaf className="h-5 w-5 text-emerald-600 mx-auto mb-1" />
            <p className="text-xs text-slate-500">Environmental</p>
            <p className="text-lg font-bold text-emerald-700">
              {data.esg_components.environmental.toFixed(0)}
            </p>
            <Progress 
              value={data.esg_components.environmental} 
              className="h-1.5 mt-1" 
            />
          </div>

          {/* Social */}
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <Users className="h-5 w-5 text-blue-600 mx-auto mb-1" />
            <p className="text-xs text-slate-500">Social</p>
            <p className="text-lg font-bold text-blue-700">
              {data.esg_components.social.toFixed(0)}
            </p>
            <Progress 
              value={data.esg_components.social} 
              className="h-1.5 mt-1" 
            />
          </div>

          {/* Governance */}
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <Building2 className="h-5 w-5 text-purple-600 mx-auto mb-1" />
            <p className="text-xs text-slate-500">Governance</p>
            <p className="text-lg font-bold text-purple-700">
              {data.esg_components.governance.toFixed(0)}
            </p>
            <Progress 
              value={data.esg_components.governance} 
              className="h-1.5 mt-1" 
            />
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-slate-600 italic">
          {data.description}
        </p>

        {/* Toggle Details Button */}
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
              Show Details & Explanation
            </>
          )}
        </Button>

        {/* Expandable Details */}
        {showDetails && explanation && (
          <div className="space-y-4 pt-4 border-t">
            {/* Top Contributing Factors */}
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-3">
                Top Contributing Factors
              </h4>
              <div className="space-y-2">
                {explanation.top_factors.slice(0, 4).map((factor, idx) => (
                  <div
                    key={factor.feature}
                    className="flex items-center justify-between p-2 bg-slate-50 rounded"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-slate-400">
                        #{idx + 1}
                      </span>
                      <span className="text-sm font-medium">
                        {factor.feature.replace(/_/g, " ")}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-24">
                        <Progress 
                          value={factor.importance * 100} 
                          className="h-2" 
                        />
                      </div>
                      <span className="text-xs text-slate-500 w-12 text-right">
                        {factor.importance_pct}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Interpretation */}
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>AI Interpretation:</strong> {explanation.interpretation}
              </p>
            </div>

            {/* Probability Distribution */}
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-3">
                Risk Probability Distribution
              </h4>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs w-24 text-slate-500">Low Risk</span>
                  <Progress 
                    value={data.probabilities.LOW_RISK * 100} 
                    className="h-2 flex-1" 
                  />
                  <span className="text-xs w-12 text-right">
                    {(data.probabilities.LOW_RISK * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs w-24 text-slate-500">Medium Risk</span>
                  <Progress 
                    value={data.probabilities.MEDIUM_RISK * 100} 
                    className="h-2 flex-1" 
                  />
                  <span className="text-xs w-12 text-right">
                    {(data.probabilities.MEDIUM_RISK * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs w-24 text-slate-500">High Risk</span>
                  <Progress 
                    value={data.probabilities.HIGH_RISK * 100} 
                    className="h-2 flex-1" 
                  />
                  <span className="text-xs w-12 text-right">
                    {(data.probabilities.HIGH_RISK * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Model Info */}
            <div className="pt-2 border-t text-xs text-slate-400 space-y-1">
              <p>
                <strong>Model:</strong> XGBoost Classifier | <strong>Accuracy:</strong> 97.05% | <strong>AUC:</strong> 0.9985
              </p>
              <p>
                <strong>Training Data:</strong> 11K records, 1000 companies (Kaggle ESG Dataset)
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
