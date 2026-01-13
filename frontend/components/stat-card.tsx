import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

const variantStyles = {
  default: {
    container: "bg-white border-slate-200",
    iconBg: "bg-gradient-to-br from-slate-100 to-slate-50",
    iconColor: "text-slate-600",
    valueColor: "text-slate-900",
  },
  success: {
    container: "bg-gradient-to-br from-emerald-50 to-white border-emerald-200",
    iconBg: "bg-gradient-to-br from-emerald-500 to-emerald-600",
    iconColor: "text-white",
    valueColor: "text-emerald-700",
  },
  warning: {
    container: "bg-gradient-to-br from-amber-50 to-white border-amber-200",
    iconBg: "bg-gradient-to-br from-amber-500 to-orange-500",
    iconColor: "text-white",
    valueColor: "text-amber-700",
  },
  danger: {
    container: "bg-gradient-to-br from-red-50 to-white border-red-200",
    iconBg: "bg-gradient-to-br from-red-500 to-rose-600",
    iconColor: "text-white",
    valueColor: "text-red-700",
  },
  info: {
    container: "bg-gradient-to-br from-blue-50 to-white border-blue-200",
    iconBg: "bg-gradient-to-br from-blue-500 to-indigo-600",
    iconColor: "text-white",
    valueColor: "text-blue-700",
  },
};

export function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  className,
  variant = "default",
}: StatCardProps) {
  const styles = variantStyles[variant];

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl border p-6 shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1 cursor-default group",
        styles.container,
        className
      )}
    >
      {/* Decorative gradient orb */}
      <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-gradient-to-br from-current/5 to-transparent blur-2xl group-hover:scale-150 transition-transform duration-500" />
      
      <div className="relative flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className={cn("text-3xl font-bold tracking-tight", styles.valueColor)}>
            {value}
          </p>
          {trend && (
            <p
              className={cn(
                "text-xs font-medium flex items-center gap-1",
                trend.isPositive ? "text-emerald-600" : "text-red-600"
              )}
            >
              <span className={cn(
                "inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px]",
                trend.isPositive ? "bg-emerald-100" : "bg-red-100"
              )}>
                {trend.isPositive ? "↑" : "↓"}
              </span>
              {Math.abs(trend.value)}% from last month
            </p>
          )}
        </div>
        <div
          className={cn(
            "p-4 rounded-2xl shadow-lg transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3",
            styles.iconBg
          )}
        >
          <Icon className={cn("h-6 w-6", styles.iconColor)} />
        </div>
      </div>
    </div>
  );
}
