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
  FileCheck2,
} from "lucide-react";

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
  badge?: string;
}

interface NavSection {
  title: string;
  code: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: "OPERATIONAL DOMAINS",
    code: "01",
    items: [
      { label: "Executive Cockpit", path: "/", icon: LayoutDashboard },
      { label: "Pune Land Studio", path: "/land", icon: Map, badge: "GIS" },
      { label: "Builder & ERP", path: "/builder", icon: Building2 },
    ],
  },
  {
    title: "INTELLIGENCE ENGINES",
    code: "02",
    items: [
      { label: "Market Analytics", path: "/analytics", icon: TrendingUp },
      { label: "Financial Engine", path: "/finance", icon: DollarSign },
      { label: "RERA & Clearances", path: "/rera", icon: FileCheck2 },
    ],
  },
  {
    title: "QUANTUM SUITE",
    code: "03",
    items: [
      { label: "Quantum Lab (3D)", path: "/quantum", icon: Atom, badge: "Qiskit" },
      { label: "QAOA Optimizer", path: "/qaoa", icon: Cpu },
      { label: "Verification Bench", path: "/benchmarks", icon: BarChart3 },
    ],
  },
  {
    title: "SYSTEM",
    code: "04",
    items: [{ label: "Settings & Nodes", path: "/settings", icon: Settings }],
  },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-slate-800 bg-[#020617] transition-all duration-300",
        collapsed ? "w-[72px]" : "w-64"
      )}
    >
      {/* ── Brand Header ───────────────────────────────────────────── */}
      <div className="flex h-16 items-center gap-3 border-b border-slate-800 px-4">
        <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 border border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.2)]">
          <Zap className="h-4 w-4 text-cyan-400" />
          <span className="absolute -top-1 -right-1 flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
          </span>
        </div>
        {!collapsed && (
          <div className="flex flex-col overflow-hidden">
            <span className="font-display text-sm font-bold tracking-wider text-white">
              QUANTUM ESTATE
            </span>
            <div className="flex items-center gap-1.5 font-mono text-[9px] text-cyan-400 tracking-widest uppercase">
              <span>X-PLATFORM</span>
              <span className="text-slate-600">/</span>
              <span className="text-slate-400">PMRDA</span>
            </div>
          </div>
        )}
      </div>

      {/* ── Navigation Links ───────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title}>
            {!collapsed && (
              <div className="mb-2 flex items-center justify-between px-3">
                <span className="font-mono text-[9px] font-bold tracking-[0.2em] text-slate-500 uppercase">
                  {section.title}
                </span>
                <span className="font-mono text-[9px] text-slate-600">
                  [{section.code}]
                </span>
              </div>
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
                        "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-all duration-150",
                        isActive
                          ? "bg-cyan-500/10 text-cyan-300 font-semibold border border-cyan-500/20"
                          : "text-slate-400 hover:bg-slate-900/60 hover:text-slate-200"
                      )}
                    >
                      {/* Left glowing edge bar */}
                      {isActive && (
                        <div className="absolute -left-3 top-1.5 bottom-1.5 w-[3px] rounded-r bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)]" />
                      )}

                      <Icon
                        className={cn(
                          "h-4 w-4 shrink-0 transition-colors",
                          isActive
                            ? "text-cyan-400"
                            : "text-slate-500 group-hover:text-slate-300"
                        )}
                      />

                      {!collapsed && (
                        <div className="flex flex-1 items-center justify-between">
                          <span>{item.label}</span>
                          {item.badge && (
                            <span className="rounded bg-slate-900 px-1.5 py-0.5 font-mono text-[9px] text-slate-400 border border-slate-800">
                              {item.badge}
                            </span>
                          )}
                        </div>
                      )}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* ── Footer Telemetry & Collapse Toggle ──────────────────────── */}
      <div className="border-t border-slate-800 p-3">
        {!collapsed && (
          <div className="mb-2 rounded-lg bg-slate-950 p-2.5 border border-slate-800/80 font-mono text-[10px] space-y-1">
            <div className="flex justify-between text-slate-400">
              <span>Kernel:</span>
              <span className="text-emerald-400">SciPy COBYLA</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Backend:</span>
              <span className="text-cyan-400">AerSimulator</span>
            </div>
          </div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex w-full items-center justify-center rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-900 hover:text-slate-300"
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
