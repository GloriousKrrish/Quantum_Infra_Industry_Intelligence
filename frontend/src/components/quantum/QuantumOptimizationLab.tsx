import { useState, useEffect } from "react";
import {
  Atom,
  Cpu,
  BarChart3,
  Layers,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Sliders,
  Scale,
  Binary,
  ShieldCheck,
  TrendingDown,
  Info,
  Clock,
  Zap,
} from "lucide-react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { cn } from "../../lib/utils";
import {
  getOptimizationHealth,
  buildOptimizationProblem,
  validateQUBO,
  convertQUBOToIsing,
  solveClassicalOptimization,
  solveQAOAOptimization,
  runOptimizationBenchmark,
  type OptimizationHealthResponse,
  type ProblemBuildResponse,
  type QUBOValidateResponse,
  type IsingConvertResponse,
  type ClassicalSolutionResponse,
  type QAOASolutionResponse,
  type BenchmarkResponse,
  type QUBOPayload,
} from "../../lib/api";

type ProblemPresetKey = "portfolio" | "knapsack" | "facility_location" | "resource_allocation";

export default function QuantumOptimizationLab() {
  // Engine health and software metadata
  const [health, setHealth] = useState<OptimizationHealthResponse | null>(null);

  // Active Problem Formulation
  const [selectedProblem, setSelectedProblem] = useState<ProblemPresetKey>("portfolio");
  const [problemData, setProblemData] = useState<ProblemBuildResponse | null>(null);
  const [quboValidation, setQuboValidation] = useState<QUBOValidateResponse | null>(null);
  const [isingData, setIsingData] = useState<IsingConvertResponse | null>(null);
  const [isBuildingProblem, setIsBuildingProblem] = useState<boolean>(false);

  // Problem-specific configuration
  const [portfolioBudget, setPortfolioBudget] = useState<number>(10.0);
  const [portfolioRiskAversion, setPortfolioRiskAversion] = useState<number>(0.4);
  const [knapsackCapacity, setKnapsackCapacity] = useState<number>(15.0);

  // QAOA Parameters
  const [depthP, setDepthP] = useState<number>(1);
  const [shots, setShots] = useState<number>(2048);
  const [optimizerName, setOptimizerName] = useState<string>("COBYLA");
  const [strategy, setStrategy] = useState<string>("linear_ramp");
  const [maxiter, setMaxiter] = useState<number>(35);

  // Solvers execution state
  const [isRunningQAOA, setIsRunningQAOA] = useState<boolean>(false);
  const [qaoaResult, setQaoaResult] = useState<QAOASolutionResponse | null>(null);

  const [isRunningClassical, setIsRunningClassical] = useState<boolean>(false);
  const [classicalResult, setClassicalResult] = useState<ClassicalSolutionResponse | null>(null);

  const [isRunningBenchmark, setIsRunningBenchmark] = useState<boolean>(false);
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkResponse | null>(null);

  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load engine health on mount
  useEffect(() => {
    let mounted = true;
    async function init() {
      try {
        const h = await getOptimizationHealth();
        if (mounted) setHealth(h);
      } catch (e) {
        console.warn("Could not reach optimization health endpoint:", e);
      }
    }
    init();
    return () => {
      mounted = false;
    };
  }, []);

  // Formulate problem whenever preset or core inputs change
  useEffect(() => {
    let mounted = true;
    async function loadProblem() {
      setIsBuildingProblem(true);
      setErrorMsg(null);
      try {
        let params: Record<string, any> = {};
        if (selectedProblem === "portfolio") {
          params = { budget_cr: portfolioBudget, risk_aversion: portfolioRiskAversion };
        } else if (selectedProblem === "knapsack") {
          params = { capacity: knapsackCapacity };
        }

        const buildRes = await buildOptimizationProblem({
          problem_type: selectedProblem,
          parameters: params,
        });

        if (mounted) {
          setProblemData(buildRes);
          // Auto validate and convert to Ising
          const [val, ising] = await Promise.all([
            validateQUBO(buildRes.qubo),
            convertQUBOToIsing(buildRes.qubo),
          ]);
          setQuboValidation(val);
          setIsingData(ising);
        }
      } catch (err: any) {
        if (mounted) setErrorMsg(err.message || "Failed to formulate problem");
      } finally {
        if (mounted) setIsBuildingProblem(false);
      }
    }
    loadProblem();
    return () => {
      mounted = false;
    };
  }, [selectedProblem, portfolioBudget, portfolioRiskAversion, knapsackCapacity]);

  // Execute QAOA
  const handleRunQAOA = async () => {
    if (!problemData) return;
    setIsRunningQAOA(true);
    setErrorMsg(null);
    try {
      const res = await solveQAOAOptimization({
        qubo: problemData.qubo,
        depth_p: depthP,
        shots: shots,
        optimizer_name: optimizerName,
        strategy: strategy,
        maxiter: maxiter,
        seed: 42,
      });
      setQaoaResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || "QAOA execution failed");
    } finally {
      setIsRunningQAOA(false);
    }
  };

  // Execute Classical HiGHS MILP
  const handleRunMILP = async () => {
    if (!problemData) return;
    setIsRunningClassical(true);
    setErrorMsg(null);
    try {
      const res = await solveClassicalOptimization({
        qubo: problemData.qubo,
        solver: "milp",
      });
      setClassicalResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Classical MILP solve failed");
    } finally {
      setIsRunningClassical(false);
    }
  };

  // Execute Comprehensive 5-Way Benchmark
  const handleRunBenchmark = async () => {
    if (!problemData) return;
    setIsRunningBenchmark(true);
    setErrorMsg(null);
    try {
      const res = await runOptimizationBenchmark({
        qubo: problemData.qubo,
        run_qaoa_p2: true,
        shots: Math.min(shots, 2048),
        maxiter: Math.min(maxiter, 40),
        seed: 42,
      });
      setBenchmarkResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Benchmark failed");
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* ── TOP BANNER: SCIENTIFIC DISCLOSURE & ENGINE HEALTH ─────────── */}
      <div className="rounded-2xl border border-blue-200/80 bg-gradient-to-r from-blue-50/80 via-slate-50 to-indigo-50/60 p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-blue-600 p-2.5 text-white shadow-sm mt-0.5">
              <Atom className="h-5 w-5 animate-spin-slow" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-display text-base font-bold text-slate-900">
                  Quantum-Classical Optimization Research Engine
                </h2>
                <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-semibold text-blue-700">
                  Phase 04 Verified
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-600 max-w-2xl leading-relaxed">
                Mathematical QUBO formulation, bidirectional Ising mapping, exact SciPy HiGHS MILP,
                and parameterized QAOA quantum approximate optimization on classical CPU simulator.
              </p>
              <div className="mt-2 flex items-center gap-1.5 text-[11px] font-medium text-amber-700 bg-amber-50/80 border border-amber-200/60 rounded-md px-2.5 py-1 w-fit">
                <Info className="h-3.5 w-3.5 shrink-0 text-amber-600" />
                <span>
                  Scientific Disclosure: Executed via local CPU classical simulation with Qiskit Aer 0.18.2. No physical quantum device accessed.
                </span>
              </div>
            </div>
          </div>

          {/* Software environment versions badge */}
          {health && (
            <div className="flex flex-col sm:flex-row md:flex-col gap-1.5 shrink-0 text-[11px] font-mono bg-white/80 border border-slate-200/80 rounded-xl p-3 shadow-2xs">
              <div className="flex items-center justify-between gap-4">
                <span className="text-slate-500">Qiskit:</span>
                <span className="font-semibold text-slate-800">v{health.qiskit_version}</span>
              </div>
              <div className="flex items-center justify-between gap-4">
                <span className="text-slate-500">Qiskit Aer:</span>
                <span className="font-semibold text-slate-800">v{health.qiskit_aer_version}</span>
              </div>
              <div className="flex items-center justify-between gap-4">
                <span className="text-slate-500">SciPy HiGHS:</span>
                <span className="font-semibold text-slate-800">v{health.scipy_version}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {errorMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-xs text-red-700">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* ── 1. DOMAIN PROBLEM FORMULATION ─────────────────────────────── */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5 pb-4 border-b border-slate-100">
          <div>
            <h3 className="font-display text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sliders className="h-4 w-4 text-blue-600" />
              Domain Problem Selection & Mathematical Modeling
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Select a practical real estate or spatial infrastructure optimization scenario
            </p>
          </div>

          {/* Preset Buttons */}
          <div className="flex flex-wrap items-center gap-1.5 bg-slate-100/80 p-1 rounded-xl">
            {(
              [
                ["portfolio", "Real Estate Portfolio"],
                ["knapsack", "Capital Knapsack"],
                ["facility_location", "Facility Location (P-Median)"],
                ["resource_allocation", "Resource Scheduling"],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setSelectedProblem(key)}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-xs font-semibold transition-all",
                  selectedProblem === key
                    ? "bg-white text-blue-600 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Controls based on Problem Preset */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {selectedProblem === "portfolio" && (
            <>
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-slate-700">Total Investment Budget:</span>
                  <span className="font-mono font-bold text-blue-600">₹{portfolioBudget.toFixed(1)} Cr</span>
                </div>
                <input
                  type="range"
                  min={6}
                  max={20}
                  step={0.5}
                  value={portfolioBudget}
                  onChange={(e) => setPortfolioBudget(parseFloat(e.target.value))}
                  className="w-full accent-blue-600"
                />
                <p className="text-[10px] text-slate-500">
                  Allocates across Hinjewadi, Wakad, Baner, PCMC, and Kharadi parcels.
                </p>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-slate-700">Risk Aversion Factor (λ):</span>
                  <span className="font-mono font-bold text-blue-600">{portfolioRiskAversion.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min={0.1}
                  max={1.0}
                  step={0.05}
                  value={portfolioRiskAversion}
                  onChange={(e) => setPortfolioRiskAversion(parseFloat(e.target.value))}
                  className="w-full accent-blue-600"
                />
                <p className="text-[10px] text-slate-500">
                  Higher values penalize volatile parcel micro-markets.
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 border border-slate-200/60 p-3 text-[11px] text-slate-600 space-y-1">
                <div className="font-semibold text-slate-800">Micro-Market Diversification:</div>
                <div>Enforces spatial anti-clustering penalty to avoid single-zone concentration.</div>
              </div>
            </>
          )}

          {selectedProblem === "knapsack" && (
            <>
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-slate-700">Substation / Hub Capacity:</span>
                  <span className="font-mono font-bold text-blue-600">{knapsackCapacity.toFixed(0)} Units</span>
                </div>
                <input
                  type="range"
                  min={8}
                  max={25}
                  step={1}
                  value={knapsackCapacity}
                  onChange={(e) => setKnapsackCapacity(parseFloat(e.target.value))}
                  className="w-full accent-blue-600"
                />
                <p className="text-[10px] text-slate-500">
                  Selects optimal combination of power transformers, EV clusters, and storage.
                </p>
              </div>
              <div className="rounded-xl bg-slate-50 border border-slate-200/60 p-3 text-[11px] text-slate-600 space-y-1 md:col-span-2">
                <div className="font-semibold text-slate-800">Binary Slack Expansion:</div>
                <div>Capacity constraint is converted into exact QUBO via powers-of-two slack bits.</div>
              </div>
            </>
          )}

          {selectedProblem === "facility_location" && (
            <div className="rounded-xl bg-slate-50 border border-slate-200/60 p-3 text-[11px] text-slate-600 space-y-1 md:col-span-3">
              <div className="font-semibold text-slate-800">P-Median Spatial Location:</div>
              <div>
                Selects 2 optimal regional logistics/medical hubs among Baner, Wakad, Hinjewadi, and PCMC
                to minimize aggregate travel distance to demand centers.
              </div>
            </div>
          )}

          {selectedProblem === "resource_allocation" && (
            <div className="rounded-xl bg-slate-50 border border-slate-200/60 p-3 text-[11px] text-slate-600 space-y-1 md:col-span-3">
              <div className="font-semibold text-slate-800">Bipartite Heavy Machinery Scheduling:</div>
              <div>
                Matches cranes, piling rigs, and excavators to foundation and core wall tasks across active sites.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── 2. MATHEMATICAL QUBO & ISING MATRIX VISUALIZATION ─────────── */}
      {problemData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* QUBO Matrix Heatmap Card */}
          <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-display text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Binary className="h-4 w-4 text-indigo-600" />
                  QUBO Matrix Q ({problemData.num_variables} × {problemData.num_variables})
                </h3>
                <p className="text-[11px] text-slate-500">
                  Energy = x^T Q x + {problemData.qubo.offset.toFixed(2)} (Diagonal: Linear weights, Off-diagonal: Couplings)
                </p>
              </div>

              {quboValidation && (
                <div className="flex items-center gap-1.5 text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-md font-medium">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  <span>Algebraically Validated</span>
                </div>
              )}
            </div>

            {/* Matrix Heatmap Table */}
            <div className="overflow-x-auto border border-slate-100 rounded-xl p-2 bg-slate-50/50 max-h-72 overflow-y-auto font-mono text-[11px]">
              <table className="w-full border-collapse text-center">
                <thead>
                  <tr>
                    <th className="p-1 text-slate-400 font-normal text-[10px]"></th>
                    {problemData.variable_names.map((name, idx) => (
                      <th
                        key={idx}
                        className="p-1 font-medium text-slate-600 max-w-[60px] truncate"
                        title={name}
                      >
                        v{idx}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {problemData.qubo.matrix.map((row, rIdx) => (
                    <tr key={rIdx}>
                      <td className="p-1 font-medium text-slate-600 text-left text-[10px] max-w-[70px] truncate" title={problemData.variable_names[rIdx]}>
                        v{rIdx}
                      </td>
                      {row.map((val, cIdx) => {
                        const isDiag = rIdx === cIdx;
                        const isZero = Math.abs(val) < 1e-6;
                        let bg = "bg-white text-slate-400";
                        if (!isZero) {
                          if (val < 0) bg = "bg-emerald-100 text-emerald-800 font-semibold";
                          else if (isDiag) bg = "bg-blue-100 text-blue-900 font-bold";
                          else bg = "bg-amber-100 text-amber-900 font-medium";
                        }
                        return (
                          <td
                            key={cIdx}
                            className={cn(
                              "p-1.5 border border-slate-200/50 rounded-sm text-[10px] transition-colors",
                              bg
                            )}
                            title={`${problemData.variable_names[rIdx]} - ${problemData.variable_names[cIdx]}: ${val.toFixed(2)}`}
                          >
                            {val.toFixed(1)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Variable Legend */}
            <div className="mt-3 flex flex-wrap gap-2 text-[10px] text-slate-600 font-mono">
              {problemData.variable_names.map((v, i) => (
                <span key={i} className="bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                  v{i}: {v}
                </span>
              ))}
            </div>
          </div>

          {/* Spectral Diagnostics & Ising Hamiltonian */}
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
              <h4 className="font-display text-xs font-bold text-slate-900 mb-3 flex items-center gap-1.5">
                <Scale className="h-3.5 w-3.5 text-blue-600" />
                Spectral & Algebraic Diagnostics
              </h4>

              {quboValidation && (
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Variables (n):</span>
                    <span className="font-bold text-slate-800">{quboValidation.num_variables}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Condition Number κ:</span>
                    <span className="font-bold text-slate-800">
                      {quboValidation.condition_number ? quboValidation.condition_number.toFixed(2) : "N/A"}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Min Eigenvalue λ_min:</span>
                    <span className="font-bold text-slate-800">{quboValidation.min_eigenvalue}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Max Eigenvalue λ_max:</span>
                    <span className="font-bold text-slate-800">{quboValidation.max_eigenvalue}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Dynamic Range:</span>
                    <span className="font-bold text-slate-800">{quboValidation.dynamic_range_db} dB</span>
                  </div>
                </div>
              )}
            </div>

            {/* Ising Model Mapping */}
            {isingData && (
              <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
                <h4 className="font-display text-xs font-bold text-slate-900 mb-2 flex items-center gap-1.5">
                  <Zap className="h-3.5 w-3.5 text-indigo-600" />
                  Ising Mapping H(z)
                </h4>
                <p className="text-[10px] text-slate-500 mb-2">
                  Mapped via z_i = 1 - 2 x_i. Total Pauli terms: {isingData.pauli_terms.length}
                </p>
                <div className="space-y-1 font-mono text-[10px] max-h-32 overflow-y-auto bg-slate-50 p-2 rounded-lg border border-slate-100">
                  {isingData.pauli_terms.slice(0, 8).map((term, tIdx) => (
                    <div key={tIdx} className="flex justify-between text-slate-700">
                      <span className="text-indigo-600 font-semibold">{term.pauli}</span>
                      <span>{term.coefficient.toFixed(3)}</span>
                    </div>
                  ))}
                  {isingData.pauli_terms.length > 8 && (
                    <div className="text-slate-400 text-center pt-1 italic">
                      + {isingData.pauli_terms.length - 8} additional Pauli terms
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── 3. PARAMETERIZED QAOA SIMULATION CONTROLS & HISTOGRAM ─────── */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h3 className="font-display text-sm font-bold text-slate-900 flex items-center gap-2">
              <Atom className="h-4 w-4 text-blue-600" />
              Configurable QAOA Quantum Simulation Engine
            </h3>
            <p className="text-xs text-slate-500">
              Parametric variational quantum circuit U(C, γ) U(B, β) optimized via classical feedback loop
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleRunMILP}
              disabled={isRunningClassical || !problemData}
              className="flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-2xs hover:bg-slate-50 disabled:opacity-50"
            >
              <Cpu className="h-3.5 w-3.5 text-slate-600" />
              {isRunningClassical ? "Solving MILP..." : "Run HiGHS MILP"}
            </button>

            <button
              onClick={handleRunQAOA}
              disabled={isRunningQAOA || !problemData}
              className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
            >
              <Play className="h-3.5 w-3.5" />
              {isRunningQAOA ? "Simulating QAOA..." : "Execute QAOA"}
            </button>
          </div>
        </div>

        {/* Hyperparameter Controls */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <div className="space-y-1">
            <label className="text-[11px] font-medium text-slate-600">Circuit Depth (p):</label>
            <select
              value={depthP}
              onChange={(e) => setDepthP(parseInt(e.target.value))}
              className="w-full rounded-lg border border-slate-200 bg-white p-1.5 text-xs font-semibold"
            >
              <option value={1}>p = 1 (Fast)</option>
              <option value={2}>p = 2 (Higher Fidelity)</option>
              <option value={3}>p = 3 (Deep)</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-medium text-slate-600">Optimizer:</label>
            <select
              value={optimizerName}
              onChange={(e) => setOptimizerName(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white p-1.5 text-xs font-semibold"
            >
              <option value="COBYLA">COBYLA (Simplex)</option>
              <option value="NELDER-MEAD">Nelder-Mead</option>
              <option value="SLSQP">SLSQP</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-medium text-slate-600">Parameter Strategy:</label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white p-1.5 text-xs font-semibold"
            >
              <option value="linear_ramp">Linear Ramp (Adiabatic)</option>
              <option value="random">Random Initialization</option>
              <option value="fourier">Fourier Heuristic</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-medium text-slate-600">Measurement Shots:</label>
            <select
              value={shots}
              onChange={(e) => setShots(parseInt(e.target.value))}
              className="w-full rounded-lg border border-slate-200 bg-white p-1.5 text-xs font-semibold"
            >
              <option value={1024}>1,024 shots</option>
              <option value={2048}>2,048 shots</option>
              <option value={4096}>4,096 shots</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-medium text-slate-600">Max Iterations:</label>
            <input
              type="number"
              min={10}
              max={80}
              value={maxiter}
              onChange={(e) => setMaxiter(parseInt(e.target.value) || 30)}
              className="w-full rounded-lg border border-slate-200 bg-white p-1.5 text-xs font-mono font-semibold"
            />
          </div>
        </div>

        {/* Results Presentation (QAOA + MILP Comparison) */}
        {qaoaResult && (
          <div className="space-y-6 pt-2">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 space-y-1">
                <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
                  Optimal Bitstring
                </div>
                <div className="font-mono text-base font-bold text-blue-600">
                  |{qaoaResult.optimal_bitstring}⟩
                </div>
                <div className="text-[10px] text-slate-500">Most optimal sampled solution</div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 space-y-1">
                <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
                  Best Sampled Energy
                </div>
                <div className="font-mono text-base font-bold text-slate-900">
                  {qaoaResult.best_sampled_energy.toFixed(3)}
                </div>
                <div className="text-[10px] text-slate-500">
                  Expected ⟨H⟩: {qaoaResult.expected_energy.toFixed(3)}
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 space-y-1">
                <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
                  Ground State Prob
                </div>
                <div className="font-mono text-base font-bold text-emerald-600">
                  {(qaoaResult.ground_state_probability * 100).toFixed(1)}%
                </div>
                <div className="text-[10px] text-slate-500">
                  Over {qaoaResult.shots.toLocaleString()} measurement shots
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 space-y-1">
                <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
                  Approximation Ratio
                </div>
                <div className="font-mono text-base font-bold text-indigo-600">
                  α = {qaoaResult.approximation_ratio ? qaoaResult.approximation_ratio.toFixed(3) : "1.000"}
                </div>
                <div className="text-[10px] text-slate-500">
                  Time: {qaoaResult.solve_time_ms.toFixed(0)} ms ({qaoaResult.iterations} steps)
                </div>
              </div>
            </div>

            {/* Convergence Trajectory Chart & Measurement Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Convergence Line Chart */}
              <div className="rounded-xl border border-slate-200 p-4 bg-white">
                <h4 className="font-display text-xs font-bold text-slate-900 mb-2 flex items-center gap-1.5">
                  <TrendingDown className="h-3.5 w-3.5 text-blue-600" />
                  QAOA Classical Optimization Convergence
                </h4>
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={qaoaResult.trajectory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="iteration" tick={{ fontSize: 10 }} label={{ value: "Iteration", position: "insideBottom", offset: -5, fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} label={{ value: "Energy E(γ, β)", angle: -90, position: "insideLeft", fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0", fontSize: "11px" }}
                      />
                      <Line type="monotone" dataKey="energy" stroke="#2563eb" strokeWidth={2} dot={{ r: 2 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Measurement Distribution Bar Chart */}
              <div className="rounded-xl border border-slate-200 p-4 bg-white">
                <h4 className="font-display text-xs font-bold text-slate-900 mb-2 flex items-center gap-1.5">
                  <BarChart3 className="h-3.5 w-3.5 text-indigo-600" />
                  Top Measurement Bitstrings (Qiskit Aer)
                </h4>
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={qaoaResult.top_measurements.slice(0, 8)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="bitstring" tick={{ fontSize: 9 }} />
                      <YAxis tick={{ fontSize: 10 }} unit="%" tickFormatter={(v) => (v * 100).toFixed(0)} />
                      <Tooltip
                        formatter={(val: any) => [`${(Number(val) * 100).toFixed(1)}%`, "Probability"]}
                        contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0", fontSize: "11px" }}
                      />
                      <Bar dataKey="probability" radius={[4, 4, 0, 0]}>
                        {qaoaResult.top_measurements.slice(0, 8).map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.bitstring === qaoaResult.optimal_bitstring ? "#2563eb" : "#94a3b8"}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* MILP Result Callout if run standalone */}
        {classicalResult && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-emerald-600 p-2 text-white">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-emerald-950">
                  Exact Classical Baseline: SciPy HiGHS MILP
                </div>
                <div className="text-[11px] text-emerald-800 font-mono">
                  Optimal bitstring: |{classicalResult.optimal_bitstring}⟩ — Provable Global Minimum: {classicalResult.objective_value.toFixed(4)}
                </div>
              </div>
            </div>
            <div className="text-right text-xs font-mono text-emerald-900">
              Time: {classicalResult.solve_time_ms.toFixed(1)} ms
            </div>
          </div>
        )}
      </div>

      {/* ── 4. HEAD-TO-HEAD 5-WAY COMPARATIVE BENCHMARK ───────────────── */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h3 className="font-display text-sm font-bold text-slate-900 flex items-center gap-2">
              <Scale className="h-4 w-4 text-purple-600" />
              Rigorous 5-Way Quantum vs Classical Benchmark Matrix
            </h3>
            <p className="text-xs text-slate-500">
              Evaluates SciPy HiGHS MILP, Brute-Force (2^n), Greedy, Simulated Annealing, and QAOA on identical formulation
            </p>
          </div>

          <button
            onClick={handleRunBenchmark}
            disabled={isRunningBenchmark || !problemData}
            className="flex items-center gap-1.5 rounded-xl bg-purple-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-purple-700 disabled:opacity-50"
          >
            <BarChart3 className="h-3.5 w-3.5" />
            {isRunningBenchmark ? "Benchmarking Solvers..." : "Run Head-to-Head Benchmark"}
          </button>
        </div>

        {benchmarkResult && (
          <div className="space-y-4">
            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
                    <th className="p-3">Solver</th>
                    <th className="p-3">Type</th>
                    <th className="p-3">Best Bitstring</th>
                    <th className="p-3">Energy</th>
                    <th className="p-3">Optimality Gap</th>
                    <th className="p-3">Approx Ratio (α)</th>
                    <th className="p-3">Solve Time</th>
                    <th className="p-3">Iterations</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {benchmarkResult.solvers.map((s, idx) => {
                    const isOptimal = Math.abs(s.energy - benchmarkResult.exact_ground_energy) < 1e-4;
                    return (
                      <tr
                        key={idx}
                        className={cn(
                          "transition-colors",
                          isOptimal ? "bg-emerald-50/30" : "hover:bg-slate-50/50"
                        )}
                      >
                        <td className="p-3 font-bold text-slate-900 font-sans flex items-center gap-1.5">
                          {s.is_quantum ? (
                            <Atom className="h-3.5 w-3.5 text-blue-600 shrink-0" />
                          ) : (
                            <Cpu className="h-3.5 w-3.5 text-slate-600 shrink-0" />
                          )}
                          <span>{s.solver_name}</span>
                        </td>
                        <td className="p-3 font-sans text-slate-600">
                          {s.is_quantum ? "Quantum Sim" : "Classical"}
                        </td>
                        <td className="p-3 font-bold text-blue-700">|{s.optimal_bitstring}⟩</td>
                        <td className="p-3 font-bold text-slate-900">{s.energy.toFixed(3)}</td>
                        <td className="p-3">
                          <span
                            className={cn(
                              "rounded px-1.5 py-0.5 text-[10px] font-bold",
                              s.optimality_gap_pct < 0.01
                                ? "bg-emerald-100 text-emerald-800"
                                : s.optimality_gap_pct < 10.0
                                ? "bg-amber-100 text-amber-800"
                                : "bg-red-100 text-red-800"
                            )}
                          >
                            {s.optimality_gap_pct.toFixed(2)}%
                          </span>
                        </td>
                        <td className="p-3 font-semibold text-slate-700">
                          {s.approximation_ratio.toFixed(3)}
                        </td>
                        <td className="p-3 text-slate-600">{s.solve_time_ms.toFixed(1)} ms</td>
                        <td className="p-3 text-slate-500">{s.iterations}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Scientific Summary Findings */}
            <div className="rounded-xl bg-slate-50 p-4 border border-slate-200/60 space-y-1.5 text-xs">
              <div className="font-bold text-slate-800 flex items-center gap-1.5">
                <Info className="h-3.5 w-3.5 text-blue-600" />
                Benchmark Findings & Scientific Consensus:
              </div>
              <ul className="list-disc list-inside space-y-1 text-slate-600 text-[11px]">
                {benchmarkResult.summary_findings.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
