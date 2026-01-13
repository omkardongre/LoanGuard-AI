"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Bell,
  Check,
  AlertTriangle,
  XCircle,
  Clock,
  Loader2,
  RefreshCw,
  Shield,
  Leaf,
  Brain,
  Filter,
} from "lucide-react";
import {
  fetchAlerts,
  acknowledgeAlert,
  type Alert,
} from "@/lib/api";

const severityConfig = {
  CRITICAL: {
    bg: "bg-red-100",
    text: "text-red-700",
    border: "border-red-500",
    icon: XCircle,
    iconColor: "text-red-500",
  },
  HIGH: {
    bg: "bg-red-100",
    text: "text-red-700",
    border: "border-red-500",
    icon: XCircle,
    iconColor: "text-red-500",
  },
  MEDIUM: {
    bg: "bg-amber-100",
    text: "text-amber-700",
    border: "border-amber-500",
    icon: AlertTriangle,
    iconColor: "text-amber-500",
  },
  LOW: {
    bg: "bg-blue-100",
    text: "text-blue-700",
    border: "border-blue-500",
    icon: Bell,
    iconColor: "text-blue-500",
  },
};

function getAlertTypeIcon(type: string) {
  if (type?.includes("covenant")) return Shield;
  if (type?.includes("esg")) return Leaf;
  if (type?.includes("prediction") || type?.includes("breach")) return Brain;
  return Bell;
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [acknowledging, setAcknowledging] = useState<string | null>(null);

  async function loadAlerts() {
    try {
      setLoading(true);
      const response = await fetchAlerts({ limit: 100 });
      setAlerts(response.alerts || []);
    } catch (err) {
      console.error("Failed to load alerts:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAlerts();
  }, []);

  async function handleAcknowledge(alertId: string) {
    setAcknowledging(alertId);
    try {
      await acknowledgeAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) =>
          a.alert_id === alertId ? { ...a, acknowledged: true, is_acknowledged: true } : a
        )
      );
    } catch (err) {
      console.error("Failed to acknowledge alert:", err);
    } finally {
      setAcknowledging(null);
    }
  }

  async function handleMarkAllRead() {
    const unreadAlerts = alerts.filter((a) => !a.acknowledged && !a.is_acknowledged);
    for (const alert of unreadAlerts) {
      await handleAcknowledge(alert.alert_id);
    }
  }

  // Filter alerts
  const filteredAlerts = alerts.filter((alert) => {
    const isAcknowledged = alert.acknowledged || alert.is_acknowledged;
    
    switch (filter) {
      case "unread":
        return !isAcknowledged;
      case "high":
        return alert.severity === "HIGH" || alert.severity === "CRITICAL";
      case "covenant":
        return alert.type?.includes("covenant") || alert.alert_type?.includes("covenant");
      case "esg":
        return alert.type?.includes("esg") || alert.alert_type?.includes("esg");
      case "prediction":
        return (
          alert.type?.includes("prediction") ||
          alert.type?.includes("breach") ||
          alert.alert_type?.includes("prediction")
        );
      default:
        return true;
    }
  });

  // Stats
  const stats = {
    total: alerts.length,
    unread: alerts.filter((a) => !a.acknowledged && !a.is_acknowledged).length,
    high: alerts.filter((a) => a.severity === "HIGH" || a.severity === "CRITICAL").length,
    covenant: alerts.filter(
      (a) => a.type?.includes("covenant") || a.alert_type?.includes("covenant")
    ).length,
    esg: alerts.filter((a) => a.type?.includes("esg") || a.alert_type?.includes("esg"))
      .length,
  };

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
            <div className="p-3 rounded-2xl bg-gradient-to-br from-red-500 to-rose-600 shadow-lg pulse-alert">
              <Bell className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">Alerts</h1>
              <p className="text-slate-500">
                {stats.unread} unacknowledged alerts
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadAlerts} className="hover:bg-blue-50 transition-colors">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button
              variant="outline"
              onClick={handleMarkAllRead}
              disabled={stats.unread === 0}
              className="hover:bg-emerald-50 transition-colors"
            >
              <Check className="h-4 w-4 mr-2" />
              Mark All Read
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <Card
            className={`cursor-pointer transition-all hover:shadow-lg hover:-translate-y-0.5 group ${
              filter === "all" ? "ring-2 ring-blue-500" : ""
            }`}
            onClick={() => setFilter("all")}
          >
            <CardContent className="pt-4 pb-4 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-slate-400 to-slate-500">
                <Bell className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="text-xs text-slate-500">All</p>
                <p className="text-xl font-bold">{stats.total}</p>
              </div>
            </CardContent>
          </Card>
          <Card
            className={`cursor-pointer transition-all hover:shadow-lg hover:-translate-y-0.5 group ${
              filter === "unread" ? "ring-2 ring-red-500" : ""
            }`}
            onClick={() => setFilter("unread")}
          >
            <CardContent className="pt-4 pb-4 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-red-500 to-rose-600">
                <AlertTriangle className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Unread</p>
                <p className="text-xl font-bold text-red-600">{stats.unread}</p>
              </div>
            </CardContent>
          </Card>
          <Card
            className={`cursor-pointer transition-all hover:shadow-lg hover:-translate-y-0.5 group ${
              filter === "high" ? "ring-2 ring-orange-500" : ""
            }`}
            onClick={() => setFilter("high")}
          >
            <CardContent className="pt-4 pb-4 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-orange-500 to-red-500">
                <XCircle className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="text-xs text-slate-500">High</p>
                <p className="text-xl font-bold text-orange-600">{stats.high}</p>
              </div>
            </CardContent>
          </Card>
          <Card
            className={`cursor-pointer transition-all hover:shadow-lg hover:-translate-y-0.5 group ${
              filter === "covenant" ? "ring-2 ring-blue-500" : ""
            }`}
            onClick={() => setFilter("covenant")}
          >
            <CardContent className="pt-4 pb-4 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600">
                <Shield className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Covenant</p>
                <p className="text-xl font-bold text-blue-600">{stats.covenant}</p>
              </div>
            </CardContent>
          </Card>
          <Card
            className={`cursor-pointer transition-all hover:shadow-lg hover:-translate-y-0.5 group ${
              filter === "esg" ? "ring-2 ring-emerald-500" : ""
            }`}
            onClick={() => setFilter("esg")}
          >
            <CardContent className="pt-4 pb-4 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600">
                <Leaf className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="text-xs text-slate-500">ESG</p>
                <p className="text-xl font-bold text-emerald-600">{stats.esg}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Alerts List */}
        <Card className="overflow-hidden">
          <CardHeader className="pb-3 bg-gradient-to-r from-slate-50 to-white border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-gradient-to-br from-slate-600 to-slate-700">
                  <Bell className="h-4 w-4 text-white" />
                </div>
                {filter === "all"
                  ? "All Alerts"
                  : filter === "unread"
                  ? "Unread Alerts"
                  : filter === "high"
                  ? "High Priority"
                  : filter === "covenant"
                  ? "Covenant Alerts"
                  : filter === "esg"
                  ? "ESG Alerts"
                  : "Alerts"}
              </CardTitle>
              <Badge variant="outline" className="text-sm">{filteredAlerts.length} alerts</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {filteredAlerts.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <Bell className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                <p>No alerts found</p>
                {filter !== "all" && (
                  <Button
                    variant="link"
                    onClick={() => setFilter("all")}
                    className="mt-2"
                  >
                    View all alerts
                  </Button>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {filteredAlerts.map((alert) => {
                  const severity = alert.severity || "MEDIUM";
                  const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.MEDIUM;
                  const Icon = config.icon;
                  const TypeIcon = getAlertTypeIcon(alert.type || alert.alert_type || "");
                  const isAcknowledged = alert.acknowledged || alert.is_acknowledged;

                  return (
                    <div
                      key={alert.alert_id}
                      className={`bg-white rounded-xl border p-4 shadow-sm transition-opacity ${
                        !isAcknowledged ? `border-l-4 ${config.border}` : "opacity-70"
                      }`}
                    >
                      <div className="flex items-start gap-4">
                        <div className={`p-2 rounded-full ${config.bg}`}>
                          <Icon className={`h-5 w-5 ${config.iconColor}`} />
                        </div>

                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <span
                              className={`text-xs font-medium px-2 py-0.5 rounded ${config.bg} ${config.text}`}
                            >
                              {severity}
                            </span>
                            <span className="text-xs text-slate-400 flex items-center gap-1">
                              <TypeIcon className="h-3 w-3" />
                              {(alert.type || alert.alert_type || "")
                                .replace(/_/g, " ")
                                .toUpperCase()}
                            </span>
                            <span className="text-xs text-slate-400">•</span>
                            <a
                              href={`/loans/${alert.loan_id}`}
                              className="text-xs text-emerald-600 hover:underline"
                            >
                              {alert.loan_id}
                            </a>
                          </div>

                          <p className="text-slate-900 font-medium">
                            {alert.title || alert.message}
                          </p>
                          {alert.title && alert.message && (
                            <p className="text-sm text-slate-600 mt-1">
                              {alert.message}
                            </p>
                          )}

                          <div className="flex items-center gap-4 mt-2">
                            <div className="flex items-center gap-1 text-xs text-slate-400">
                              <Clock className="h-3 w-3" />
                              {formatTimeAgo(alert.created_at)}
                            </div>
                            {isAcknowledged && (
                              <span className="text-xs text-emerald-600 flex items-center gap-1">
                                <Check className="h-3 w-3" />
                                Acknowledged
                              </span>
                            )}
                          </div>
                        </div>

                        {!isAcknowledged && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleAcknowledge(alert.alert_id)}
                            disabled={acknowledging === alert.alert_id}
                          >
                            {acknowledging === alert.alert_id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <>
                                <Check className="h-4 w-4 mr-1" />
                                Ack
                              </>
                            )}
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Alert Types Legend */}
        <Card className="mt-6">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-slate-500" />
                  <span className="text-sm text-slate-600">Covenant Alerts</span>
                </div>
                <div className="flex items-center gap-2">
                  <Leaf className="h-4 w-4 text-emerald-500" />
                  <span className="text-sm text-slate-600">ESG Alerts</span>
                </div>
                <div className="flex items-center gap-2">
                  <Brain className="h-4 w-4 text-purple-500" />
                  <span className="text-sm text-slate-600">ML Predictions</span>
                </div>
              </div>
              <p className="text-xs text-slate-400">
                Alerts are fetched from the API in real-time
              </p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
