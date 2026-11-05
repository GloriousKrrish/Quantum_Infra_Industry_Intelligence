import { useState, useEffect } from "react";
import {
  Calculator,
  Compass,
  Layers,
  ChevronRight,
  Info,
  CheckCircle2,
  Atom,
} from "lucide-react";
import type { GateSpec, StateAmplitude } from "../../lib/api";
import { fetchQuantumGates } from "../../lib/api";

interface QuantumMathExplorerProps {
  statevector?: StateAmplitude[];
  numQubits?: number;
}

export default function QuantumMathExplorer({
  statevector = [],
  numQubits = 2,
}: QuantumMathExplorerProps) {
  const [gates, setGates] = useState<GateSpec[]>([]);
  const [selectedGateId, setSelectedGateId] = useState<string>("H");
  const [loadingGates, setLoadingGates] = useState<boolean>(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchQuantumGates();
        setGates(data);
        if (data.length > 0) setSelectedGateId(data[0].id);
      } catch (err) {
        console.error("Failed to fetch gates:", err);
      } finally {
        setLoadingGates(false);
      }
    }
    load();
  }, []);

  const selectedGate = gates.find((g) => g.id === selectedGateId) || gates[0];

  return (
    <div className="flex flex-col space-y-6">
      {/* ── Top Header ────────────────────────────────────────────────── */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex items-center gap-2 mb-1">
          <Calculator className="h-5 w-5 text-blue-600" />
          <h2 className="font-display text-base font-bold text-slate-900">
            Quantum Mathematical Foundations & Statevector Explorer
          </h2>
        </div>
        <p className="text-xs text-slate-500 max-w-3xl leading-relaxed">
          Inspect exact complex probability amplitudes, quantum phases, matrix unitaries, and the foundational relationship $P(|x\rangle) = |\alpha_x|^2$.
        </p>
      </div>

      {/* ── Statevector Amplitudes Table ──────────────────────────────── */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-display text-sm font-bold text-slate-900">
              Computational Basis Amplitudes: |ψ⟩ = ∑ αᵢ|i⟩
            </h3>
            <span className="text-[11px] text-slate-500 font-mono">
              Dimension: 2^{numQubits} = {Math.pow(2, numQubits)} Hilbert Space Orthogonal Basis Vectors
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-mono text-slate-600 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200">
              Qiskit Ordering: <b>|q_{numQubits - 1}…q₀⟩</b> (LSB rightmost = q₀)
            </span>
            <div className="flex items-center gap-1.5 text-xs font-mono text-emerald-700 bg-emerald-50 px-3 py-1 rounded-lg border border-emerald-200 font-bold">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Normalization: ∑|αᵢ|² = 1.0000
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold text-slate-600">
                <th className="py-2.5 px-3">State |i⟩</th>
                <th className="py-2.5 px-3">Bitstring</th>
                <th className="py-2.5 px-3">Complex Amplitude (α = a + bi)</th>
                <th className="py-2.5 px-3">Magnitude |α|</th>
                <th className="py-2.5 px-3">Phase Angle (rad / deg)</th>
                <th className="py-2.5 px-3">Measurement Prob (|α|²)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {statevector.map((amp) => {
                const hasProbability = amp.probability > 0.0001;
                return (
                  <tr
                    key={amp.index}
                    className={`transition-colors ${
                      hasProbability ? "bg-blue-50/20 font-medium" : "text-slate-400"
                    }`}
                  >
                    <td className="py-2.5 px-3 font-bold text-slate-900">{amp.ket}</td>
                    <td className="py-2.5 px-3 text-blue-700 font-semibold">{amp.bitstring}</td>
                    <td className="py-2.5 px-3">
                      {amp.real >= 0 ? "+" : ""}
                      {amp.real.toFixed(4)} {amp.imag >= 0 ? "+" : ""}
                      {amp.imag.toFixed(4)}i
                    </td>
                    <td className="py-2.5 px-3 font-bold text-slate-800">{amp.magnitude.toFixed(4)}</td>
                    <td className="py-2.5 px-3">
                      {amp.phase_rad.toFixed(3)} rad ({amp.phase_deg.toFixed(1)}°)
                    </td>
                    <td className="py-2.5 px-3 font-bold">
                      <div className="flex items-center gap-2">
                        <div className="w-20 bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${amp.probability * 100}%` }}
                          />
                        </div>
                        <span className="text-blue-700 font-mono text-xs">
                          {(amp.probability * 100).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Gate Unitary Matrix Viewer ─────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Gate Selection Menu */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
          <span className="text-xs font-bold text-slate-900 block border-b border-slate-100 pb-2">
            Unitary Gate Catalog
          </span>
          <div className="grid grid-cols-2 gap-2">
            {gates.map((g) => (
              <button
                key={g.id}
                onClick={() => setSelectedGateId(g.id)}
                className={`flex items-center justify-between rounded-xl px-3 py-2 text-xs font-bold border transition-all ${
                  selectedGateId === g.id
                    ? "border-blue-600 bg-blue-50 text-blue-700 shadow-2xs"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                <span>{g.symbol || g.id}</span>
                <span className="text-[10px] text-slate-400 font-normal">{g.num_qubits}Q</span>
              </button>
            ))}
          </div>
        </div>

        {/* Matrix Inspector */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
          {selectedGate && (
            <>
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h3 className="font-display text-sm font-bold text-slate-900">
                    {selectedGate.name} ({selectedGate.symbol})
                  </h3>
                  <span className="text-xs text-slate-500">{selectedGate.description}</span>
                </div>
                <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-mono font-semibold text-slate-700">
                  {selectedGate.num_qubits} Qubit{selectedGate.num_qubits > 1 ? "s" : ""}
                </span>
              </div>

              {/* LaTeX Formulation */}
              <div className="rounded-xl bg-slate-50 p-4 border border-slate-200/80 font-mono text-xs text-slate-800 space-y-1">
                <span className="text-[10px] font-semibold text-slate-400 uppercase block">Matrix Definition:</span>
                <p className="text-sm font-bold text-blue-900">{selectedGate.latex}</p>
                <p className="text-xs text-slate-600 mt-1"><b>Physical Effect:</b> {selectedGate.effect}</p>
              </div>

              {/* Numerical Matrix Grid */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-700">Numerical Unitary Elements U:</span>
                <div className="overflow-x-auto rounded-xl border border-slate-200 bg-slate-50/50 p-3">
                  <table className="font-mono text-xs text-center border-separate border-spacing-2">
                    <tbody>
                      {selectedGate.matrix.map((row, rIdx) => (
                        <tr key={rIdx}>
                          {row.map((val, cIdx) => (
                            <td
                              key={cIdx}
                              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-800 font-semibold shadow-2xs min-w-[70px]"
                            >
                              {val.real !== 0 && val.imag !== 0
                                ? `${val.real.toFixed(2)} + ${val.imag.toFixed(2)}i`
                                : val.imag !== 0
                                ? `${val.imag.toFixed(2)}i`
                                : val.real.toFixed(2)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

