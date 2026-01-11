"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  Shield,
  Leaf,
  Bell,
  MessageSquare,
  Settings,
  ShieldAlert,
  Upload,
  BarChart3,
  Wallet,
  ArrowRightLeft,
  Building2,
  Target,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/loans", label: "Loans", icon: FileText },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/covenants", label: "Covenants", icon: Shield },
  { href: "/greenwashing", label: "Greenwashing", icon: ShieldAlert },
  { href: "/esg", label: "ESG", icon: Leaf },
  { href: "/sll", label: "SLL Monitoring", icon: Target },
  { href: "/fund-finance", label: "Fund Finance", icon: Wallet },
  { href: "/transition-loans", label: "Transition", icon: ArrowRightLeft },
  { href: "/sllb", label: "SLLB & Regional", icon: Building2 },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/chat", label: "AI Chat", icon: MessageSquare },
];



export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-900 text-white min-h-screen p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Shield className="h-6 w-6 text-emerald-400" />
          LoanGuard AI
        </h1>
        <p className="text-xs text-slate-400 mt-1">Covenant & ESG Compliance</p>
      </div>

      <nav className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                isActive
                  ? "bg-emerald-600 text-white"
                  : "text-slate-300 hover:bg-slate-800"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="absolute bottom-4 left-4 right-4">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800"
        >
          <Settings className="h-4 w-4" />
          Settings
        </Link>
      </div>
    </aside>
  );
}
