"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Upload, Search, Filter, Loader2, FileText, Briefcase, ExternalLink, Leaf } from "lucide-react";
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

  useEffect(() => {
    async function loadLoans() {
      try {
        setLoading(true);
        const data = await fetchLoans();
        setLoans(data.loans);
        setTotal(data.total);
      } catch (err) {
        console.error("Failed to fetch loans:", err);
        // Keep empty state on error
      } finally {
        setLoading(false);
      }
    }
    loadLoans();
  }, []);
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

        {/* Filters */}
        <div className="flex gap-4 mb-6">
          <div className="flex-1 relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 group-focus-within:text-emerald-500 transition-colors" />
            <input
              type="text"
              placeholder="Search by borrower, loan ID..."
              className="w-full pl-12 pr-4 py-3 border-2 rounded-xl focus:outline-none focus:ring-0 focus:border-emerald-500 transition-colors bg-white shadow-sm"
            />
          </div>
          <Button variant="outline" className="px-6 rounded-xl border-2 hover:bg-slate-50 hover:border-slate-300 transition-all">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
        </div>

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
