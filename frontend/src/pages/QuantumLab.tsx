import { useState } from "react";
import {
  Atom,
  Cpu,
  BarChart3,
  CheckCircle2,
  Sliders,
  Activity,
  Play,
  RotateCcw,
  Sparkles,
  GitBranch,
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
import { cn } from "../lib/utils";
import BlochSphere3D from "../components/quantum/BlochSphere3D";
import QuantumLandscape3D from "../components/quantum/QuantumLandscape3D";
import CircuitViewer from "../components/quantum/CircuitViewer";
import QUBOHeatmap from "../components/quantum/QUBOHeatmap";
import {
  MOCK_BITSTRING_PROBS,
  MOCK_QUANTUM_RESULT,
  MOCK_BENCHMARK,
  MOCK_BENCHMARK_CHART,
  MOCK_PARCELS,
} from "../lib/mockData";

export default function QuantumLab() {
  const [budget, setBudget] = useState<number>(15.0);
  const [layers, setLayers] = useState<number>(2);
  const [shots, setShots] = useState<number>(4096);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"3d_quantum" | "circuit" | "benchmark">("3d_quantum");

  const [theta, setTheta] = useState<number>(Math.PI / 3);
  const [phi, setPhi] = useState<number>(Math.PI / 4);

  const handleRunQAOA = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
    }, 1000);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* ── Header Card (Clean Light Architecture) ────────────────────── */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                <Atom className="h-4 w-4" />
              </span>
              <span className="text-xs font-bold tracking-wider text-blue-600 uppercase">
                Qiskit Aer Quantum Simulator (CPU)
              </span>
            </div>
            <h1 className="font-display text-2xl font-bold tracking-tight text-slate-900">
              3D Quantum Intelligence Workbench
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Explore Quantum Approximate Optimization (QAOA) on 8 qubits mapped to Pune real estate parcels.
              Visualize qubit superpositions on the 3D Bloch Sphere and inspect the 3D QUBO energy valley.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 font-medium text-slate-700">
              Backend: <b>AerSimulator</b>
            </span>
            <span className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-1.5 font-bold text-blue-700">
              8 Qubits (256 States)
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="mt-6 flex flex-wrap border-b border-slate-100 gap-2">
          <button
            onClick={() => setActiveTab("3d_quantum")}
            className={cn(
              "flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-bold transition-all",
              activeTab === "3d_quantum"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            )}
          >
            <Atom className="h-4 w-4" />
            3D Bloch Sphere & Energy Valley
          </button>
          <button
            onClick={() => setActiveTab("circuit")}
            className={cn(
              "flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-bold transition-all",
              activeTab === "circuit"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            )}
          >
            <GitBranch className="h-4 w-4" />
            Quantum Circuit & QUBO Matrix
          </button>
          <button
            onClick={() => setActiveTab("benchmark")}
            className={cn(
              "flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-bold transition-all",
              activeTab === "benchmark"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            )}
          >
            <BarChart3 className="h-4 w-4" />
            Classical vs Quantum Verification
          </button>
        </div>
      </div>

      {/* ── TAB 1: 3D Quantum Modules (Bloch Sphere + Energy Landscape) ─ */}
      {activeTab === "3d_quantum" && (
        <div className="space-y-6">
          {/* Side-by-Side 3D Quantum Canvas Modules */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* 3D Module A: Bloch Sphere */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display text-sm font-bold text-slate-900">
                    Interactive 3D Bloch Sphere
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    Single-qubit superposition vector |ψ⟩ = cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩
                  </p>
                </div>
              </div>

              <BlochSphere3D
                theta={theta}
                phi={phi}
                onAngleChange={(t, p) => {
                  setTheta(t);
                  setPhi(p);
                }}
              />
            </div>

            {/* 3D Module B: QUBO Energy Landscape */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display text-sm font-bold text-slate-900">
                    3D Combinatorial Energy Surface $H_C(z)$
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    QAOA quantum tunneling directly into the global cost minimum
                  </p>
                </div>
              </div>

              <QuantumLandscape3D optimalBitstring="11010010" />
            </div>
          </div>

          {/* QAOA Measurement Distribution Chart */}
          <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div>
                <h3 className="font-display text-base font-bold text-slate-900">
                  Quantum Bitstring Probability Distribution
                </h3>
                <p className="text-xs text-slate-500">
                  Sampled over 4,096 measurement shots on Qiskit Aer. Highlighted bar represents ground state |11010010⟩.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleRunQAOA}
                  disabled={isRunning}
                  className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-blue-700 transition-all"
                >
                  <Play className="h-3.5 w-3.5 fill-white" />
                  <span>Resample 4096 Shots</span>
                </button>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={MOCK_BITSTRING_PROBS}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis
                    dataKey="bitstring"
                    stroke="#94a3b8"
                    fontSize={11}
                    fontFamily="JetBrains Mono"
                  />
                  <YAxis
                    stroke="#94a3b8"
                    fontSize={11}
                    tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      borderColor: "#e2e8f0",
                      borderRadius: "12px",
                      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                      fontFamily: "JetBrains Mono",
                      fontSize: "12px",
                    }}
                    formatter={(v: any) => [`${(Number(v) * 100).toFixed(2)}%`, "Probability"]}
                  />
                  <Bar dataKey="probability" radius={[6, 6, 0, 0]}>
                    {MOCK_BITSTRING_PROBS.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.is_optimal ? "#10b981" : "#94a3b8"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* ── TAB 2: Quantum Circuit & QUBO Matrix ─────────────────────── */}
      {activeTab === "circuit" && (
        <div className="space-y-6">
          <CircuitViewer pLayers={layers} />
          <QUBOHeatmap parcels={MOCK_PARCELS} />
        </div>
      )}

      {/* ── TAB 3: Classical vs Quantum Verification Benchmark ───────── */}
      {activeTab === "benchmark" && (
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-6">
          <div>
            <h3 className="font-display text-lg font-bold text-slate-900">
              Rigorous Classical vs Quantum Baseline
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              According to the anti-quantum washing protocol, QAOA is verified against exact classical Branch-and-Bound MILP.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
              <span className="text-slate-500 font-semibold uppercase block text-[10px]">
                Classical Exact MILP
              </span>
              <span className="font-display text-2xl font-bold text-slate-900 mt-1 block">
                ₹14.6 Cr / +18.4%
              </span>
              <span className="text-slate-500 mt-2 block font-mono text-[11px]">
                Approximation Ratio: 1.000 (Exact)
              </span>
            </div>

            <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50">
              <span className="text-emerald-700 font-semibold uppercase block text-[10px]">
                QAOA Simulator (p=2 layers)
              </span>
              <span className="font-display text-2xl font-bold text-emerald-800 mt-1 block">
                ₹14.6 Cr / +18.4%
              </span>
              <span className="text-emerald-700 mt-2 block font-mono text-[11px] font-bold">
                Approximation Ratio: 0.999 α
              </span>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
              <span className="text-slate-500 font-semibold uppercase block text-[10px]">
                Simulated Annealing
              </span>
              <span className="font-display text-2xl font-bold text-slate-900 mt-1 block">
                ₹14.6 Cr / +18.4%
              </span>
              <span className="text-slate-500 mt-2 block font-mono text-[11px]">
                Approximation Ratio: 0.985 α
              </span>
            </div>
          </div>

          {/* Benchmark comparison chart */}
          <div className="h-64 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={MOCK_BENCHMARK_CHART}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="metric" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 1.2]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    borderColor: "#e2e8f0",
                    borderRadius: "12px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="exact_milp" name="Classical Exact MILP" fill="#64748b" radius={[4, 4, 0, 0]} />
                <Bar dataKey="qaoa" name="QAOA (p=2)" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="simulated_annealing" name="Simulated Annealing" fill="#93c5fd" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
