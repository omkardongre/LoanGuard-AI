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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ClipboardList,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  AlertTriangle,
  User,
  DollarSign,
  Building2,
  MessageSquare,
} from "lucide-react";

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types
interface ApprovalRequest {
  request_id: string;
  loan_id: string;
  borrower_name: string;
  amount: number;
  sector: string;
  committee_decision: string;
  committee_confidence: number;
  committee_reasoning: string;
  vote_breakdown: Record<string, number>;
  created_at: string;
  status: string;
  reviewed_by?: string;
  reviewed_at?: string;
  reviewer_notes?: string;
  final_decision?: string;
}

// Fetch pending approvals
async function fetchPendingApprovals(): Promise<ApprovalRequest[]> {
  const response = await fetch(`${API_BASE}/api/risk-committee/approvals/pending`);
  if (!response.ok) throw new Error("Failed to fetch approvals");
  const data = await response.json();
  return data.pending || [];
}

// Approve request
async function approveRequest(
  requestId: string,
  approver: string,
  notes: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/risk-committee/approvals/${requestId}/approve`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approver, notes }),
    }
  );
  if (!response.ok) throw new Error("Failed to approve request");
}

// Reject request
async function rejectRequest(
  requestId: string,
  approver: string,
  notes: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/risk-committee/approvals/${requestId}/reject`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approver, notes }),
    }
  );
  if (!response.ok) throw new Error("Failed to reject request");
}

export function ApprovalQueueCard() {
  const [loading, setLoading] = useState(false);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [approverName, setApproverName] = useState("Manager");
  const [notes, setNotes] = useState<Record<string, string>>({});

  // Load approvals on mount
  useEffect(() => {
    loadApprovals();
  }, []);

  async function loadApprovals() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchPendingApprovals();
      setApprovals(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load approvals");
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(requestId: string) {
    try {
      setActionLoading(requestId);
      await approveRequest(requestId, approverName, notes[requestId] || "");
      await loadApprovals();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleReject(requestId: string) {
    try {
      setActionLoading(requestId);
      await rejectRequest(requestId, approverName, notes[requestId] || "");
      await loadApprovals();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rejection failed");
    } finally {
      setActionLoading(null);
    }
  }

  function updateNotes(requestId: string, value: string) {
    setNotes((prev) => ({ ...prev, [requestId]: value }));
  }

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  return (
    <Card className="border-2 border-amber-200">
      <CardHeader className="bg-gradient-to-r from-amber-50 to-orange-50">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <ClipboardList className="h-5 w-5 text-amber-600" />
            Approval Queue
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={`${
                approvals.length > 0
                  ? "bg-amber-100 text-amber-800 border-amber-300"
                  : "bg-emerald-100 text-emerald-800 border-emerald-300"
              }`}
            >
              {approvals.length} Pending
            </Badge>
            <Button
              size="sm"
              variant="ghost"
              onClick={loadApprovals}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>
        <CardDescription>
          Review and approve REFER decisions from the Risk Committee
        </CardDescription>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {/* Approver Name */}
        <div className="flex items-center gap-2 p-2 bg-slate-50 rounded-lg">
          <User className="h-4 w-4 text-slate-500" />
          <Label className="text-xs text-slate-600">Approver:</Label>
          <Input
            value={approverName}
            onChange={(e) => setApproverName(e.target.value)}
            className="h-7 text-xs flex-1 max-w-[200px]"
            placeholder="Your name"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto text-amber-500" />
            <p className="text-sm text-slate-500 mt-2">Loading approvals...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && approvals.length === 0 && (
          <div className="text-center py-8 text-slate-500">
            <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-emerald-400" />
            <p className="text-sm font-medium">All caught up!</p>
            <p className="text-xs">No pending approval requests</p>
          </div>
        )}

        {/* Approval Cards */}
        {approvals.map((request) => (
          <div
            key={request.request_id}
            className="p-4 bg-white border-2 border-amber-200 rounded-lg space-y-3"
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-amber-500" />
                <span className="text-sm font-medium">{request.loan_id}</span>
              </div>
              <Badge className="bg-amber-100 text-amber-800">
                REFER
              </Badge>
            </div>

            {/* Details */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-1">
                <Building2 className="h-3 w-3 text-slate-400" />
                <span className="text-slate-600">{request.borrower_name}</span>
              </div>
              <div className="flex items-center gap-1">
                <DollarSign className="h-3 w-3 text-slate-400" />
                <span className="text-slate-600">{formatCurrency(request.amount)}</span>
              </div>
            </div>

            {/* Reasoning */}
            <div className="p-2 bg-slate-50 rounded text-xs text-slate-600">
              <p className="line-clamp-2">{request.committee_reasoning}</p>
            </div>

            {/* Vote Breakdown */}
            <div className="flex gap-1 flex-wrap">
              {Object.entries(request.vote_breakdown).map(
                ([vote, count]) =>
                  count > 0 && (
                    <Badge
                      key={vote}
                      variant="outline"
                      className={`text-[10px] ${
                        vote === "approve"
                          ? "border-emerald-300 text-emerald-700"
                          : vote === "decline"
                          ? "border-red-300 text-red-700"
                          : "border-amber-300 text-amber-700"
                      }`}
                    >
                      {vote}: {count}
                    </Badge>
                  )
              )}
            </div>

            {/* Notes Input */}
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-slate-400" />
              <Input
                value={notes[request.request_id] || ""}
                onChange={(e) => updateNotes(request.request_id, e.target.value)}
                placeholder="Add notes (optional)"
                className="h-8 text-xs flex-1"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={() => handleApprove(request.request_id)}
                disabled={actionLoading === request.request_id}
                className="flex-1 bg-emerald-600 hover:bg-emerald-700"
              >
                {actionLoading === request.request_id ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <CheckCircle2 className="h-4 w-4 mr-1" />
                    Approve
                  </>
                )}
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => handleReject(request.request_id)}
                disabled={actionLoading === request.request_id}
                className="flex-1"
              >
                {actionLoading === request.request_id ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <XCircle className="h-4 w-4 mr-1" />
                    Reject
                  </>
                )}
              </Button>
            </div>

            {/* Timestamp */}
            <p className="text-[10px] text-slate-400 text-right">
              Created: {formatDate(request.created_at)}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
