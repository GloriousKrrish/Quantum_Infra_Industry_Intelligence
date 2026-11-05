import { useState, useEffect } from "react";
import {
  Sparkles,
  GitMerge,
  Play,
  RotateCcw,
  CheckCircle2,
  Info,
  Layers,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { CircuitSimulateResponse } from "../../lib/api";
import { simulateQuantumCircuit } from "../../lib/api";
import BlochSphere3D from "./BlochSphere3D";

const BELL_STATES = [
  {
    id: "phi_plus",
    name: "|Φ+⟩ Bell State",
    formula: "|\\Phi^+\\rangle = \\frac{|00\\rangle + |11\\rangle}{\\sqrt{2}}",
    circuit: [
      { gate: "H", targets: [0], controls: [] },
      { gate: "CX", targets: [1], controls: [0] },
    ],
    correlation: "Perfect positive correlation: whenever q₀=0, q₁=0; whenever q₀=1, q₁=1.",
    purity: 0.5,
  },
  {
    id: "phi_minus",
    name: "|Φ−⟩ Bell State",
    formula: "|\\Phi^-\\rangle = \\frac{|00\\rangle - |11\\rangle}{\\sqrt{2}}",
    circuit: [
      { gate: "X", targets: [0], controls: [] },
      { gate: "H", targets: [0], controls: [] },
      { gate: "CX", targets: [1], controls: [0] },
    ],
    correlation: "Perfect positive correlation with negative phase on |11⟩.",
    purity: 0.5,
  },
  {
    id: "psi_plus",
    name: "|Ψ+⟩ Bell State",
    formula: "|\\Psi^+\\rangle = \\frac{|01\\rangle + |10\\rangle}{\\sqrt{2}}",
    circuit: [
      { gate: "H", targets: [0], controls: [] },
      { gate: "X", targets: [1], controls: [] },
      { gate: "CX", targets: [1], controls: [0] },
    ],
    correlation: "Perfect anti-correlation: whenever q₀=0, q₁=1; whenever q₀=1, q₁=0.",
    purity: 0.5,
  },
  {
    id: "psi_minus",
    name: "|Ψ−⟩ Bell State (Singlet)",
    formula: "|\\Psi^-\\rangle = \\frac{|01\\rangle - |10\\rangle}{\\sqrt{2}}",
    circuit: [
      { gate: "X", targets: [0], controls: [] },
      { gate: "H", targets: [0], controls: [] },
      { gate: "X", targets: [1], controls: [] },
      { gate: "CX", targets: [1], controls: [0] },
    ],
    correlation: "Singlet anti-correlated state with zero total angular momentum (S=0).",
    purity: 0.5,
  },
];

export default function EntanglementLab() {
  const [selectedStateId, setSelectedStateId] = useState<string>("phi_plus");
  const [ghzQubits, setGhzQubits] = useState<number>(3);
  const [mode, setMode] = useState<"bell" | "ghz">("bell");

  const [simResult, setSimResult] = useState<CircuitSimulateResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [inspectedQubit, setInspectedQubit] = useState<number>(0);

  const activeBell = BELL_STATES.find((b) => b.id === selectedStateId) || BELL_STATES[0];

  const runEntanglementSim = async () => {
    setLoading(true);
    try {
      let ops = activeBell.circuit;
      let nQubits = 2;

      if (mode === "ghz") {
        nQubits = ghzQubits;
        ops = [{ gate: "H", targets: [0], controls: [] }];
        for (let i = 0; i < ghzQubits - 1; i++) {
          ops.push({ gate: "CX", targets: [i + 1], controls: [i] });
        }
      }

      const res = await simulateQuantumCircuit({
        num_qubits: nQubits,
        operations: ops,
        shots: 2048,
      });
      setSimResult(res);
      setInspectedQubit(0);
    } catch (err) {
      console.error("Entanglement simulation error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runEntanglementSim();
  }, [selectedStateId, mode, ghzQubits]);

  const blochInfo = simResult?.qubit_bloch_vectors?.[inspectedQubit];

  return (
    <div className="flex flex-col space-y-6">
      {/* ── Top Header & State Selector ───────────────────────────────── */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-600" />
              <h2 className="font-display text-base font-bold text-slate-900">
                Quantum Entanglement & Non-Locality Laboratory
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Prepare maximally entangled Bell states and multi-qubit GHZ states. Observe perfect measurement correlations and inspect mixed reduced density matrices.
            </p>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center rounded-xl bg-slate-100 p-1 text-xs font-bold">
            <button
              onClick={() => setMode("bell")}
              className={`rounded-lg px-3 py-1.5 transition-all ${
                mode === "bell" ? "bg-white text-blue-700 shadow-2xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              2-Qubit Bell States (4)
            </button>
            <button
              onClick={() => setMode("ghz")}
              className={`rounded-lg px-3 py-1.5 transition-all ${
                mode === "ghz" ? "bg-white text-purple-700 shadow-2xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              N-Qubit GHZ State
            </button>
          </div>
        </div>

        {/* State Selection Bar */}
        {mode === "bell" ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {BELL_STATES.map((b) => (
              <button
                key={b.id}
                onClick={() => setSelectedStateId(b.id)}
                className={`flex flex-col text-left rounded-xl p-3 border transition-all ${
                  selectedStateId === b.id
                    ? "border-blue-500 bg-blue-50/50 shadow-xs ring-1 ring-blue-500"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center justify-between font-bold text-xs text-slate-900 mb-1">
                  <span>{b.name}</span>
                  {selectedStateId === b.id && <CheckCircle2 className="h-3.5 w-3.5 text-blue-600" />}
                </div>
                <div className="font-mono text-[11px] text-blue-700 font-semibold mb-1">
                  {b.formula}
                </div>
                <p className="text-[10px] text-slate-500 line-clamp-2">
                  {b.correlation}
                </p>
              </button>
            ))}
          </div>
        ) : (
          <div className="flex items-center gap-4 text-xs font-medium bg-purple-50/50 p-4 rounded-xl border border-purple-100">
            <span className="font-bold text-purple-900">GHZ Qubit Count:</span>
            {[3, 4, 5, 6].map((n) => (
              <button
                key={n}
                onClick={() => setGhzQubits(n)}
                className={`rounded-lg px-3 py-1 font-mono text-xs font-bold transition-all ${
                  ghzQubits === n
                    ? "bg-purple-600 text-white shadow-xs"
                    : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                }`}
              >
                {n} Qubits (|{Array(n).fill("0").join("")}⟩ + |{Array(n).fill("1").join("")}⟩)/√2
              </button>
            ))}
          </div>
        )}
      </div>

      {/* ── Correlation Charts & Bloch Sphere Inspector ───────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Module A: Correlated Measurement Distribution */}
        <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Joint Measurement Correlation (2,048 Shots)
            </h3>
            <span className="text-[11px] font-mono text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-lg border border-emerald-200">
              Correlated Basis
            </span>
          </div>

          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={simResult?.measurements || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="bitstring" tick={{ fill: "#334155", fontSize: 11, fontFamily: "monospace" }} />
                <YAxis tick={{ fill: "#64748b", fontSize: 10 }} unit="%" />
                <Tooltip
                  formatter={(val: any, name: any, item: any) => [
                    `${val}% (${item.payload.count} shots)`,
                    "Measurement Probability",
                  ]}
                  contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                />
                <Bar dataKey="percentage" radius={[6, 6, 0, 0]}>
                  {simResult?.measurements.map((entry, index) => (
                    <Cell key={index} fill={entry.percentage > 10 ? "#2563eb" : "#cbd5e1"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-600 border border-slate-200/80">
            <b className="text-slate-800 block mb-0.5">Quantum Non-Locality Analysis:</b>
            Notice that only the correlated bitstrings appear in the measurement distribution (e.g. 50% |00⟩ and 50% |11⟩). The intermediate states (|01⟩ and |10⟩) have exact 0.0% probability.
          </div>
        </div>

        {/* Module B: Reduced Density Matrix & Bloch Sphere */}
        <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Qubit Reduced State ρ_k = Tr_others(ρ)
            </h3>

            {/* Qubit Selector */}
            <div className="flex items-center gap-1 font-mono text-xs">
              {Array.from({ length: mode === "bell" ? 2 : ghzQubits }).map((_, i) => (
                <button
                  key={i}
                  onClick={() => setInspectedQubit(i)}
                  className={`rounded-lg px-2 py-0.5 text-xs font-bold transition-all ${
                    inspectedQubit === i
                      ? "bg-blue-600 text-white shadow-2xs"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  q_{i}
                </button>
              ))}
            </div>
          </div>

          {blochInfo && (
            <BlochSphere3D
              blochVector={blochInfo.bloch_vector}
              purity={blochInfo.purity}
              stateClassification={blochInfo.state_classification}
              qubitLabel={`Qubit q_${inspectedQubit}`}
            />
          )}
        </div>
      </div>

      {/* ── Scientific Distinction Callout ───────────────────────────── */}
      <div className="rounded-2xl border border-blue-200 bg-blue-50/50 p-5 text-xs text-blue-900 space-y-2">
        <div className="flex items-center gap-2 font-bold text-sm text-blue-950">
          <Info className="h-4 w-4 text-blue-600" />
          Superposition vs. Entanglement: Crucial Scientific Distinction
        </div>
        <p className="leading-relaxed">
          <b>Superposition</b> is a single-particle property where a quantum state is a linear combination of basis vectors (|ψ⟩ = α|0⟩ + β|1⟩).
          Its state vector lies on the surface of the Bloch sphere (|r| = 1.00, Purity = 1.00).
        </p>
        <p className="leading-relaxed">
          <b>Entanglement</b> is a multi-particle property where the joint state |Ψ_AB⟩ cannot be factored into product states |ψ_A⟩ ⊗ |ψ_B⟩.
          When you inspect an individual entangled qubit by tracing out the rest of the register, it has <b>no pure single-qubit state</b>; its reduced density matrix is a mixed state inside the sphere (|r| = 0.00, Purity γ = 0.50).
        </p>
      </div>
    </div>
  );
}
