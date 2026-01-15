"use client";

import { useEffect, useState, useCallback } from "react";
import { Sidebar } from "@/components/sidebar";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Upload, Search, Filter, Loader2, FileText, Briefcase, ExternalLink, Leaf, X } from "lucide-react";
import { fetchLoans, type Loan } from "@/lib/api";

function formatCurrency(amount: number, currency: string = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 0,
  }).format(amount);
}

export default function LoansPage() {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [showFilters, setShowFilters] = useState(false);

  // Debounced search
  const loadLoans = useCallback(async (search?: string, status?: string) => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (search && search.trim()) params.append("search", search.trim());
      if (status && status !== "ALL") params.append("status", status);
      
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
      const url = `${API_BASE}/api/loans${params.toString() ? `?${params.toString()}` : ""}`;
      const res = await fetch(url);
      const data = await res.json();
      setLoans(data.loans || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error("Failed to fetch loans:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLoans();
  }, [loadLoans]);

  // Search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      loadLoans(searchTerm, statusFilter);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm, statusFilter, loadLoans]);

  const clearFilters = () => {
    setSearchTerm("");
    setStatusFilter("");
    setShowFilters(false);
  };

  if (loading && loans.length === 0) {
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
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg">
              <Briefcase className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">Loan Portfolio</h1>
              <p className="text-slate-500">Manage and monitor all loans</p>
            </div>
          </div>
          <a href="/upload">
            <Button className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 shadow-lg">
              <Upload className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
          </a>
        </div>

        {/* Search & Filters */}
        <div className="flex gap-4 mb-6">
          <div className="flex-1 relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 group-focus-within:text-emerald-500 transition-colors" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by borrower, loan ID..."
              className="w-full pl-12 pr-10 py-3 border-2 rounded-xl focus:outline-none focus:ring-0 focus:border-emerald-500 transition-colors bg-white shadow-sm"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm("")}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          <div className="relative">
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className={`px-6 rounded-xl border-2 hover:bg-slate-50 hover:border-slate-300 transition-all ${statusFilter ? "border-emerald-500 bg-emerald-50" : ""}`}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters {statusFilter && `(${statusFilter})`}
            </Button>
            {showFilters && (
              <div className="absolute top-full mt-2 right-0 bg-white border rounded-xl shadow-lg p-4 z-10 min-w-48">
                <h4 className="font-semibold mb-3 text-slate-700">Status</h4>
                <div className="flex flex-col gap-2">
                  {["ALL", "GREEN", "AMBER", "RED"].map((s) => (
                    <button
                      key={s}
                      onClick={() => { setStatusFilter(s === "ALL" ? "" : s); setShowFilters(false); }}
                      className={`text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        (s === "ALL" && !statusFilter) || statusFilter === s
                          ? "bg-emerald-100 text-emerald-800"
                          : "hover:bg-slate-100"
                      }`}
                    >
                      {s === "ALL" ? "All Status" : s === "GREEN" ? "✅ Compliant" : s === "AMBER" ? "⚠️ Warning" : "❌ Breach"}
                    </button>
                  ))}
                </div>
                {(searchTerm || statusFilter) && (
                  <button onClick={clearFilters} className="mt-3 text-sm text-red-600 hover:underline">
                    Clear all filters
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Active Filters */}
        {(searchTerm || statusFilter) && (
          <div className="flex gap-2 mb-4">
            {searchTerm && (
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                Search: "{searchTerm}"
                <button onClick={() => setSearchTerm("")}><X className="h-3 w-3" /></button>
              </span>
            )}
            {statusFilter && (
              <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${
                statusFilter === "GREEN" ? "bg-emerald-100 text-emerald-800" :
                statusFilter === "AMBER" ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"
              }`}>
                Status: {statusFilter}
                <button onClick={() => setStatusFilter("")}><X className="h-3 w-3" /></button>
              </span>
            )}
          </div>
        )}

        {/* Loans Table */}
        <div className="bg-white rounded-2xl border shadow-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-slate-100 to-slate-50 border-b">
              <tr>
                <th className="text-left p-4 font-semibold text-slate-700">Loan ID</th>
                <th className="text-left p-4 font-semibold text-slate-700">Borrower</th>
                <th className="text-left p-4 font-semibold text-slate-700">Amount</th>
                <th className="text-left p-4 font-semibold text-slate-700">Type</th>
                <th className="text-left p-4 font-semibold text-slate-700">Maturity</th>
                <th className="text-left p-4 font-semibold text-slate-700">Covenants</th>
                <th className="text-left p-4 font-semibold text-slate-700">Status</th>
                <th className="text-left p-4 font-semibold text-slate-700">SLL</th>
              </tr>
            </thead>
            <tbody>
              {loans.map((loan) => (
                <tr
                  key={loan.loan_id}
                  className={`border-b hover:bg-gradient-to-r hover:from-blue-50 hover:to-transparent transition-all cursor-pointer group border-l-4 ${
                    loan.status === "GREEN" ? "border-l-emerald-500" :
                    loan.status === "AMBER" ? "border-l-amber-500" : "border-l-red-500"
                  }`}
                >
                  <td className="p-4">
                    <a
                      href={`/loans/${loan.loan_id}`}
                      className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1 group-hover:underline"
                    >
                      <FileText className="h-4 w-4" />
                      {loan.loan_id}
                    </a>
                  </td>
                  <td className="p-4 font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                    {loan.borrower_name}
                  </td>
                  <td className="p-4 text-slate-700 font-medium">
                    {formatCurrency(loan.facility_amount, loan.currency)}
                  </td>
                  <td className="p-4 text-slate-600">
                    <span className="px-2 py-1 bg-slate-100 rounded-md text-sm">
                      {loan.loan_type || "Term Loan"}
                    </span>
                  </td>
                  <td className="p-4 text-slate-600">{loan.maturity_date}</td>
                  <td className="p-4">
                    <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-md text-sm font-medium">
                      {loan.covenant_count || "-"}
                    </span>
                  </td>
                  <td className="p-4">
                    <StatusBadge status={loan.status} size="sm" />
                  </td>
                  <td className="p-4">
                    {loan.is_sll && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-emerald-100 to-teal-100 text-emerald-800">
                        <Leaf className="h-3 w-3" />
                        SLL
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-slate-500">
            Showing 1-{loans.length} of {total} loans
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled>
              Previous
            </Button>
            <Button variant="outline" size="sm">
              Next
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
