import { Sidebar } from "@/components/sidebar";
import { Button } from "@/components/ui/button";
import { Bell, Check, AlertTriangle, XCircle, Clock } from "lucide-react";

const alerts = [
  {
    id: "ALT-001",
    loan: "LOAN-0003",
    type: "covenant_breach",
    severity: "HIGH",
    message: "Debt/EBITDA covenant breached - actual 4.5x vs threshold 4.0x",
    created: "2025-01-03T10:30:00",
    acknowledged: false,
  },
  {
    id: "ALT-002",
    loan: "LOAN-0002",
    type: "covenant_warning",
    severity: "MEDIUM",
    message: "Interest Coverage approaching threshold - buffer only 4%",
    created: "2025-01-03T09:15:00",
    acknowledged: false,
  },
  {
    id: "ALT-003",
    loan: "LOAN-0005",
    type: "esg_warning",
    severity: "MEDIUM",
    message: "ESG KPI behind target - Board Diversity at 33% vs 40% target",
    created: "2025-01-02T16:45:00",
    acknowledged: false,
  },
  {
    id: "ALT-004",
    loan: "LOAN-0003",
    type: "breach_prediction",
    severity: "HIGH",
    message: "ML model predicts 72% breach probability in next 90 days",
    created: "2025-01-02T14:20:00",
    acknowledged: true,
  },
  {
    id: "ALT-005",
    loan: "LOAN-0001",
    type: "document_processed",
    severity: "LOW",
    message: "Loan agreement processed - 5 covenants extracted",
    created: "2025-01-02T11:00:00",
    acknowledged: true,
  },
  {
    id: "ALT-006",
    loan: "LOAN-0007",
    type: "covenant_warning",
    severity: "MEDIUM",
    message: "Current Ratio declining trend detected over 3 quarters",
    created: "2025-01-01T15:30:00",
    acknowledged: true,
  },
];

const severityConfig = {
  HIGH: {
    bg: "bg-red-100",
    text: "text-red-700",
    icon: XCircle,
    iconColor: "text-red-500",
  },
  MEDIUM: {
    bg: "bg-amber-100",
    text: "text-amber-700",
    icon: AlertTriangle,
    iconColor: "text-amber-500",
  },
  LOW: {
    bg: "bg-blue-100",
    text: "text-blue-700",
    icon: Bell,
    iconColor: "text-blue-500",
  },
};

export default function AlertsPage() {
  const unacknowledged = alerts.filter((a) => !a.acknowledged).length;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Alerts</h1>
            <p className="text-slate-500">
              {unacknowledged} unacknowledged alerts
            </p>
          </div>
          <Button variant="outline">
            <Check className="h-4 w-4 mr-2" />
            Mark All Read
          </Button>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          <Button variant="default" size="sm" className="bg-slate-900">
            All ({alerts.length})
          </Button>
          <Button variant="outline" size="sm">
            Unread ({unacknowledged})
          </Button>
          <Button variant="outline" size="sm">
            High Priority ({alerts.filter((a) => a.severity === "HIGH").length})
          </Button>
          <Button variant="outline" size="sm">
            Covenant ({alerts.filter((a) => a.type.includes("covenant")).length}
            )
          </Button>
          <Button variant="outline" size="sm">
            ESG ({alerts.filter((a) => a.type.includes("esg")).length})
          </Button>
        </div>

        {/* Alerts List */}
        <div className="space-y-3">
          {alerts.map((alert) => {
            const config =
              severityConfig[alert.severity as keyof typeof severityConfig];
            const Icon = config.icon;

            return (
              <div
                key={alert.id}
                className={`bg-white rounded-xl border p-4 shadow-sm ${
                  !alert.acknowledged ? "border-l-4 border-l-emerald-500" : ""
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`p-2 rounded-full ${config.bg}`}>
                    <Icon className={`h-5 w-5 ${config.iconColor}`} />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded ${config.bg} ${config.text}`}
                      >
                        {alert.severity}
                      </span>
                      <span className="text-xs text-slate-400">
                        {alert.type.replace(/_/g, " ").toUpperCase()}
                      </span>
                      <span className="text-xs text-slate-400">•</span>
                      <a
                        href={`/loans/${alert.loan}`}
                        className="text-xs text-emerald-600 hover:underline"
                      >
                        {alert.loan}
                      </a>
                    </div>

                    <p className="text-slate-900 font-medium">
                      {alert.message}
                    </p>

                    <div className="flex items-center gap-4 mt-2">
                      <div className="flex items-center gap-1 text-xs text-slate-400">
                        <Clock className="h-3 w-3" />
                        {new Date(alert.created).toLocaleString()}
                      </div>
                      {alert.acknowledged && (
                        <span className="text-xs text-emerald-600 flex items-center gap-1">
                          <Check className="h-3 w-3" />
                          Acknowledged
                        </span>
                      )}
                    </div>
                  </div>

                  {!alert.acknowledged && (
                    <Button variant="outline" size="sm">
                      Acknowledge
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
