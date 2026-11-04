import { useState, useMemo } from "react";
import {
  MapPin,
  Droplets,
  Zap,
  PipetteIcon,
  Route,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { cn } from "../lib/utils";
import { MOCK_PARCELS } from "../lib/mockData";
import type { Parcel } from "../lib/api";

// ─── Infrastructure Score Bar ─────────────────────────────────────────────────

function InfraBar({ label, value, icon: Icon, color }: {
  label: string;
  value: number;
  icon: React.ElementType;
  color: string;
}) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <Icon className={cn("h-3.5 w-3.5 shrink-0", color)} />
      <span className="w-14 text-[11px] text-slate-500">{label}</span>
      <div className="flex-1">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
          <div
            className={cn("h-full rounded-full transition-all duration-500", color.replace("text-", "bg-"))}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      <span className="w-8 text-right font-mono text-[11px] text-slate-400">{pct}</span>
    </div>
  );
}

// ─── Parcel Card ──────────────────────────────────────────────────────────────

function ParcelCard({
  parcel,
  isSelected,
  onSelect,
}: {
  parcel: Parcel;
  isSelected: boolean;
  onSelect: (p: Parcel) => void;
}) {
  const statusColors: Record<string, string> = {
    Available: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    "Under Review": "bg-amber-500/10 text-amber-400 border-amber-500/20",
    Shortlisted: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  };

  return (
    <div
      onClick={() => onSelect(parcel)}
      className={cn(
        "group cursor-pointer rounded-xl border bg-slate-900/80 p-4 transition-all duration-300 hover:shadow-lg",
        isSelected
          ? "border-cyan-500/40 shadow-[0_0_20px_rgba(6,182,212,0.1)]"
          : "border-slate-700/50 hover:border-slate-600/50"
      )}
    >
      {/* Header */}
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 group-hover:text-cyan-400 transition-colors">
            {parcel.name}
          </h3>
          <p className="flex items-center gap-1 text-[11px] text-slate-500">
            <MapPin className="h-3 w-3" />
            {parcel.location}
          </p>
        </div>
        <span
          className={cn(
            "inline-flex rounded-full border px-2 py-0.5 text-[10px] font-medium",
            statusColors[parcel.status]
          )}
        >
          {parcel.status}
        </span>
      </div>

      {/* Key metrics */}
      <div className="mb-3 grid grid-cols-3 gap-2 rounded-lg bg-slate-800/50 p-2.5">
        <div>
          <p className="text-[10px] text-slate-500">Area</p>
          <p className="font-mono text-xs font-semibold text-slate-200">{parcel.area_acres} ac</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-500">Price</p>
          <p className="font-mono text-xs font-semibold text-slate-200">₹{parcel.price_cr} Cr</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-500">Return</p>
          <p className={cn("font-mono text-xs font-semibold", parcel.return_pct >= 17 ? "text-emerald-400" : "text-slate-300")}>
            {parcel.return_pct}%
          </p>
        </div>
      </div>

      {/* Infrastructure scores */}
      <div className="space-y-1.5">
        <InfraBar label="Water" value={parcel.infra_scores.water} icon={Droplets} color="text-blue-400" />
        <InfraBar label="Power" value={parcel.infra_scores.power} icon={Zap} color="text-amber-400" />
        <InfraBar label="Sewage" value={parcel.infra_scores.sewage} icon={PipetteIcon} color="text-violet-400" />
        <InfraBar label="Road" value={parcel.infra_scores.road} icon={Route} color="text-emerald-400" />
      </div>

      {/* Utility score badge + action */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Utility</span>
          <span
            className={cn(
              "rounded-md px-2 py-0.5 font-mono text-xs font-bold",
              parcel.utility_score >= 0.85
                ? "bg-emerald-500/10 text-emerald-400"
                : parcel.utility_score >= 0.70
                  ? "bg-amber-500/10 text-amber-400"
                  : "bg-rose-500/10 text-rose-400"
            )}
          >
            {(parcel.utility_score * 100).toFixed(0)}
          </span>
        </div>
        <button className="rounded-lg bg-cyan-500/10 px-3 py-1 text-[11px] font-medium text-cyan-400 transition-colors hover:bg-cyan-500/20">
          Analyze
        </button>
      </div>
    </div>
  );
}

// ─── Detail Sidebar Panel ─────────────────────────────────────────────────────

function DetailPanel({ parcel, onClose }: { parcel: Parcel; onClose: () => void }) {
  const infraItems = [
    { label: "Water Supply", value: parcel.infra_scores.water, icon: Droplets, color: "text-blue-400" },
    { label: "Power Grid", value: parcel.infra_scores.power, icon: Zap, color: "text-amber-400" },
    { label: "Sewage System", value: parcel.infra_scores.sewage, icon: PipetteIcon, color: "text-violet-400" },
    { label: "Road Connectivity", value: parcel.infra_scores.road, icon: Route, color: "text-emerald-400" },
  ];

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900/80 p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">Parcel Details</h3>
        <button onClick={onClose} className="rounded-lg p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300">
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Parcel name and location */}
      <div className="mb-4 rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-3">
        <h4 className="font-semibold text-cyan-400">{parcel.name}</h4>
        <p className="text-xs text-slate-500">{parcel.location}</p>
      </div>

      {/* Key stats */}
      <div className="mb-4 grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-slate-800/50 p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Area</p>
          <p className="mt-0.5 font-mono text-lg font-bold text-slate-100">{parcel.area_acres} ac</p>
        </div>
        <div className="rounded-lg bg-slate-800/50 p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Price</p>
          <p className="mt-0.5 font-mono text-lg font-bold text-slate-100">₹{parcel.price_cr} Cr</p>
        </div>
        <div className="rounded-lg bg-slate-800/50 p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">ROI</p>
          <p className={cn("mt-0.5 font-mono text-lg font-bold", parcel.return_pct >= 17 ? "text-emerald-400" : "text-slate-100")}>
            {parcel.return_pct}%
          </p>
        </div>
        <div className="rounded-lg bg-slate-800/50 p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Utility</p>
          <p className="mt-0.5 font-mono text-lg font-bold text-cyan-400">{(parcel.utility_score * 100).toFixed(0)}</p>
        </div>
      </div>

      {/* Full infrastructure breakdown */}
      <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Infrastructure Breakdown
      </h4>
      <div className="space-y-3">
        {infraItems.map((item) => {
          const pct = Math.round(item.value * 100);
          const Icon = item.icon;
          return (
            <div key={item.label}>
              <div className="mb-1 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon className={cn("h-3.5 w-3.5", item.color)} />
                  <span className="text-xs text-slate-300">{item.label}</span>
                </div>
                <span className="font-mono text-xs font-semibold text-slate-200">{pct}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className={cn("h-full rounded-full transition-all duration-700", item.color.replace("text-", "bg-"))}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Action buttons */}
      <div className="mt-5 flex gap-2">
        <button className="flex-1 rounded-lg bg-cyan-500 px-4 py-2 text-xs font-semibold text-slate-950 transition-colors hover:bg-cyan-400">
          Run QAOA
        </button>
        <button className="flex-1 rounded-lg border border-slate-600 px-4 py-2 text-xs font-semibold text-slate-300 transition-colors hover:bg-slate-800">
          Compare
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// LAND STUDIO PAGE
// ═══════════════════════════════════════════════════════════════════════════════

export default function LandStudio() {
  const [budget, setBudget] = useState(15);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedParcel, setSelectedParcel] = useState<Parcel | null>(null);

  // Filter parcels by budget and search
  const filteredParcels = useMemo(() => {
    return MOCK_PARCELS.filter((p) => {
      const withinBudget = p.price_cr <= budget;
      const matchesSearch =
        !searchQuery ||
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.location.toLowerCase().includes(searchQuery.toLowerCase());
      return withinBudget && matchesSearch;
    });
  }, [budget, searchQuery]);

  return (
    <div className="space-y-6">
      {/* ── Top Controls: Budget Slider + Search ──────────────── */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-900/80 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:gap-8">
          {/* Budget Slider */}
          <div className="flex-1">
            <div className="mb-2 flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
                <SlidersHorizontal className="h-4 w-4 text-cyan-400" />
                Investment Budget
              </label>
              <span className="rounded-md bg-cyan-500/10 px-2.5 py-0.5 font-mono text-sm font-bold text-cyan-400">
                ₹{budget.toFixed(1)} Cr
              </span>
            </div>
            <input
              type="range"
              min={5}
              max={25}
              step={0.5}
              value={budget}
              onChange={(e) => setBudget(parseFloat(e.target.value))}
              className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-800 accent-cyan-400
                [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-cyan-400 [&::-webkit-slider-thumb]:shadow-[0_0_10px_rgba(6,182,212,0.5)]"
            />
            <div className="mt-1 flex justify-between text-[10px] text-slate-600">
              <span>₹5 Cr</span>
              <span>₹15 Cr</span>
              <span>₹25 Cr</span>
            </div>
          </div>

          {/* Search */}
          <div className="relative lg:w-72">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search parcels..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 w-full rounded-lg border border-slate-700/50 bg-slate-800/50 pl-9 pr-4 text-sm text-slate-300 placeholder-slate-500 outline-none focus:border-cyan-500/50"
            />
          </div>
        </div>

        {/* Result count */}
        <p className="mt-3 text-xs text-slate-500">
          Showing <span className="font-semibold text-slate-300">{filteredParcels.length}</span> parcels within ₹{budget.toFixed(1)} Cr budget
        </p>
      </div>

      {/* ── Main Area: Parcels Grid + Detail Panel ────────────── */}
      <div className="flex gap-6">
        {/* Parcel Cards Grid */}
        <div className={cn("grid gap-4 transition-all", selectedParcel ? "flex-1 grid-cols-1 md:grid-cols-2" : "flex-1 grid-cols-1 md:grid-cols-2 xl:grid-cols-3")}>
          {filteredParcels.map((parcel) => (
            <ParcelCard
              key={parcel.id}
              parcel={parcel}
              isSelected={selectedParcel?.id === parcel.id}
              onSelect={setSelectedParcel}
            />
          ))}
          {filteredParcels.length === 0 && (
            <div className="col-span-full flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700/50 py-16">
              <MapPin className="mb-3 h-8 w-8 text-slate-600" />
              <p className="text-sm text-slate-500">No parcels found within budget</p>
              <p className="text-xs text-slate-600">Try increasing the budget limit</p>
            </div>
          )}
        </div>

        {/* Detail Sidebar */}
        {selectedParcel && (
          <div className="hidden w-80 shrink-0 lg:block">
            <div className="sticky top-24">
              <DetailPanel parcel={selectedParcel} onClose={() => setSelectedParcel(null)} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
