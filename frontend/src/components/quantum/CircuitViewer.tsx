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
    <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-950/80 p-5 backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-cyan-400" />
          <h3 className="font-display text-sm font-semibold text-white">
            QAOA Parameterized Quantum Circuit Diagram
          </h3>
        </div>
        <div className="flex items-center gap-3 font-mono text-[11px] text-slate-400">
          <span className="rounded bg-cyan-500/10 px-2 py-0.5 text-cyan-400 border border-cyan-500/20">
            p = {pLayers} Layers
          </span>
          <span>8 Qubits</span>
          <span>28 CNOT Entanglers</span>
        </div>
      </div>

      {/* Circuit Canvas Scrollable Container */}
      <div className="overflow-x-auto pb-2">
        <div className="min-w-[680px] space-y-2.5 font-mono text-xs">
          {qubits.map((q) => (
            <div key={q.id} className="flex items-center gap-2">
              {/* Qubit Label */}
              <div className="w-28 shrink-0 text-[11px] text-slate-400 truncate">
                {q.label}
              </div>

              {/* Wire with Gates */}
              <div className="relative flex flex-1 items-center">
                {/* Horizontal Wire Line */}
                <div className="absolute inset-x-0 h-[1.5px] bg-slate-800" />

                {/* Initial State */}
                <span className="relative z-10 mr-2 text-[11px] text-slate-500 bg-slate-950 px-1">
                  {q.initial}
                </span>

                {/* Step 1: Hadamard Gate */}
                <div
                  onClick={() => setSelectedGate("Hadamard Gate (H): Places qubit into uniform superposition (|0⟩ + |1⟩)/√2.")}
                  className="relative z-10 mx-2 flex h-7 w-7 cursor-pointer items-center justify-center rounded border border-cyan-500/40 bg-cyan-950/80 text-[11px] font-bold text-cyan-300 shadow-sm transition-transform hover:scale-110 active:scale-95"
                  title="Hadamard Gate: Superposition"
                >
                  H
                </div>

                {/* Step 2: Cost Unitary Block U_C(gamma) */}
                <div
                  onClick={() =>
                    setSelectedGate(
                      `Cost Unitary U_C(γ=${gamma.toFixed(2)}): Implements exp(-i γ H_P) encoding land utility and budget constraint penalty.`
                    )
                  }
                  className="relative z-10 mx-3 flex h-7 flex-1 max-w-[130px] cursor-pointer items-center justify-center rounded border border-indigo-500/40 bg-indigo-950/80 px-2 text-[10px] font-semibold text-indigo-300 transition-transform hover:scale-105"
                  title="Cost Hamiltonian Unitary"
                >
                  e<sup>-i&gamma;H<sub>P</sub></sup>
                </div>

                {/* Step 3: Mixer Unitary Block U_M(beta) */}
                <div
                  onClick={() =>
                    setSelectedGate(
                      `Mixer Unitary U_M(β=${beta.toFixed(2)}): Transverse field rotation exp(-i β ∑ X_i) driving quantum interference.`
                    )
                  }
                  className="relative z-10 mx-3 flex h-7 w-16 cursor-pointer items-center justify-center rounded border border-amber-500/40 bg-amber-950/80 text-[10px] font-semibold text-amber-300 transition-transform hover:scale-105"
                  title="Mixer Unitary: Transverse X"
                >
                  R<sub>X</sub>(2&beta;)
                </div>

                {/* Repeat Layer for p=2 */}
                {pLayers > 1 && (
                  <>
                    <div
                      className="relative z-10 mx-2 flex h-7 flex-1 max-w-[100px] cursor-pointer items-center justify-center rounded border border-indigo-500/30 bg-indigo-950/40 px-1 text-[9px] text-indigo-400"
                      title="Layer 2 Cost Unitary"
                    >
                      e<sup>-i&gamma;₂H<sub>P</sub></sup>
                    </div>
                    <div
                      className="relative z-10 mx-2 flex h-7 w-14 cursor-pointer items-center justify-center rounded border border-amber-500/30 bg-amber-950/40 text-[9px] text-amber-400"
                      title="Layer 2 Mixer Unitary"
                    >
                      R<sub>X</sub>(2&beta;₂)
                    </div>
                  </>
                )}

                {/* Measurement Meter */}
                <div
                  onClick={() => setSelectedGate("Measurement Gate: Projects quantum state into classical bit register c[i].")}
                  className="relative z-10 ml-auto flex h-7 w-8 cursor-pointer items-center justify-center rounded border border-slate-700 bg-slate-900 text-[10px] font-bold text-slate-300 hover:text-cyan-400"
                  title="Measurement Meter"
                >
                  [M]
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Gate Explainer Banner */}
      {selectedGate && (
        <div className="mt-3 rounded-lg border border-cyan-500/30 bg-cyan-950/30 p-2.5 text-xs text-cyan-200 font-mono animate-fadeIn">
          {selectedGate}
        </div>
      )}
    </div>
  );
}
