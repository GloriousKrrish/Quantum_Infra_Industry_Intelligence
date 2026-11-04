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
import CityTwin3D from "../components/3d/CityTwin3D";
import type { Parcel } from "../lib/api";

// ─── Infrastructure Score Bar (Clean Light Theme) ─────────────────────────────

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
      <span className="w-16 text-[10px] font-medium text-slate-500 uppercase">{label}</span>
      <div className="flex-1">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className={cn("h-full rounded-full transition-all duration-500", color.replace("text-", "bg-"))}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      <span className="w-8 text-right font-mono text-[10px] text-slate-600">{pct}%</span>
    </div>
  );
}

// ─── Parcel Card (Clean Light Theme) ──────────────────────────────────────────

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
        "group cursor-pointer rounded-2xl border p-5 transition-all duration-200 relative overflow-hidden bg-white shadow-xs hover:shadow-md",
        isSelected
          ? "border-blue-600 ring-2 ring-blue-500/10"
          : "border-slate-200/80 hover:border-slate-300"
      )}
    >
      {isWinner && (
        <div className="absolute top-0 right-0 bg-emerald-50 text-emerald-700 border-b border-l border-emerald-200 font-mono text-[9px] px-2.5 py-0.5 rounded-bl font-bold uppercase tracking-wider">
          QAOA Winner
        </div>
      )}

      {/* Header */}
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h3 className="font-display text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
            {parcel.name}
          </h3>
          <p className="flex items-center gap-1 text-xs text-slate-500 mt-0.5">
            <MapPin className="h-3 w-3 text-slate-400" />
            {parcel.location}
          </p>
        </div>
        <span className="font-mono text-xs font-bold text-slate-900 bg-slate-50 px-2 py-1 rounded-lg border border-slate-200">
          ₹{parcel.price_cr} Cr
        </span>
      </div>

      {/* Quick stats */}
      <div className="mb-3 grid grid-cols-2 gap-2 border-y border-slate-100 py-2.5 text-xs">
        <div>
          <span className="text-[10px] text-slate-400 block uppercase">Area</span>
          <span className="font-semibold text-slate-800">{parcel.area_acres} Acres</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block uppercase">Proj. Return</span>
          <span className="font-semibold text-emerald-600">+{parcel.return_pct}%</span>
        </div>
      </div>

      {/* Infrastructure Mini Bars */}
      <div className="space-y-1.5">
        <InfraBar label="Water" value={parcel.infra_scores.water} icon={Droplets} color="text-sky-500" />
        <InfraBar label="Power" value={parcel.infra_scores.power} icon={Zap} color="text-amber-500" />
        <InfraBar label="Road" value={parcel.infra_scores.road} icon={Route} color="text-emerald-500" />
      </div>
    </div>
  );
}

// ─── Detail Sidebar Panel (Clean Light Theme) ─────────────────────────────────

