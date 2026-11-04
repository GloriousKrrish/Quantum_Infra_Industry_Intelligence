import { useLocation } from "react-router-dom";
import { Bell, Search, User } from "lucide-react";

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/": {
    title: "Project Overview",
    subtitle: "PMRDA Pune Region · 3D Digital Twin & Quantum Optimization",
  },
  "/land": {
    title: "Land & Infrastructure",
    subtitle: "Cadastral Parcels · Feasibility & Deterministic IS 1172 Utility Calculator",
  },
  "/quantum": {
    title: "Quantum Intelligence",
    subtitle: "QAOA Multi-Parcel Optimizer, Qiskit Aer Circuit & 3D Bloch Sphere",
  },
  "/qaoa": {
    title: "QAOA Optimizer",
    subtitle: "Quadratic Unconstrained Binary Optimization on Ising Hamiltonians",
  },
  "/benchmarks": {
    title: "Verification Benchmarks",
    subtitle: "Side-by-side verification: Exact MILP vs Simulated Annealing vs QAOA",
  },
};

export default function Header() {
  const location = useLocation();
  const meta = PAGE_TITLES[location.pathname] || {
    title: "QUANTUM ESTATE X",
    subtitle: "Real Estate & Infrastructure Intelligence Ecosystem",
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-8 backdrop-blur-md">
      {/* Page Title */}
      <div>
        <h1 className="font-display text-lg font-bold text-slate-900 tracking-tight">
          {meta.title}
        </h1>
        <p className="text-xs text-slate-500">{meta.subtitle}</p>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-4">
        {/* Simple Search */}
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search parcels..."
            className="h-9 w-60 rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-xs text-slate-800 placeholder-slate-400 outline-none transition-all focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-100"
          />
        </div>

        {/* Notifications */}
        <button
          className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 transition-colors"
          title="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-blue-600" />
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-600 border border-slate-200">
            <User className="h-4 w-4" />
          </div>
          <span className="text-xs font-semibold text-slate-700 hidden sm:block">
            Lead Developer
          </span>
        </div>
      </div>
    </header>
  );
}
