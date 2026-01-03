import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: "GREEN" | "AMBER" | "RED" | string;
  size?: "sm" | "md" | "lg";
}

export function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  const colors = {
    GREEN: "bg-emerald-100 text-emerald-800 border-emerald-200",
    AMBER: "bg-amber-100 text-amber-800 border-amber-200",
    RED: "bg-red-100 text-red-800 border-red-200",
    ON_TRACK: "bg-emerald-100 text-emerald-800 border-emerald-200",
    AT_RISK: "bg-amber-100 text-amber-800 border-amber-200",
    BEHIND: "bg-red-100 text-red-800 border-red-200",
  };

  const sizes = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-sm",
    lg: "px-3 py-1.5 text-base",
  };

  const colorClass = colors[status as keyof typeof colors] || colors.AMBER;

  return (
    <span
      className={cn(
        "inline-flex items-center font-medium rounded-full border",
        colorClass,
        sizes[size]
      )}
    >
      <span
        className={cn(
          "w-2 h-2 rounded-full mr-1.5",
          status === "GREEN" || status === "ON_TRACK"
            ? "bg-emerald-500"
            : status === "AMBER" || status === "AT_RISK"
            ? "bg-amber-500"
            : "bg-red-500"
        )}
      />
      {status}
    </span>
  );
}
