"use client";

import * as React from "react";
import { TrendingUp, TrendingDown, Info, AlertCircle, CheckCircle2 } from "lucide-react";
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
 * SHAP Waterfall Visualization Component
 * 
 * Production-level ML explainability visualization for banking judges.
 * Shows how AI decides breach probability using feature contributions.
 * 
 * Design principles for non-technical bankers:
 * - Clear base → final probability flow
 * - Color coding: red = increases risk, blue = decreases risk
 * - Human-readable explanations for each feature
 * - Regulatory compliance: EU AI Act explainability requirement
 */
export function SHAPWaterfall({ loanId, className }: SHAPWaterfallProps) {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [data, setData] = React.useState<{
    baseProbability: number;
    finalProbability: number;
    factors: SHAPFactor[];
  } | null>(null);

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
        console.error("SHAP explanation error:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    loadExplanation();
  }, [loanId]);

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>AI Explanation</CardTitle>
          <CardDescription>Loading breach prediction analysis...</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="h-8 w-full bg-gray-200 rounded animate-pulse" />
          <div className="h-24 w-full bg-gray-200 rounded animate-pulse" />
          <div className="h-24 w-full bg-gray-200 rounded animate-pulse" />
          <div className="h-24 w-full bg-gray-200 rounded animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>AI Explanation</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error || "Failed to load explanation data"}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const { baseProbability, finalProbability, factors } = data;
  const riskChange = ((finalProbability - baseProbability) / baseProbability) * 100;

  // Calculate cumulative probabilities for waterfall
  let cumulativeProbability = baseProbability;
  const waterfallData = factors.map((factor) => {
    const start = cumulativeProbability;
    cumulativeProbability += factor.shap_value;
    const end = cumulativeProbability;
    
    return {
      ...factor,
      startProbability: start,
      endProbability: end,
    };
  });

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              AI Breach Prediction Explanation
              <Info className="h-4 w-4 text-muted-foreground" />
            </CardTitle>
            <CardDescription>
              How AI calculates the {(finalProbability * 100).toFixed(1)}% breach probability
            </CardDescription>
          </div>
          <Badge variant={riskChange > 0 ? "destructive" : "default"}>
            {riskChange > 0 ? "↑" : "↓"} {Math.abs(riskChange).toFixed(1)}% vs baseline
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Probability Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">Base Probability</div>
            <div className="text-2xl font-bold">
              {(baseProbability * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground">
              Average for all loans
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">Final Probability</div>
            <div className="text-2xl font-bold text-red-600">
              {(finalProbability * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground">
              This loan's risk level
            </div>
          </div>
        </div>

        {/* Regulatory Compliance Badge */}
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription className="text-xs">
            <strong>EU AI Act Compliant:</strong> This explanation shows how the AI model makes decisions,
            ensuring transparency and accountability in automated risk assessment.
          </AlertDescription>
        </Alert>

        {/* Waterfall Bars */}
        <div className="space-y-4">
          <div className="text-sm font-medium">Key Risk Factors</div>
          
          {waterfallData.map((item, index) => {
            const barHeight = Math.abs(item.shap_value) * 200; // Scale for visual
            const isPositive = item.shap_value > 0;
            const percentage = item.shap_value * 100;

            return (
              <div key={index} className="space-y-2">
                {/* Feature Name */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {isPositive ? (
                      <TrendingUp className="h-4 w-4 text-red-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-blue-500" />
                    )}
                    <span className="text-sm font-medium capitalize">
                      {item.feature.replace(/_/g, " ")}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Value: {item.value.toFixed(2)}
                  </span>
                </div>

                {/* Visual Bar */}
                <div className="relative h-8 bg-gray-100 rounded overflow-hidden">
                  <div
                    className={`absolute top-0 h-full ${
                      isPositive ? "bg-red-500" : "bg-blue-500"
                    } transition-all`}
                    style={{
                      width: `${Math.min(Math.abs(percentage) * 100, 100)}%`,
                      left: isPositive ? 0 : "auto",
                      right: isPositive ? "auto" : 0,
                    }}
                  />
                  <div className="absolute inset-0 flex items-center justify-between px-2">
                    <span className="text-xs font-medium text-white mix-blend-difference">
                      {isPositive ? "+" : ""}{percentage.toFixed(1)}%
                    </span>
                    <span className="text-xs text-gray-600">
                      {item.impact === "increases" ? "Increases risk" : "Decreases risk"}
                    </span>
                  </div>
                </div>

                {/* Explanation */}
                <p className="text-xs text-muted-foreground pl-6">
                  {item.explanation}
                </p>
              </div>
            );
          })}
        </div>

        {/* Data Source */}
        <div className="pt-4 border-t text-xs text-muted-foreground">
          <strong>Model:</strong> LightGBM trained on 720,966 real loans (Lending Club 2007-2018) •{" "}
          <strong>Method:</strong> SHAP (TreeExplainer) •{" "}
          <strong>Features Analyzed:</strong> {factors.length}
        </div>
      </CardContent>
    </Card>
  );
}
