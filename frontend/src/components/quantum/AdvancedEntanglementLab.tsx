import React, { useState, useEffect } from "react";
import {
  Sparkles,
  GitMerge,
  Sliders,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  ShieldCheck,
  Zap,
} from "lucide-react";
import {
  analyzeEntanglement,
  type EntanglementAnalyzeResponse,
} from "../../lib/api";

const PRESETS = [
  { id: "bell_phi_plus", name: "|Φ+⟩ Bell State", desc: "Maximally entangled 2-qubit state, C=1.0, Rank=2" },
  { id: "bell_psi_minus", name: "|Ψ−⟩ Singlet State", desc: "Anti-correlated rotationally invariant singlet, C=1.0" },
  { id: "werner_state", name: "Werner State ρ_W(p)", desc: "Mixture with white noise; transition at p > 1/3" },
  { id: "w_state_3q", name: "3-Qubit W-State", desc: "Robust multipartite entanglement resistant to qubit loss" },
  { id: "ghz_state_3q", name: "3-Qubit GHZ State", desc: "Maximally entangled tripartite state" },
  { id: "classical_correlated_separable", name: "Classical Mixture (Separable)", desc: "50% |00⟩ + 50% |11⟩; classical correlation only, C=0.0" },
];

export default function AdvancedEntanglementLab() {
  const [selectedPreset, setSelectedPreset] = useState<string>("bell_phi_plus");
  const [wernerP, setWernerP] = useState<number>(0.75);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<EntanglementAnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeEntanglement({
        preset: selectedPreset,
        werner_parameter_p: wernerP,
      });
      setResult(res);
    } catch (err: any) {
      console.error("Entanglement analysis failed:", err);
      setError(err.response?.data?.detail || err.message || "Failed to analyze entanglement.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleAnalyze();
  }, [selectedPreset, wernerP]);

  return (
    <div className="space-y-6">
      {/* Control Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-blue-600" />
              <h2 className="font-display text-lg font-bold text-slate-900">
                Advanced Entanglement Analysis & Quantum Witness
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Distinguish true quantum entanglement from classical statistical correlation using Schmidt rank decomposition, Wootters' concurrence C(ρ), and Peres-Horodecki positive partial transpose (PPT) negativity.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`font-mono text-xs font-bold px-3 py-1.5 rounded-xl border ${
                result?.entanglement_classification === "ENTANGLED"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-slate-100 text-slate-600 border-slate-200"
              }`}
            >
              STATUS: {result?.entanglement_classification ?? "ANALYZING"}
            </span>
          </div>
        </div>

        {/* Preset Selector */}
        <div className="mt-6">
          <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            Select Entangled or Separable Quantum State
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-2.5 mt-2">
            {PRESETS.map((p) => (
              <button
                key={p.id}
                onClick={() => setSelectedPreset(p.id)}
                className={`p-3 rounded-xl border text-left transition-all text-xs ${
                  selectedPreset === p.id
                    ? "border-blue-600 bg-blue-50/60 ring-2 ring-blue-500/10"
                    : "border-slate-200 bg-white hover:border-slate-300"
                }`}
              >
                <div className="font-bold text-slate-800">{p.name}</div>
                <div className="text-[10px] text-slate-400 mt-1 line-clamp-2">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Werner State Parameter Slider (shown when Werner preset selected) */}
        {selectedPreset === "werner_state" && (
          <div className="mt-5 p-4 rounded-xl border border-blue-200 bg-blue-50/50 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-blue-900">
                Werner Mixture Parameter p: ρ_W(p) = p |Φ+⟩⟨Φ+| + (1-p)/4 · I₄
              </span>
              <span className="font-mono text-blue-700 font-bold bg-white px-2 py-0.5 rounded border border-blue-200">
                p = {wernerP.toFixed(2)} {wernerP > 0.3333 ? "(ENTANGLED, p > 1/3)" : "(SEPARABLE, p ≤ 1/3)"}
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.02"
              value={wernerP}
              onChange={(e) => setWernerP(parseFloat(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-blue-700 font-mono">
              <span>p = 0.0 (Maximally Mixed Noise)</span>
              <span className="font-bold text-amber-700">p = 0.333 (Critical Boundary p = 1/3)</span>
              <span>p = 1.0 (Pure Bell State)</span>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Card 1: Wootters' Concurrence */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-display text-sm font-bold text-slate-900">
                Wootters' Concurrence C(ρ)
              </h3>
              <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200">
                {result.concurrence.toFixed(4)}
              </span>
            </div>

            <p className="text-xs text-slate-500">
              Concurrence measures entanglement of formation for arbitrary mixed states. C = 0 implies separability; C = 1 implies maximal entanglement.
            </p>

            <div className="space-y-2">
              <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden border border-slate-200">
                <div
                  className="bg-blue-600 h-full rounded-full transition-all"
                  style={{ width: `${result.concurrence * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>0.0 (Separable)</span>
                <span>0.5</span>
                <span>1.0 (Maximal)</span>
              </div>
            </div>

            <div className="p-3 rounded-xl border border-slate-100 bg-slate-50 text-xs text-slate-600 space-y-1">
              <span className="font-bold text-slate-800 block">Calculation Method:</span>
              <p className="text-[11px] leading-relaxed">
                Eigenvalues of R = √(√ρ ρ̃ √ρ) where ρ̃ = (σ_y ⊗ σ_y) ρ* (σ_y ⊗ σ_y). C = max(0, λ₁ - λ₂ - λ₃ - λ₄).
              </p>
            </div>
          </div>

          {/* Card 2: Peres-Horodecki PPT Negativity */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-display text-sm font-bold text-slate-900">
                Peres-Horodecki PPT Criterion
              </h3>
              <span className="font-mono text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
                N = {result.negativity.toFixed(4)}
              </span>
            </div>

            <p className="text-xs text-slate-500">
              If the partial transpose ρ^{"{T_B}"} possesses any negative eigenvalues, the bipartite state is definitively non-separable (Peres 1996).
            </p>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500">Negativity N(ρ):</span>
                <span className="font-mono font-bold text-emerald-700">
                  {result.negativity.toFixed(4)}
                </span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500">Logarithmic Negativity E_N:</span>
                <span className="font-mono font-bold text-slate-800">
                  {result.logarithmic_negativity.toFixed(4)}
                </span>
              </div>
              <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500">PPT Criterion Status:</span>
                <span className="font-mono font-bold text-slate-900">
                  {result.negativity > 1e-4 ? "Negative Eigenvalue Detected (N > 0)" : "All Eigenvalues ≥ 0 (PPT)"}
                </span>
              </div>
            </div>
          </div>

          {/* Card 3: Schmidt Decomposition or Explanation */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Schmidt Decomposition & State Notes
            </h3>

            {result.schmidt_decomposition ? (
              <div className="space-y-3 text-xs">
                <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-slate-500">Schmidt Rank k:</span>
                  <span className="font-mono font-bold text-purple-700">
                    {result.schmidt_decomposition.schmidt_rank} (k &gt; 1 = Entangled)
                  </span>
                </div>
                <div className="flex justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-slate-500">Entanglement Entropy:</span>
                  <span className="font-mono font-bold text-slate-800">
                    {result.schmidt_decomposition.entanglement_entropy.toFixed(4)} bits
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-slate-500 block mb-1">Schmidt Coefficients (λ_k):</span>
                  <span className="font-mono text-[11px] font-bold text-slate-700">
                    [{result.schmidt_decomposition.schmidt_coefficients.map((c) => c.toFixed(3)).join(", ")}]
                  </span>
                </div>
              </div>
            ) : (
              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-600 space-y-2">
                <span className="font-bold text-slate-800 block">Mixed State Regime</span>
                <p className="text-[11px] leading-relaxed">
                  Schmidt decomposition applies directly to pure bipartite vectors |ψ_AB⟩. For mixed density operators (such as Werner states or statistical mixtures), Wootters' concurrence and PPT negativity serve as the definitive witnesses.
                </p>
              </div>
            )}

            <div className="p-3 rounded-xl border border-blue-100 bg-blue-50/50 text-[11px] text-blue-900 space-y-1">
              <span className="font-bold block">Scientific Explanation:</span>
              <p className="text-[10px] text-blue-800 leading-relaxed">
                {result.explanation}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
