import { useState } from "react";
import {
  Play,
  RotateCcw,
  Plus,
  Trash2,
  Sparkles,
  Cpu,
  Layers,
  Sliders,
  Settings,
  HelpCircle,
} from "lucide-react";
import type { GateOperation, CircuitSimulateResponse } from "../../lib/api";
import { simulateQuantumCircuit } from "../../lib/api";

interface CircuitBuilderProps {
  onSimulationComplete: (result: CircuitSimulateResponse) => void;
  initialQubits?: number;
  initialOps?: GateOperation[];
}

const AVAILABLE_GATES = [
  { id: "H", name: "Hadamard", color: "bg-blue-50 border-blue-300 text-blue-700", qubits: 1 },
  { id: "X", name: "Pauli-X (NOT)", color: "bg-emerald-50 border-emerald-300 text-emerald-700", qubits: 1 },
  { id: "Y", name: "Pauli-Y", color: "bg-teal-50 border-teal-300 text-teal-700", qubits: 1 },
  { id: "Z", name: "Pauli-Z (Phase)", color: "bg-indigo-50 border-indigo-300 text-indigo-700", qubits: 1 },
  { id: "S", name: "Phase (S)", color: "bg-cyan-50 border-cyan-300 text-cyan-700", qubits: 1 },
  { id: "T", name: "T Gate", color: "bg-sky-50 border-sky-300 text-sky-700", qubits: 1 },
  { id: "RX", name: "Rx(θ)", color: "bg-amber-50 border-amber-300 text-amber-700", qubits: 1, parameterized: true },
  { id: "RY", name: "Ry(θ)", color: "bg-amber-50 border-amber-300 text-amber-700", qubits: 1, parameterized: true },
  { id: "RZ", name: "Rz(φ)", color: "bg-amber-50 border-amber-300 text-amber-700", qubits: 1, parameterized: true },
  { id: "CX", name: "CNOT (CX)", color: "bg-purple-50 border-purple-300 text-purple-700", qubits: 2, isControlled: true },
  { id: "CZ", name: "Controlled-Z", color: "bg-purple-50 border-purple-300 text-purple-700", qubits: 2, isControlled: true },
  { id: "SWAP", name: "SWAP", color: "bg-rose-50 border-rose-300 text-rose-700", qubits: 2 },
  { id: "CCX", name: "Toffoli (CCX)", color: "bg-violet-50 border-violet-300 text-violet-700", qubits: 3, isControlled: true },
];

