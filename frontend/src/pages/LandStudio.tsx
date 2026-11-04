import { useState, useMemo } from "react";
import {
  MapPin,
  Droplets,
  Zap,
  Pipette,
  Route,
  Search,
  SlidersHorizontal,
  X,
  Map as MapIcon,
  LayoutGrid,
  Columns,
  Cpu,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { cn } from "../lib/utils";
import { MOCK_PARCELS, MOCK_QUANTUM_RESULT } from "../lib/mockData";
import PuneMap from "../components/gis/PuneMap";
import type { Parcel } from "../lib/api";

// ─── Infrastructure Score Bar ─────────────────────────────────────────────────

function InfraBar({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number;
  icon: React.ElementType;
  color: string;
}) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <Icon className={cn("h-3.5 w-3.5 shrink-0", color)} />
      <span className="w-16 text-[10px] font-mono text-slate-500 uppercase">{label}</span>
      <div className="flex-1">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-900 border border-slate-800">
          <div
            className={cn("h-full rounded-full transition-all duration-500", color.replace("text-", "bg-"))}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      <span className="w-8 text-right font-mono text-[10px] text-slate-400">{pct}%</span>
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
  const isWinner = MOCK_QUANTUM_RESULT.selected_parcels.includes(parcel.name);

  return (
    <div
      onClick={() => onSelect(parcel)}
      className={cn(
        "group cursor-pointer rounded-xl border p-4 transition-all duration-200 relative overflow-hidden",
        isSelected
          ? "border-cyan-400 bg-cyan-950/20 shadow-[0_0_15px_rgba(34,211,238,0.1)]"
          : "border-slate-800 bg-slate-950/80 hover:border-slate-700 hover:bg-slate-900/60"
      )}
    >
      {isWinner && (
        <div className="absolute top-0 right-0 bg-cyan-500/20 text-cyan-300 border-b border-l border-cyan-500/30 font-mono text-[9px] px-2 py-0.5 rounded-bl font-semibold uppercase tracking-wider">
          QAOA Ground State
        </div>
      )}

      {/* Header */}
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h3 className="font-display text-sm font-bold text-white group-hover:text-cyan-300 transition-colors">
            {parcel.name}
          </h3>
          <p className="flex items-center gap-1 text-[11px] font-mono text-slate-500 mt-0.5">
            <MapPin className="h-3 w-3 text-slate-500" />
            {parcel.location}
          </p>
        </div>
        <span className="font-mono text-xs font-bold text-white bg-slate-900 px-2 py-1 rounded border border-slate-800">
          ₹{parcel.price_cr} Cr
        </span>
      </div>

      {/* Quick stats */}
      <div className="mb-3 grid grid-cols-2 gap-2 border-y border-slate-900 py-2 font-mono text-xs">
        <div>
          <span className="text-[10px] text-slate-500 block uppercase">Area</span>
          <span className="font-semibold text-slate-300">{parcel.area_acres} Acres</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 block uppercase">Proj. Return</span>
          <span className="font-semibold text-emerald-400">+{parcel.return_pct}%</span>
        </div>
      </div>

      {/* Infrastructure Mini Bars */}
      <div className="space-y-1.5">
        <InfraBar label="Water" value={parcel.infra_scores.water} icon={Droplets} color="text-sky-400" />
        <InfraBar label="Power" value={parcel.infra_scores.power} icon={Zap} color="text-amber-400" />
        <InfraBar label="Road" value={parcel.infra_scores.road} icon={Route} color="text-emerald-400" />
      </div>
    </div>
  );
}

// ─── Detail Sidebar Panel ─────────────────────────────────────────────────────

