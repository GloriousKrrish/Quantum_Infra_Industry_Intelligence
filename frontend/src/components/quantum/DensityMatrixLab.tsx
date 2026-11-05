import React, { useState, useEffect } from "react";
import {
  Layers,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Eye,
  RefreshCw,
  Sliders,
} from "lucide-react";
import {
  analyzeDensityMatrix,
  type DensityMatrixAnalyzeResponse,
} from "../../lib/api";

const PRESETS = [
  { id: "bell_phi_plus", name: "|Φ+⟩ Bell State (2Q Pure Entangled)", desc: "ρ = (|00⟩+|11⟩)(⟨00|+⟨11|)/2, purity = 1.0, subsystem purity = 0.5" },
  { id: "pure_zero", name: "|0⟩ Ground State (1Q Pure)", desc: "ρ = |0⟩⟨0|, purity = 1.0, rank = 1" },
  { id: "pure_plus", name: "|+⟩ Superposition State (1Q Pure)", desc: "ρ = |+⟩⟨+|, purity = 1.0, rank = 1" },
  { id: "maximally_mixed_1q", name: "Maximally Mixed 1-Qubit (I/2)", desc: "ρ = diag(0.5, 0.5), purity = 0.5, rank = 2" },
  { id: "maximally_mixed_2q", name: "Maximally Mixed 2-Qubit (I/4)", desc: "ρ = diag(0.25, 0.25, 0.25, 0.25), purity = 0.25, rank = 4" },
];

