"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Upload, Search, Filter, Loader2 } from "lucide-react";
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
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              Loan Portfolio
            </h1>
            <p className="text-slate-500">Manage and monitor all loans</p>
          </div>
          <Button className="bg-emerald-600 hover:bg-emerald-700">
            <Upload className="h-4 w-4 mr-2" />
            Upload Document
          </Button>
        </div>

        {/* Filters */}
        <div className="flex gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search loans..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
        </div>

        {/* Loans Table */}
        <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b">
              <tr>
                <th className="text-left p-4 font-medium text-slate-600">
                  Loan ID
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Borrower
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Amount
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Type
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Maturity
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Covenants
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Status
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  SLL
                </th>
              </tr>
            </thead>
            <tbody>
              {loans.map((loan) => (
                <tr
                  key={loan.loan_id}
                  className="border-b hover:bg-slate-50 cursor-pointer"
                >
                  <td className="p-4">
                    <a
                      href={`/loans/${loan.loan_id}`}
                      className="text-emerald-600 hover:underline font-medium"
                    >
                      {loan.loan_id}
                    </a>
                  </td>
                  <td className="p-4 font-medium text-slate-900">
                    {loan.borrower_name}
                  </td>
                  <td className="p-4 text-slate-600">
                    {formatCurrency(loan.facility_amount, loan.currency)}
                  </td>
                  <td className="p-4 text-slate-600">
                    {loan.loan_type || "Term Loan"}
                  </td>
                  <td className="p-4 text-slate-600">{loan.maturity_date}</td>
                  <td className="p-4 text-slate-600">
                    {loan.covenant_count || "-"}
                  </td>
                  <td className="p-4">
                    <StatusBadge status={loan.status} size="sm" />
                  </td>
                  <td className="p-4">
                    {loan.is_sll && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800">
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
