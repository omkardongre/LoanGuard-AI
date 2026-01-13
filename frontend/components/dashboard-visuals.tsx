"use client";

import { cn } from "@/lib/utils";

interface CircularGaugeProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

const variantColors = {
  default: { stroke: "#64748b", bg: "#f1f5f9" },
  success: { stroke: "#10b981", bg: "#d1fae5" },
  warning: { stroke: "#f59e0b", bg: "#fef3c7" },
  danger: { stroke: "#ef4444", bg: "#fee2e2" },
  info: { stroke: "#3b82f6", bg: "#dbeafe" },
};

export function CircularGauge({
  value,
  max = 100,
  size = 140,
  strokeWidth = 12,
  label,
  sublabel,
  variant = "default",
}: CircularGaugeProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const percentage = Math.min((value / max) * 100, 100);
  const offset = circumference - (percentage / 100) * circumference;
  const colors = variantColors[variant];

  return (
    <div className="relative inline-flex flex-col items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors.bg}
          strokeWidth={strokeWidth}
          className="opacity-50"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
          style={{
            filter: `drop-shadow(0 0 6px ${colors.stroke}40)`,
          }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-slate-900">{label || value}</span>
        {sublabel && <span className="text-xs text-slate-500">{sublabel}</span>}
      </div>
    </div>
  );
}

interface AnimatedProgressBarProps {
  value: number;
  label: string;
  sublabel?: string;
  variant?: "success" | "warning" | "danger" | "info";
  showPercentage?: boolean;
}

const progressVariants = {
  success: "from-emerald-500 to-emerald-400",
  warning: "from-amber-500 to-orange-400",
  danger: "from-red-500 to-rose-400",
  info: "from-blue-500 to-indigo-400",
};

const progressBgVariants = {
  success: "bg-emerald-100",
  warning: "bg-amber-100",
  danger: "bg-red-100",
  info: "bg-blue-100",
};

const textVariants = {
  success: "text-emerald-600",
  warning: "text-amber-600",
  danger: "text-red-600",
  info: "text-blue-600",
};

export function AnimatedProgressBar({
  value,
  label,
  sublabel,
  variant = "success",
  showPercentage = true,
}: AnimatedProgressBarProps) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-700">{label}</span>
          {sublabel && (
            <span className="text-xs text-slate-400">{sublabel}</span>
          )}
        </div>
        {showPercentage && (
          <span className={cn("text-sm font-bold", textVariants[variant])}>
            {value.toFixed(0)}%
          </span>
        )}
      </div>
      <div className={cn("h-3 rounded-full overflow-hidden", progressBgVariants[variant])}>
        <div
          className={cn(
            "h-full rounded-full bg-gradient-to-r transition-all duration-1000 ease-out relative",
            progressVariants[variant]
          )}
          style={{ width: `${Math.min(value, 100)}%` }}
        >
          {/* Animated shine effect */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
          </div>
        </div>
      </div>
    </div>
  );
}

interface RiskMetricCardProps {
  value: number;
  label: string;
  variant: "critical" | "high" | "medium" | "low";
}

const riskColors = {
  critical: { bg: "bg-gradient-to-br from-red-500 to-rose-600", text: "text-white" },
  high: { bg: "bg-gradient-to-br from-orange-500 to-amber-500", text: "text-white" },
  medium: { bg: "bg-gradient-to-br from-amber-400 to-yellow-400", text: "text-amber-900" },
  low: { bg: "bg-gradient-to-br from-emerald-400 to-green-500", text: "text-white" },
};

export function RiskMetricCard({ value, label, variant }: RiskMetricCardProps) {
  const colors = riskColors[variant];
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl p-4 text-center shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl cursor-default",
        colors.bg
      )}
    >
      {/* Decorative circles */}
      <div className="absolute -top-4 -right-4 w-16 h-16 rounded-full bg-white/10" />
      <div className="absolute -bottom-2 -left-2 w-10 h-10 rounded-full bg-white/10" />
      
      <div className="relative">
        <p className={cn("text-3xl font-bold", colors.text)}>{value}</p>
        <p className={cn("text-xs font-semibold uppercase tracking-wider mt-1", colors.text, "opacity-90")}>
          {label}
        </p>
      </div>
    </div>
  );
}

interface ExposureBarProps {
  name: string;
  percentage: number;
  index: number;
}

const barColors = [
  "from-violet-500 to-purple-500",
  "from-blue-500 to-cyan-500",
  "from-emerald-500 to-teal-500",
  "from-amber-500 to-orange-500",
  "from-rose-500 to-pink-500",
];

export function ExposureBar({ name, percentage, index }: ExposureBarProps) {
  return (
    <div className="group">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900 transition-colors">
          {name}
        </span>
        <span className="text-sm font-bold text-slate-600">{percentage.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full bg-gradient-to-r transition-all duration-700 ease-out group-hover:opacity-80",
            barColors[index % barColors.length]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
