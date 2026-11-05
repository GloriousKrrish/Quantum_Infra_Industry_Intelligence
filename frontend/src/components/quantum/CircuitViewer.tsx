import { useState } from "react";
import { Cpu } from "lucide-react";

interface CircuitViewerProps {
  pLayers?: number;
  gamma?: number;
  beta?: number;
  optimalParameters?: {
    gammas: number[];
    betas: number[];
  };
  qubitLabels?: string[];
}

export default function CircuitViewer({
  pLayers = 2,
  gamma = 0.6827,
  beta = 0.4179,
  optimalParameters,
  qubitLabels,
}: CircuitViewerProps) {
  const [selectedGate, setSelectedGate] = useState<string | null>(null);

  const g1 = optimalParameters?.gammas?.[0] ?? gamma;
  const b1 = optimalParameters?.betas?.[0] ?? beta;
  const g2 = optimalParameters?.gammas?.[1] ?? 0.3415;
  const b2 = optimalParameters?.betas?.[1] ?? 0.2089;

  const defaultNames = [
    "q₀ (Wagholi East)",
    "q₁ (Chakan Industrial)",
    "q₂ (Hinjawadi Phase 3)",
    "q₃ (Talegaon Dabhade)",
    "q₄ (Hadapsar Extension)",
    "q₅ (Pirangut Corridor)",
    "q₆ (Kharadi IT Hub)",
    "q₇ (Mamurdi PCMC)",
  ];

  const labels = qubitLabels && qubitLabels.length >= 8
    ? qubitLabels.map((name, i) => `q${i} (${name})`)
    : defaultNames;

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
            p = {pLayers} Layers
          </span>
          <span>8 Qubits</span>
          <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
            &gamma;*={g1.toFixed(3)}, &beta;*={b1.toFixed(3)}
          </span>
        </div>
      </div>

      {/* Circuit Canvas Container */}
      <div className="overflow-x-auto pb-3">
        <div className="min-w-[680px] space-y-3 font-mono text-xs">
          {labels.map((label, idx) => (
            <div key={idx} className="flex items-center gap-2">
              {/* Qubit Label */}
              <div className="w-32 shrink-0 text-xs font-semibold text-slate-700 truncate" title={label}>
                {label}
              </div>

              {/* Wire with Gates */}
              <div className="relative flex flex-1 items-center">
                {/* Wire Line */}
                <div className="absolute inset-x-0 h-[2px] bg-slate-200" />

                {/* Initial State */}
                <span className="relative z-10 mr-2 text-xs font-bold text-slate-400 bg-white px-1">
                  |0⟩
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
                      `Cost Unitary U_C(γ₁=${g1.toFixed(
                        4
                      )}): Implements exp(-i γ₁ H_C) encoding land utility and budget constraint penalty.`
                    )
                  }
                  className="relative z-10 mx-3 flex h-8 flex-1 max-w-[130px] cursor-pointer items-center justify-center rounded-lg border border-indigo-200 bg-indigo-50 px-2 text-xs font-semibold text-indigo-700 transition-transform hover:scale-105"
                  title="Cost Hamiltonian Unitary"
                >
                  e<sup>-i({g1.toFixed(2)})H<sub>C</sub></sup>
                </div>

                {/* Step 3: Mixer Unitary Block U_M(beta) */}
                <div
                  onClick={() =>
                    setSelectedGate(
                      `Mixer Unitary U_M(β₁=${b1.toFixed(
                        4
                      )}): Transverse field rotation exp(-i β₁ ∑ X_i) driving quantum interference.`
                    )
                  }
                  className="relative z-10 mx-3 flex h-8 w-20 cursor-pointer items-center justify-center rounded-lg border border-amber-200 bg-amber-50 text-xs font-semibold text-amber-700 transition-transform hover:scale-105"
                  title="Mixer Unitary: Transverse X"
                >
                  R<sub>X</sub>({(2 * b1).toFixed(2)})
                </div>

                {/* Repeat Layer for p=2 */}
                {pLayers > 1 && (
                  <>
                    <div
                      onClick={() =>
                        setSelectedGate(
                          `Layer 2 Cost Unitary U_C(γ₂=${g2.toFixed(4)}) from Scipy COBYLA optimizer.`
                        )
                      }
                      className="relative z-10 mx-2 flex h-8 flex-1 max-w-[110px] cursor-pointer items-center justify-center rounded-lg border border-indigo-200 bg-indigo-50 px-1 text-[11px] text-indigo-600 font-medium"
                      title="Layer 2 Cost Unitary"
                    >
                      e<sup>-i({g2.toFixed(2)})H<sub>C</sub></sup>
                    </div>
                    <div
                      onClick={() =>
                        setSelectedGate(
                          `Layer 2 Mixer Unitary U_M(β₂=${b2.toFixed(4)}) from Scipy COBYLA optimizer.`
                        )
                      }
                      className="relative z-10 mx-2 flex h-8 w-18 cursor-pointer items-center justify-center rounded-lg border border-amber-200 bg-amber-50 text-[11px] text-amber-600 font-medium"
                      title="Layer 2 Mixer Unitary"
                    >
                      R<sub>X</sub>({(2 * b2).toFixed(2)})
                    </div>
                  </>
                )}

                {/* Measurement Meter */}
                <div
                  onClick={() =>
                    setSelectedGate(
                      "Measurement Meter: Samples continuous state into discrete classical bitstring over 4,096 shots."
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
