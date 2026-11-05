import React, { useState, useEffect } from "react";
import {
  Activity,
  Play,
  RotateCcw,
  Sliders,
  Sparkles,
  Info,
  Clock,
  Zap,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  simulateStateEvolution,
  type StateEvolutionResponse,
} from "../../lib/api";

const HAMILTONIANS = [
  { id: "pauli_x", name: "Pauli X (σ_x)", qubits: 1, desc: "Bit-flip precession rotation around X-axis" },
  { id: "pauli_y", name: "Pauli Y (σ_y)", qubits: 1, desc: "Phase and bit rotation around Y-axis" },
  { id: "pauli_z", name: "Pauli Z (σ_z)", qubits: 1, desc: "Phase precession rotation around Z-axis" },
  { id: "hadamard", name: "Hadamard (H)", qubits: 1, desc: "Evolution under balanced superposition operator" },
  { id: "general_b_field", name: "Magnetic B-Field (B·σ)", qubits: 1, desc: "Precession in arbitrary magnetic field vector" },
  { id: "ising_zz", name: "Ising Coupling (Z ⊗ Z)", qubits: 2, desc: "2-qubit longitudinal spin-spin interaction" },
  { id: "exchange_xy", name: "Exchange Coupling (XX + YY)", qubits: 2, desc: "Flip-flop energy exchange between spins" },
  { id: "heisenberg_xxx", name: "Heisenberg XXX", qubits: 2, desc: "Isotropic exchange interaction (XX + YY + ZZ)" },
];

const INITIAL_STATES: Record<number, Array<{ id: string; name: string }>> = {
  1: [
    { id: "zero", name: "|0⟩ Ground State" },
    { id: "one", name: "|1⟩ Excited State" },
    { id: "plus", name: "|+⟩ Superposition" },
    { id: "minus", name: "|-⟩ Superposition" },
    { id: "plus_i", name: "|+i⟩ Circular Phase" },
    { id: "minus_i", name: "|-i⟩ Circular Phase" },
  ],
  2: [
    { id: "00", name: "|00⟩ Ground State" },
    { id: "01", name: "|01⟩ State" },
    { id: "10", name: "|10⟩ State" },
    { id: "11", name: "|11⟩ State" },
    { id: "bell_phi_plus", name: "|Φ+⟩ Bell State" },
  ],
};

