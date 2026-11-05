import React, { useState, useEffect } from "react";
import {
  FileText,
  Play,
  RotateCcw,
  Sparkles,
  Info,
  CheckCircle2,
  Sliders,
  Scale,
  ShieldCheck,
} from "lucide-react";
import {
  analyzeQuantumInformation,
  type QuantumInformationResponse,
} from "../../lib/api";

const STATE_PRESETS = [
  { id: "pure_zero", name: "|0⟩ Ground State", desc: "Pure state, S(ρ)=0, Purity=1.0" },
  { id: "pure_one", name: "|1⟩ Excited State", desc: "Orthogonal to |0⟩, F(|0⟩,|1⟩)=0" },
  { id: "pure_plus", name: "|+⟩ Superposition", desc: "Non-orthogonal to |0⟩, F(|0⟩,|+⟩)=0.5" },
  { id: "maximally_mixed_1q", name: "Maximally Mixed (I/2)", desc: "Maximum entropy S(ρ)=1.0, Purity=0.5" },
  { id: "bell_phi_plus", name: "|Φ+⟩ Bell State", desc: "2-qubit pure entangled state, S(ρ)=0" },
  { id: "werner_state", name: "Werner State (p=0.5)", desc: "Mixture of Bell state and white noise" },
];

export default function EntropyInformationLab() {
  const [stateA, setStateA] = useState<string>("pure_zero");
  const [stateB, setStateB] = useState<string>("pure_plus");
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<QuantumInformationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeQuantumInformation({
        state_a_preset: stateA,
        state_b_preset: stateB,
      });
      setResult(res);
    } catch (err: any) {
      console.error("Quantum information analysis failed:", err);
      setError(err.response?.data?.detail || err.message || "Failed to analyze quantum information.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleAnalyze();
  }, [stateA, stateB]);

  return (
    <div className="space-y-6">
      {/* Control Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Scale className="h-5 w-5 text-blue-600" />
              <h2 className="font-display text-lg font-bold text-slate-900">
                Quantum Information, Von Neumann Entropy & Fidelity
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Compute Von Neumann entropy S(ρ) = -Tr(ρ log₂ ρ), Jozsa quantum state fidelity F(ρ, σ), and trace distance D(ρ, σ). Verify the fundamental Fuchs-van de Graaf inequality bounds.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-xs"
            >
              <Sparkles className="h-3.5 w-3.5" />
              {loading ? "Computing..." : "Compare States"}
            </button>
          </div>
        </div>

        {/* State Selectors */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-blue-700 block mb-1.5">
              Select State A (ρ)
            </label>
            <select
              value={stateA}
              onChange={(e) => setStateA(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              {STATE_PRESETS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} — {p.desc}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 block mb-1.5">
              Select State B (σ)
            </label>
            <select
              value={stateB}
              onChange={(e) => setStateB(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
            >
              {STATE_PRESETS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} — {p.desc}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Column 1: State A Metrics */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-display text-sm font-bold text-blue-900">
                State A: {result.state_A.name}
              </h3>
              <span className="font-mono text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-200 font-bold">
                {result.state_A.classification}
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500">Von Neumann Entropy S(ρ):</span>
                <span className="font-mono font-bold text-slate-800">
                  {result.state_A.von_neumann_entropy.toFixed(4)} bits
                </span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500">Shannon Entropy H(p):</span>
                <span className="font-mono font-bold text-slate-800">
                  {result.state_A.shannon_entropy.toFixed(4)} bits
                </span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500">Purity Tr(ρ²):</span>
                <span className="font-mono font-bold text-blue-700">
                  {result.state_A.purity.toFixed(4)}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500 block mb-1">Eigenvalues:</span>
                <span className="font-mono text-[11px] font-bold text-slate-700">
                  [{result.state_A.eigenvalues.map((v) => v.toFixed(3)).join(", ")}]
                </span>
              </div>
            </div>
          </div>

          {/* Column 2: State B Metrics */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-display text-sm font-bold text-emerald-900">
                State B: {result.state_B.name}
              </h3>
              <span className="font-mono text-[10px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200 font-bold">
                {result.state_B.classification}
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500">Von Neumann Entropy S(σ):</span>
                <span className="font-mono font-bold text-slate-800">
                  {result.state_B.von_neumann_entropy.toFixed(4)} bits
                </span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500">Shannon Entropy H(p):</span>
                <span className="font-mono font-bold text-slate-800">
                  {result.state_B.shannon_entropy.toFixed(4)} bits
                </span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500">Purity Tr(σ²):</span>
                <span className="font-mono font-bold text-emerald-700">
                  {result.state_B.purity.toFixed(4)}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500 block mb-1">Eigenvalues:</span>
                <span className="font-mono text-[11px] font-bold text-slate-700">
                  [{result.state_B.eigenvalues.map((v) => v.toFixed(3)).join(", ")}]
                </span>
              </div>
            </div>
          </div>

          {/* Column 3: Relational Distance & Fuchs-van de Graaf Inequality */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Relational Distances & Bounds
            </h3>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl border border-blue-100 bg-blue-50/50">
                <div className="flex justify-between">
                  <span className="text-blue-900 font-bold">Jozsa Fidelity F(ρ, σ):</span>
                  <span className="font-mono font-bold text-blue-700">
                    {result.relational_metrics.fidelity_F.toFixed(4)}
                  </span>
                </div>
                <span className="text-[10px] text-blue-700 block mt-0.5">
                  Squared Fidelity: {result.relational_metrics.squared_fidelity_F.toFixed(4)}
                </span>
              </div>

              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                <div className="flex justify-between">
                  <span className="text-slate-700 font-bold">Trace Distance D(ρ, σ):</span>
                  <span className="font-mono font-bold text-slate-900">
                    {result.relational_metrics.trace_distance_D.toFixed(4)}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  Maximum distinguishability between the two states
                </span>
              </div>

              {/* Fuchs-van de Graaf Bounds Card */}
              <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/60 space-y-2">
                <div className="flex items-center gap-1.5 text-emerald-900 font-bold">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  <span>Fuchs-van de Graaf Inequality</span>
                </div>
                <div className="text-[11px] font-mono text-emerald-950 font-bold bg-white/80 p-2 rounded border border-emerald-200/70 text-center">
                  {result.relational_metrics.fuchs_van_de_graaf_bounds.lower_bound.toFixed(3)} ≤ {result.relational_metrics.trace_distance_D.toFixed(3)} ≤ {result.relational_metrics.fuchs_van_de_graaf_bounds.upper_bound.toFixed(3)}
                </div>
                <div className="flex justify-between text-[10px] text-emerald-800">
                  <span>1 - √F ≤ D(ρ,σ) ≤ √(1 - F)</span>
                  <span className="font-bold">
                    {result.relational_metrics.fuchs_van_de_graaf_bounds.is_satisfied ? "✓ VERIFIED" : "VIOLATED"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