function DetailPanel({ parcel, onClose }: { parcel: Parcel; onClose: () => void }) {
  const navigate = useNavigate();

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-lg space-y-4">
      <div className="flex items-start justify-between border-b border-slate-100 pb-3">
        <div>
          <span className="text-[9px] font-bold uppercase tracking-wider text-blue-600">
            PMRDA Record #{parcel.id}
          </span>
          <h2 className="font-display text-base font-bold text-slate-900 mt-0.5">{parcel.name}</h2>
          <p className="text-xs text-slate-500">{parcel.location}</p>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="rounded-xl bg-slate-50 p-3 border border-slate-100">
          <span className="text-[10px] text-slate-500 block">Acquisition Price</span>
          <span className="text-sm font-bold text-slate-900">₹{parcel.price_cr} Cr</span>
        </div>
        <div className="rounded-xl bg-slate-50 p-3 border border-slate-100">
          <span className="text-[10px] text-slate-500 block">Total Area</span>
          <span className="text-sm font-bold text-slate-900">{parcel.area_acres} Acres</span>
        </div>
      </div>

      {/* Infrastructure breakdown */}
      <div className="space-y-2 border-t border-slate-100 pt-3">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Deterministic IS 1172 Breakdown
        </span>
        <InfraBar label="Water Supply" value={parcel.infra_scores.water} icon={Droplets} color="text-sky-500" />
        <InfraBar label="Power Grid" value={parcel.infra_scores.power} icon={Zap} color="text-amber-500" />
        <InfraBar label="Road Access" value={parcel.infra_scores.road} icon={Route} color="text-emerald-500" />
        <InfraBar label="Sewage Net" value={parcel.infra_scores.sewage} icon={Pipette} color="text-indigo-500" />
      </div>

      <div className="border-t border-slate-100 pt-3 flex gap-2">
        <button
          onClick={() => navigate("/quantum")}
          className="flex-1 flex items-center justify-center gap-1.5 rounded-xl bg-blue-600 px-3 py-2 text-xs font-bold text-white hover:bg-blue-700 transition-all shadow-xs"
        >
          <Cpu className="h-3.5 w-3.5" />
          Test in QAOA Lab
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
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Top Controls: Budget Slider + Search + View Mode ──────────────── */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          {/* Budget Slider */}
          <div className="flex-1 max-w-xl">
            <div className="mb-2 flex items-center justify-between">
              <label className="flex items-center gap-2 font-display text-sm font-semibold text-slate-800">
                <SlidersHorizontal className="h-4 w-4 text-blue-600" />
                Capital Budget Constraint (₹ Cr)
              </label>
              <span className="rounded-lg bg-blue-50 px-3 py-1 font-mono text-sm font-bold text-blue-700 border border-blue-100">
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
              className="w-full accent-blue-600 cursor-pointer"
            />
            <div className="mt-1 flex justify-between font-mono text-[10px] text-slate-400">
              <span>₹5 Cr (Entry)</span>
              <span>₹15 Cr (PMRDA Baseline)</span>
              <span>₹25 Cr (Megasite)</span>
            </div>
          </div>

          {/* Search & View Switcher */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search micro-market..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-10 w-56 rounded-xl border border-slate-200 bg-slate-50 pl-8 pr-3 text-xs text-slate-800 placeholder-slate-400 outline-none focus:border-blue-500 focus:bg-white"
              />
            </div>

            {/* View Mode Toggle */}
            <div className="flex rounded-xl border border-slate-200 bg-slate-50 p-1">
              <button
                onClick={() => setViewMode("split")}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all",
                  viewMode === "split"
                    ? "bg-white text-blue-700 font-semibold shadow-xs"
                    : "text-slate-500 hover:text-slate-800"
                )}
                title="Split 3D & Grid"
              >
                <Columns className="h-3.5 w-3.5" />
                Split 3D
              </button>
              <button
                onClick={() => setViewMode("map")}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all",
                  viewMode === "map"
                    ? "bg-white text-blue-700 font-semibold shadow-xs"
                    : "text-slate-500 hover:text-slate-800"
                )}
                title="Full 3D Twin"
              >
                <MapIcon className="h-3.5 w-3.5" />
                Full 3D
              </button>
              <button
                onClick={() => setViewMode("grid")}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all",
                  viewMode === "grid"
                    ? "bg-white text-blue-700 font-semibold shadow-xs"
                    : "text-slate-500 hover:text-slate-800"
                )}
                title="Grid Only"
              >
                <LayoutGrid className="h-3.5 w-3.5" />
                Grid
              </button>
            </div>
          </div>
        </div>

        <p className="mt-4 text-xs text-slate-500 border-t border-slate-100 pt-3">
          Showing <b className="text-slate-900 font-semibold">{filteredParcels.length}</b> eligible PMRDA parcels within budget &le; ₹{budget.toFixed(1)} Cr
        </p>
      </div>

      {/* ── Main Workspace Body ───────────────────────────────────────────── */}
      {viewMode === "split" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
          {/* 3D City Twin on Left (7 cols) */}
          <div className="lg:col-span-7 h-[540px] rounded-2xl overflow-hidden border border-slate-200 shadow-xs bg-white">
            <CityTwin3D
              parcels={filteredParcels}
              selectedParcelId={selectedParcel?.id ?? null}
              onSelectParcel={setSelectedParcel}
              winningParcels={MOCK_QUANTUM_RESULT.selected_parcels}
            />
          </div>

          {/* Cards on Right (5 cols) */}
          <div className="lg:col-span-5 flex flex-col gap-4 overflow-y-auto max-h-[540px] pr-1">
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
        <div className="h-[600px] rounded-2xl overflow-hidden border border-slate-200 shadow-xs bg-white">
          <CityTwin3D
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

      {/* Detail Drawer when parcel is selected */}
      {selectedParcel && (
        <div className="fixed bottom-6 right-8 z-50 w-88 shadow-xl">
          <DetailPanel parcel={selectedParcel} onClose={() => setSelectedParcel(null)} />
        </div>
      )}
    </div>
  );
}
