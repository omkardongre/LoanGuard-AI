"use client";

import { useState, useCallback, useEffect } from "react";
import { Sidebar } from "@/components/sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Upload,
  FileText,
  CheckCircle,
  AlertTriangle,
  Loader2,
  X,
  Download,
  Eye,
  ArrowRight,
} from "lucide-react";
import {
  fetchLoans,
  uploadDocument,
  fetchDocument,
  type Loan,
  type DocumentParseResult,
} from "@/lib/api";

interface UploadedFile {
  file: File;
  status: "pending" | "uploading" | "processing" | "complete" | "error";
  progress: number;
  result?: DocumentParseResult;
  error?: string;
}

export default function UploadPage() {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [selectedLoan, setSelectedLoan] = useState<string>("");
  const [createdLoanId, setCreatedLoanId] = useState<string | null>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadLoans() {
      try {
        const response = await fetchLoans({ limit: 100 });
        setLoans(response.loans || []);
      } catch (err) {
        console.error("Failed to load loans:", err);
      } finally {
        setLoading(false);
      }
    }
    loadLoans();
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      addFiles(selectedFiles);
    }
  }, []);

  function addFiles(newFiles: File[]) {
    const validFiles = newFiles.filter((file) => {
      const validTypes = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
      ];
      return validTypes.includes(file.type) || file.name.endsWith(".pdf");
    });

    const uploadedFiles: UploadedFile[] = validFiles.map((file) => ({
      file,
      status: "pending",
      progress: 0,
    }));

    setFiles((prev) => [...prev, ...uploadedFiles]);
  }

  async function handleUpload() {
    if (!selectedLoan) {
      return;
    }

    const pendingFiles = files.filter((f) => f.status === "pending");

    for (let i = 0; i < pendingFiles.length; i++) {
      const fileIndex = files.findIndex((f) => f === pendingFiles[i]);

      // Update status to uploading
      setFiles((prev) =>
        prev.map((f, idx) =>
          idx === fileIndex ? { ...f, status: "uploading" as const, progress: 30 } : f
        )
      );

      try {
        // Upload the file
        const result = await uploadDocument(selectedLoan, pendingFiles[i].file);

        // Update status to processing
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === fileIndex ? { ...f, status: "processing" as const, progress: 60 } : f
          )
        );

        // Poll for completion (simplified - real implementation would poll)
        await new Promise((resolve) => setTimeout(resolve, 1000));

        // Update to complete and capture the created loan ID
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === fileIndex
              ? { ...f, status: "complete" as const, progress: 100, result }
              : f
          )
        );
        
        // If this was a NEW_LOAN, capture the actual created loan ID
        if (result.loan_id && result.loan_id !== "NEW_LOAN") {
          setCreatedLoanId(result.loan_id);
        }
      } catch (err) {
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === fileIndex
              ? {
                  ...f,
                  status: "error" as const,
                  error: err instanceof Error ? err.message : "Upload failed",
                }
              : f
          )
        );
      }
    }
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, idx) => idx !== index));
  }

  const pendingCount = files.filter((f) => f.status === "pending").length;
  const completeCount = files.filter((f) => f.status === "complete").length;
  const totalCovenants = files
    .filter((f) => f.result)
    .reduce((sum, f) => sum + (f.result?.covenants_extracted || 0), 0);

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 p-8 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8 flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg">
              <Upload className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">Document Upload</h1>
              <p className="text-slate-500">
                Upload loan agreements to extract covenants using Affinda AI
              </p>
            </div>
          </div>

          {/* Loan Selection */}
          <Card className="mb-6 overflow-hidden">
            <CardHeader className="bg-gradient-to-r from-slate-50 to-white border-b">
              <CardTitle className="flex items-center gap-3">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-white text-sm font-bold">1</span>
                Select Target Loan
              </CardTitle>
            </CardHeader>
            <CardContent>
              <select
                value={selectedLoan}
                onChange={(e) => setSelectedLoan(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="">Select a loan to associate documents...</option>
                <option value="NEW_LOAN">+ Create New Loan</option>
                {loans.map((loan) => (
                  <option key={loan.loan_id} value={loan.loan_id}>
                    {loan.loan_id} - {loan.borrower_name}
                  </option>
                ))}
              </select>
              {selectedLoan === "NEW_LOAN" && (
                <p className="text-sm text-amber-600 mt-2">
                  A new loan will be created from the extracted document data.
                </p>
              )}
            </CardContent>
          </Card>

          {/* Upload Area */}
          <Card className="mb-6 overflow-hidden">
            <CardHeader className="bg-gradient-to-r from-slate-50 to-white border-b">
              <CardTitle className="flex items-center gap-3">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 text-white text-sm font-bold">2</span>
                Upload Documents
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 ${
                  isDragging
                    ? "border-emerald-500 bg-gradient-to-br from-emerald-50 to-teal-50 scale-[1.02]"
                    : "border-slate-300 hover:border-emerald-400 hover:bg-slate-50"
                }`}
              >
                <div className={`p-4 rounded-full mx-auto mb-6 ${isDragging ? "bg-gradient-to-br from-emerald-100 to-teal-100" : "bg-slate-100"} transition-colors`}>
                  <Upload
                    className={`h-12 w-12 ${
                      isDragging ? "text-emerald-500" : "text-slate-400"
                    }`}
                  />
                </div>
                <p className="text-xl font-semibold text-slate-800 mb-2">
                  Drag & drop loan documents here
                </p>
                <p className="text-slate-500 mb-6">or click to browse your files</p>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload">
                  <Button
                    variant="outline"
                    className="cursor-pointer"
                    onClick={() => document.getElementById("file-upload")?.click()}
                  >
                    Browse Files
                  </Button>
                </label>
                <p className="text-xs text-slate-400 mt-4">
                  Supported: PDF, DOC, DOCX, TXT (max 50MB per file)
                </p>
              </div>
            </CardContent>
          </Card>

          {/* File List */}
          {files.length > 0 && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>3. Files ({files.length})</span>
                  {pendingCount > 0 && (
                    <Button
                      onClick={handleUpload}
                      disabled={!selectedLoan}
                      className="bg-emerald-600 hover:bg-emerald-700"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      Upload {pendingCount} Files
                    </Button>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {files.map((file, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-4 p-4 bg-slate-50 rounded-lg"
                    >
                      <div
                        className={`p-2 rounded-lg ${
                          file.status === "complete"
                            ? "bg-emerald-100"
                            : file.status === "error"
                            ? "bg-red-100"
                            : "bg-slate-200"
                        }`}
                      >
                        <FileText
                          className={`h-5 w-5 ${
                            file.status === "complete"
                              ? "text-emerald-600"
                              : file.status === "error"
                              ? "text-red-600"
                              : "text-slate-500"
                          }`}
                        />
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-900 truncate">
                          {file.file.name}
                        </p>
                        <p className="text-sm text-slate-500">
                          {(file.file.size / 1024 / 1024).toFixed(2)} MB
                        </p>

                        {(file.status === "uploading" ||
                          file.status === "processing") && (
                          <div className="mt-2">
                            <Progress value={file.progress} className="h-1" />
                            <p className="text-xs text-slate-500 mt-1">
                              {file.status === "uploading"
                                ? "Uploading..."
                                : "Processing with Affinda AI..."}
                            </p>
                          </div>
                        )}

                        {file.status === "complete" && file.result && (
                          <div className="mt-2 flex items-center gap-2">
                            <Badge variant="outline" className="text-emerald-600">
                              {file.result.covenants_extracted || 0} covenants
                            </Badge>
                            <span className="text-xs text-slate-500">
                              Confidence:{" "}
                              {((file.result.extraction_confidence || 0) * 100).toFixed(
                                0
                              )}
                              %
                            </span>
                          </div>
                        )}

                        {file.status === "error" && (
                          <p className="text-sm text-red-600 mt-1">{file.error}</p>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        {file.status === "complete" ? (
                          <CheckCircle className="h-5 w-5 text-emerald-500" />
                        ) : file.status === "error" ? (
                          <AlertTriangle className="h-5 w-5 text-red-500" />
                        ) : file.status === "uploading" ||
                          file.status === "processing" ? (
                          <Loader2 className="h-5 w-5 text-emerald-600 animate-spin" />
                        ) : null}

                        {file.status === "pending" && (
                          <button
                            onClick={() => removeFile(idx)}
                            className="p-1 hover:bg-slate-200 rounded"
                          >
                            <X className="h-4 w-4 text-slate-500" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Results Summary */}
          {completeCount > 0 && (
            <Card className="bg-emerald-50 border-emerald-200">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <CheckCircle className="h-8 w-8 text-emerald-600" />
                    <div>
                      <p className="font-semibold text-emerald-900">
                        {completeCount} documents processed successfully
                      </p>
                      <p className="text-sm text-emerald-700">
                        Extracted {totalCovenants} covenants
                      </p>
                    </div>
                  </div>
                  <a href={`/loans/${createdLoanId || (selectedLoan !== "NEW_LOAN" ? selectedLoan : files.find(f => f.result?.loan_id)?.result?.loan_id || selectedLoan)}`}>
                    <Button className="bg-emerald-600 hover:bg-emerald-700">
                      View Loan
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </a>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Processing Info */}
          <Card className="mt-6">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <Eye className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">
                    Affinda AI Document Intelligence
                  </h3>
                  <p className="text-sm text-slate-600 mt-1">
                    Documents are processed using Affinda's AI to automatically extract:
                  </p>
                  <ul className="text-sm text-slate-600 mt-2 list-disc list-inside space-y-1">
                    <li>Loan agreement terms and conditions</li>
                    <li>Financial covenants (Debt/EBITDA, Interest Coverage, etc.)</li>
                    <li>ESG KPIs and Sustainability Performance Targets</li>
                    <li>Margin ratchet schedules</li>
                    <li>Key dates and parties</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
