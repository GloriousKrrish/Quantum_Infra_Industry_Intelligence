import React, { useState, useEffect } from "react";
import {
  Scan,
  Play,
  RotateCcw,
  Sparkles,
  Info,
  CheckCircle2,
  Sliders,
  Check,
  Eye,
} from "lucide-react";
import {
  reconstructTomography,
  type TomographyResponse,
  type GateOperation,
} from "../../lib/api";

const STATE_PRESETS: Array<{ id: string; name: string; ops: GateOperation[]; desc: string }> = [
  { id: "zero", name: "|0⟩ Ground State", ops: [], desc: "⟨σ_z⟩ = +1.0, ⟨σ_x⟩ = 0, ⟨σ_y⟩ = 0" },
  { id: "one", name: "|1⟩ Excited State", ops: [{ gate: "X", targets: [0] }], desc: "⟨σ_z⟩ = -1.0, ⟨σ_x⟩ = 0, ⟨σ_y⟩ = 0" },
  { id: "plus", name: "|+⟩ Superposition", ops: [{ gate: "H", targets: [0] }], desc: "⟨σ_x⟩ = +1.0, ⟨σ_z⟩ = 0, ⟨σ_y⟩ = 0" },
  { id: "plus_i", name: "|+i⟩ Phase State", ops: [{ gate: "H", targets: [0] }, { gate: "S", targets: [0] }], desc: "⟨σ_y⟩ = +1.0, ⟨σ_x⟩ = 0, ⟨σ_z⟩ = 0" },
  { id: "t_state", name: "T-Gate State (H + T)", ops: [{ gate: "H", targets: [0] }, { gate: "T", targets: [0] }], desc: "Non-Clifford magic state on the equatorial plane" },
];