export default function StateEvolutionLab() {
  const [hamiltonianType, setHamiltonianType] = useState<string>("pauli_x");
  const [initialState, setInitialState] = useState<string>("zero");
  const [omega, setOmega] = useState<number>(1.0);
  const [jCoupling, setJCoupling] = useState<number>(1.0);
  const [totalTime, setTotalTime] = useState<number>(6.28);
  const [steps, setSteps] = useState<number>(40);
  const [scrubberIndex, setScrubberIndex] = useState<number>(0);

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<StateEvolutionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const activeHam = HAMILTONIANS.find((h) => h.id === hamiltonianType) || HAMILTONIANS[0];
  const availableStates = INITIAL_STATES[activeHam.qubits] || INITIAL_STATES[1];

  // Reset initial state when switching qubit count
  useEffect(() => {
    if (!availableStates.some((s) => s.id === initialState)) {
      setInitialState(availableStates[0].id);
    }
  }, [hamiltonianType]);

  const handleSimulate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await simulateStateEvolution({
        hamiltonian_type: hamiltonianType,
        initial_state_name: initialState,
        omega,
        j_coupling: jCoupling,
        total_time: totalTime,
        num_steps: steps,
      });
      setResult(res);
      setScrubberIndex(0);
    } catch (err: any) {
      console.error("Evolution failed:", err);
      setError(err.response?.data?.detail || err.message || "Failed to simulate evolution.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSimulate();
  }, [hamiltonianType, initialState, omega, jCoupling, totalTime, steps]);

  // Transform trajectory data for LineChart
  const chartData = (result?.trajectory || []).map((pt) => {
    const row: Record<string, number> = { time: pt.time };
    pt.amplitudes.forEach((amp) => {
      row[amp.ket] = amp.probability;
    });
    return row;
  });

  const currentSlice = result?.trajectory?.[scrubberIndex] || result?.trajectory?.[0];

  return (
    <div className="space-y-6">
      {/* Configuration Header Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-600" />
              <h2 className="font-display text-lg font-bold text-slate-900">
                Continuous Hamiltonian State Evolution U(t) = exp(-iHt/ℏ)
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Solve the time-dependent Schrödinger equation continuously under single-qubit and interacting 2-qubit spin Hamiltonians with exact matrix exponentials.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSimulate}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-xs"
            >
              <Play className="h-3.5 w-3.5" />
              {loading ? "Simulating..." : "Recompute Evolution"}
            </button>
          </div>
        </div>

        {/* Controls Grid */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Hamiltonian Operator (H)
            </label>
            <select
              value={hamiltonianType}
              onChange={(e) => setHamiltonianType(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              {HAMILTONIANS.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name} ({h.qubits}Q)
                </option>
              ))}
            </select>
            <span className="text-[10px] text-slate-400 mt-1 block">
              {activeHam.desc}
            </span>
          </div>

          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Initial State |ψ(0)⟩
            </label>
            <select
              value={initialState}
              onChange={(e) => setInitialState(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              {availableStates.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <span className="text-[10px] text-slate-400 mt-1 block font-mono">
              Dimension: 2^{activeHam.qubits} = {Math.pow(2, activeHam.qubits)}
            </span>
          </div>

          <div>
            <div className="flex justify-between items-center text-[11px]">
              <label className="font-bold uppercase tracking-wider text-slate-500">
                {activeHam.qubits === 1 ? "Angular Frequency ω" : "Coupling Strength J"}
              </label>
              <span className="font-mono text-slate-700 font-bold">
                {activeHam.qubits === 1 ? `${omega.toFixed(2)} rad/s` : `${jCoupling.toFixed(2)} rad/s`}
              </span>
            </div>
            <input
              type="range"
              min="0.2"
              max="5.0"
              step="0.1"
              value={activeHam.qubits === 1 ? omega : jCoupling}
              onChange={(e) =>
                activeHam.qubits === 1
                  ? setOmega(parseFloat(e.target.value))
                  : setJCoupling(parseFloat(e.target.value))
              }
              className="mt-2.5 w-full accent-blue-600 cursor-pointer"
            />
            <span className="text-[10px] text-slate-400 block mt-1">
              Energy scale parameter
            </span>
          </div>

          <div>
            <div className="flex justify-between items-center text-[11px]">
              <label className="font-bold uppercase tracking-wider text-slate-500">
                Total Time Window (T)
              </label>
              <span className="font-mono text-slate-700 font-bold">
                {totalTime.toFixed(2)} s
              </span>
            </div>
            <input
              type="range"
              min="1.0"
              max="15.0"
              step="0.5"
              value={totalTime}
              onChange={(e) => setTotalTime(parseFloat(e.target.value))}
              className="mt-2.5 w-full accent-blue-600 cursor-pointer"
            />
            <span className="text-[10px] text-slate-400 block mt-1">
              Periodicity & recurrence horizon
            </span>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
            {error}
          </div>
        )}
      </div>

      {/* Main Results Grid */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Cols: Continuous Probability Trajectory Chart */}
          <div className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <h3 className="font-display text-sm font-bold text-slate-900">
                  Continuous State Probability Trajectory P_k(t) = |⟨k|ψ(t)⟩|²
                </h3>
                <span className="text-[11px] text-slate-500 font-mono">
                  Formula: {result.formula_latex} • Energy Expectation ⟨H⟩ = {result.energy_expectation} ℏω
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-mono font-bold text-slate-600">
                  Overlap |⟨ψ(0)|ψ(T)⟩|²: {result.initial_overlap_final}
                </span>
              </div>
            </div>

            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey="time"
                    tick={{ fill: "#64748b", fontSize: 10, fontFamily: "monospace" }}
                    unit="s"
                  />
                  <YAxis tick={{ fill: "#64748b", fontSize: 10 }} domain={[0, 1]} unit="" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      borderRadius: "8px",
                      border: "1px solid #e2e8f0",
                      fontSize: "11px",
                      fontFamily: "monospace",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px", fontFamily: "monospace" }} />
                  {result.trajectory[0]?.amplitudes.map((amp, idx) => {
                    const colors = ["#2563eb", "#059669", "#d97706", "#dc2626"];
                    return (
                      <Line
                        key={amp.ket}
                        type="monotone"
                        dataKey={amp.ket}
                        stroke={colors[idx % colors.length]}
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                      />
                    );
                  })}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Time Scrubber */}
            <div className="pt-2 border-t border-slate-100">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-blue-600" />
                  Time Scrubber: t = {currentSlice?.time?.toFixed(3)} s
                </span>
                <span className="text-[11px] text-slate-400 font-mono">
                  Slice {scrubberIndex + 1} of {result.trajectory.length}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max={result.trajectory.length - 1}
                value={scrubberIndex}
                onChange={(e) => setScrubberIndex(parseInt(e.target.value))}
                className="w-full accent-blue-600 mt-2 cursor-pointer"
              />
            </div>
          </div>

          {/* Right Col: Instantaneous State Properties at Selected Time */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Instantaneous State Snapshot at t = {currentSlice?.time?.toFixed(3)} s
            </h3>

            {/* Eigenvalues & Energy Conservation Card */}
            <div className="rounded-xl border border-slate-200/80 bg-slate-50 p-3 space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Hamiltonian Spectrum:</span>
                <span className="font-mono font-bold text-slate-800">
                  [{result.eigenvalues.join(", ")}]
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Energy Gap ΔE:</span>
                <span className="font-mono font-bold text-emerald-700">
                  {result.energy_gap} ℏω
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Recurrence Period:</span>
                <span className="font-mono font-bold text-blue-700">
                  {result.recurrence_period ? `${result.recurrence_period} s` : "Aperiodic"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">⟨H⟩ Energy Conservation:</span>
                <span className="font-mono font-bold text-slate-900">
                  {result.energy_expectation} ℏω (Exact)
                </span>
              </div>
            </div>

            {/* Amplitudes Table */}
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-2">
                Basis State Amplitudes
              </span>
              <div className="space-y-2">
                {currentSlice?.amplitudes.map((amp) => (
                  <div
                    key={amp.bitstring}
                    className="flex items-center justify-between p-2 rounded-xl border border-slate-100 bg-slate-50/50 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-blue-700">{amp.ket}</span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        ({amp.real >= 0 ? "+" : ""}{amp.real.toFixed(3)}
                        {amp.imag >= 0 ? "+" : ""}{amp.imag.toFixed(3)}i)
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="font-mono font-bold text-slate-900">
                        {(amp.probability * 100).toFixed(1)}%
                      </span>
                      <div className="w-16 bg-slate-200 h-1.5 rounded-full overflow-hidden mt-0.5">
                        <div
                          className="bg-blue-600 h-full rounded-full transition-all"
                          style={{ width: `${amp.probability * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 1-Qubit Bloch Vector Coordinates */}
            {currentSlice?.bloch_vector && (
              <div className="pt-2 border-t border-slate-100">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-2">
                  Bloch Vector (r_x, r_y, r_z)
                </span>
                <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
                  <div className="p-2 rounded-lg bg-blue-50 border border-blue-100">
                    <span className="text-[10px] text-blue-600 block">X</span>
                    <span className="font-bold text-blue-900">{currentSlice.bloch_vector.x}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-emerald-50 border border-emerald-100">
                    <span className="text-[10px] text-emerald-600 block">Y</span>
                    <span className="font-bold text-emerald-900">{currentSlice.bloch_vector.y}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-purple-50 border border-purple-100">
                    <span className="text-[10px] text-purple-600 block">Z</span>
                    <span className="font-bold text-purple-900">{currentSlice.bloch_vector.z}</span>
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