export default function CircuitBuilder({
  onSimulationComplete,
  initialQubits = 2,
  initialOps = [
    { gate: "H", targets: [0], controls: [] },
    { gate: "CX", targets: [1], controls: [0] },
  ],
}: CircuitBuilderProps) {
  const [numQubits, setNumQubits] = useState<number>(initialQubits);
  const [operations, setOperations] = useState<GateOperation[]>(initialOps);
  const [shots, setShots] = useState<number>(1024);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Add Gate Dialog State
  const [selectedGateId, setSelectedGateId] = useState<string>("H");
  const [targetQubit, setTargetQubit] = useState<number>(0);
  const [controlQubit, setControlQubit] = useState<number>(1);
  const [controlQubit2, setControlQubit2] = useState<number>(0);
  const [paramAngle, setParamAngle] = useState<number>(1.5708); // pi / 2

  const selectedGateMeta = AVAILABLE_GATES.find((g) => g.id === selectedGateId) || AVAILABLE_GATES[0];

  const handleAddGate = () => {
    setErrorMsg(null);
    const gateId = selectedGateMeta.id;
    let newOp: GateOperation;

    if (gateId === "CX" || gateId === "CZ") {
      if (controlQubit === targetQubit) {
        setErrorMsg("Control and target qubits cannot be identical.");
        return;
      }
      newOp = { gate: gateId, targets: [targetQubit], controls: [controlQubit] };
    } else if (gateId === "SWAP") {
      if (controlQubit === targetQubit) {
        setErrorMsg("SWAP requires two distinct qubits.");
        return;
      }
      newOp = { gate: gateId, targets: [targetQubit, controlQubit], controls: [] };
    } else if (gateId === "CCX") {
      if (new Set([controlQubit, controlQubit2, targetQubit]).size !== 3) {
        setErrorMsg("Toffoli requires 3 distinct qubits (2 controls, 1 target).");
        return;
      }
      newOp = { gate: gateId, targets: [targetQubit], controls: [controlQubit, controlQubit2] };
    } else if (selectedGateMeta.parameterized) {
      newOp = { gate: gateId, targets: [targetQubit], controls: [], params: paramAngle };
    } else {
      newOp = { gate: gateId, targets: [targetQubit], controls: [] };
    }

    setOperations([...operations, newOp]);
  };

  const handleRemoveGate = (index: number) => {
    const updated = [...operations];
    updated.splice(index, 1);
    setOperations(updated);
  };

  const handleClearCircuit = () => {
    setOperations([]);
    setErrorMsg(null);
  };

  const handleRunSimulation = async () => {
    setIsSimulating(true);
    setErrorMsg(null);
    try {
      const res = await simulateQuantumCircuit({
        num_qubits: numQubits,
        operations,
        shots,
      });
      onSimulationComplete(res);
    } catch (err: any) {
      console.error("Simulation failed:", err);
      setErrorMsg(err.response?.data?.detail || err.message || "Circuit execution failed.");
    } finally {
      setIsSimulating(false);
    }
  };

  // Quick Preset Loader
  const loadPreset = (presetName: string) => {
    setErrorMsg(null);
    if (presetName === "bell") {
      setNumQubits(2);
      setOperations([
        { gate: "H", targets: [0], controls: [] },
        { gate: "CX", targets: [1], controls: [0] },
      ]);
    } else if (presetName === "ghz") {
      setNumQubits(3);
      setOperations([
        { gate: "H", targets: [0], controls: [] },
        { gate: "CX", targets: [1], controls: [0] },
        { gate: "CX", targets: [2], controls: [1] },
      ]);
    } else if (presetName === "superposition") {
      setNumQubits(4);
      setOperations([
        { gate: "H", targets: [0], controls: [] },
        { gate: "H", targets: [1], controls: [] },
        { gate: "H", targets: [2], controls: [] },
        { gate: "H", targets: [3], controls: [] },
      ]);
    } else if (presetName === "teleportation") {
      setNumQubits(3);
      setOperations([
        { gate: "RY", targets: [0], controls: [], params: 1.0472 },
        { gate: "H", targets: [1], controls: [] },
        { gate: "CX", targets: [2], controls: [1] },
        { gate: "CX", targets: [1], controls: [0] },
        { gate: "H", targets: [0], controls: [] },
        { gate: "CX", targets: [2], controls: [1] },
        { gate: "CZ", targets: [2], controls: [0] },
      ]);
    }
  };

  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-6">
      {/* ── Header & Toolbar ────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-blue-600" />
            <h3 className="font-display text-base font-bold text-slate-900">
              Interactive Quantum Circuit Playground
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Design 1 to 8 qubit circuits, insert single/multi-qubit unitary gates, and execute on Qiskit Aer C++ simulator.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Preset Buttons */}
          <span className="text-[11px] font-semibold text-slate-500 mr-1">Presets:</span>
          <button
            onClick={() => loadPreset("bell")}
            className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
          >
            Bell State
          </button>
          <button
            onClick={() => loadPreset("ghz")}
            className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
          >
            GHZ State
          </button>
          <button
            onClick={() => loadPreset("superposition")}
            className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
          >
            4-Qubit Uniform
          </button>
          <button
            onClick={() => loadPreset("teleportation")}
            className="rounded-lg border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-700 hover:bg-blue-100 transition-colors"
          >
            Teleportation
          </button>
        </div>
      </div>

      {/* Error Message */}
      {errorMsg && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
          {errorMsg}
        </div>
      )}

      {/* ── Circuit Schematic Grid ─────────────────────────────────────── */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-slate-50/50 p-4 min-h-[220px]">
        <div className="min-w-[650px] space-y-4 font-mono">
          {Array.from({ length: numQubits }).map((_, qIdx) => (
            <div key={qIdx} className="flex items-center gap-3">
              {/* Wire Label */}
              <div className="flex w-24 shrink-0 items-center gap-1.5 text-xs font-bold text-slate-700">
                <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[11px]">q_{qIdx}</span>
                <span className="text-slate-400 font-normal">|0⟩</span>
              </div>

              {/* Wire Line with Gate Sequence */}
              <div className="relative flex flex-1 items-center gap-2">
                {/* Horizontal Wire Line */}
                <div className="absolute inset-x-0 h-[2px] bg-slate-300" />

                {/* Operations along this wire */}
                {operations.map((op, opIdx) => {
                  const isTarget = op.targets.includes(qIdx);
                  const isControl = op.controls?.includes(qIdx);
                  const isControlledGate = Boolean(op.controls && op.controls.length > 0);

                  if (!isTarget && !isControl) {
                    return (
                      <div key={opIdx} className="relative z-10 flex h-9 w-12 items-center justify-center">
                        <div className="h-1.5 w-1.5 rounded-full bg-slate-300" />
                      </div>
                    );
                  }

                  if (isControl) {
                    return (
                      <div
                        key={opIdx}
                        className="relative z-10 flex h-9 w-12 items-center justify-center cursor-pointer group"
                        title={`Control Qubit for ${op.gate}`}
                      >
                        <div className="h-3.5 w-3.5 rounded-full bg-purple-600 shadow-xs ring-2 ring-white" />
                      </div>
                    );
                  }

                  // Target gate representation
                  const meta = AVAILABLE_GATES.find((g) => g.id === op.gate);
                  const paramDisplay = op.params
                    ? typeof op.params === "number"
                      ? `(${op.params.toFixed(2)})`
                      : ""
                    : "";

                  return (
                    <div
                      key={opIdx}
                      className="relative z-10 flex h-9 min-w-12 items-center justify-center px-1.5 cursor-pointer group"
                      title={`${op.gate} on q_${qIdx} (Click to remove)`}
                    >
                      <div
                        onClick={() => handleRemoveGate(opIdx)}
                        className={`flex h-8 min-w-10 items-center justify-center rounded-lg border px-2 text-xs font-bold shadow-xs transition-transform hover:scale-105 active:scale-95 ${
                          meta?.color || "bg-white border-slate-300 text-slate-800"
                        }`}
                      >
                        {op.gate === "CX" && isControlledGate ? "⊕" : `${op.gate}${paramDisplay}`}
                        <span className="hidden group-hover:inline ml-1 text-rose-500 font-mono text-[9px]">×</span>
                      </div>
                    </div>
                  );
                })}

                {/* Trailing Measurement Indicator */}
                <div className="relative z-10 ml-auto flex h-8 w-8 items-center justify-center rounded-lg border border-slate-300 bg-white text-[11px] font-bold text-slate-600 shadow-2xs">
                  M
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Gate Insertion Toolbar & Simulation Controls ──────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
        {/* Module A: Add Gate Controls */}
        <div className="lg:col-span-2 space-y-3 rounded-xl border border-slate-200 bg-slate-50/70 p-4">
          <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
            <Plus className="h-4 w-4 text-blue-600" />
            Append Gate to Circuit
          </span>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            {/* Gate Type */}
            <div>
              <label className="text-[10px] font-semibold uppercase text-slate-500 block mb-1">Gate</label>
              <select
                value={selectedGateId}
                onChange={(e) => setSelectedGateId(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-bold text-slate-800 outline-none focus:border-blue-500"
              >
                {AVAILABLE_GATES.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.id} — {g.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Target Qubit */}
            <div>
              <label className="text-[10px] font-semibold uppercase text-slate-500 block mb-1">Target Qubit</label>
              <select
                value={targetQubit}
                onChange={(e) => setTargetQubit(parseInt(e.target.value))}
                className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-medium text-slate-800 outline-none focus:border-blue-500"
              >
                {Array.from({ length: numQubits }).map((_, i) => (
                  <option key={i} value={i}>
                    q_{i}
                  </option>
                ))}
              </select>
            </div>

            {/* Control Qubit (for 2-qubit / 3-qubit gates) */}
            {selectedGateMeta.qubits >= 2 && (
              <div>
                <label className="text-[10px] font-semibold uppercase text-slate-500 block mb-1">
                  {selectedGateMeta.id === "SWAP" ? "Second Qubit" : "Control Qubit 1"}
                </label>
                <select
                  value={controlQubit}
                  onChange={(e) => setControlQubit(parseInt(e.target.value))}
                  className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-medium text-slate-800 outline-none focus:border-blue-500"
                >
                  {Array.from({ length: numQubits }).map((_, i) => (
                    <option key={i} value={i}>
                      q_{i}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Second Control Qubit for Toffoli */}
            {selectedGateMeta.id === "CCX" && (
              <div>
                <label className="text-[10px] font-semibold uppercase text-slate-500 block mb-1">Control Qubit 2</label>
                <select
                  value={controlQubit2}
                  onChange={(e) => setControlQubit2(parseInt(e.target.value))}
                  className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-medium text-slate-800 outline-none focus:border-blue-500"
                >
                  {Array.from({ length: numQubits }).map((_, i) => (
                    <option key={i} value={i}>
                      q_{i}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Parameter Angle Slider for Rotations */}
            {selectedGateMeta.parameterized && (
              <div>
                <label className="text-[10px] font-semibold uppercase text-slate-500 block mb-1">
                  Angle: {(paramAngle / Math.PI).toFixed(2)}π rad
                </label>
                <input
                  type="range"
                  min={0}
                  max={Math.PI * 2}
                  step={0.1}
                  value={paramAngle}
                  onChange={(e) => setParamAngle(parseFloat(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer mt-1"
                />
              </div>
            )}
          </div>

          <div className="flex items-center gap-3 pt-1">
            <button
              onClick={handleAddGate}
              className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Gate
            </button>
            <button
              onClick={handleClearCircuit}
              className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 transition-colors"
            >
              <Trash2 className="h-3.5 w-3.5 text-slate-400" />
              Clear Circuit
            </button>
            <span className="text-[11px] text-slate-400 font-mono ml-auto">
              {operations.length} Gates • {numQubits} Qubits
            </span>
          </div>
        </div>

        {/* Module B: Simulation Settings & Run Trigger */}
        <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50/70 p-4 flex flex-col justify-between">
          <div className="space-y-3">
            <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
              <Settings className="h-4 w-4 text-blue-600" />
              Register & Aer Simulator
            </span>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="text-[10px] font-semibold uppercase text-slate-500 block mb-1">Qubit Count</label>
                <select
                  value={numQubits}
                  onChange={(e) => setNumQubits(parseInt(e.target.value))}
                  className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-bold text-slate-800 outline-none focus:border-blue-500"
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
                    <option key={n} value={n}>
                      {n} Qubit{n > 1 ? "s" : ""} ({Math.pow(2, n)} dim)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] font-semibold uppercase text-slate-500 block mb-1">Aer Shots</label>
                <select
                  value={shots}
                  onChange={(e) => setShots(parseInt(e.target.value))}
                  className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 font-bold text-slate-800 outline-none focus:border-blue-500"
                >
                  <option value={512}>512 Shots</option>
                  <option value={1024}>1,024 Shots</option>
                  <option value={2048}>2,048 Shots</option>
                  <option value={4096}>4,096 Shots</option>
                </select>
              </div>
            </div>
          </div>

          <button
            onClick={handleRunSimulation}
            disabled={isSimulating}
            className={`w-full flex items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold text-white shadow-xs transition-all ${
              isSimulating
                ? "bg-slate-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 active:scale-[0.99]"
            }`}
          >
            <Play className={`h-4 w-4 ${isSimulating ? "animate-spin" : ""}`} />
            {isSimulating ? "Simulating on Qiskit Aer..." : "Execute Circuit (Qiskit Aer)"}
          </button>
        </div>
      </div>
    </div>
  );
}
