import { useLocation } from "react-router-dom";
import { Bell, Search, User } from "lucide-react";

// ─── Route-to-Title Mapping ───────────────────────────────────────────────────

const PAGE_TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/land": "Land Studio",
  "/builder": "Builder Workspace",
  "/analytics": "Market Analytics",
  "/finance": "Finance Engine",
  "/quantum": "Quantum Lab",
  "/qaoa": "QAOA Optimizer",
  "/benchmarks": "Benchmarks",
  "/settings": "Settings",
};

// ─── Header Component ────────────────────────────────────────────────────────

export default function Header() {
  const location = useLocation();
  const title = PAGE_TITLES[location.pathname] || "QUANTUM ESTATE X";

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-700/50 bg-slate-950/80 px-6 backdrop-blur-xl">
      {/* ── Page Title ─────────────────────────────────────────── */}
      <div>
        <h1 className="text-lg font-semibold text-slate-100">{title}</h1>
        <p className="text-xs text-slate-500">Pune Metropolitan Region • ₹15 Cr Budget</p>
      </div>

      {/* ── Right Actions ──────────────────────────────────────── */}
      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search parcels, models..."
            className="h-9 w-64 rounded-lg border border-slate-700/50 bg-slate-900/80 pl-9 pr-4 text-sm text-slate-300 placeholder-slate-500 outline-none transition-colors focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20"
          />
        </div>

        {/* Notification Bell */}
        <button className="relative rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-800/50 hover:text-slate-200">
          <Bell className="h-5 w-5" />
          {/* Active notification dot */}
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(6,182,212,0.6)]" />
        </button>

        {/* User Avatar */}
        <button className="flex items-center gap-2 rounded-lg p-1.5 transition-colors hover:bg-slate-800/50">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-violet-500">
            <User className="h-4 w-4 text-white" />
          </div>
          <span className="hidden text-sm font-medium text-slate-300 lg:block">Researcher</span>
        </button>
      </div>
    </header>
  );
}
