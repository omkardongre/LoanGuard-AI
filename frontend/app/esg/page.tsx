import { Sidebar } from "@/components/sidebar";
import { StatusBadge } from "@/components/status-badge";
import { Leaf, TrendingUp, AlertTriangle, CheckCircle } from "lucide-react";

const esgLoans = [
  {
    loan_id: "LOAN-0001",
    borrower: "Acme Corporation",
    kpis: [
      {
        name: "Carbon Emissions",
        baseline: 100000,
        target: 70000,
        current: 82000,
        progress: 60,
        status: "ON_TRACK",
      },
      {
        name: "Renewable Energy %",
        baseline: 20,
        target: 50,
        current: 38,
        progress: 60,
        status: "ON_TRACK",
      },
    ],
    greenwashing_risk: "LOW",
    spt_achieved: true,
    margin_adjustment: "-5 bps",
  },
  {
    loan_id: "LOAN-0003",
    borrower: "TechStart Inc",
    kpis: [
      {
        name: "Board Diversity %",
        baseline: 25,
        target: 40,
        current: 33,
        progress: 53,
        status: "AT_RISK",
      },
      {
        name: "Water Usage",
        baseline: 500000,
        target: 350000,
        current: 420000,
        progress: 53,
        status: "AT_RISK",
      },
    ],
    greenwashing_risk: "MEDIUM",
    spt_achieved: false,
    margin_adjustment: "+2.5 bps",
  },
  {
    loan_id: "LOAN-0004",
    borrower: "Energy Solutions Ltd",
    kpis: [
      {
        name: "Carbon Emissions",
        baseline: 200000,
        target: 120000,
        current: 135000,
        progress: 81,
        status: "ON_TRACK",
      },
      {
        name: "Safety Incidents",
        baseline: 10,
        target: 3,
        current: 4,
        progress: 86,
        status: "ON_TRACK",
      },
    ],
    greenwashing_risk: "LOW",
    spt_achieved: true,
    margin_adjustment: "-7.5 bps",
  },
];

export default function ESGPage() {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900">ESG Compliance</h1>
          <p className="text-slate-500">
            Sustainability-linked loan monitoring
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl border p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <Leaf className="h-5 w-5 text-emerald-500" />
              <p className="text-sm text-slate-500">SLL Loans</p>
            </div>
            <p className="text-2xl font-bold text-slate-900">18</p>
          </div>
          <div className="bg-white rounded-xl border p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="h-5 w-5 text-emerald-500" />
              <p className="text-sm text-slate-500">SPT Achieved</p>
            </div>
            <p className="text-2xl font-bold text-emerald-600">14</p>
          </div>
          <div className="bg-white rounded-xl border p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-5 w-5 text-blue-500" />
              <p className="text-sm text-slate-500">Avg ESG Score</p>
            </div>
            <p className="text-2xl font-bold text-slate-900">72.5</p>
          </div>
          <div className="bg-white rounded-xl border p-4 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              <p className="text-sm text-slate-500">Greenwashing Risk</p>
            </div>
            <p className="text-2xl font-bold text-amber-600">3</p>
          </div>
        </div>

        {/* ESG Loan Cards */}
        <div className="space-y-6">
          {esgLoans.map((loan) => (
            <div
              key={loan.loan_id}
              className="bg-white rounded-xl border shadow-sm overflow-hidden"
            >
              <div className="p-4 border-b flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">
                    {loan.borrower}
                  </h3>
                  <p className="text-sm text-slate-500">{loan.loan_id}</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Margin Adjustment</p>
                    <p
                      className={`font-semibold ${
                        loan.margin_adjustment.startsWith("-")
                          ? "text-emerald-600"
                          : "text-red-600"
                      }`}
                    >
                      {loan.margin_adjustment}
                    </p>
                  </div>
                  <StatusBadge
                    status={
                      loan.greenwashing_risk === "LOW"
                        ? "GREEN"
                        : loan.greenwashing_risk === "MEDIUM"
                        ? "AMBER"
                        : "RED"
                    }
                  />
                </div>
              </div>

              <div className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {loan.kpis.map((kpi, idx) => (
                    <div key={idx} className="p-4 bg-slate-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-medium text-slate-900">{kpi.name}</p>
                        <StatusBadge status={kpi.status} size="sm" />
                      </div>
                      <div className="mb-2">
                        <div className="flex justify-between text-xs text-slate-500 mb-1">
                          <span>Progress: {kpi.progress}%</span>
                          <span>Target: {kpi.target.toLocaleString()}</span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              kpi.status === "ON_TRACK"
                                ? "bg-emerald-500"
                                : "bg-amber-500"
                            }`}
                            style={{ width: `${Math.min(kpi.progress, 100)}%` }}
                          />
                        </div>
                      </div>
                      <div className="flex justify-between text-xs text-slate-500">
                        <span>Baseline: {kpi.baseline.toLocaleString()}</span>
                        <span>Current: {kpi.current.toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
