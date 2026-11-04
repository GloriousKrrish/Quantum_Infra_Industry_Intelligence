import { useState } from "react";
import { Cpu } from "lucide-react";

interface CircuitViewerProps {
  pLayers?: number;
  gamma?: number;
  beta?: number;
}

export default function CircuitViewer({
  pLayers = 2,
  gamma = 0.785,
  beta = 0.392,
}: CircuitViewerProps) {
  const [selectedGate, setSelectedGate] = useState<string | null>(null);

  const qubits = [
    { id: 0, label: "q₀ (Hinjewadi)", initial: "|0⟩" },
    { id: 1, label: "q₁ (Wakad)", initial: "|0⟩" },
    { id: 2, label: "q₂ (Baner)", initial: "|0⟩" },
    { id: 3, label: "q₃ (Kharadi)", initial: "|0⟩" },
    { id: 4, label: "q₄ (Wagholi)", initial: "|0⟩" },
    { id: 5, label: "q₅ (Hadapsar)", initial: "|0⟩" },
    { id: 6, label: "q₆ (Viman Ngr)", initial: "|0⟩" },
    { id: 7, label: "q₇ (Chakan)", initial: "|0⟩" },
  ];

  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-blue-600" />
          <h3 className="font-display text-sm font-bold text-slate-900">
            QAOA Parameterized Quantum Circuit Architecture
          </h3>
        </div>
        <div className="flex items-center gap-3 font-mono text-xs text-slate-500">
          <span className="rounded-lg bg-blue-50 px-2.5 py-0.5 text-blue-700 font-semibold border border-blue-100">
            p = {pLayers} Alternating Layers
          </span>
          <span>8 Qubits</span>
          <span>28 CNOT Entanglers</span>
        </div>
      </div>

      {/* Circuit Canvas Container */}
      <div className="overflow-x-auto pb-3">
        <div className="min-w-[680px] space-y-3 font-mono text-xs">
          {qubits.map((q) => (
            <div key={q.id} className="flex items-center gap-2">
              {/* Qubit Label */}
              <div className="w-28 shrink-0 text-xs font-semibold text-slate-700 truncate">
                {q.label}
              </div>

              {/* Wire with Gates */}
              <div className="relative flex flex-1 items-center">
                {/* Wire Line */}
                <div className="absolute inset-x-0 h-[2px] bg-slate-200" />

                {/* Initial State */}
                <span className="relative z-10 mr-2 text-xs font-bold text-slate-400 bg-white px-1">
                  {q.initial}
                </span>

                {/* Step 1: Hadamard Gate */}
                <div
                  onClick={() =>
                    setSelectedGate(
                      "Hadamard Gate (H): Places qubit into uniform superposition (|0⟩ + |1⟩)/√2."
                    )
                  }
                  className="relative z-10 mx-2 flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg border border-blue-300 bg-blue-50 text-xs font-bold text-blue-700 shadow-xs transition-transform hover:scale-110 active:scale-95"
                  title="Hadamard Gate: Superposition"
                >
                  H
                </div>

                {/* Step 2: Cost Unitary Block U_C(gamma) */}
                <div
                  onClick={() =>
                    setSelectedGate(
                      `Cost Unitary U_C(γ=${gamma.toFixed(
                        2
                      )}): Implements exp(-i γ H_P) encoding land utility and budget constraint penalty.`
                    )
                  }
                  className="relative z-10 mx-3 flex h-8 flex-1 max-w-[130px] cursor-pointer items-center justify-center rounded-lg border border-indigo-200 bg-indigo-50 px-2 text-xs font-semibold text-indigo-700 transition-transform hover:scale-105"
                  title="Cost Hamiltonian Unitary"
                >
                  e<sup>-i&gamma;H<sub>P</sub></sup>
                </div>

                {/* Step 3: Mixer Unitary Block U_M(beta) */}
                <div
                  onClick={() =>
                    setSelectedGate(
                      `Mixer Unitary U_M(β=${beta.toFixed(
                        2
                      )}): Transverse field rotation exp(-i β ∑ X_i) driving quantum interference.`
                    )
                  }
                  className="relative z-10 mx-3 flex h-8 w-16 cursor-pointer items-center justify-center rounded-lg border border-amber-200 bg-amber-50 text-xs font-semibold text-amber-700 transition-transform hover:scale-105"
                  title="Mixer Unitary: Transverse X"
                >
                  R<sub>X</sub>(2&beta;)
                </div>

                {/* Repeat Layer for p=2 */}
                {pLayers > 1 && (
                  <>
                    <div
                      className="relative z-10 mx-2 flex h-8 flex-1 max-w-[100px] cursor-pointer items-center justify-center rounded-lg border border-indigo-200 bg-indigo-50 px-1 text-[11px] text-indigo-600 font-medium"
                      title="Layer 2 Cost Unitary"
                    >
                      e<sup>-i&gamma;₂H<sub>P</sub></sup>
                    </div>
                    <div
                      className="relative z-10 mx-2 flex h-8 w-14 cursor-pointer items-center justify-center rounded-lg border border-amber-200 bg-amber-50 text-[11px] text-amber-600 font-medium"
                      title="Layer 2 Mixer Unitary"
                    >
                      R<sub>X</sub>(2&beta;₂)
                    </div>
                  </>
                )}

                {/* Measurement Meter */}
                <div
                  onClick={() =>
                    setSelectedGate(
                      "Measurement Meter: Collapses continuous state amplitudes into discrete classical bit values."
                    )
                  }
                  className="relative z-10 ml-auto flex h-8 w-9 cursor-pointer items-center justify-center rounded-lg border border-slate-300 bg-slate-100 text-xs font-bold text-slate-700 hover:bg-slate-200 transition-colors"
                  title="Measurement Meter"
                >
                  [M]
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Explainer Banner */}
      {selectedGate && (
        <div className="mt-3 rounded-xl border border-blue-200 bg-blue-50/80 p-3 text-xs text-blue-900 font-mono">
          {selectedGate}
        </div>
      )}
    </div>
  );
}
