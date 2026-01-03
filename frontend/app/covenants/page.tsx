import { Sidebar } from "@/components/sidebar";
import { StatusBadge } from "@/components/status-badge";
import { Shield, TrendingDown, TrendingUp, AlertTriangle } from "lucide-react";

const covenants = [
  {
    id: "COV-001",
    loan: "LOAN-0001",
    name: "Debt/EBITDA",
    threshold: "≤ 4.0x",
    actual: "3.8x",
    buffer: 5.0,
    status: "GREEN" as const,
    trend: "stable",
  },
  {
    id: "COV-002",
    loan: "LOAN-0001",
    name: "Interest Coverage",
    threshold: "≥ 2.5x",
    actual: "2.6x",
    buffer: 4.0,
    status: "AMBER" as const,
    trend: "down",
  },
  {
    id: "COV-003",
    loan: "LOAN-0002",
    name: "Current Ratio",
    threshold: "≥ 1.2x",
    actual: "1.35x",
    buffer: 12.5,
    status: "GREEN" as const,
    trend: "up",
  },
  {
    id: "COV-004",
    loan: "LOAN-0002",
    name: "Net Worth",
    threshold: "≥ $50M",
    actual: "$52M",
    buffer: 4.0,
    status: "AMBER" as const,
    trend: "stable",
  },
  {
    id: "COV-005",
    loan: "LOAN-0003",
    name: "Debt/EBITDA",
    threshold: "≤ 4.0x",
    actual: "4.5x",
    buffer: -12.5,
    status: "RED" as const,
    trend: "down",
  },
  {
    id: "COV-006",
    loan: "LOAN-0003",
    name: "CapEx Limit",
    threshold: "≤ $25M",
    actual: "$22M",
    buffer: 12.0,
    status: "GREEN" as const,
    trend: "stable",
  },
  {
    id: "COV-007",
    loan: "LOAN-0004",
    name: "Interest Coverage",
    threshold: "≥ 3.0x",
    actual: "4.2x",
    buffer: 40.0,
    status: "GREEN" as const,
    trend: "up",
  },
  {
    id: "COV-008",
    loan: "LOAN-0005",
    name: "Fixed Charge Coverage",
    threshold: "≥ 1.1x",
    actual: "1.15x",
    buffer: 4.5,
    status: "AMBER" as const,
    trend: "down",
  },
];

export default function CovenantsPage() {
  const statusCounts = {
    GREEN: covenants.filter((c) => c.status === "GREEN").length,
    AMBER: covenants.filter((c) => c.status === "AMBER").length,
    RED: covenants.filter((c) => c.status === "RED").length,
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900">
            Covenant Monitoring
          </h1>
          <p className="text-slate-500">
            Track covenant compliance across portfolio
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl border p-4 shadow-sm">
            <p className="text-sm text-slate-500">Total Covenants</p>
            <p className="text-2xl font-bold text-slate-900">
              {covenants.length}
            </p>
          </div>
          <div className="bg-white rounded-xl border p-4 shadow-sm border-l-4 border-l-emerald-500">
            <p className="text-sm text-slate-500">Compliant</p>
            <p className="text-2xl font-bold text-emerald-600">
              {statusCounts.GREEN}
            </p>
          </div>
          <div className="bg-white rounded-xl border p-4 shadow-sm border-l-4 border-l-amber-500">
            <p className="text-sm text-slate-500">Warning</p>
            <p className="text-2xl font-bold text-amber-600">
              {statusCounts.AMBER}
            </p>
          </div>
          <div className="bg-white rounded-xl border p-4 shadow-sm border-l-4 border-l-red-500">
            <p className="text-sm text-slate-500">Breach</p>
            <p className="text-2xl font-bold text-red-600">
              {statusCounts.RED}
            </p>
          </div>
        </div>

        {/* Covenants Table */}
        <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold text-slate-900">
              All Covenants
            </h2>
          </div>
          <table className="w-full">
            <thead className="bg-slate-50 border-b">
              <tr>
                <th className="text-left p-4 font-medium text-slate-600">
                  Covenant
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Loan
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Threshold
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Actual
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Buffer
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Trend
                </th>
                <th className="text-left p-4 font-medium text-slate-600">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {covenants.map((cov) => (
                <tr key={cov.id} className="border-b hover:bg-slate-50">
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-slate-400" />
                      <span className="font-medium text-slate-900">
                        {cov.name}
                      </span>
                    </div>
                  </td>
                  <td className="p-4">
                    <a
                      href={`/loans/${cov.loan}`}
                      className="text-emerald-600 hover:underline"
                    >
                      {cov.loan}
                    </a>
                  </td>
                  <td className="p-4 text-slate-600">{cov.threshold}</td>
                  <td className="p-4 font-medium text-slate-900">
                    {cov.actual}
                  </td>
                  <td className="p-4">
                    <span
                      className={`font-medium ${
                        cov.buffer < 0
                          ? "text-red-600"
                          : cov.buffer < 10
                          ? "text-amber-600"
                          : "text-emerald-600"
                      }`}
                    >
                      {cov.buffer > 0 ? "+" : ""}
                      {cov.buffer}%
                    </span>
                  </td>
                  <td className="p-4">
                    {cov.trend === "up" && (
                      <TrendingUp className="h-4 w-4 text-emerald-500" />
                    )}
                    {cov.trend === "down" && (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                    {cov.trend === "stable" && (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="p-4">
                    <StatusBadge status={cov.status} size="sm" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Breach Prediction */}
        <div className="mt-8 bg-white rounded-xl border p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            <h2 className="text-lg font-semibold text-slate-900">
              ML Breach Predictions
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <p className="text-sm text-red-600 font-medium">LOAN-0003</p>
              <p className="text-2xl font-bold text-red-700">72%</p>
              <p className="text-xs text-red-600">
                Breach probability (90 days)
              </p>
            </div>
            <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
              <p className="text-sm text-amber-600 font-medium">LOAN-0002</p>
              <p className="text-2xl font-bold text-amber-700">35%</p>
              <p className="text-xs text-amber-600">
                Breach probability (90 days)
              </p>
            </div>
            <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
              <p className="text-sm text-amber-600 font-medium">LOAN-0005</p>
              <p className="text-2xl font-bold text-amber-700">28%</p>
              <p className="text-xs text-amber-600">
                Breach probability (90 days)
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
