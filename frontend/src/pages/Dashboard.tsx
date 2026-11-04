import { useState } from "react";
import {
  MapPin,
  Cpu,
  IndianRupee,
  Bot,
  Brain,
  Grid3X3,
  Atom,
  Server,
  GitMerge,
  Sparkles,
  Play,
} from "lucide-react";
import { cn } from "../lib/utils";
import PuneMap from "../components/gis/PuneMap";
import {
  MOCK_PARCELS,
  MOCK_QUANTUM_RESULT,
  MOCK_WORKFLOW_STEPS,
} from "../lib/mockData";
import type { Parcel } from "../lib/api";

const STEP_ICONS: Record<string, React.ElementType> = {
  Bot,
  MapPin,
  Brain,
  Grid3X3,
  Atom,
  Cpu,
  Server,
  GitMerge,
  Sparkles,
};

export default function Dashboard() {
  const [selectedParcel, setSelectedParcel] = useState<Parcel>(MOCK_PARCELS[0]);
  const [activeStep, setActiveStep] = useState<number>(6);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  const winningParcels = MOCK_QUANTUM_RESULT.selected_parcels;

  const handleRunSimulation = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setIsSimulating(false);
      setActiveStep(9);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      {/* ─── Row 1: Tactical HUD Telemetry Cards ─────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {/* Metric 1 */}
        <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-950/90 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs uppercase tracking-wider text-slate-400">
              PMRDA Parcels Analyzed
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <MapPin className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-display text-2xl font-bold text-white">8 Parcels</span>
            <span className="font-mono text-[11px] font-medium text-emerald-400">100% Cadastral Verified</span>
          </div>
          <div className="mt-2 flex items-center justify-between border-t border-slate-900 pt-2 font-mono text-[10px] text-slate-500">
            <span>Region: Pune Metro</span>
            <span>Area: 42.1 Acres Total</span>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-950/90 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs uppercase tracking-wider text-slate-400">
              QAOA Approximation Ratio
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Cpu className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-display text-2xl font-bold text-cyan-400 font-mono">0.999 &alpha;</span>
            <span className="font-mono text-[11px] font-medium text-slate-400">vs Exact MILP</span>
          </div>
          <div className="mt-2 flex items-center justify-between border-t border-slate-900 pt-2 font-mono text-[10px] text-slate-500">
            <span>Circuit: p=2 Layers</span>
            <span className="text-cyan-400 font-semibold">COBYLA Optimized</span>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-950/90 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs uppercase tracking-wider text-slate-400">
              Target Budget Allocation
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <IndianRupee className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-display text-2xl font-bold text-white">₹14.6 / 15.0 Cr</span>
            <span className="font-mono text-[11px] font-medium text-amber-400">97.3% Cap</span>
          </div>
          <div className="mt-2 flex items-center justify-between border-t border-slate-900 pt-2 font-mono text-[10px] text-slate-500">
            <span>Remaining: ₹0.40 Cr</span>
            <span className="text-emerald-400">Strictly Compliant</span>
          </div>
        </div>

        {/* Metric 4 */}
        <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-950/90 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs uppercase tracking-wider text-slate-400">
              Decisional Recommendation
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Sparkles className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-display text-2xl font-bold text-white">READY TO EXEC</span>
            <span className="font-mono text-[11px] font-medium text-emerald-400">Go Decision</span>
          </div>
          <div className="mt-2 flex items-center justify-between border-t border-slate-900 pt-2 font-mono text-[10px] text-slate-500">
            <span>Confidence: 94.8%</span>
            <span>RERA In-Principle</span>
          </div>
        </div>
      </div>

      {/* ─── Row 2: Split Cockpit: Geospatial GIS + Executive Briefing ─── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Interactive Pune GIS Studio (7 cols) */}
        <div className="lg:col-span-7 flex flex-col rounded-2xl border border-slate-800 bg-slate-950/90 p-5 backdrop-blur-md space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-emerald-400" />
              <h2 className="font-display text-sm font-semibold text-white">
                Pune PMRDA Spatial GIS Cockpit
              </h2>
            </div>
            <div className="flex items-center gap-2 font-mono text-[11px]">
              <span className="text-slate-400">Focus:</span>
              <span className="text-cyan-400 font-semibold">{selectedParcel.name}</span>
            </div>
          </div>

          {/* Interactive Leaflet Map Canvas */}
          <div className="h-[380px] w-full rounded-xl overflow-hidden">
            <PuneMap
              parcels={MOCK_PARCELS}
              selectedParcelId={selectedParcel.id}
              onSelectParcel={setSelectedParcel}
              winningParcels={winningParcels}
            />
          </div>

          {/* Focused Parcel Quick Telemetry */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 font-mono text-xs">
            <div className="rounded-lg bg-slate-900/60 p-2.5 border border-slate-800">
              <span className="text-[10px] text-slate-500 block">Acquisition Cost:</span>
              <span className="text-white font-bold text-sm">₹{selectedParcel.price_cr} Cr</span>
            </div>
            <div className="rounded-lg bg-slate-900/60 p-2.5 border border-slate-800">
              <span className="text-[10px] text-slate-500 block">Plot Area:</span>
              <span className="text-white font-bold text-sm">{selectedParcel.area_acres} Acres</span>
            </div>
            <div className="rounded-lg bg-slate-900/60 p-2.5 border border-slate-800">
              <span className="text-[10px] text-slate-500 block">5-Yr Projected Return:</span>
              <span className="text-emerald-400 font-bold text-sm">+{selectedParcel.return_pct}%</span>
            </div>
            <div className="rounded-lg bg-slate-900/60 p-2.5 border border-slate-800">
              <span className="text-[10px] text-slate-500 block">Infra Readiness:</span>
              <span className="text-cyan-400 font-bold text-sm">
                {(selectedParcel.utility_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Pune ₹15 Cr Case Study Executive Briefing (5 cols) */}
        <div className="lg:col-span-5 flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-950/90 p-5 backdrop-blur-md space-y-4">
          <div className="space-y-2 border-b border-slate-800 pb-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] uppercase tracking-wider text-cyan-400 font-bold">
                [Golden Workflow: Pune ₹15 Cr Brief]
              </span>
              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-mono text-emerald-400 border border-emerald-500/20">
                PMRDA Jurisdictional Scope
              </span>
            </div>
            <h2 className="font-display text-base font-bold text-white">
              AI-Synthesized Development Brief
            </h2>
            <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2.5 text-xs text-slate-300 italic">
              "Find the best development opportunity within ₹15 crore around Pune, considering land price, water, electricity, sewage, road access and expected returns."
            </div>
          </div>

          {/* Optimal Portfolio Cards */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-mono text-slate-400">QAOA Optimal Selection Set:</span>
              <span className="font-mono text-cyan-400 font-bold">|11010010⟩</span>
            </div>

            <div className="space-y-2">
              {winningParcels.map((name, idx) => (
                <div
                  key={name}
                  className="flex items-center justify-between rounded-lg border border-cyan-500/30 bg-cyan-950/20 px-3 py-2 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded bg-cyan-500/20 text-[10px] font-mono font-bold text-cyan-400">
                      {idx + 1}
                    </span>
                    <span className="font-medium text-white">{name}</span>
                  </div>
                  <span className="font-mono text-cyan-300 font-semibold">Selected</span>
                </div>
              ))}
            </div>
          </div>

          {/* Synthesis Stats */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3 space-y-2 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Total Capital Committed:</span>
              <span className="text-white font-bold">₹14.6 Cr</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Contingency Reserve:</span>
              <span className="text-emerald-400 font-bold">₹0.40 Cr</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Water Demand (IS 1172):</span>
              <span className="text-cyan-400">84,240 LPD</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Estimated Power Load:</span>
              <span className="text-amber-400">367.1 kVA</span>
            </div>
          </div>

          {/* Trigger Button */}
          <button
            onClick={handleRunSimulation}
            disabled={isSimulating}
            className={cn(
              "w-full flex items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold transition-all",
              isSimulating
                ? "bg-slate-800 text-slate-400 cursor-not-allowed"
                : "bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-lg shadow-cyan-500/20 active:scale-[0.98]"
            )}
          >
            {isSimulating ? (
              <>
                <Atom className="h-4 w-4 animate-spin text-cyan-400" />
                Simulating QAOA Quantum Circuit...
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Re-Run Pune Computational Pipeline
              </>
            )}
          </button>
        </div>
      </div>

      {/* ─── Row 3: 9-Step Computational Heart Stepper ──────────────── */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/90 p-5 backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-cyan-400" />
            <h2 className="font-display text-sm font-semibold text-white">
              The 9-Step Computational Heart
            </h2>
          </div>
          <span className="font-mono text-xs text-slate-400">
            End-to-End Execution Sequence · Pune ₹15 Cr Case
          </span>
        </div>

        {/* Stepper Grid */}
        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3 lg:grid-cols-9">
          {MOCK_WORKFLOW_STEPS.map((step) => {
            const Icon = STEP_ICONS[step.icon] || Cpu;
            const isCompleted = step.step < activeStep;
            const isActive = step.step === activeStep;

            return (
              <div
                key={step.step}
                className={cn(
                  "relative flex flex-col justify-between rounded-xl border p-3 transition-all",
                  isActive
                    ? "border-cyan-400 bg-cyan-950/30 shadow-[0_0_12px_rgba(34,211,238,0.15)]"
                    : isCompleted
                    ? "border-emerald-500/30 bg-emerald-950/10 text-slate-300"
                    : "border-slate-800/80 bg-slate-900/40 text-slate-500 opacity-60"
                )}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-[10px] font-bold">
                    0{step.step}
                  </span>
                  <Icon
                    className={cn(
                      "h-4 w-4",
                      isActive
                        ? "text-cyan-400 animate-pulse"
                        : isCompleted
                        ? "text-emerald-400"
                        : "text-slate-600"
                    )}
                  />
                </div>
                <div>
                  <h3 className="font-display text-xs font-bold text-white mb-1">
                    {step.name}
                  </h3>
                  <p className="text-[10px] text-slate-400 line-clamp-2">
                    {step.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
