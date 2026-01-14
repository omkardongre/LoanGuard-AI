"use client";

import * as React from "react";
import { Phone, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  makeCovenantBreachCall,
  getCallStatus,
  type CovenantBreachCallRequest,
} from "@/lib/api";

interface VoiceCallButtonProps {
  variant?: "covenant-breach";
  loanId?: string;
  breachType?: string;
  threshold?: string;
  actualValue?: string;
  severity?: "HIGH" | "MEDIUM" | "LOW" | "CRITICAL";
  phoneNumber?: string; // Optional - will prompt if not provided
  size?: "default" | "sm" | "lg";
  className?: string;
}

export function VoiceCallButton({
  variant = "covenant-breach",
  loanId,
  breachType,
  threshold,
  actualValue,
  severity = "HIGH",
  phoneNumber,
  size = "default",
  className,
}: VoiceCallButtonProps) {
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [callStatus, setCallStatus] = React.useState<string | null>(null);
  const [conversationId, setConversationId] = React.useState<string | null>(null);
  const [transcript, setTranscript] = React.useState<Array<{
    role: string;
    message: string;
  }>>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [enteredPhoneNumber, setEnteredPhoneNumber] = React.useState(phoneNumber || "");

  const handleMakeCall = async () => {
    setLoading(true);
    setError(null);
    setCallStatus("initiating");

    try {
      if (variant === "covenant-breach") {
        if (!loanId || !breachType || !enteredPhoneNumber) {
          throw new Error("Missing required fields for covenant breach call");
        }

        const request: CovenantBreachCallRequest = {
          loan_id: loanId,
          breach_type: breachType,
          severity,
          phone_number: enteredPhoneNumber,
          threshold,
          actual_value: actualValue,
        };

        const response = await makeCovenantBreachCall(request);
        
        if (response.success && response.call_result) {
          setCallStatus(response.call_result.status);
          setConversationId(response.call_result.conversation_id);
          setTranscript(response.call_result.transcript || []);

          // Start polling for call status
          if (response.call_result.conversation_id) {
            pollCallStatus(response.call_result.conversation_id);
          }
        } else {
          throw new Error(response.error || "Failed to initiate call");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to make call");
      setCallStatus("error");
      setLoading(false);
    }
  };

  const pollCallStatus = async (convId: string) => {
    const pollInterval = 2000; // 2 seconds
    const maxAttempts = 180; // 6 minutes max
    let attempts = 0;

    const poll = async () => {
      try {
        const status = await getCallStatus(convId);
        setCallStatus(status.status);
        setTranscript(status.transcript || []);

        if (status.status === "done" || status.status === "failed") {
          setLoading(false);
          return;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, pollInterval);
        } else {
          setCallStatus("timeout");
          setLoading(false);
        }
      } catch (err) {
        console.error("Poll error:", err);
        setError(err instanceof Error ? err.message : "Failed to get call status");
        setLoading(false);
      }
    };

    poll();
  };

  const getStatusColor = (status: string | null) => {
    switch (status) {
      case "done":
        return "bg-green-500";
      case "failed":
      case "error":
        return "bg-red-500";
      case "in-progress":
      case "initiated":
        return "bg-blue-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStatusLabel = (status: string | null) => {
    if (!status) return "Ready";
    return status.charAt(0).toUpperCase() + status.slice(1).replace("-", " ");
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant={severity === "HIGH" || severity === "CRITICAL" ? "destructive" : "default"}
          size={size}
          className={className}
        >
          <Phone className="mr-2 h-4 w-4" />
          Call Risk Committee
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Voice Alert: Covenant Breach</DialogTitle>
          <DialogDescription>
            Make a voice call to the Risk Committee about this covenant breach.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Call Details */}
          <div className="grid gap-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Loan ID:</span>
              <span className="font-mono">{loanId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Breach Type:</span>
              <span>{breachType}</span>
            </div>
          </div>

          {/* Phone Number Input */}
          {!callStatus && (
            <div className="space-y-2">
              <Label htmlFor="phone-number">Risk Committee Phone Number</Label>
              <Input
                id="phone-number"
                type="tel"
                placeholder="+1 (415) 555-1234"
                value={enteredPhoneNumber}
                onChange={(e) => setEnteredPhoneNumber(e.target.value)}
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground">
                Enter phone number in format: +1 (xxx) xxx-xxxx
              </p>
            </div>
          )}

          {/* Call Details (After Call) */}
          {callStatus && (
            <div className="grid gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Phone Called:</span>
                <span className="font-mono">{enteredPhoneNumber}</span>
              </div>
            </div>
          )}

          {/* Call Status */}
          {callStatus && (
            <div className="flex items-center gap-2">
              <Badge className={getStatusColor(callStatus)}>
                {getStatusLabel(callStatus)}
              </Badge>
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {conversationId && (
                <span className="text-xs text-muted-foreground font-mono">
                  ID: {conversationId.substring(0, 12)}...
                </span>
              )}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Success Message */}
          {callStatus === "done" && !error && (
            <Alert>
              <CheckCircle2 className="h-4 w-4" />
              <AlertDescription>
                Call completed successfully. Transcript below.
              </AlertDescription>
            </Alert>
          )}

          {/* Transcript */}
          {transcript.length > 0 && (
            <div className="border rounded-lg p-4">
              <div className="text-sm font-medium mb-2">Call Transcript:</div>
              <div className="max-h-[200px] overflow-y-auto">
                <div className="space-y-3">
                  {transcript.map((turn, idx) => (
                    <div
                      key={idx}
                      className={`text-sm ${
                        turn.role === "agent"
                          ? "text-blue-600"
                          : "text-gray-700"
                      }`}
                    >
                      <div className="font-semibold">
                        {turn.role === "agent" ? "AI Agent" : "Human"}:
                      </div>
                      <div className="pl-4">{turn.message}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          {!callStatus && (
            <Button onClick={handleMakeCall} disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Make Call
            </Button>
          )}
          {(callStatus === "done" || callStatus === "failed" || callStatus === "error") && (
            <>
              <Button 
                variant="outline" 
                onClick={() => {
                  setCallStatus(null);
                  setConversationId(null);
                  setTranscript([]);
                  setError(null);
                  setLoading(false);
                }}
              >
                Try Again
              </Button>
              <Button onClick={() => setOpen(false)}>Close</Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