function DetailPanel({ parcel, onClose }: { parcel: Parcel; onClose: () => void }) {
  const navigate = useNavigate();

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/95 p-5 backdrop-blur-md space-y-4">
      <div className="flex items-start justify-between border-b border-slate-800 pb-3">
        <div>
          <span className="font-mono text-[9px] uppercase tracking-wider text-cyan-400 font-bold">
            Cadastral Record PMRDA-#{parcel.id.toString().padStart(4, "0")}
          </span>
          <h2 className="font-display text-base font-bold text-white mt-0.5">{parcel.name}</h2>
          <p className="text-xs font-mono text-slate-500">{parcel.location}</p>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1 text-slate-500 hover:bg-slate-900 hover:text-slate-300"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3 font-mono text-xs">
        <div className="rounded bg-slate-900/60 p-2 border border-slate-800">
          <span className="text-[10px] text-slate-500 block">Asking Price</span>
          <span className="text-sm font-bold text-white">₹{parcel.price_cr} Cr</span>
        </div>
        <div className="rounded bg-slate-900/60 p-2 border border-slate-800">
          <span className="text-[10px] text-slate-500 block">Total Area</span>
          <span className="text-sm font-bold text-white">{parcel.area_acres} Acres</span>
        </div>
      </div>

      {/* Infrastructure breakdown */}
      <div className="space-y-2.5 border-t border-slate-900 pt-3">
        <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Deterministic IS 1172 Breakdown
        </span>
        <InfraBar label="Water Supply" value={parcel.infra_scores.water} icon={Droplets} color="text-sky-400" />
        <InfraBar label="Power Grid" value={parcel.infra_scores.power} icon={Zap} color="text-amber-400" />
        <InfraBar label="Road Access" value={parcel.infra_scores.road} icon={Route} color="text-emerald-400" />
        <InfraBar label="Sewage Net" value={parcel.infra_scores.sewage} icon={Pipette} color="text-violet-400" />
      </div>

      <div className="border-t border-slate-800 pt-3 flex gap-2">
        <button
          onClick={() => navigate("/quantum")}
          className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-cyan-500 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-cyan-400"
        >
          <Cpu className="h-3.5 w-3.5" />
          Feed to QAOA
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN LAND STUDIO PAGE
// ═══════════════════════════════════════════════════════════════════════════════

export default function LandStudio() {
  const [budget, setBudget] = useState(15.0);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedParcel, setSelectedParcel] = useState<Parcel | null>(MOCK_PARCELS[0]);
  const [viewMode, setViewMode] = useState<"split" | "map" | "grid">("split");

  // Filter parcels
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
      {/* ── Top Controls: Budget Slider + Search + View Mode ──────────────── */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-5 backdrop-blur-md">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          {/* Budget Slider */}
          <div className="flex-1 max-w-xl">
            <div className="mb-2 flex items-center justify-between">
              <label className="flex items-center gap-2 font-display text-sm font-semibold text-white">
                <SlidersHorizontal className="h-4 w-4 text-cyan-400" />
                Capital Budget Constraint (₹ Cr)
              </label>
              <span className="rounded-lg bg-cyan-500/10 px-3 py-0.5 font-mono text-sm font-bold text-cyan-400 border border-cyan-500/30">
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
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <div className="mt-1 flex justify-between font-mono text-[10px] text-slate-500">
              <span>₹5 Cr (Entry)</span>
              <span>₹15 Cr (PMRDA Baseline)</span>
              <span>₹25 Cr (Megasite)</span>
            </div>
          </div>

          {/* Search & View Switcher */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Search micro-market..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-9 w-52 rounded-lg border border-slate-800 bg-slate-900/90 pl-8 pr-3 font-mono text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-cyan-500/50"
              />
            </div>

            {/* View Mode Toggle */}
            <div className="flex rounded-lg border border-slate-800 bg-slate-900/80 p-0.5">
              <button
                onClick={() => setViewMode("split")}
                className={cn(
                  "flex items-center gap-1 rounded px-2.5 py-1 text-xs font-mono transition-colors",
                  viewMode === "split" ? "bg-cyan-500/20 text-cyan-300 font-semibold" : "text-slate-400 hover:text-slate-200"
                )}
                title="Split Map & Grid"
              >
                <Columns className="h-3.5 w-3.5" />
                Split
              </button>
              <button
                onClick={() => setViewMode("map")}
                className={cn(
                  "flex items-center gap-1 rounded px-2.5 py-1 text-xs font-mono transition-colors",
                  viewMode === "map" ? "bg-cyan-500/20 text-cyan-300 font-semibold" : "text-slate-400 hover:text-slate-200"
                )}
                title="Map Only"
              >
                <MapIcon className="h-3.5 w-3.5" />
                GIS Map
              </button>
              <button
                onClick={() => setViewMode("grid")}
                className={cn(
                  "flex items-center gap-1 rounded px-2.5 py-1 text-xs font-mono transition-colors",
                  viewMode === "grid" ? "bg-cyan-500/20 text-cyan-300 font-semibold" : "text-slate-400 hover:text-slate-200"
                )}
                title="Grid Only"
              >
                <LayoutGrid className="h-3.5 w-3.5" />
                Grid
              </button>
            </div>
          </div>
        </div>

        <p className="mt-3 font-mono text-[11px] text-slate-400 border-t border-slate-900 pt-2">
          Displaying <b className="text-white">{filteredParcels.length}</b> eligible PMRDA parcels within budget &le; ₹{budget.toFixed(1)} Cr
        </p>
      </div>

      {/* ── Main Workspace Body ───────────────────────────────────────────── */}
      {viewMode === "split" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Map on Left (6 cols) */}
          <div className="lg:col-span-6 h-[560px] rounded-2xl overflow-hidden border border-slate-800">
            <PuneMap
              parcels={filteredParcels}
              selectedParcelId={selectedParcel?.id ?? null}
              onSelectParcel={setSelectedParcel}
              winningParcels={MOCK_QUANTUM_RESULT.selected_parcels}
            />
          </div>

          {/* Cards on Right (6 cols) */}
          <div className="lg:col-span-6 flex flex-col gap-4 overflow-y-auto max-h-[560px] pr-1">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {filteredParcels.map((parcel) => (
                <ParcelCard
                  key={parcel.id}
                  parcel={parcel}
                  isSelected={selectedParcel?.id === parcel.id}
                  onSelect={setSelectedParcel}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {viewMode === "map" && (
        <div className="h-[620px] rounded-2xl overflow-hidden border border-slate-800">
          <PuneMap
            parcels={filteredParcels}
            selectedParcelId={selectedParcel?.id ?? null}
            onSelectParcel={setSelectedParcel}
            winningParcels={MOCK_QUANTUM_RESULT.selected_parcels}
          />
        </div>
      )}

      {viewMode === "grid" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredParcels.map((parcel) => (
            <ParcelCard
              key={parcel.id}
              parcel={parcel}
              isSelected={selectedParcel?.id === parcel.id}
              onSelect={setSelectedParcel}
            />
          ))}
        </div>
      )}

      {/* Floating Detail Drawer when parcel is selected */}
      {selectedParcel && (
        <div className="fixed bottom-6 right-6 z-50 w-88 shadow-2xl">
          <DetailPanel parcel={selectedParcel} onClose={() => setSelectedParcel(null)} />
        </div>
      )}
    </div>
  );
}
