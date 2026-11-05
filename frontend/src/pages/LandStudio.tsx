import { useState, useMemo, useEffect } from "react";
import {
  MapPin,
  Droplets,
  Zap,
  Pipette,
  Route,
  Search,
  SlidersHorizontal,
  LayoutGrid,
  Columns,
  Cpu,
  Wifi,
  WifiOff,
  ShieldCheck,
  Building2,
  FileText,
  ArrowUpDown,
  Navigation,
  ExternalLink,
  ChevronRight,
  Filter,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { cn } from "../lib/utils";
import { MOCK_PARCELS, MOCK_QUANTUM_RESULT } from "../lib/mockData";
import CityTwin3D from "../components/3d/CityTwin3D";
import PuneMap from "../components/gis/PuneMap";
import ParcelProfileModal from "../components/real_estate/ParcelProfileModal";
import { fetchParcels, type LandParcel } from "../lib/api";

// ─── Infrastructure Score Bar ────────────────────────────────────────────────

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

// ─── Parcel Card Component ───────────────────────────────────────────────────

function ParcelCard({
  parcel,
  isSelected,
  onSelect,
  onOpenModal,
}: {
  parcel: LandParcel;
  isSelected: boolean;
  onSelect: (p: LandParcel) => void;
  onOpenModal: (p: LandParcel) => void;
}) {
  const isWinner = MOCK_QUANTUM_RESULT.decoded_solution.selected_parcels.includes(parcel.name);
  const pricePerAcre = parcel.price_per_acre_crore ?? Number((parcel.price_crore / parcel.area_acres).toFixed(2));

  return (
    <div
      onClick={() => onSelect(parcel)}
      className={cn(
        "group cursor-pointer rounded-2xl border p-5 transition-all duration-200 relative overflow-hidden bg-white shadow-xs hover:shadow-md flex flex-col justify-between",
        isSelected
          ? "border-blue-600 ring-2 ring-blue-500/15"
          : "border-slate-200/90 hover:border-slate-300"
      )}
    >
      {isWinner && (
        <div className="absolute top-0 right-0 bg-emerald-50 text-emerald-800 border-b border-l border-emerald-200 font-mono text-[9px] px-2.5 py-0.5 rounded-bl font-bold uppercase tracking-wider flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          QAOA Winner
        </div>
      )}

      <div>
        {/* Header */}
        <div className="mb-2.5 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-1.5 mb-1">
              <span className="font-mono text-[10px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-100">
                {parcel.id}
              </span>
              <span className="font-mono text-[10px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md capitalize">
                {parcel.zone_type}
              </span>
            </div>
            <h3 className="font-display text-base font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
              {parcel.name}
            </h3>
            <p className="flex items-center gap-1 text-xs text-slate-500 mt-0.5">
              <MapPin className="h-3 w-3 text-slate-400" />
              {parcel.location || `${parcel.name}, Pune`}
            </p>
          </div>

          <div className="text-right">
            <span className="font-mono text-sm font-bold text-slate-900 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200 block">
              ₹{parcel.price_crore.toFixed(1)} Cr
            </span>
            <span className="font-mono text-[10px] text-slate-500 mt-0.5 block">
              ₹{pricePerAcre.toFixed(2)} Cr / Acre
            </span>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="mb-3 grid grid-cols-3 gap-2 border-y border-slate-100 py-2.5 text-xs text-center">
          <div>
            <span className="text-[10px] text-slate-400 block uppercase font-medium">Area</span>
            <span className="font-semibold text-slate-800">{parcel.area_acres} Acres</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 block uppercase font-medium">Proj. Return</span>
            <span className="font-semibold text-emerald-600">+{parcel.projected_return_pct}%</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 block uppercase font-medium">Suitability</span>
            <span className="font-mono font-semibold text-blue-600">
              {Math.round((parcel.utility_score || 0.75) * 100)}%
            </span>
          </div>
        </div>

        {/* Infrastructure Mini Bars */}
        <div className="space-y-1.5 mb-4">
          <InfraBar label="Water" value={parcel.water_score} icon={Droplets} color="text-sky-500" />
          <InfraBar label="Power" value={parcel.electricity_score} icon={Zap} color="text-amber-500" />
          <InfraBar label="Road" value={parcel.road_score} icon={Route} color="text-emerald-500" />
        </div>
      </div>

      {/* Card Action Footer */}
      <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
        <span className="text-[10px] font-medium text-slate-400 flex items-center gap-1">
          <ShieldCheck className="h-3 w-3 text-emerald-600" />
          Cadastral Verified
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onOpenModal(parcel);
          }}
          className="text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 hover:underline text-xs"
        >
          View Full Dossier
          <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN LAND STUDIO PAGE
// ═══════════════════════════════════════════════════════════════════════════════

export default function LandStudio() {
  const navigate = useNavigate();
  const [allParcels, setAllParcels] = useState<LandParcel[]>(MOCK_PARCELS);
  const [selectedParcel, setSelectedParcel] = useState<LandParcel | null>(MOCK_PARCELS[0]);
  const [modalParcel, setModalParcel] = useState<LandParcel | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  // Search & Filtering States
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedZone, setSelectedZone] = useState<string>("all");
  const [budgetCap, setBudgetCap] = useState(40.0);
  const [minArea, setMinArea] = useState<number>(0);
  const [sortBy, setSortBy] = useState<string>("utility_desc");

  // View Mode: "split" (3D + List), "gis" (OpenStreetMap + List), "3d" (Full 3D), "grid" (Card Grid)
  const [viewMode, setViewMode] = useState<"split" | "gis" | "3d" | "grid">("split");
  const [isLive, setIsLive] = useState<boolean>(false);

  // Fetch live parcels from FastAPI
  useEffect(() => {
    let isMounted = true;
    async function load() {
      try {
        const live = await fetchParcels();
        if (isMounted && live && live.length > 0) {
          setAllParcels(live);
          setSelectedParcel(live[0]);
          setIsLive(true);
        }
      } catch (e) {
        console.warn("FastAPI parcels endpoint unreachable, using fallback:", e);
        setIsLive(false);
      }
    }
    load();
    return () => {
      isMounted = false;
    };
  }, []);

  // Filter & Sort parcels client-side for immediate responsive interaction
  const filteredParcels = useMemo(() => {
    let result = allParcels.filter((p) => {
      // 1. Budget filter (individual plot price <= budgetCap)
      const withinBudget = p.price_crore <= budgetCap;

      // 2. Search query (matches name or ID)
      const q = searchQuery.trim().toLowerCase();
      const matchesSearch =
        !q ||
        p.name.toLowerCase().includes(q) ||
        p.id.toLowerCase().includes(q) ||
        (p.location && p.location.toLowerCase().includes(q));

      // 3. Category/Zone filter
      const matchesZone = selectedZone === "all" || p.zone_type.toLowerCase() === selectedZone.toLowerCase();

      // 4. Area filter
      const matchesArea = p.area_acres >= minArea;

      return withinBudget && matchesSearch && matchesZone && matchesArea;
    });

    // Sorting
    result.sort((a, b) => {
      if (sortBy === "price_asc") return a.price_crore - b.price_crore;
      if (sortBy === "price_desc") return b.price_crore - a.price_crore;
      if (sortBy === "area_asc") return a.area_acres - b.area_acres;
      if (sortBy === "area_desc") return b.area_acres - a.area_acres;
      if (sortBy === "price_per_acre_asc") {
        const ppaA = a.price_per_acre_crore ?? a.price_crore / a.area_acres;
        const ppaB = b.price_per_acre_crore ?? b.price_crore / b.area_acres;
        return ppaA - ppaB;
      }
      // default: utility_desc
      return (b.utility_score || 0) - (a.utility_score || 0);
    });

    return result;
  }, [allParcels, budgetCap, searchQuery, selectedZone, minArea, sortBy]);

  function handleOpenModal(parcel: LandParcel) {
    setModalParcel(parcel);
    setIsModalOpen(true);
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* ── Connectivity Banner ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 rounded-xl border px-4 py-2.5 text-xs bg-white shadow-2xs">
        <div className="flex items-center gap-2">
          {isLive ? (
            <>
              <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <Wifi className="h-4 w-4 text-emerald-600" />
              <span className="font-semibold text-slate-800">
                Connected to FastAPI Real Estate & Quantum Optimization Engine (Port 8000)
              </span>
            </>
          ) : (
            <>
              <span className="flex h-2.5 w-2.5 rounded-full bg-amber-500" />
              <WifiOff className="h-4 w-4 text-amber-600" />
              <span className="font-medium text-slate-600">
                Offline Demonstration Mode (Using labelled synthetic PMRDA Pune dataset)
              </span>
            </>
          )}
        </div>
        <div className="flex items-center gap-3 font-mono text-[11px] text-slate-500">
          <span>{allParcels.length} Registered Micro-Markets</span>
          <span>•</span>
          <span>PMRDA DP 2021-2041</span>
        </div>
      </div>

      {/* ── Top Filter, Search & View Controls ─────────────────────────── */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h1 className="font-display text-xl font-bold text-slate-900 tracking-tight">
              PMRDA Land Intelligence Studio
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Comprehensive land intelligence, infrastructure proximity, development feasibility, and QAOA compatibility.
            </p>
          </div>

          {/* View Mode Switcher */}
          <div className="flex rounded-xl border border-slate-200 bg-slate-50 p-1 self-start md:self-auto">
            <button
              onClick={() => setViewMode("split")}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all",
                viewMode === "split"
                  ? "bg-white text-blue-700 shadow-2xs"
                  : "text-slate-500 hover:text-slate-800"
              )}
            >
              <Columns className="h-3.5 w-3.5" />
              Split 3D
            </button>
            <button
              onClick={() => setViewMode("gis")}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all",
                viewMode === "gis"
                  ? "bg-white text-blue-700 shadow-2xs"
                  : "text-slate-500 hover:text-slate-800"
              )}
            >
              <MapPin className="h-3.5 w-3.5" />
              GIS Map
            </button>
            <button
              onClick={() => setViewMode("3d")}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all",
                viewMode === "3d"
                  ? "bg-white text-blue-700 shadow-2xs"
                  : "text-slate-500 hover:text-slate-800"
              )}
            >
              <Building2 className="h-3.5 w-3.5" />
              Full 3D
            </button>
            <button
              onClick={() => setViewMode("grid")}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all",
                viewMode === "grid"
                  ? "bg-white text-blue-700 shadow-2xs"
                  : "text-slate-500 hover:text-slate-800"
              )}
            >
              <LayoutGrid className="h-3.5 w-3.5" />
              Grid
            </button>
          </div>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          {/* Search Box (4 cols) */}
          <div className="md:col-span-4">
            <label className="text-[10px] font-semibold uppercase text-slate-500 block mb-1">
              Search Parcel ID or Location
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="e.g. PUNE-003, Hinjawadi, Kharadi..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-3 text-xs text-slate-800 placeholder-slate-400 outline-none focus:border-blue-500 focus:bg-white transition-all font-medium"
              />
            </div>
          </div>

          {/* Category Pills (3 cols) */}
          <div className="md:col-span-3">
            <label className="text-[10px] font-semibold uppercase text-slate-500 block mb-1">
              Land Category / Zoning
            </label>
            <select
              value={selectedZone}
              onChange={(e) => setSelectedZone(e.target.value)}
              className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 text-xs font-semibold text-slate-800 outline-none focus:border-blue-500"
            >
              <option value="all">All Zones ({allParcels.length})</option>
              <option value="commercial">Commercial / IT Hubs</option>
              <option value="residential">Residential Belts</option>
              <option value="mixed">Mixed-Use Integrated</option>
              <option value="industrial">Industrial PEB Corridors</option>
            </select>
          </div>

          {/* Sort Dropdown (3 cols) */}
          <div className="md:col-span-3">
            <label className="text-[10px] font-semibold uppercase text-slate-500 block mb-1 flex items-center gap-1">
              <ArrowUpDown className="h-3 w-3 text-slate-400" />
              Sort Ranking
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 text-xs font-semibold text-slate-800 outline-none focus:border-blue-500"
            >
              <option value="utility_desc">Suitability Score (Highest First)</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="price_per_acre_asc">Price per Acre: Lowest First</option>
              <option value="area_asc">Land Area: Smallest First</option>
              <option value="area_desc">Land Area: Largest First</option>
            </select>
          </div>

          {/* Reset button (2 cols) */}
          <div className="md:col-span-2">
            <button
              onClick={() => {
                setSearchQuery("");
                setSelectedZone("all");
                setBudgetCap(40.0);
                setMinArea(0);
                setSortBy("utility_desc");
              }}
              className="h-10 w-full rounded-xl border border-slate-200 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors"
            >
              Reset Filters
            </button>
          </div>
        </div>

        {/* Budget & Area Slider Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 border-t border-slate-100">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-600 font-medium">Max Parcel Price Cap:</span>
              <span className="font-mono font-bold text-blue-700">₹{budgetCap.toFixed(1)} Cr</span>
            </div>
            <input
              type="range"
              min={8}
              max={60}
              step={0.5}
              value={budgetCap}
              onChange={(e) => setBudgetCap(parseFloat(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
            <div className="flex justify-between font-mono text-[10px] text-slate-400 mt-0.5">
              <span>₹8.0 Cr</span>
              <span>₹40.0 Cr (Standard Demonstration Baseline)</span>
              <span>₹60.0 Cr</span>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-600 font-medium">Minimum Land Area:</span>
              <span className="font-mono font-bold text-slate-800">{minArea} Acres</span>
            </div>
            <input
              type="range"
              min={0}
              max={10}
              step={0.5}
              value={minArea}
              onChange={(e) => setMinArea(parseFloat(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
            <div className="flex justify-between font-mono text-[10px] text-slate-400 mt-0.5">
              <span>0 Acres</span>
              <span>5 Acres</span>
              <span>10+ Acres</span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500 border-t border-slate-100 pt-3">
          <span>
            Displaying <b className="text-slate-900 font-bold">{filteredParcels.length}</b> of {allParcels.length} verified PMRDA parcels
          </span>
          <span className="text-[11px] font-mono text-slate-400">
            Source: {allParcels[0]?.data_provenance}
          </span>
        </div>
      </div>

      {/* ── Main Workspace: Based on Selected View Mode ─────────────────── */}

      {/* VIEW 1: Split 3D Digital Twin + List */}
      {viewMode === "split" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
          <div className="lg:col-span-7 h-[580px] rounded-2xl overflow-hidden border border-slate-200 shadow-xs bg-white">
            <CityTwin3D
              parcels={filteredParcels}
              selectedParcelId={selectedParcel?.id ?? null}
              onSelectParcel={(p) => setSelectedParcel(p)}
              winningParcels={MOCK_QUANTUM_RESULT.decoded_solution.selected_parcels}
            />
          </div>

          <div className="lg:col-span-5 flex flex-col gap-4 overflow-y-auto max-h-[580px] pr-1">
            {filteredParcels.map((parcel) => (
              <ParcelCard
                key={parcel.id}
                parcel={parcel}
                isSelected={selectedParcel?.id === parcel.id}
                onSelect={(p) => setSelectedParcel(p)}
                onOpenModal={handleOpenModal}
              />
            ))}
          </div>
        </div>
      )}

      {/* VIEW 2: GIS Map + List */}
      {viewMode === "gis" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
          <div className="lg:col-span-7 h-[580px] rounded-2xl overflow-hidden border border-slate-200 shadow-xs bg-white">
            <PuneMap
              parcels={filteredParcels}
              selectedParcelId={selectedParcel?.id ?? null}
              onSelectParcel={(p) => setSelectedParcel(p)}
              onOpenProfile={handleOpenModal}
              winningParcels={MOCK_QUANTUM_RESULT.decoded_solution.selected_parcels}
            />
          </div>

          <div className="lg:col-span-5 flex flex-col gap-4 overflow-y-auto max-h-[580px] pr-1">
            {filteredParcels.map((parcel) => (
              <ParcelCard
                key={parcel.id}
                parcel={parcel}
                isSelected={selectedParcel?.id === parcel.id}
                onSelect={(p) => setSelectedParcel(p)}
                onOpenModal={handleOpenModal}
              />
            ))}
          </div>
        </div>
      )}

      {/* VIEW 3: Full 3D Digital Twin */}
      {viewMode === "3d" && (
        <div className="h-[620px] rounded-2xl overflow-hidden border border-slate-200 shadow-xs bg-white">
          <CityTwin3D
            parcels={filteredParcels}
            selectedParcelId={selectedParcel?.id ?? null}
            onSelectParcel={(p) => setSelectedParcel(p)}
            winningParcels={MOCK_QUANTUM_RESULT.decoded_solution.selected_parcels}
          />
        </div>
      )}

      {/* VIEW 4: Cadastral Cards Grid */}
      {viewMode === "grid" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredParcels.map((parcel) => (
            <ParcelCard
              key={parcel.id}
              parcel={parcel}
              isSelected={selectedParcel?.id === parcel.id}
              onSelect={(p) => setSelectedParcel(p)}
              onOpenModal={handleOpenModal}
            />
          ))}
        </div>
      )}

      {/* ── Active Selection Action Bar (Sticky at Bottom) ─────────────── */}
      {selectedParcel && (
        <div className="sticky bottom-4 z-40 rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-xl backdrop-blur-md flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-700 font-bold font-mono text-sm border border-blue-200">
              {selectedParcel.id.replace("PUNE-", "P")}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display text-sm font-bold text-slate-900">
                  {selectedParcel.name}
                </span>
                <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] text-slate-600 capitalize">
                  {selectedParcel.zone_type}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                ₹{selectedParcel.price_crore.toFixed(1)} Cr • {selectedParcel.area_acres} Acres • +{selectedParcel.projected_return_pct}% Projected Return
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleOpenModal(selectedParcel)}
              className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 transition-colors shadow-2xs"
            >
              <FileText className="h-4 w-4" />
              Open Detailed Intelligence Dossier
            </button>
            <button
              onClick={() => navigate("/quantum")}
              className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
            >
              <Cpu className="h-4 w-4 text-blue-600" />
              Test in QAOA Lab
            </button>
          </div>
        </div>
      )}

      {/* ── Detailed Land Profile Modal (Sections A - F) ───────────────── */}
      {modalParcel && (
        <ParcelProfileModal
          parcel={modalParcel}
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onOpenQuantumLab={() => navigate("/quantum")}
        />
      )}
    </div>
  );
}
