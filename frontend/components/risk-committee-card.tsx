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
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Users,
  Shield,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Brain,
  Scale,
  Activity,
  FileText,
  Download,
  MessageSquare,
  RotateCcw,
  Target,
} from "lucide-react";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types
interface AgentVote {
  agent: string;
  vote: string;
  confidence: number;
  reasoning: string;
  risk_factors: string[];
  recommendations: string[];
}

interface AuditEntry {
  timestamp: string;
  agent: string;
  action: string;
  details: Record<string, unknown>;
}

interface RiskCommitteeResult {
  success: boolean;
  loan_id: string;
  borrower_name: string;
  sector: string;
  amount: number;
  final_decision: string;
  final_confidence: number;
  final_reasoning: string;
  consensus_achieved: boolean;
  agent_votes: AgentVote[];
  vote_summary: Record<string, number>;
  audit_trail: AuditEntry[];
  workflow_started: string;
  workflow_completed: string;
  total_agents: number;
  // Debate mode fields
  rounds_completed?: number;
  max_rounds?: number;
  convergence_achieved?: boolean;
  convergence_round?: number;
  round_history?: Array<{
    round: number;
    majority_vote: string;
    consensus_rate: number;
    average_confidence: number;
  }>;
}

// Fetch function
async function runRiskCommittee(params: {
  loan_id: string;
  borrower_name: string;
  sector: string;
  amount: number;
  credit_score: number;
}): Promise<RiskCommitteeResult> {
  const response = await fetch(`${API_BASE}/api/risk-committee/assess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!response.ok) throw new Error("Risk Committee assessment failed");
  return response.json();
}

// Run debate mode
async function runDebateMode(params: {
  loan_id: string;
  borrower_name: string;
  sector: string;
  amount: number;
  credit_score: number;
  max_rounds: number;
}): Promise<RiskCommitteeResult> {
  const response = await fetch(`${API_BASE}/api/risk-committee/debate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!response.ok) throw new Error("Debate mode failed");
  return response.json();
}

