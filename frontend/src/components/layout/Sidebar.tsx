import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "../../lib/utils";
import {
  LayoutDashboard,
  Map,
  Building2,
  TrendingUp,
  DollarSign,
  Atom,
  Cpu,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";

// ─── Navigation Configuration ─────────────────────────────────────────────────

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: "ECOSYSTEM",
    items: [
      { label: "Dashboard", path: "/", icon: LayoutDashboard },
      { label: "Land Studio", path: "/land", icon: Map },
      { label: "Builder Workspace", path: "/builder", icon: Building2 },
    ],
  },
  {
    title: "INTELLIGENCE",
    items: [
      { label: "Market Analytics", path: "/analytics", icon: TrendingUp },
      { label: "Finance Engine", path: "/finance", icon: DollarSign },
    ],
  },
  {
    title: "QUANTUM",
    items: [
      { label: "Quantum Lab", path: "/quantum", icon: Atom },
      { label: "QAOA Optimizer", path: "/qaoa", icon: Cpu },
      { label: "Benchmarks", path: "/benchmarks", icon: BarChart3 },
    ],
  },
  {
    title: "SYSTEM",
    items: [
      { label: "Settings", path: "/settings", icon: Settings },
    ],
  },
];

// ─── Sidebar Component ───────────────────────────────────────────────────────

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-slate-700/50 bg-slate-950 transition-all duration-300",
        collapsed ? "w-[72px]" : "w-64"
      )}
    >
      {/* ── Logo ──────────────────────────────────────────────────── */}
      <div className="flex h-16 items-center gap-3 border-b border-slate-700/50 px-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 shadow-[0_0_15px_rgba(6,182,212,0.15)]">
          <Zap className="h-5 w-5 text-cyan-400" />
        </div>
        {!collapsed && (
          <div className="flex flex-col overflow-hidden">
            <span className="text-sm font-bold tracking-wider text-cyan-400 drop-shadow-[0_0_8px_rgba(6,182,212,0.4)]">
              QUANTUM ESTATE
            </span>
            <span className="text-[10px] font-medium tracking-[0.3em] text-slate-500">
              X-PLATFORM
            </span>
          </div>
        )}
      </div>

      {/* ── Navigation ────────────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="mb-6">
            {!collapsed && (
              <p className="mb-2 px-3 text-[10px] font-semibold tracking-[0.2em] text-slate-500">
                {section.title}
              </p>
            )}
            <ul className="space-y-1">
              {section.items.map((item) => {
                const isActive = location.pathname === item.path;
                const Icon = item.icon;

                return (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      className={cn(
                        "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                        isActive
                          ? "bg-cyan-500/10 text-cyan-400"
                          : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                      )}
                    >
                      {/* Active indicator bar */}
                      {isActive && (
                        <div className="absolute -left-3 top-1/2 h-6 w-[3px] -translate-y-1/2 rounded-r-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.6)]" />
                      )}

                      <Icon
                        className={cn(
                          "h-[18px] w-[18px] shrink-0 transition-colors",
                          isActive ? "text-cyan-400" : "text-slate-500 group-hover:text-slate-300"
                        )}
                      />

                      {!collapsed && <span>{item.label}</span>}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* ── Collapse Toggle ───────────────────────────────────────── */}
      <div className="border-t border-slate-700/50 p-3">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex w-full items-center justify-center rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-800/50 hover:text-slate-300"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
