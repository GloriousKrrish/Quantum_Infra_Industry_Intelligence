import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "../../lib/utils";
import {
  Boxes,
  Atom,
  Building2,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Zap,
} from "lucide-react";

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Geospatial Digital Twin", path: "/", icon: Boxes, badge: "3D GIS" },
  { label: "3D Quantum Lab", path: "/quantum", icon: Atom, badge: "Qiskit Aer" },
  { label: "Land Intelligence Studio", path: "/land", icon: Building2, badge: "IS 1172" },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-slate-200 bg-white transition-all duration-300",
        collapsed ? "w-18" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-5">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white shadow-xs">
          <Zap className="h-5 w-5" />
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <span className="font-display text-sm font-bold tracking-tight text-slate-900">
              QUANTUM ESTATE X
            </span>
            <span className="font-mono text-[10px] text-slate-500 uppercase tracking-wider">
              Pune PMRDA 3D Platform
            </span>
          </div>
        )}
      </div>

      {/* Primary Navigation Links */}
      <div className="flex-1 px-3 py-6 space-y-1.5">
        <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          {!collapsed ? "Core Modules" : "•"}
        </div>

        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "group flex items-center justify-between rounded-xl px-3 py-2.5 text-xs font-semibold transition-all",
                isActive
                  ? "bg-blue-50 text-blue-700 shadow-xs border border-blue-200/60"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0 transition-colors",
                    isActive ? "text-blue-600" : "text-slate-400 group-hover:text-slate-600"
                  )}
                />
                {!collapsed && <span>{item.label}</span>}
              </div>

              {!collapsed && item.badge && (
                <span
                  className={cn(
                    "font-mono text-[9px] px-1.5 py-0.5 rounded-md",
                    isActive
                      ? "bg-blue-600 text-white font-bold"
                      : "bg-slate-100 text-slate-500"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Dual Quantum-Classical Verified Badge */}
      {!collapsed && (
        <div className="mx-3 mb-4 rounded-2xl border border-slate-200 bg-slate-50/70 p-3.5 text-xs">
          <div className="flex items-center gap-2 font-semibold text-slate-800 mb-1">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <span>Anti-Quantum Washing</span>
          </div>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            Strict classical validation: Qiskit QAOA verified against exact MILP (0.999&nbsp;$\alpha$).
          </p>
        </div>
      )}

      {/* Footer Collapse Button */}
      <div className="border-t border-slate-200 p-3">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex w-full items-center justify-center rounded-xl p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
    </aside>
  );
}