export default function TomographyLab() {
  const [selectedPresetId, setSelectedPresetId] = useState<string>("plus_i");
  const [shots, setShots] = useState<number>(2048);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<TomographyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const activePreset = STATE_PRESETS.find((p) => p.id === selectedPresetId) || STATE_PRESETS[0];

  const handleReconstruct = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await reconstructTomography({
        operations: activePreset.ops,
        shots,
      });
      setResult(res);
    } catch (err: any) {
      console.error("Tomography error:", err);
      setError(err.response?.data?.detail || err.message || "Failed to reconstruct state tomography.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleReconstruct();
  }, [selectedPresetId, shots]);

  return (
    <div className="space-y-6">
      {/* Control Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Scan className="h-5 w-5 text-blue-600" />
              <h2 className="font-display text-lg font-bold text-slate-900">
                Quantum State Tomography (QST)
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Reconstruct an unknown density matrix ρ directly from experimental Pauli measurements in the X, Y, and Z bases: ρ = ½(I + ⟨σ_x⟩σ_x + ⟨σ_y⟩σ_y + ⟨σ_z⟩σ_z).
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`font-mono text-xs font-bold px-3 py-1.5 rounded-xl border ${
                result && result.fidelity_reconstructed > 0.95
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-blue-50 text-blue-700 border-blue-200"
              }`}
            >
              FIDELITY: {result ? `${(result.fidelity_reconstructed * 100).toFixed(2)}%` : "..."}
            </span>
          </div>
        </div>

        {/* State Preset Selector */}
        <div className="mt-6">
          <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            Target Quantum State to Reconstruct
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3 mt-2">
            {STATE_PRESETS.map((p) => (
              <button
                key={p.id}
                onClick={() => setSelectedPresetId(p.id)}
                className={`p-3 rounded-xl border text-left transition-all text-xs ${
                  selectedPresetId === p.id
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

        {/* Shots Slider */}
        <div className="mt-4 max-w-xs">
          <div className="flex justify-between items-center text-xs">
            <label className="font-bold uppercase tracking-wider text-slate-500">
              Shots per Pauli Basis
            </label>
            <span className="font-mono text-slate-700 font-bold">{shots} shots</span>
          </div>
          <input
            type="range"
            min="512"
            max="4096"
            step="512"
            value={shots}
            onChange={(e) => setShots(parseInt(e.target.value))}
            className="w-full accent-blue-600 mt-2 cursor-pointer"
          />
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Card 1: Pauli Measurement Expectations */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4 text-xs">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Pauli Basis Expectation Values
            </h3>

            <div className="space-y-3">
              {/* Pauli X */}
              <div className="p-3 rounded-xl border border-blue-100 bg-blue-50/50 space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-blue-900">⟨σ_x⟩ (Hadamard Basis):</span>
                  <span className="font-mono font-bold text-blue-700">
                    {result.pauli_measurements.x.expected_val.toFixed(4)}
                    {result.pauli_measurements.x.std_err !== undefined && (
                      <span className="text-[10px] text-slate-500 font-normal ml-1">
                        ±{result.pauli_measurements.x.std_err.toFixed(3)}
                      </span>
                    )}
                  </span>
                </div>
                <div className="flex justify-between text-[10px] text-blue-800 font-mono">
                  <span>P(|+⟩) = {(result.pauli_measurements.x.prob_plus * 100).toFixed(1)}%</span>
                  <span>P(|-⟩) = {(result.pauli_measurements.x.prob_minus * 100).toFixed(1)}%</span>
                </div>
              </div>

              {/* Pauli Y */}
              <div className="p-3 rounded-xl border border-emerald-100 bg-emerald-50/50 space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-emerald-900">⟨σ_y⟩ (Phase Basis S†H):</span>
                  <span className="font-mono font-bold text-emerald-700">
                    {result.pauli_measurements.y.expected_val.toFixed(4)}
                    {result.pauli_measurements.y.std_err !== undefined && (
                      <span className="text-[10px] text-slate-500 font-normal ml-1">
                        ±{result.pauli_measurements.y.std_err.toFixed(3)}
                      </span>
                    )}
                  </span>
                </div>
                <div className="flex justify-between text-[10px] text-emerald-800 font-mono">
                  <span>P(|+i⟩) = {(result.pauli_measurements.y.prob_plus_i * 100).toFixed(1)}%</span>
                  <span>P(|-i⟩) = {(result.pauli_measurements.y.prob_minus_i * 100).toFixed(1)}%</span>
                </div>
              </div>

              {/* Pauli Z */}
              <div className="p-3 rounded-xl border border-purple-100 bg-purple-50/50 space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-purple-900">⟨σ_z⟩ (Computational Basis):</span>
                  <span className="font-mono font-bold text-purple-700">
                    {result.pauli_measurements.z.expected_val.toFixed(4)}
                    {result.pauli_measurements.z.std_err !== undefined && (
                      <span className="text-[10px] text-slate-500 font-normal ml-1">
                        ±{result.pauli_measurements.z.std_err.toFixed(3)}
                      </span>
                    )}
                  </span>
                </div>
                <div className="flex justify-between text-[10px] text-purple-800 font-mono">
                  <span>P(|0⟩) = {(result.pauli_measurements.z.prob_0 * 100).toFixed(1)}%</span>
                  <span>P(|1⟩) = {(result.pauli_measurements.z.prob_1 * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Bloch Vector Comparison */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4 text-xs">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Bloch Vector: Reconstructed vs. True
            </h3>

            <div className="p-3 rounded-xl border border-slate-100 bg-slate-50 space-y-2">
              <span className="text-slate-600 font-bold block">Reconstructed Coordinates (QST):</span>
              <div className="grid grid-cols-3 gap-2 text-center font-mono">
                <div className="p-2 bg-white rounded border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">r_x</span>
                  <span className="font-bold text-slate-800">{result.reconstructed_bloch_vector.x}</span>
                </div>
                <div className="p-2 bg-white rounded border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">r_y</span>
                  <span className="font-bold text-slate-800">{result.reconstructed_bloch_vector.y}</span>
                </div>
                <div className="p-2 bg-white rounded border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">r_z</span>
                  <span className="font-bold text-slate-800">{result.reconstructed_bloch_vector.z}</span>
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl border border-slate-100 bg-slate-50 space-y-2">
              <span className="text-slate-600 font-bold block">Theoretical True Coordinates:</span>
              <div className="grid grid-cols-3 gap-2 text-center font-mono text-slate-500">
                <div className="p-2 bg-white rounded border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">r_x</span>
                  <span>{result.true_bloch_vector.x}</span>
                </div>
                <div className="p-2 bg-white rounded border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">r_y</span>
                  <span>{result.true_bloch_vector.y}</span>
                </div>
                <div className="p-2 bg-white rounded border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">r_z</span>
                  <span>{result.true_bloch_vector.z}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 font-mono">
              <span className="text-emerald-900 font-bold">Trace Distance D:</span>
              <span className="font-bold text-emerald-700">{result.trace_distance.toFixed(4)}</span>
            </div>
          </div>

          {/* Card 3: Reconstructed Density Matrix */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4 text-xs">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Reconstructed Density Matrix ρ_rec
            </h3>

            <div className="p-3 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
              <div className="grid grid-cols-2 gap-2 text-center font-mono">
                {result.reconstructed_density_matrix.map((row, rIdx) =>
                  row.map((cell, cIdx) => (
                    <div key={`${rIdx}-${cIdx}`} className="p-3 bg-white rounded-lg border border-slate-200">
                      <div className="font-bold text-slate-800">{cell.real.toFixed(3)}</div>
                      {Math.abs(cell.imag) > 1e-3 && (
                        <div className="text-[10px] text-purple-600">
                          {cell.imag >= 0 ? "+" : ""}{cell.imag.toFixed(3)}i
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="space-y-2 pt-1 font-mono text-xs">
              <div className="flex justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500">Reconstructed Purity:</span>
                <span className="font-bold text-blue-700">{result.purity_reconstructed.toFixed(4)}</span>
              </div>
              <div className="flex justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-500">Reconstruction Fidelity:</span>
                <span className="font-bold text-emerald-700">{(result.fidelity_reconstructed * 100).toFixed(2)}%</span>
              </div>
              {result.fidelity_raw !== undefined && result.is_raw_psd === false && (
                <div className="flex justify-between p-2 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-[11px]">
                  <span>Raw (Pre-Projection) Fidelity:</span>
                  <span className="font-bold">{(result.fidelity_raw * 100).toFixed(2)}%</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Statistical Notice Banner */}
      {result?.statistical_notice && (
        <div className="rounded-2xl border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-900 flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold uppercase tracking-wider text-[11px] text-blue-800">
              Statistical Sampling Notice
            </span>
            <p className="leading-relaxed text-[11px]">
              {result.statistical_notice}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