export default function DensityMatrixLab() {
  const [selectedPreset, setSelectedPreset] = useState<string>("bell_phi_plus");
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<DensityMatrixAnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeDensityMatrix({ preset: selectedPreset });
      setResult(res);
    } catch (err: any) {
      console.error("Density matrix analysis failed:", err);
      setError(err.response?.data?.detail || err.message || "Failed to analyze density matrix.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleAnalyze();
  }, [selectedPreset]);

  return (
    <div className="space-y-6">
      {/* Control Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Layers className="h-5 w-5 text-blue-600" />
              <h2 className="font-display text-lg font-bold text-slate-900">
                Quantum Density Operator Laboratory (ρ)
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Inspect density operators, verify mathematical axioms (Hermiticity, unit trace, positive semi-definiteness), compute purity γ = Tr(ρ²), and calculate subsystem partial traces Tr_B(ρ_AB).
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-xs"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              {loading ? "Analyzing..." : "Re-analyze"}
            </button>
          </div>
        </div>

        {/* Preset Selector */}
        <div className="mt-6">
          <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            Select State Density Matrix Preset
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3 mt-2">
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

        {error && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Mathematical Axioms & Spectral Decomposition */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Fundamental Axiom Validation
            </h3>

            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl border border-slate-100 bg-slate-50 text-xs">
                <div>
                  <span className="font-bold text-slate-700 block">Hermiticity (ρ = ρ†)</span>
                  <span className="text-[10px] text-slate-400">Conjugate transpose symmetry</span>
                </div>
                <span
                  className={`font-mono font-bold px-2.5 py-1 rounded-lg border text-[11px] ${
                    result.is_hermitian
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : "bg-rose-50 text-rose-700 border-rose-200"
                  }`}
                >
                  {result.is_hermitian ? "VERIFIED (True)" : "VIOLATED"}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl border border-slate-100 bg-slate-50 text-xs">
                <div>
                  <span className="font-bold text-slate-700 block">Unit Trace Tr(ρ) = 1.0</span>
                  <span className="text-[10px] text-slate-400">Conservation of total probability</span>
                </div>
                <span className="font-mono font-bold text-slate-800 px-2.5 py-1 rounded-lg border border-slate-200 bg-white text-[11px]">
                  {result.trace.toFixed(4)}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl border border-slate-100 bg-slate-50 text-xs">
                <div>
                  <span className="font-bold text-slate-700 block">Positive Semi-Definiteness (ρ ≥ 0)</span>
                  <span className="text-[10px] text-slate-400">All eigenvalues λ_i ≥ 0</span>
                </div>
                <span
                  className={`font-mono font-bold px-2.5 py-1 rounded-lg border text-[11px] ${
                    result.is_positive_semidefinite
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : "bg-rose-50 text-rose-700 border-rose-200"
                  }`}
                >
                  {result.is_positive_semidefinite ? "VERIFIED (λ_i ≥ 0)" : "NON-PSD"}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl border border-slate-100 bg-slate-50 text-xs">
                <div>
                  <span className="font-bold text-slate-700 block">Purity γ = Tr(ρ²)</span>
                  <span className="text-[10px] text-slate-400">1.0 = Pure, 1/d = Maximally Mixed</span>
                </div>
                <span className="font-mono font-bold text-blue-700 px-2.5 py-1 rounded-lg border border-blue-200 bg-blue-50 text-[11px]">
                  {result.purity.toFixed(4)}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl border border-slate-100 bg-slate-50 text-xs">
                <div>
                  <span className="font-bold text-slate-700 block">State Classification</span>
                  <span className="text-[10px] text-slate-400">Rank = {result.rank} of {result.dimension}</span>
                </div>
                <span className="font-mono font-bold text-purple-700 px-2.5 py-1 rounded-lg border border-purple-200 bg-purple-50 text-[11px]">
                  {result.classification}
                </span>
              </div>
            </div>

            {/* Eigenvalue Spectrum */}
            <div className="pt-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-2">
                Eigenvalue Spectrum (λ_i)
              </span>
              <div className="space-y-1.5">
                {result.eigenvalues.map((ev, idx) => (
                  <div key={idx} className="flex justify-between items-center text-xs font-mono">
                    <span className="text-slate-500">λ_{idx}:</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-slate-200 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-blue-600 h-full rounded-full"
                          style={{ width: `${Math.max(0, Math.min(100, ev * 100))}%` }}
                        />
                      </div>
                      <span className="font-bold text-slate-800 w-12 text-right">{ev.toFixed(4)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Middle & Right Columns: Matrix Viewer and Partial Trace Subsystems */}
          <div className="lg:col-span-2 space-y-6">
            {/* Full Matrix Heat Grid */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="font-display text-sm font-bold text-slate-900">
                  Full Density Matrix ρ ({result.dimension} × {result.dimension})
                </h3>
                <span className="text-xs font-mono text-slate-500">
                  {result.num_qubits} Qubit{result.num_qubits > 1 ? "s" : ""}
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono border-collapse">
                  <tbody>
                    {result.matrix.map((row, rIdx) => (
                      <tr key={rIdx} className="border-b border-slate-100">
                        {row.map((cell, cIdx) => {
                          const isDiagonal = rIdx === cIdx;
                          const mag = Math.sqrt(cell.real ** 2 + cell.imag ** 2);
                          return (
                            <td
                              key={cIdx}
                              className={`p-3 text-center border-r border-slate-100 ${
                                isDiagonal ? "bg-blue-50/40" : ""
                              }`}
                            >
                              <div className="font-bold text-slate-800">
                                {cell.real.toFixed(3)}
                              </div>
                              {Math.abs(cell.imag) > 1e-4 && (
                                <div className="text-[10px] text-purple-600">
                                  {cell.imag >= 0 ? "+" : ""}{cell.imag.toFixed(3)}i
                                </div>
                              )}
                              <div className="text-[9px] text-slate-400 mt-0.5">
                                |ρ| = {mag.toFixed(2)}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Subsystem Partial Trace (if 2 qubits) */}
            {result.num_qubits === 2 && result.reduced_density_matrix_A && (
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
                <div>
                  <h3 className="font-display text-sm font-bold text-slate-900">
                    Bipartite Subsystem Reduction (Partial Trace)
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Tracing out environmental subsystems demonstrates quantum entanglement: a pure global state (Tr(ρ²)=1) yielding a mixed subsystem (Tr(ρ_A²)&lt;1) is the definitive signature of entanglement.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Subsystem A */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-slate-800">Subsystem A: ρ_A = Tr_B(ρ_AB)</span>
                      <span className="font-mono text-blue-700 bg-blue-100/70 px-2 py-0.5 rounded font-bold">
                        Purity: {result.purity_subsystem_A?.toFixed(4)}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono">
                      {result.reduced_density_matrix_A.map((row, rIdx) =>
                        row.map((cell, cIdx) => (
                          <div key={`${rIdx}-${cIdx}`} className="p-2 bg-white rounded border border-slate-200">
                            <span className="font-bold">{cell.real.toFixed(3)}</span>
                          </div>
                        ))
                      )}
                    </div>
                    <span className="text-[10px] text-slate-500 block">
                      {result.purity_subsystem_A && result.purity_subsystem_A < 0.99
                        ? "⚠️ Subsystem is mixed despite pure composite system → Entangled state"
                        : "✓ Subsystem is pure → Product/Separable state"}
                    </span>
                  </div>

                  {/* Subsystem B */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-slate-800">Subsystem B: ρ_B = Tr_A(ρ_AB)</span>
                      <span className="font-mono text-emerald-700 bg-emerald-100/70 px-2 py-0.5 rounded font-bold">
                        Purity: {result.purity_subsystem_B?.toFixed(4)}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono">
                      {result.reduced_density_matrix_B?.map((row, rIdx) =>
                        row.map((cell, cIdx) => (
                          <div key={`${rIdx}-${cIdx}`} className="p-2 bg-white rounded border border-slate-200">
                            <span className="font-bold">{cell.real.toFixed(3)}</span>
                          </div>
                        ))
                      )}
                    </div>
                    <span className="text-[10px] text-slate-500 block">
                      Reduced state of the second qubit tracing over qubit 0
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
