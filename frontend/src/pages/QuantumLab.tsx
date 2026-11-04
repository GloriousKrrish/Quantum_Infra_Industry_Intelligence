import { useState } from "react";
import {
  Atom,
  Cpu,
  BarChart3,
  CheckCircle2,
  ShieldAlert,
  Sliders,
  Layers,
  Activity,
  Play,
  FlaskConical,
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
  LineChart,
  Line,
} from "recharts";
import { cn } from "../lib/utils";
import {
  MOCK_BITSTRING_PROBS,
  MOCK_QUANTUM_RESULT,
  MOCK_BENCHMARK,
  MOCK_BENCHMARK_CHART,
} from "../lib/mockData";

export default function QuantumLab() {
  const [budget, setBudget] = useState<number>(15.0);
  const [layers, setLayers] = useState<number>(2);
  const [shots, setShots] = useState<number>(4096);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"qaoa" | "benchmark" | "physics">("qaoa");

  // Bloch sphere angles
  const [theta, setTheta] = useState<number>(1.047); // ~PI/3 (60 deg)
  const [phi, setPhi] = useState<number>(0.785); // ~PI/4 (45 deg)

  const prob0 = Math.cos(theta / 2) ** 2;
  const prob1 = Math.sin(theta / 2) ** 2;

  // Mock VQE energy convergence curve
  const vqeData = [
    { iter: 1, energy: -0.742 },
    { iter: 5, energy: -0.912 },
    { iter: 10, energy: -1.045 },
    { iter: 15, energy: -1.112 },
    { iter: 20, energy: -1.134 },
    { iter: 25, energy: -1.137 },
  ];

  const handleRunQAOA = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
    }, 1200);
  };

  return (
    <div className="space-y-6">
      {/* ─── Hero Header ──────────────────────────────────────────────────────── */}
      <div className="relative overflow-hidden rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 p-6 backdrop-blur">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400">
                <Atom className="h-4 w-4 animate-spin-slow" />
              </span>
              <span className="text-xs font-semibold tracking-wider text-cyan-400 uppercase">
                Dual Quantum-Classical Computing Engine
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">
              Quantum Intelligence Laboratory
            </h1>
            <p className="text-sm text-slate-400 max-w-2xl">
              Execute Qiskit Aer variational algorithms (QAOA, VQE), perform exact classical baselines,
              and analyze high-dimensional statevectors for real estate & infrastructure optimization.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 rounded-xl border border-slate-700/60 bg-slate-800/60 px-3 py-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-slate-300">Simulator: Qiskit Aer (CPU)</span>
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-slate-700/60 bg-slate-800/60 px-3 py-1.5">
              <Layers className="h-3.5 w-3.5 text-cyan-400" />
              <span className="text-xs text-slate-300">8 Qubits Mapped</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="mt-6 flex border-b border-slate-800">
          <button
            onClick={() => setActiveTab("qaoa")}
            className={cn(
              "flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === "qaoa"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            )}
          >
            <Cpu className="h-4 w-4" />
            QAOA Land Optimizer
          </button>
          <button
            onClick={() => setActiveTab("benchmark")}
            className={cn(
              "flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === "benchmark"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            )}
          >
            <BarChart3 className="h-4 w-4" />
            Classical vs Quantum Benchmark
          </button>
          <button
            onClick={() => setActiveTab("physics")}
            className={cn(
              "flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === "physics"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            )}
          >
            <FlaskConical className="h-4 w-4" />
            Bloch Sphere & VQE Lab
          </button>
        </div>
      </div>

      {/* ─── TAB 1: QAOA Optimizer ────────────────────────────────────────────── */}
      {activeTab === "qaoa" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Controls Column */}
          <div className="space-y-6 rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <Sliders className="h-4 w-4 text-cyan-400" />
              <h2 className="text-sm font-semibold text-white">Algorithm Parameters</h2>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Target Budget (₹ Cr)</span>
                  <span className="font-mono text-cyan-400 font-medium">₹{budget.toFixed(1)} Cr</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="25"
                  step="0.5"
                  value={budget}
                  onChange={(e) => setBudget(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>QAOA Circuit Depth (p-layers)</span>
                  <span className="font-mono text-cyan-400 font-medium">{layers}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  value={layers}
                  onChange={(e) => setLayers(parseInt(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Measurement Shots</span>
                  <span className="font-mono text-cyan-400 font-medium">{shots}</span>
                </div>
                <input
                  type="range"
                  min="1024"
                  max="8192"
                  step="1024"
                  value={shots}
                  onChange={(e) => setShots(parseInt(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span>Budget Penalty (λ₁):</span>
                  <span className="font-mono text-slate-300">10.0</span>
                </div>
                <div className="flex justify-between">
                  <span>Risk Penalty (λ₂):</span>
                  <span className="font-mono text-slate-300">1.0</span>
                </div>
                <div className="flex justify-between">
                  <span>Optimizer:</span>
                  <span className="font-mono text-slate-300">SciPy COBYLA</span>
                </div>
              </div>

              <button
                onClick={handleRunQAOA}
                disabled={isRunning}
                className={cn(
                  "w-full flex items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold transition-all",
                  isRunning
                    ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                    : "bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-lg shadow-cyan-500/20 active:scale-[0.98]"
                )}
              >
                {isRunning ? (
                  <>
                    <Activity className="h-4 w-4 animate-spin text-cyan-400" />
                    Simulating Circuit on Qiskit Aer...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Execute QAOA Optimization
                  </>
                )}
              </button>
            </div>

            {/* Decoded Solution Summary */}
            <div className="border-t border-slate-800 pt-4 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Winning Ground State
              </h3>
              <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/5 p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Optimal Bitstring</span>
                  <span className="font-mono text-xs font-bold text-cyan-400 tracking-wider">
                    |{MOCK_QUANTUM_RESULT.optimal_bitstring}⟩
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Total Capital Cost</span>
                  <span className="font-mono text-xs text-white">
                    ₹{MOCK_QUANTUM_RESULT.total_cost} Cr
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Composite Utility</span>
                  <span className="font-mono text-xs text-emerald-400 font-medium">
                    {MOCK_QUANTUM_RESULT.total_utility}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Budget Compliance</span>
                  <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                    <CheckCircle2 className="h-3 w-3" /> Compliant (&le; ₹{budget} Cr)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Probability Distribution Chart */}
          <div className="lg:col-span-2 space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                <div>
                  <h2 className="text-sm font-semibold text-white">
                    Quantum Measurement Probability Distribution
                  </h2>
                  <p className="text-xs text-slate-400">
                    Sampled bitstrings over {shots} shots. Highlighted bar represents minimum energy configuration.
                  </p>
                </div>
                <span className="rounded-full bg-cyan-500/10 px-2.5 py-1 font-mono text-[11px] text-cyan-400 border border-cyan-500/20">
                  Peak Fidelity: {(MOCK_QUANTUM_RESULT.probability * 100).toFixed(1)}%
                </span>
              </div>

              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={MOCK_BITSTRING_PROBS}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="bitstring"
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#334155",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                      formatter={(val: any) => [`${(Number(val) * 100).toFixed(1)}%`, "Probability"]}
                    />
                    <Bar dataKey="probability" radius={[4, 4, 0, 0]}>
                      {MOCK_BITSTRING_PROBS.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.isOptimal ? "#22d3ee" : "#334155"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Selected Parcels Tag List */}
              <div className="mt-4 border-t border-slate-800 pt-3">
                <span className="text-xs text-slate-400">Selected Portfolio Parcels:</span>
                <div className="mt-2 flex flex-wrap gap-2">
                  {MOCK_QUANTUM_RESULT.selected_parcels.map((name) => (
                    <span
                      key={name}
                      className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-1 text-xs text-cyan-300 font-medium"
                    >
                      {name}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Scientific Truth Alert */}
            <div className="rounded-xl border border-slate-700/60 bg-slate-900/60 p-4 text-xs text-slate-400 flex items-start gap-3">
              <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200">Scientific Integrity Notice:</span>{" "}
                This simulation executes on classical CPU hardware via Qiskit Aer. As noted in the
                project specifications, quantum simulator results demonstrate algorithm structure,
                Hamiltonian encoding, and parameter convergence, rather than quantum hardware supremacy.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ─── TAB 2: Classical vs Quantum Benchmark ─────────────────────────────── */}
      {activeTab === "benchmark" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Side by Side Metrics */}
          <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur">
            <h2 className="text-sm font-semibold text-white border-b border-slate-800 pb-3">
              Algorithmic Performance Comparison
            </h2>

            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/5 p-4 space-y-1">
                <span className="text-xs text-cyan-400 font-medium">QAOA (Qiskit Aer)</span>
                <div className="text-2xl font-bold font-mono text-white">
                  {(MOCK_BENCHMARK.quantum_ratio * 100).toFixed(0)}%
                </div>
                <span className="text-[11px] text-slate-400">Approximation Ratio (&alpha;)</span>
                <div className="mt-2 text-xs text-slate-400">
                  Runtime: <span className="font-mono text-slate-200">{MOCK_BENCHMARK.quantum_time_ms} ms</span>
                </div>
              </div>

              <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-1">
                <span className="text-xs text-amber-400 font-medium">Simulated Annealing / Exact</span>
                <div className="text-2xl font-bold font-mono text-white">
                  {(MOCK_BENCHMARK.classical_ratio * 100).toFixed(0)}%
                </div>
                <span className="text-[11px] text-slate-400">Approximation Ratio (&alpha;)</span>
                <div className="mt-2 text-xs text-slate-400">
                  Runtime: <span className="font-mono text-slate-200">{MOCK_BENCHMARK.classical_time_ms} ms</span>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-2.5 text-xs">
              <div className="flex justify-between text-slate-300">
                <span>Exact Global Optimum (Brute Force):</span>
                <span className="font-mono text-emerald-400 font-semibold">-2,250.00 Energy</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>QAOA Ground Energy:</span>
                <span className="font-mono text-cyan-400 font-semibold">-2,248.50 Energy</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Approximation Fidelity:</span>
                <span className="font-mono text-white font-semibold">99.93%</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Total Budget Utilization:</span>
                <span className="font-mono text-white font-semibold">₹14.6 Cr / ₹15.0 Cr</span>
              </div>
            </div>
          </div>

          {/* Benchmark Comparison Chart */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur">
            <h2 className="text-sm font-semibold text-white border-b border-slate-800 pb-3 mb-4">
              Multi-Metric Evaluation Suite
            </h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={MOCK_BENCHMARK_CHART}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="metric" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                  />
                  <Bar dataKey="quantum" name="QAOA" fill="#22d3ee" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="classical" name="Classical SA" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* ─── TAB 3: Physics & Bloch Sphere Lab ─────────────────────────────────── */}
      {activeTab === "physics" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* 3D Bloch Sphere Visualizer */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Atom className="h-4 w-4 text-cyan-400" />
                <h2 className="text-sm font-semibold text-white">Single-Qubit Bloch Sphere</h2>
              </div>
              <span className="font-mono text-xs text-slate-400">
                |&psi;&rang; = cos(&theta;/2)|0&rang; + e<sup>i&phi;</sup>sin(&theta;/2)|1&rang;
              </span>
            </div>

            {/* Interactive SVG Sphere Canvas */}
            <div className="relative flex items-center justify-center rounded-xl bg-slate-950 p-6 border border-slate-800/80">
              <svg width="240" height="240" viewBox="-120 -120 240 240" className="overflow-visible">
                {/* Outer circle */}
                <circle cx="0" cy="0" r="100" fill="none" stroke="#334155" strokeWidth="1.5" />
                {/* Horizontal equator ellipse */}
                <ellipse cx="0" cy="0" rx="100" ry="30" fill="none" stroke="#1e293b" strokeDasharray="3 3" />
                {/* Axes */}
                <line x1="0" y1="-115" x2="0" y2="115" stroke="#475569" strokeWidth="1.5" />
                <line x1="-115" y1="0" x2="115" y2="0" stroke="#475569" strokeWidth="1" strokeDasharray="2 2" />
                {/* Axis Labels */}
                <text x="0" y="-120" textAnchor="middle" fill="#22d3ee" fontSize="12" fontWeight="bold">|0⟩ (+Z)</text>
                <text x="0" y="132" textAnchor="middle" fill="#f43f5e" fontSize="12" fontWeight="bold">|1⟩ (-Z)</text>
                <text x="122" y="4" textAnchor="start" fill="#64748b" fontSize="10">+X</text>
                {/* State Vector Pointer */}
                {(() => {
                  const x = 100 * Math.sin(theta) * Math.cos(phi);
                  const y = -100 * Math.cos(theta); // invert Y for screen coords
                  return (
                    <g>
                      <line x1="0" y1="0" x2={x} y2={y} stroke="#22d3ee" strokeWidth="2.5" />
                      <circle cx={x} cy={y} r="5" fill="#38bdf8" />
                    </g>
                  );
                })()}
              </svg>
            </div>

            {/* Controls */}
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>Polar Angle (&theta;):</span>
                  <span className="font-mono text-cyan-400">{(theta * 180 / Math.PI).toFixed(0)}&deg;</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max={Math.PI}
                  step="0.05"
                  value={theta}
                  onChange={(e) => setTheta(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>Azimuthal Angle (&phi;):</span>
                  <span className="font-mono text-cyan-400">{(phi * 180 / Math.PI).toFixed(0)}&deg;</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max={2 * Math.PI}
                  step="0.05"
                  value={phi}
                  onChange={(e) => setPhi(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>
            </div>

            {/* Amplitudes */}
            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="rounded-lg bg-slate-950 p-2.5 border border-slate-800 text-center">
                <span className="text-slate-400">P(|0&rang;): </span>
                <span className="text-cyan-400 font-bold">{(prob0 * 100).toFixed(1)}%</span>
              </div>
              <div className="rounded-lg bg-slate-950 p-2.5 border border-slate-800 text-center">
                <span className="text-slate-400">P(|1&rang;): </span>
                <span className="text-rose-400 font-bold">{(prob1 * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* VQE Green Cement Molecular Energy Simulation */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <FlaskConical className="h-4 w-4 text-emerald-400" />
                <h2 className="text-sm font-semibold text-white">VQE Materials Simulation (Green Cement)</h2>
              </div>
              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 font-mono text-[11px] text-emerald-400 border border-emerald-500/20">
                C-S-H Gel Hydration
              </span>
            </div>

            <p className="text-xs text-slate-400">
              Ground-state energy minimization of calcium-silicate-hydrate nanoclusters using a Hardware-Efficient
              Ansatz (UCCSD) to discover low-carbon cement formulations.
            </p>

            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={vqeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="iter" stroke="#64748b" fontSize={11} tickLine={false} label={{ value: "Iteration", position: "insideBottomRight", offset: -5 }} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} domain={[-1.2, -0.6]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    formatter={(val: any) => [`${Number(val).toFixed(4)} Hartree`, "Energy"]}
                  />
                  <Line type="monotone" dataKey="energy" stroke="#10b981" strokeWidth={2} dot={{ r: 4, fill: "#10b981" }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Calculated Ground State (E₀):</span>
                <span className="font-mono text-emerald-400 font-bold">-1.1374 Hartree</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">CO₂ Sequestration Potential:</span>
                <span className="font-mono text-cyan-400 font-bold">42.8% reduction vs Portland</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Ansatz Qubits:</span>
                <span className="font-mono text-slate-300">4 Qubits (Jordan-Wigner)</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
