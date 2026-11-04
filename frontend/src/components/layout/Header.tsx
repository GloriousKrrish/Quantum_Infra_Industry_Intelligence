import { useState } from "react";
import { useLocation } from "react-router-dom";
import { Bell, Search, User, Terminal, Globe } from "lucide-react";

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/": {
    title: "Executive Command Center",
    subtitle: "PMRDA Pune Region · Hybrid Quantum-Classical Decision Dashboard",
  },
  "/land": {
    title: "Land & Geospatial Studio",
    subtitle: "Cadastral Parcels · Multi-Criteria Infrastructure Readiness Scoring",
  },
  "/builder": {
    title: "Builder & Development Workspace",
    subtitle: "Project Feasibility · Critical Path Construction Job-Shop (JSSP)",
  },
  "/analytics": {
    title: "Market Intelligence & Forecasting",
    subtitle: "XGBoost Regression · Micro-Market Appreciation & Rental Yields",
  },
  "/finance": {
    title: "Financial Engineering & Risk",
    subtitle: "Capital Allocation · Value-at-Risk & Monte Carlo Cash Flow",
  },
  "/quantum": {
    title: "Quantum Intelligence Laboratory",
    subtitle: "Qiskit Aer Simulator · QAOA, VQE, 3D Bloch Sphere & Benchmarks",
  },
  "/qaoa": {
    title: "QAOA Multi-Parcel Optimizer",
    subtitle: "Quadratic Unconstrained Binary Optimization on Ising Hamiltonians",
  },
  "/benchmarks": {
    title: "Algorithmic Verification Benchmarks",
    subtitle: "Approximation Ratio (α) · Classical MILP vs Simulated Annealing vs QAOA",
  },
  "/settings": {
    title: "System & Simulation Config",
    subtitle: "Qiskit Backend Setup · API Gateways & Tenant Permissions",
  },
};

export default function Header() {
  const location = useLocation();
  const pageMeta = PAGE_TITLES[location.pathname] || {
    title: "QUANTUM ESTATE X",
    subtitle: "Real Estate & Infrastructure Ecosystem",
  };

  const [role, setRole] = useState<string>("Lead Researcher");

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-800 bg-slate-950/90 px-6 backdrop-blur-xl">
      {/* ── Left: Page Title & Geographic Context ──────────────── */}
      <div className="flex flex-col">
        <div className="flex items-center gap-2">
          <h1 className="font-display text-base font-bold text-white tracking-wide">
            {pageMeta.title}
          </h1>
          <span className="hidden sm:inline-flex items-center gap-1 rounded bg-cyan-500/10 px-2 py-0.5 font-mono text-[10px] text-cyan-400 border border-cyan-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
            LIVE SIMULATION
          </span>
        </div>
        <p className="font-mono text-[11px] text-slate-400">{pageMeta.subtitle}</p>
      </div>

      {/* ── Center: Telemetry Badges ───────────────────────────── */}
      <div className="hidden xl:flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-1 font-mono text-[11px] text-slate-300">
          <Globe className="h-3.5 w-3.5 text-emerald-400" />
          <span>PMRDA (18.52° N, 73.85° E)</span>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-1 font-mono text-[11px] text-slate-300">
          <Terminal className="h-3.5 w-3.5 text-cyan-400" />
          <span>Qiskit Aer (p=2, 8-qubit)</span>
        </div>
      </div>

      {/* ── Right: Search, Notifications & Role ────────────────── */}
      <div className="flex items-center gap-3">
        {/* Search Input */}
        <div className="relative hidden md:block">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search parcels, Hamiltonians..."
            className="h-8 w-56 rounded-lg border border-slate-800 bg-slate-900/90 pl-8 pr-3 font-mono text-xs text-slate-200 placeholder-slate-500 outline-none transition-colors focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20"
          />
        </div>

        {/* Notification Bell */}
        <button
          className="relative rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-900 hover:text-slate-200"
          title="System Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
        </button>

        {/* Role Switcher */}
        <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/80 px-2.5 py-1">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-tr from-cyan-600 to-indigo-600">
            <User className="h-3.5 w-3.5 text-white" />
          </div>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="bg-transparent font-mono text-xs text-slate-200 outline-none cursor-pointer"
          >
            <option value="Lead Researcher" className="bg-slate-950 text-slate-200">
              Researcher
            </option>
            <option value="Builder / Developer" className="bg-slate-950 text-slate-200">
              Builder / Dev
            </option>
            <option value="Financial Underwriter" className="bg-slate-950 text-slate-200">
              Finance Underwriter
            </option>
            <option value="RERA Auditor" className="bg-slate-950 text-slate-200">
              RERA Auditor
            </option>
          </select>
        </div>
      </div>
    </header>
  );
}