// Download PDF report
async function downloadPDFReport(params: {
  loan_id: string;
  borrower_name: string;
  sector: string;
  amount: number;
  credit_score: number;
}): Promise<void> {
  const response = await fetch(`${API_BASE}/api/risk-committee/report/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!response.ok) throw new Error("PDF generation failed");
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `credit_decision_${params.loan_id}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

// Component props
interface RiskCommitteeCardProps {
  loanId?: string;
  borrowerName?: string;
  sector?: string;
  amount?: number;
}

export function RiskCommitteeCard({
  loanId = "DEMO-001",
  borrowerName = "Sample Corporation",
  sector = "energy",
  amount = 5000000,
}: RiskCommitteeCardProps) {
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [result, setResult] = useState<RiskCommitteeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAudit, setShowAudit] = useState(false);
  const [showRoundHistory, setShowRoundHistory] = useState(false);
  
  // Debate mode state
  const [debateMode, setDebateMode] = useState(false);
  const [maxRounds, setMaxRounds] = useState(2);
  
  // Form state
  const [formLoanId, setFormLoanId] = useState(loanId);
  const [formBorrower, setFormBorrower] = useState(borrowerName);
  const [formSector, setFormSector] = useState(sector);
  const [formAmount, setFormAmount] = useState(amount);
  const [formCreditScore, setFormCreditScore] = useState(700);

  const sectors = [
    { id: "energy", name: "Energy (Oil & Gas)" },
    { id: "technology", name: "Technology" },
    { id: "healthcare", name: "Healthcare" },
    { id: "real_estate", name: "Real Estate" },
    { id: "manufacturing", name: "Manufacturing" },
    { id: "financial_services", name: "Financial Services" },
    { id: "retail", name: "Retail" },
    { id: "agriculture", name: "Agriculture" },
  ];

  // Run assessment (standard or debate mode)
  async function handleAssess() {
    try {
      setLoading(true);
      setError(null);
      
      const baseParams = {
        loan_id: formLoanId,
        borrower_name: formBorrower,
        sector: formSector,
        amount: formAmount,
        credit_score: formCreditScore,
      };
      
      let data: RiskCommitteeResult;
      
      if (debateMode) {
        data = await runDebateMode({ ...baseParams, max_rounds: maxRounds });
      } else {
        data = await runRiskCommittee(baseParams);
      }
      
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
  
  // Download PDF report
  async function handleDownloadPDF() {
    try {
      setPdfLoading(true);
      await downloadPDFReport({
        loan_id: formLoanId,
        borrower_name: formBorrower,
        sector: formSector,
        amount: formAmount,
        credit_score: formCreditScore,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF download failed");
    } finally {
      setPdfLoading(false);
    }
  }

  // Get decision styling
  const getDecisionStyle = (decision: string) => {
    switch (decision) {
      case "approve":
        return { icon: CheckCircle2, color: "text-emerald-600", bg: "bg-emerald-50", label: "APPROVED" };
      case "decline":
        return { icon: XCircle, color: "text-red-600", bg: "bg-red-50", label: "DECLINED" };
      case "caution":
        return { icon: AlertTriangle, color: "text-amber-600", bg: "bg-amber-50", label: "CAUTION" };
      default:
        return { icon: HelpCircle, color: "text-blue-600", bg: "bg-blue-50", label: "REFER" };
    }
  };

  // Get vote badge color
  const getVoteBadgeColor = (vote: string) => {
    switch (vote) {
      case "approve":
        return "bg-emerald-100 text-emerald-800";
      case "decline":
        return "bg-red-100 text-red-800";
      case "caution":
        return "bg-amber-100 text-amber-800";
      default:
        return "bg-blue-100 text-blue-800";
    }
  };

  return (
    <Card className="border-2 border-slate-200">
      <CardHeader className="bg-gradient-to-r from-purple-50 to-indigo-50">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5 text-purple-600" />
            Risk Committee
          </CardTitle>
          <Badge variant="outline" className="bg-purple-100 text-purple-800 border-purple-300">
            5 AI Agents
          </Badge>
        </div>
        <CardDescription>
          Multi-agent debate-style credit decision with full audit trail
        </CardDescription>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {/* Input Form */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-lg">
          <div className="space-y-2">
            <Label className="text-xs font-medium">Loan ID</Label>
            <Input 
              value={formLoanId} 
              onChange={(e) => setFormLoanId(e.target.value)}
              placeholder="LOAN-001"
              className="h-8 text-sm"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-medium">Borrower Name</Label>
            <Input 
              value={formBorrower} 
              onChange={(e) => setFormBorrower(e.target.value)}
              placeholder="Company Name"
              className="h-8 text-sm"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-medium">Sector</Label>
            <Select value={formSector} onValueChange={setFormSector}>
              <SelectTrigger className="h-8 text-sm">
                <SelectValue placeholder="Select sector" />
              </SelectTrigger>
              <SelectContent>
                {sectors.map((s) => (
                  <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-medium">Amount ($)</Label>
            <Input 
              type="number"
              value={formAmount} 
              onChange={(e) => setFormAmount(Number(e.target.value))}
              className="h-8 text-sm"
            />
          </div>
          <div className="col-span-2 space-y-2">
            <Label className="text-xs font-medium">Credit Score: {formCreditScore}</Label>
            <input 
              type="range"
              min="300"
              max="850"
              value={formCreditScore}
              onChange={(e) => setFormCreditScore(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        </div>

        {/* Debate Mode Toggle */}
        <div className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg border border-indigo-200">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-indigo-600" />
            <span className="text-sm font-medium text-indigo-800">Multi-Round Debate</span>
          </div>
          <div className="flex items-center gap-3">
            {debateMode && (
              <div className="flex items-center gap-2">
                <Label className="text-xs text-indigo-600">Rounds:</Label>
                <Select value={String(maxRounds)} onValueChange={(v) => setMaxRounds(Number(v))}>
                  <SelectTrigger className="h-7 w-16 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="2">2</SelectItem>
                    <SelectItem value="3">3</SelectItem>
                    <SelectItem value="4">4</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
            <Button
              size="sm"
              variant={debateMode ? "default" : "outline"}
              onClick={() => setDebateMode(!debateMode)}
              className={debateMode ? "bg-indigo-600 hover:bg-indigo-700" : ""}
            >
              {debateMode ? (
                <>
                  <Target className="h-3 w-3 mr-1" />
                  ON
                </>
              ) : (
                "OFF"
              )}
            </Button>
          </div>
        </div>

        {/* Run Button */}
        <Button 
          onClick={handleAssess} 
          disabled={loading} 
          className={`w-full ${debateMode ? "bg-indigo-600 hover:bg-indigo-700" : "bg-purple-600 hover:bg-purple-700"}`}
        >
          {loading ? (
            <RefreshCw className="h-4 w-4 animate-spin mr-2" />
          ) : debateMode ? (
            <RotateCcw className="h-4 w-4 mr-2" />
          ) : (
            <Brain className="h-4 w-4 mr-2" />
          )}
          {loading 
            ? (debateMode ? `Debate Round in Progress...` : "Committee Deliberating...")
            : (debateMode ? `Start ${maxRounds}-Round Debate` : "Convene Risk Committee")
          }
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
            {/* Final Decision */}
            <div className={`p-4 rounded-lg ${getDecisionStyle(result.final_decision).bg}`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {(() => {
                    const Icon = getDecisionStyle(result.final_decision).icon;
                    return <Icon className={`h-6 w-6 ${getDecisionStyle(result.final_decision).color}`} />;
                  })()}
                  <span className={`text-2xl font-bold ${getDecisionStyle(result.final_decision).color}`}>
                    {getDecisionStyle(result.final_decision).label}
                  </span>
                </div>
                <Badge className={result.consensus_achieved ? "bg-emerald-600" : "bg-amber-600"}>
                  {result.consensus_achieved ? "Consensus" : "Split Vote"}
                </Badge>
              </div>
              <p className="text-sm text-slate-700">{result.final_reasoning}</p>
            </div>

            {/* Confidence & Vote Summary */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500">Confidence</p>
                <div className="flex items-center gap-2">
                  <Progress value={result.final_confidence * 100} className="h-2 flex-1" />
                  <span className="text-sm font-bold">{(result.final_confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">Vote Summary</p>
                <div className="flex gap-1 flex-wrap">
                  {Object.entries(result.vote_summary).map(([vote, count]) => (
                    count > 0 && (
                      <Badge key={vote} className={getVoteBadgeColor(vote)}>
                        {vote}: {count}
                      </Badge>
                    )
                  ))}
                </div>
              </div>
            </div>

            {/* Agent Votes */}
            <div>
              <p className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <Scale className="h-4 w-4" />
                Agent Deliberations ({result.total_agents} agents)
              </p>
              <div className="space-y-2">
                {result.agent_votes.map((agent, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">{agent.agent}</span>
                      <Badge className={getVoteBadgeColor(agent.vote)}>
                        {agent.vote.toUpperCase()}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-600">{agent.reasoning}</p>
                    {agent.risk_factors.length > 0 && (
                      <div className="mt-1 flex gap-1 flex-wrap">
                        {agent.risk_factors.slice(0, 2).map((rf, i) => (
                          <Badge key={i} variant="outline" className="text-[10px] bg-red-50">
                            {rf}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Audit Trail Toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAudit(!showAudit)}
              className="w-full"
            >
              {showAudit ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-2" />
                  Hide Audit Trail
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-2" />
                  Show Audit Trail ({result.audit_trail.length} entries)
                </>
              )}
            </Button>

            {/* Audit Trail */}
            {showAudit && (
              <div className="p-3 bg-slate-50 rounded-lg max-h-48 overflow-y-auto">
                <p className="text-xs font-semibold text-slate-600 mb-2 flex items-center gap-1">
                  <FileText className="h-3 w-3" />
                  EU AI Act Compliance Audit Trail
                </p>
                <div className="space-y-1">
                  {result.audit_trail.map((entry, idx) => (
                    <div key={idx} className="text-[10px] p-1 bg-white rounded border">
                      <span className="text-slate-400">{entry.timestamp.split('T')[1]?.split('.')[0]}</span>
                      {" • "}
                      <span className="font-medium">{entry.agent}</span>
                      {" → "}
                      <span className="text-slate-600">{entry.action}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Round History (Debate Mode) */}
            {result.round_history && result.round_history.length > 0 && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowRoundHistory(!showRoundHistory)}
                  className="w-full"
                >
                  {showRoundHistory ? (
                    <>
                      <ChevronUp className="h-4 w-4 mr-2" />
                      Hide Round History
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-4 w-4 mr-2" />
                      Show Round History ({result.round_history.length} rounds)
                    </>
                  )}
                </Button>
                
                {showRoundHistory && (
                  <div className="p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                    <p className="text-xs font-semibold text-indigo-700 mb-2 flex items-center gap-1">
                      <RotateCcw className="h-3 w-3" />
                      Multi-Round Debate History
                      {result.convergence_achieved && (
                        <Badge className="ml-2 bg-emerald-500 text-[10px]">
                          Converged R{result.convergence_round}
                        </Badge>
                      )}
                    </p>
                    <div className="space-y-2">
                      {result.round_history.map((round, idx) => (
                        <div key={idx} className="p-2 bg-white rounded border text-xs">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-indigo-800">Round {round.round}</span>
                            <Badge className={getVoteBadgeColor(round.majority_vote)}>
                              {round.majority_vote.toUpperCase()}
                            </Badge>
                          </div>
                          <div className="flex gap-4 text-slate-600">
                            <span>Consensus: {(round.consensus_rate * 100).toFixed(0)}%</span>
                            <span>Confidence: {(round.average_confidence * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* PDF Download Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadPDF}
              disabled={pdfLoading}
              className="w-full border-blue-300 text-blue-700 hover:bg-blue-50"
            >
              {pdfLoading ? (
                <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              {pdfLoading ? "Generating PDF..." : "Download Credit Decision Report (PDF)"}
            </Button>

            {/* Compliance Badge */}
            <div className="flex items-center gap-2 p-2 bg-purple-50 border border-purple-200 rounded-lg">
              <Badge className="bg-purple-600 text-white">EU AI Act</Badge>
              <span className="text-xs text-purple-700">
                Full explainability and audit trail per regulatory requirements
              </span>
            </div>
          </div>
        )}

        {/* Initial State */}
        {!result && !loading && !error && (
          <div className="text-center py-8 text-slate-500">
            <Activity className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">Configure loan details and convene the committee</p>
            <p className="text-xs mt-1">5 AI agents will debate and vote on the decision</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
