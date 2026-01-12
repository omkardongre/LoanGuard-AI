"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { FileSliders, FileText, Loader2 } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

interface ExportButtonProps {
  type: "pptx-loan" | "pptx-portfolio" | "tlp-pdf" | "tlp-portfolio-pdf";
  loanId?: string;
  variant?: "default" | "outline" | "secondary";
  size?: "sm" | "default" | "lg";
  className?: string;
}

/**
 * Export Button Component for PowerPoint and TLP PDF reports.
 * 
 * Usage:
 * <ExportButton type="pptx-loan" loanId="LOAN-001" />
 * <ExportButton type="tlp-pdf" loanId="TRL-001" />
 * <ExportButton type="pptx-portfolio" />
 * <ExportButton type="tlp-portfolio-pdf" />
 */
export function ExportButton({
  type,
  loanId,
  variant = "default",
  size = "default",
  className = "",
}: ExportButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getEndpoint = (): string => {
    switch (type) {
      case "pptx-loan":
        if (!loanId) throw new Error("loanId required for loan PPTX");
        return `/api/esg/reports/pptx/loan/${loanId}`;
      case "pptx-portfolio":
        return `/api/esg/reports/pptx/portfolio`;
      case "tlp-pdf":
        if (!loanId) throw new Error("loanId required for TLP PDF");
        return `/api/esg/reports/tlp/${loanId}/pdf`;
      case "tlp-portfolio-pdf":
        return `/api/esg/reports/tlp/portfolio/pdf`;
      default:
        throw new Error(`Unknown export type: ${type}`);
    }
  };

  const getLabel = (): string => {
    switch (type) {
      case "pptx-loan":
        return "Export PowerPoint";
      case "pptx-portfolio":
        return "Export Portfolio PPTX";
      case "tlp-pdf":
        return "Download TLP Report";
      case "tlp-portfolio-pdf":
        return "Download Portfolio TLP";
      default:
        return "Export";
    }
  };

  const getIcon = () => {
    if (type.includes("pptx")) {
      return <FileSliders className="mr-2 h-4 w-4" />;
    }
    return <FileText className="mr-2 h-4 w-4" />;
  };

  const getMimeType = (): string => {
    if (type.includes("pptx")) {
      return "application/vnd.openxmlformats-officedocument.presentationml.presentation";
    }
    return "application/pdf";
  };

  const getFileExtension = (): string => {
    if (type.includes("pptx")) return "pptx";
    return "pdf";
  };

  const handleExport = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const endpoint = getEndpoint();
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Export failed: ${response.status}`);
      }

      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      
      // Generate filename
      const date = new Date().toISOString().split("T")[0];
      const prefix = type.replace("-", "_");
      const filename = loanId 
        ? `${prefix}_${loanId}_${date}.${getFileExtension()}`
        : `${prefix}_${date}.${getFileExtension()}`;
      
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
      console.error("Export error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="inline-flex flex-col">
      <Button
        variant={variant}
        size={size}
        onClick={handleExport}
        disabled={isLoading}
        className={className}
      >
        {isLoading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          getIcon()
        )}
        {isLoading ? "Generating..." : getLabel()}
      </Button>
      {error && (
        <span className="text-xs text-red-500 mt-1">{error}</span>
      )}
    </div>
  );
}

// Convenience components for specific export types
export function ExportPptxButton({
  loanId,
  variant = "default",
  size = "default",
  className = "",
}: {
  loanId?: string;
  variant?: "default" | "outline" | "secondary";
  size?: "sm" | "default" | "lg";
  className?: string;
}) {
  return (
    <ExportButton
      type={loanId ? "pptx-loan" : "pptx-portfolio"}
      loanId={loanId}
      variant={variant}
      size={size}
      className={className}
    />
  );
}

export function ExportTlpPdfButton({
  loanId,
  variant = "default",
  size = "default",
  className = "",
}: {
  loanId?: string;
  variant?: "default" | "outline" | "secondary";
  size?: "sm" | "default" | "lg";
  className?: string;
}) {
  return (
    <ExportButton
      type={loanId ? "tlp-pdf" : "tlp-portfolio-pdf"}
      loanId={loanId}
      variant={variant}
      size={size}
      className={className}
    />
  );
}
