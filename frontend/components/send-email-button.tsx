"use client";

import * as React from "react";
import { Mail, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
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
import {
  sendCovenantBreachAlert,
  sendPortfolioSummaryEmail,
  type CovenantBreachEmailRequest,
  type PortfolioSummaryEmailRequest,
} from "@/lib/api";

interface SendEmailButtonProps {
  variant?: "covenant-breach" | "portfolio-summary";
  loanId?: string;
  breachType?: string;
  threshold?: string;
  actualValue?: string;
  severity?: "HIGH" | "MEDIUM" | "LOW";
  period?: "weekly" | "monthly";
  recipients?: string[];
  size?: "default" | "sm" | "lg";
  className?: string;
}

export function SendEmailButton({
  variant = "covenant-breach",
  loanId,
  breachType,
  threshold,
  actualValue,
  severity = "HIGH",
  period = "weekly",
  recipients,
  size = "default",
  className,
}: SendEmailButtonProps) {
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState<{
    success: boolean;
    message: string;
    subject?: string;
    recipients?: string[];
  } | null>(null);

  const handleSendEmail = async () => {
    setLoading(true);
    setResult(null);

    try {
      if (variant === "covenant-breach") {
        if (!loanId || !breachType || !threshold || !actualValue) {
          throw new Error("Missing required fields for covenant breach email");
        }

        const request: CovenantBreachEmailRequest = {
          loan_id: loanId,
          breach_type: breachType,
          threshold,
          actual_value: actualValue,
          severity,
        };

        const response = await sendCovenantBreachAlert(request);
        setResult({
          success: true,
          message: response.message,
          subject: response.subject,
          recipients: response.recipients,
        });
      } else {
        const request: PortfolioSummaryEmailRequest = {
          period,
          recipients,
        };

        const response = await sendPortfolioSummaryEmail(request);
        setResult({
          success: true,
          message: response.message,
          subject: response.subject,
          recipients: response.recipients,
        });
      }
    } catch (error) {
      setResult({
        success: false,
        message: error instanceof Error ? error.message : "Failed to send email",
      });
    } finally {
      setLoading(false);
    }
  };

  const dialogTitle =
    variant === "covenant-breach"
      ? "Send Covenant Breach Alert"
      : "Send Portfolio Summary";

  const dialogDescription =
    variant === "covenant-breach"
      ? "This will send an email alert to the Risk Committee about the covenant breach."
      : `This will send a ${period} portfolio summary email to senior management.`;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size={size} className={className}>
          <Mail className="w-4 h-4" />
          {variant === "covenant-breach" ? "Alert Risk Committee" : "Email Summary"}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{dialogTitle}</DialogTitle>
          <DialogDescription>{dialogDescription}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {variant === "covenant-breach" && (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Loan ID:</span>
                <span className="font-medium">{loanId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Breach Type:</span>
                <span className="font-medium">{breachType}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Threshold:</span>
                <span className="font-medium">{threshold}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Actual Value:</span>
                <span className="font-medium text-destructive">{actualValue}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Severity:</span>
                <span
                  className={`font-medium ${
                    severity === "HIGH"
                      ? "text-destructive"
                      : severity === "MEDIUM"
                      ? "text-orange-600"
                      : "text-yellow-600"
                  }`}
                >
                  {severity}
                </span>
              </div>
            </div>
          )}

          {variant === "portfolio-summary" && (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Period:</span>
                <span className="font-medium capitalize">{period}</span>
              </div>
              {recipients && recipients.length > 0 && (
                <div>
                  <span className="text-muted-foreground">Recipients:</span>
                  <div className="mt-1 text-xs space-y-1">
                    {recipients.map((email) => (
                      <div key={email} className="font-mono">
                        {email}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {result && (
            <Alert variant={result.success ? "default" : "destructive"}>
              {result.success ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <AlertDescription className="ml-2">
                <p className="font-medium">{result.message}</p>
                {result.success && result.subject && (
                  <p className="text-xs mt-1 text-muted-foreground">
                    Subject: {result.subject}
                  </p>
                )}
                {result.success && result.recipients && result.recipients.length > 0 && (
                  <p className="text-xs mt-1 text-muted-foreground">
                    Sent to: {result.recipients.join(", ")}
                  </p>
                )}
              </AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSendEmail}
            disabled={loading || (result?.success ?? false)}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Sending...
              </>
            ) : result?.success ? (
              <>
                <CheckCircle2 className="w-4 h-4" />
                Sent
              </>
            ) : (
              <>
                <Mail className="w-4 h-4" />
                Send Email
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
