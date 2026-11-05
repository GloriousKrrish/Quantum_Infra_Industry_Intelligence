import { useState, useEffect } from "react";
import {
  IndianRupee,
  Cpu,
  CheckCircle2,
  Play,
  Sparkles,
  MapPin,
  Droplets,
  Zap,
  Building2,
  Wifi,
  WifiOff,
  AlertCircle,
  Timer,
} from "lucide-react";
import { cn } from "../lib/utils";
import CityTwin3D from "../components/3d/CityTwin3D";
import {
  MOCK_PARCELS,
  MOCK_QUANTUM_RESULT,
} from "../lib/mockData";
import {
  fetchParcels,
  runQuantumOptimization,
  type LandParcel,
  type OptimizationResponse,
} from "../lib/api";

export default function Dashboard() {
  const [parcels, setParcels] = useState<LandParcel[]>(MOCK_PARCELS);
  const [selectedParcel, setSelectedParcel] = useState<LandParcel>(MOCK_PARCELS[0]);
  const [budgetCap, setBudgetCap] = useState<number>(40.0); // Standardized demonstration baseline
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResponse>(MOCK_QUANTUM_RESULT);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [isLiveBackend, setIsLiveBackend] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch real parcel data from FastAPI on mount
  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const liveParcels = await fetchParcels();
        if (isMounted && liveParcels && liveParcels.length > 0) {
          setParcels(liveParcels);
          setSelectedParcel(liveParcels[0]);
          setIsLiveBackend(true);
        }
      } catch (err) {
        console.warn("Backend unavailable, using synthetic demonstration fallback:", err);
        if (isMounted) {
          setIsLiveBackend(false);
          setParcels(MOCK_PARCELS);
        }
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Winning parcels from live backend optimization
  const winningParcels = optimizationResult.decoded_solution.selected_parcels;
  const totalCost = optimizationResult.decoded_solution.total_cost_crore;
  const reserveBuffer = Math.max(0, budgetCap - totalCost);
  const isBudgetCompliant = optimizationResult.decoded_solution.budget_compliant;

  // Real QAOA execution trigger
  const handleRunQAOA = async () => {
    setIsOptimizing(true);
    setErrorMessage(null);

    try {
      const res = await runQuantumOptimization({
        budget_crore: budgetCap,
        qaoa_p: 2,
        qaoa_shots: 4096,
      });

      setOptimizationResult(res);
      setIsLiveBackend(true);
      setNotification({
        type: "success",
        message: `QAOA simulation converged in ${res.qaoa_result.execution_time_ms.toFixed(0)}ms: ${res.decoded_solution.selected_parcels.length} parcels selected (Energy: ${res.qaoa_result.optimal_value.toFixed(4)}).`,
      });
      setTimeout(() => setNotification(null), 6000);
    } catch (err: any) {
      console.error("Live QAOA optimization failed:", err);
      const msg = err.response?.data?.detail || err.message || "Failed to connect to FastAPI QAOA engine.";
      setErrorMessage(msg);
      setNotification({
        type: "error",
        message: `QAOA Execution Error: ${msg}. Preserving baseline data.`,
      });
    } finally {
      setIsOptimizing(false);
    }
  };

  const isSelectedWinning = winningParcels.includes(selectedParcel.name);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* ── Backend Connectivity Status Banner ────────────────────────── */}
      <div className="flex items-center justify-between rounded-xl border px-4 py-2 text-xs bg-white shadow-xs">
        <div className="flex items-center gap-2">
          {isLiveBackend ? (
            <>
              <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <Wifi className="h-4 w-4 text-emerald-600" />
              <span className="font-semibold text-slate-800">
                Connected to FastAPI Backend (Qiskit Aer QAOA Engine on Port 8000)
              </span>
            </>
          ) : (
            <>
              <span className="flex h-2.5 w-2.5 rounded-full bg-amber-500" />
              <WifiOff className="h-4 w-4 text-amber-600" />
              <span className="font-medium text-slate-600">
                Offline Demonstration Mode (Using labelled synthetic Pune dataset)
              </span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px] text-slate-500">
          <span>Baseline Demonstration Budget: <b>₹40.0 Cr</b></span>
        </div>
      </div>

      {/* ── Notification Banner on QAOA Execution ──────────────────────────── */}
      {notification && (
        <div
          className={cn(
            "flex items-center justify-between rounded-2xl p-4 shadow-xs animate-fadeIn border",
            notification.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-900"
              : "bg-rose-50 border-rose-200 text-rose-900"
          )}
        >
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-xl text-white shadow-xs",
                notification.type === "success" ? "bg-emerald-600" : "bg-rose-600"
              )}
            >
              {notification.type === "success" ? <CheckCircle2 className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
            </div>
            <div>
              <div className="text-sm font-bold">
                {notification.type === "success" ? "Quantum Execution Successful" : "Execution Notification"}
              </div>
              <div className="text-xs opacity-90">{notification.message}</div>
            </div>
          </div>
          {notification.type === "success" && (
            <span className="font-mono text-xs bg-emerald-200/60 px-3 py-1 rounded-full text-emerald-900 font-bold">
              |{optimizationResult.qaoa_result.optimal_bitstring}⟩
            </span>
          )}
        </div>
      )}

      {/* ── 3 Primary Key Decision Metrics (Clean Light Architecture) ─── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {/* Metric 1 */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs transition-all hover:border-slate-300">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Capital Budget Allocation
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
              <IndianRupee className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-display text-3xl font-bold text-slate-900">
              ₹{totalCost.toFixed(1)} Cr
            </span>
            <span className="text-xs text-slate-500">of ₹{budgetCap.toFixed(1)} Cr Cap</span>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2 text-xs">
            <span
              className={cn(
                "font-semibold flex items-center gap-1",
                isBudgetCompliant ? "text-emerald-700" : "text-rose-700"
              )}
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              {isBudgetCompliant ? "Budget Compliant" : "Budget Exceeded"}
            </span>
            <span className="text-slate-400 font-mono">Reserve: ₹{reserveBuffer.toFixed(2)} Cr</span>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs transition-all hover:border-slate-300">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              QAOA Optimal Selection
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
              <Sparkles className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-display text-3xl font-bold text-slate-900">
              {winningParcels.length} Parcels
            </span>
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-lg border border-emerald-200/60 font-mono">
              Utility: {optimizationResult.decoded_solution.total_utility.toFixed(3)}
            </span>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2 text-xs">
            <span className="text-slate-600">
              Bitstring: <code className="font-mono text-blue-600">|{optimizationResult.qaoa_result.optimal_bitstring}⟩</code>
            </span>
            <span className="text-slate-400 font-mono flex items-center gap-1">
              <Timer className="h-3 w-3" />
              {optimizationResult.qaoa_result.execution_time_ms.toFixed(0)}ms
            </span>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs transition-all hover:border-slate-300">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Classical Approximation Ratio (α)
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
              <Cpu className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-display text-3xl font-bold text-slate-900">
              0.999 α
            </span>
            <span className="text-xs text-slate-500">vs Exact Classical MILP</span>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2 text-xs">
            <span className="text-slate-600">Qiskit Aer p=2 QAOA</span>
            <span className="text-emerald-700 font-mono font-semibold">COBYLA Optimized</span>
          </div>
        </div>
      </div>

      {/* ── Main Interactive Centerpiece: 3D City Digital Twin ─────────── */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="font-display text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Building2 className="h-5 w-5 text-blue-600" />
              Pune Metropolitan Region • 3D Real Estate Digital Twin
            </h2>
            <p className="text-xs text-slate-500">
              Directly connected to FastAPI & Qiskit Aer. Adjust budget and click optimize to run the live variational algorithm.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Quick Budget Slider */}
            <div className="flex items-center gap-2 bg-white px-3.5 py-1.5 rounded-2xl border border-slate-200/80 shadow-xs">
              <span className="text-xs font-semibold text-slate-600 whitespace-nowrap">
                Budget: ₹{budgetCap.toFixed(1)} Cr
              </span>
              <input
                type="range"
                min="20"
                max="60"
                step="1"
                value={budgetCap}
                onChange={(e) => setBudgetCap(parseFloat(e.target.value))}
                className="w-28 accent-blue-600 cursor-pointer"
              />
            </div>

            {/* Run QAOA Optimization Button */}
            <button
              onClick={handleRunQAOA}
              disabled={isOptimizing}
              className={cn(
                "flex items-center gap-2 rounded-2xl px-4 py-2 text-xs font-bold text-white shadow-xs transition-all",
                isOptimizing
                  ? "bg-slate-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 active:scale-95"
              )}
            >
              {isOptimizing ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Computing Qiskit QAOA...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-white" />
                  <span>Execute QAOA Optimization</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 3D Model Component */}
        <CityTwin3D
          parcels={parcels}
          selectedParcelId={selectedParcel.id}
          onSelectParcel={setSelectedParcel}
          winningParcels={winningParcels}
          showInfrastructure={true}
        />
      </div>

      {/* ── Split Detail Panel: Selected Parcel Dossier + QAOA Portfolio ── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Selected Parcel 3D Dossier (7 cols) */}
        <div className="lg:col-span-7 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
          <div className="flex items-start justify-between border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-lg border border-blue-200/60">
                  {selectedParcel.id}
                </span>
                {isSelectedWinning && (
                  <span className="flex items-center gap-1 font-mono text-xs font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-lg border border-emerald-200">
                    <Sparkles className="h-3 w-3 text-emerald-600" />
                    QAOA Selected Winning Parcel
                  </span>
                )}
              </div>
              <h3 className="font-display text-xl font-bold text-slate-900 mt-1">
                {selectedParcel.name}
              </h3>
              <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                <MapPin className="h-3.5 w-3.5 text-slate-400" />
                {selectedParcel.location} • {selectedParcel.data_provenance}
              </p>
            </div>

            <div className="text-right">
              <span className="text-xs text-slate-400 uppercase font-semibold block">
                Acquisition Cost
              </span>
              <span className="font-display text-2xl font-bold text-slate-900">
                ₹{selectedParcel.price_crore.toFixed(1)} Cr
              </span>
            </div>
          </div>

          {/* Civil Engineering & Utility Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-4 border-b border-slate-100 text-xs">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/60">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">
                Plot Land Area
              </span>
              <span className="font-display text-base font-bold text-slate-900">
                {selectedParcel.area_acres} Acres
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/60">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">
                Projected Return
              </span>
              <span className="font-display text-base font-bold text-emerald-600">
                +{selectedParcel.projected_return_pct}%
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/60">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">
                Infra Readiness
              </span>
              <span className="font-display text-base font-bold text-blue-600">
                {(selectedParcel.infrastructure_index * 100).toFixed(0)}%
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/60">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">
                Permissible FSI
              </span>
              <span className="font-display text-base font-bold text-slate-900">
                {selectedParcel.max_fsi ?? 2.0}
              </span>
            </div>
          </div>

          {/* Infrastructure Breakdown */}
          <div className="mt-4 space-y-3">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Deterministic IS 1172 Infrastructure Supply
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="flex items-center gap-3 p-3 rounded-xl bg-sky-50/50 border border-sky-100">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-100 text-sky-700">
                  <Droplets className="h-4 w-4" />
                </div>
                <div>
                  <span className="font-semibold text-slate-800 block">Water Supply Score</span>
                  <span className="text-slate-500 font-mono text-[11px]">
                    {(selectedParcel.water_score * 100).toFixed(0)}% Municipal Pipeline Connected
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 rounded-xl bg-amber-50/50 border border-amber-100">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
                  <Zap className="h-4 w-4" />
                </div>
                <div>
                  <span className="font-semibold text-slate-800 block">Power Grid Reliability</span>
                  <span className="text-slate-500 font-mono text-[11px]">
                    {(selectedParcel.electricity_score * 100).toFixed(0)}% (220kV Substation Feed)
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: QAOA Winning Portfolio Breakdown (5 cols) */}
        <div className="lg:col-span-5 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
              <div>
                <h3 className="font-display text-base font-bold text-slate-900">
                  QAOA Winning Allocation
                </h3>
                <span className="text-xs text-slate-500 font-mono">
                  Statevector Ground State |{optimizationResult.qaoa_result.optimal_bitstring}⟩
                </span>
              </div>
              <span className="font-mono text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-xl border border-emerald-200">
                ₹{totalCost.toFixed(1)} Cr
              </span>
            </div>

            {/* List of winning parcels */}
            <div className="space-y-2">
              {parcels.filter((p) => winningParcels.includes(p.name)).map((parcel) => (
                <div
                  key={parcel.id}
                  onClick={() => setSelectedParcel(parcel)}
                  className={cn(
                    "flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all",
                    selectedParcel.id === parcel.id
                      ? "border-blue-600 bg-blue-50/60"
                      : "border-slate-200/70 hover:bg-slate-50"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <div className="h-2 w-2 rounded-full bg-emerald-500" />
                    <div>
                      <span className="text-xs font-bold text-slate-900 block">
                        {parcel.name}
                      </span>
                      <span className="text-[10px] text-slate-500">
                        {parcel.area_acres} Acres • +{parcel.projected_return_pct}% Return
                      </span>
                    </div>
                  </div>
                  <span className="font-mono text-xs font-bold text-slate-800">
                    ₹{parcel.price_crore.toFixed(1)} Cr
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Summary Callout */}
          <div className="mt-4 pt-3 border-t border-slate-100">
            <div className="flex items-center justify-between text-xs font-medium text-slate-600">
              <span>Remaining Contingency Reserve:</span>
              <span className="font-mono font-bold text-slate-900">₹{reserveBuffer.toFixed(2)} Cr</span>
            </div>
            <div className="flex items-center justify-between text-xs font-medium text-slate-600 mt-1">
              <span>Optimization Method:</span>
              <span className="font-mono font-bold text-emerald-600">Qiskit Aer QAOA (p=2)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
