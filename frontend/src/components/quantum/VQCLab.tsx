import { useState, useEffect, useCallback } from "react";
import {
  BrainCircuit,
  Cpu,
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
  BarChart3,
  Target,
  FlaskConical,
  Database,
  ArrowRight,
  Gauge,
  ListOrdered,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from "recharts";
import { cn } from "../../lib/utils";
import {
  getVQCHealth,
  getVQCAnsatzList,
  buildVQCCircuit,
  trainVQCModel,
  predictVQCModel,
  runVQCBenchmark,
  getVQCExperiments,
  type VQCHealthResponse,
  type AnsatzItemSchema,
  type CircuitBuildResponse,
  type VQCTrainResponse,
  type VQCPredictResponse,
  type VQCBenchmarkResponse,
  type VQCExperimentRecord,
} from "../../lib/api";

type LabViewMode = "train" | "benchmark" | "inference" | "experiments";

interface DatasetOption {
  id: string;
  name: string;
  features: number;
  classes: number;
  tier: "SYNTHETIC_BENCHMARK" | "PROVENANCE_TIER_3_SYNTHETIC";
  description: string;
}

const DATASETS: DatasetOption[] = [
  {
    id: "moons",
    name: "Interleaving Moons",
    features: 2,
    classes: 2,
    tier: "SYNTHETIC_BENCHMARK",
    description: "Two interleaving half-circles. Tests non-linear decision boundary capability.",
  },
  {
    id: "circles",
    name: "Concentric Circles",
    features: 2,
    classes: 2,
    tier: "SYNTHETIC_BENCHMARK",
    description: "Inner and outer circle. Demonstrates radial quantum feature mapping.",
  },
  {
    id: "linearly_separable",
    name: "Linearly Separable",
    features: 2,
    classes: 2,
    tier: "SYNTHETIC_BENCHMARK",
    description: "Two well-separated Gaussian clusters. Establishes baseline classification.",
  },
  {
    id: "iris",
    name: "Iris Binary (Setosa vs Versicolor)",
    features: 4,
    classes: 2,
    tier: "SYNTHETIC_BENCHMARK",
    description: "Botanical standard dataset reduced to 2 classes (4 features reduced to 2 via PCA).",
  },
  {
    id: "land_suitability",
    name: "Pune Land Suitability",
    features: 4,
    classes: 2,
    tier: "PROVENANCE_TIER_3_SYNTHETIC",
    description: "Infrastructure proximity, slope, zoning index & ground elevation suitability.",
  },
  {
    id: "infrastructure_risk",
    name: "Infrastructure Flood & Seismic Risk",
    features: 4,
    classes: 2,
    tier: "PROVENANCE_TIER_3_SYNTHETIC",
    description: "Hydro-geological soil stability, monsoon flood index, seismic proximity & drainage load.",
  },
];

export default function VQCLab() {
  const [viewMode, setViewMode] = useState<LabViewMode>("train");
  const [health, setHealth] = useState<VQCHealthResponse | null>(null);
  const [ansatzList, setAnsatzList] = useState<AnsatzItemSchema[]>([]);
  const [circuitStats, setCircuitStats] = useState<CircuitBuildResponse | null>(null);

  // Training Configuration State
  const [datasetName, setDatasetName] = useState<string>("moons");
  const [nSamples, setNSamples] = useState<number>(80);
  const [encoderName, setEncoderName] = useState<string>("angle_ry");
  const [ansatzType, setAnsatzType] = useState<string>("hardware_efficient");
  const [numLayers, setNumLayers] = useState<number>(2);
  const [optimizer, setOptimizer] = useState<string>("COBYLA");
  const [maxIter, setMaxIter] = useState<number>(30);
  const [learningRate, setLearningRate] = useState<number>(0.05);
  const [lossFunction, setLossFunction] = useState<string>("binary_cross_entropy");
  const [seed, setSeed] = useState<number>(42);

  // Training & Execution State
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [trainingResult, setTrainingResult] = useState<VQCTrainResponse | null>(null);
  const [trainingError, setTrainingError] = useState<string | null>(null);

  // Benchmark State
  const [isBenchmarking, setIsBenchmarking] = useState<boolean>(false);
  const [benchmarkResult, setBenchmarkResult] = useState<VQCBenchmarkResponse | null>(null);
  const [benchmarkError, setBenchmarkError] = useState<string | null>(null);

  // Live Inference State
  const [inferFeatures, setInferFeatures] = useState<number[]>([0.5, -0.2]);
  const [inferThreshold, setInferThreshold] = useState<number>(0.5);
  const [isInferring, setIsInferring] = useState<boolean>(false);
  const [inferenceResult, setInferenceResult] = useState<VQCPredictResponse | null>(null);

  // Past Experiments
  const [experiments, setExperiments] = useState<VQCExperimentRecord[]>([]);

  // Load Health & Architectures on mount
  useEffect(() => {
    async function init() {
      try {
        const [h, a] = await Promise.all([getVQCHealth(), getVQCAnsatzList()]);
        setHealth(h);
        setAnsatzList(a.ansatzes);
      } catch (err) {
        console.warn("Failed to load VQC metadata:", err);
      }
    }
    init();
  }, []);

  // Update Circuit Stats when architecture changes
  const updateCircuitInspection = useCallback(async () => {
    const selected = DATASETS.find((d) => d.id === datasetName);
    const numQubits = selected?.features === 4 && datasetName !== "iris" ? 4 : 2;
    try {
      const stats = await buildVQCCircuit({
        num_qubits: numQubits,
        ansatz_type: ansatzType,
        num_layers: numLayers,
        encoder_name: encoderName,
      });
      setCircuitStats(stats);
    } catch {
      // ignore preview error
    }
  }, [ansatzType, numLayers, encoderName, datasetName]);

  useEffect(() => {
    updateCircuitInspection();
  }, [updateCircuitInspection]);

  // Handle Training Execution
  const handleTrain = async () => {
    setIsTraining(true);
    setTrainingError(null);
    try {
      const resp = await trainVQCModel({
        dataset_name: datasetName,
        n_samples: nSamples,
        encoder_name: encoderName,
        ansatz_type: ansatzType,
        num_layers: numLayers,
        optimizer: optimizer,
        max_iter: maxIter,
        learning_rate: learningRate,
        loss_function: lossFunction,
        seed: seed,
      });
      setTrainingResult(resp);
      // Initialize inference feature vector based on dataset dimensions
      const numFeats = resp.num_qubits;
      setInferFeatures(Array(numFeats).fill(0.2));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Training failed";
      setTrainingError(msg);
    } finally {
      setIsTraining(false);
    }
  };

  // Handle Full Classical vs Quantum Benchmark
  const handleRunBenchmark = async () => {
    setIsBenchmarking(true);
    setBenchmarkError(null);
    try {
      const resp = await runVQCBenchmark({
        dataset_name: datasetName,
        n_samples: nSamples,
        encoder_name: encoderName,
        ansatz_type: ansatzType,
        num_layers: numLayers,
        max_iter: Math.min(maxIter, 40),
        seed: seed,
      });
      setBenchmarkResult(resp);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Benchmark failed";
      setBenchmarkError(msg);
    } finally {
      setIsBenchmarking(false);
    }
  };

  // Handle Live Inference
  const handleRunInference = async () => {
    if (!trainingResult || !trainingResult.weights) {
      return;
    }
    setIsInferring(true);
    try {
      const resp = await predictVQCModel({
        features: [inferFeatures],
        weights: trainingResult.weights,
        encoder_name: encoderName,
        ansatz_type: ansatzType,
        num_layers: numLayers,
        threshold: inferThreshold,
      });
      setInferenceResult(resp);
    } catch (err) {
      console.error("Inference error:", err);
    } finally {
      setIsInferring(false);
    }
  };

  // Load Experiments on demand
  const handleLoadExperiments = async () => {
    try {
      const res = await getVQCExperiments();
      setExperiments(res.experiments);
    } catch (err) {
      console.warn("Failed to load experiments:", err);
    }
  };

  const selectedDs = DATASETS.find((d) => d.id === datasetName);

  return (
    <div className="flex flex-col space-y-6 max-w-7xl mx-auto font-sans">
      {/* ── Header Card ────────────────────────────────────────────────── */}
      <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="flex h-2.5 w-2.5 rounded-full bg-purple-600 animate-pulse" />
              <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-purple-700">
                Phase 05.2 • Variational Quantum Classifier (VQC) Engine
              </span>
            </div>
            <h1 className="font-display text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Quantum Machine Learning & Hybrid Classification
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-3xl leading-relaxed">
              Parameterized quantum circuits (PQC) trained with classical optimization routines. Features exact Parameter-Shift Rule gradients, Hardware-Efficient and Strongly Entangling ansatzes, Born rule observable measurement, and rigorous head-to-head benchmarking against six classical Scikit-Learn classifiers.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-xl border border-purple-200 bg-purple-50/70 px-3 py-1.5 font-medium text-purple-800">
              Qiskit {health?.qiskit_version || "2.6.1"} • Aer {health?.qiskit_aer_version || "0.18.2"}
            </span>
            <span className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 font-medium text-slate-700">
              Scikit-Learn {health?.sklearn_version || "1.9.1"}
            </span>
          </div>
        </div>

        {/* Scientific Integrity Disclaimer */}
        <div className="mt-4 flex items-center gap-2.5 rounded-xl border border-amber-200/90 bg-amber-50/70 px-3.5 py-2.5 text-[11px] text-amber-900 leading-normal">
          <span className="font-bold uppercase tracking-wider text-amber-800 text-[10px] bg-amber-200/80 px-2 py-0.5 rounded">
            Scientific Disclaimer
          </span>
          <span>
            Quantum circuits execute via exact statevector and shot-based simulation on local classical CPU through Qiskit Aer C++ engine. No physical quantum hardware execution or quantum supremacy is claimed. Comparative benchmarks report authentic empirical execution runtimes.
          </span>
        </div>

        {/* View Mode Tabs */}
        <div className="mt-6 flex flex-wrap border-b border-slate-100 gap-1.5 overflow-x-auto text-xs font-bold pb-1">
          <button
            onClick={() => setViewMode("train")}
            className={cn(
              "flex items-center gap-1.5 border-b-2 px-3.5 py-2 transition-all whitespace-nowrap",
              viewMode === "train"
                ? "border-purple-600 text-purple-700 bg-purple-50/50 rounded-t-lg"
                : "border-transparent text-slate-500 hover:text-slate-800"
            )}
          >
            <BrainCircuit className="h-3.5 w-3.5" />
            VQC Architecture & Training
          </button>
          <button
            onClick={() => {
              setViewMode("benchmark");
              if (!benchmarkResult && !isBenchmarking) {
                handleRunBenchmark();
              }
            }}
            className={cn(
              "flex items-center gap-1.5 border-b-2 px-3.5 py-2 transition-all whitespace-nowrap",
              viewMode === "benchmark"
                ? "border-purple-600 text-purple-700 bg-purple-50/50 rounded-t-lg"
                : "border-transparent text-slate-500 hover:text-slate-800"
            )}
          >
            <Scale className="h-3.5 w-3.5" />
            Classical vs Quantum Benchmark (7 Models)
          </button>
          <button
            onClick={() => setViewMode("inference")}
            className={cn(
              "flex items-center gap-1.5 border-b-2 px-3.5 py-2 transition-all whitespace-nowrap",
              viewMode === "inference"
                ? "border-purple-600 text-purple-700 bg-purple-50/50 rounded-t-lg"
                : "border-transparent text-slate-500 hover:text-slate-800"
            )}
          >
            <FlaskConical className="h-3.5 w-3.5" />
            Live Inference Sandbox
          </button>
          <button
            onClick={() => {
              setViewMode("experiments");
              handleLoadExperiments();
            }}
            className={cn(
              "flex items-center gap-1.5 border-b-2 px-3.5 py-2 transition-all whitespace-nowrap",
              viewMode === "experiments"
                ? "border-purple-600 text-purple-700 bg-purple-50/50 rounded-t-lg"
                : "border-transparent text-slate-500 hover:text-slate-800"
            )}
          >
            <ListOrdered className="h-3.5 w-3.5" />
            Telemetry Registry
          </button>
        </div>
      </div>

      {/* ── VIEW 1: VQC ARCHITECTURE & TRAINING ──────────────────────────── */}
      {viewMode === "train" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Configuration Controls (5 Cols) */}
          <div className="lg:col-span-5 flex flex-col space-y-5">
            {/* Dataset Selector Card */}
            <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-purple-600" />
                  <h3 className="font-display text-sm font-bold text-slate-800">Dataset Selection</h3>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                  {selectedDs?.tier}
                </span>
              </div>

              <div className="space-y-2">
                {DATASETS.map((ds) => (
                  <button
                    key={ds.id}
                    onClick={() => setDatasetName(ds.id)}
                    className={cn(
                      "w-full text-left p-3 rounded-xl border transition-all text-xs flex flex-col gap-1",
                      datasetName === ds.id
                        ? "border-purple-400 bg-purple-50/40 shadow-xs"
                        : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/50"
                    )}
                  >
                    <div className="flex items-center justify-between font-bold text-slate-900">
                      <span>{ds.name}</span>
                      <span className="font-mono text-[10px] text-purple-700 bg-purple-100/70 px-1.5 py-0.5 rounded">
                        {ds.features} Feat ({ds.features === 4 && ds.id !== "iris" ? "4" : "2"} Qubits)
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 leading-snug">{ds.description}</p>
                  </button>
                ))}
              </div>

              {/* Sample Size & Seed */}
              <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    Sample Count ({nSamples})
                  </label>
                  <input
                    type="range"
                    min={40}
                    max={200}
                    step={20}
                    value={nSamples}
                    onChange={(e) => setNSamples(parseInt(e.target.value))}
                    className="w-full accent-purple-600"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    Random Seed
                  </label>
                  <input
                    type="number"
                    value={seed}
                    onChange={(e) => setSeed(parseInt(e.target.value) || 0)}
                    className="w-full rounded-lg border border-slate-200 px-2.5 py-1 text-xs"
                  />
                </div>
              </div>
            </div>

            {/* Quantum Architecture Card */}
            <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs">
              <div className="flex items-center gap-2 mb-3">
                <Cpu className="h-4 w-4 text-purple-600" />
                <h3 className="font-display text-sm font-bold text-slate-800">Quantum Circuit Architecture</h3>
              </div>

              <div className="space-y-3.5 text-xs">
                {/* Feature Encoding */}
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    Feature Map / Data Encoder
                  </label>
                  <select
                    value={encoderName}
                    onChange={(e) => setEncoderName(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-1.5 font-medium text-slate-800 bg-slate-50/50"
                  >
                    <option value="angle_ry">Angle Encoding (RY Rotations)</option>
                    <option value="angle_rx">Angle Encoding (RX Rotations)</option>
                    <option value="iqp">IQP Entangling Feature Map</option>
                    <option value="amplitude">Amplitude Encoding (L2 Normalized)</option>
                  </select>
                </div>

                {/* Parameterized Ansatz */}
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    Variational Ansatz Type
                  </label>
                  <select
                    value={ansatzType}
                    onChange={(e) => setAnsatzType(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-1.5 font-medium text-slate-800 bg-slate-50/50"
                  >
                    <option value="hardware_efficient">Hardware-Efficient Ansatz (HEA - Ry + CNOT)</option>
                    <option value="strongly_entangling">Strongly Entangling Ansatz (SEA - Euler + Entangle)</option>
                    <option value="two_local">TwoLocal Parameterized Circuit</option>
                  </select>
                </div>

                {/* Num Layers */}
                <div>
                  <div className="flex justify-between text-[11px] font-medium text-slate-600 mb-1">
                    <span>Ansatz Depth / Repetitions ({numLayers} Layers)</span>
                    <span className="font-mono text-purple-600">
                      {circuitStats ? `${circuitStats.num_parameters} Parameters` : ""}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={4}
                    value={numLayers}
                    onChange={(e) => setNumLayers(parseInt(e.target.value))}
                    className="w-full accent-purple-600"
                  />
                </div>

                {/* Circuit Inspector Pills */}
                {circuitStats && (
                  <div className="rounded-xl bg-slate-50 p-3 border border-slate-200 grid grid-cols-4 gap-2 text-center text-[10px]">
                    <div>
                      <div className="text-slate-500">Qubits</div>
                      <div className="font-bold text-slate-800 font-mono text-xs">{circuitStats.num_qubits}</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Depth</div>
                      <div className="font-bold text-slate-800 font-mono text-xs">{circuitStats.circuit_depth}</div>
                    </div>
                    <div>
                      <div className="text-slate-500">CNOTs</div>
                      <div className="font-bold text-slate-800 font-mono text-xs">{circuitStats.two_qubit_gates}</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Params</div>
                      <div className="font-bold text-purple-700 font-mono text-xs">{circuitStats.num_parameters}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Hybrid Optimization Controls Card */}
            <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs">
              <div className="flex items-center gap-2 mb-3">
                <Sliders className="h-4 w-4 text-purple-600" />
                <h3 className="font-display text-sm font-bold text-slate-800">Classical Optimizer & Loss</h3>
              </div>

              <div className="space-y-3.5 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">
                      Optimizer
                    </label>
                    <select
                      value={optimizer}
                      onChange={(e) => setOptimizer(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 px-3 py-1.5 font-medium text-slate-800 bg-slate-50/50"
                    >
                      <option value="COBYLA">COBYLA (Simplex)</option>
                      <option value="L-BFGS-B">L-BFGS-B (Param-Shift)</option>
                      <option value="Adam">Adam (Adaptive Gradient)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">
                      Loss Objective
                    </label>
                    <select
                      value={lossFunction}
                      onChange={(e) => setLossFunction(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 px-3 py-1.5 font-medium text-slate-800 bg-slate-50/50"
                    >
                      <option value="binary_cross_entropy">Binary Cross Entropy</option>
                      <option value="mean_squared_error">Mean Squared Error</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">
                      Max Iterations ({maxIter})
                    </label>
                    <input
                      type="range"
                      min={10}
                      max={60}
                      step={5}
                      value={maxIter}
                      onChange={(e) => setMaxIter(parseInt(e.target.value))}
                      className="w-full accent-purple-600"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">
                      Learning Rate ({learningRate})
                    </label>
                    <input
                      type="range"
                      min={0.01}
                      max={0.2}
                      step={0.01}
                      value={learningRate}
                      onChange={(e) => setLearningRate(parseFloat(e.target.value))}
                      className="w-full accent-purple-600"
                    />
                  </div>
                </div>

                {/* Train Action Button */}
                <button
                  onClick={handleTrain}
                  disabled={isTraining}
                  className={cn(
                    "w-full flex items-center justify-center gap-2 rounded-xl py-3 text-xs font-bold text-white transition-all shadow-md mt-2",
                    isTraining
                      ? "bg-slate-400 cursor-not-allowed"
                      : "bg-purple-600 hover:bg-purple-700 active:scale-[0.99]"
                  )}
                >
                  {isTraining ? (
                    <>
                      <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                      Training Quantum Circuit... ({maxIter} Iterations)
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 fill-white" />
                      Train Variational Quantum Classifier (VQC)
                    </>
                  )}
                </button>

                {trainingError && (
                  <div className="rounded-xl border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-800 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
                    <span>{trainingError}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Training Telemetry & Results (7 Cols) */}
          <div className="lg:col-span-7 flex flex-col space-y-5">
            {trainingResult ? (
              <>
                {/* KPI Metrics Row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      Test Accuracy
                    </span>
                    <div className="mt-1 font-display text-2xl font-bold text-purple-700">
                      {(trainingResult.test_metrics.accuracy * 100).toFixed(1)}%
                    </div>
                    <span className="text-[10px] text-slate-400">
                      F1: {trainingResult.test_metrics.f1_score.toFixed(3)}
                    </span>
                  </div>

                  <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      ROC-AUC Score
                    </span>
                    <div className="mt-1 font-display text-2xl font-bold text-slate-900">
                      {trainingResult.test_metrics.roc_auc.toFixed(3)}
                    </div>
                    <span className="text-[10px] text-slate-400">
                      Area Under Curve
                    </span>
                  </div>

                  <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      Training Runtime
                    </span>
                    <div className="mt-1 font-display text-2xl font-bold text-slate-900">
                      {(trainingResult.training_time_ms / 1000).toFixed(2)}s
                    </div>
                    <span className="text-[10px] text-slate-400">
                      {trainingResult.iterations} Iterations
                    </span>
                  </div>

                  <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      Quantum Evals
                    </span>
                    <div className="mt-1 font-display text-2xl font-bold text-slate-900">
                      {trainingResult.quantum_circuit_evaluations}
                    </div>
                    <span className="text-[10px] text-slate-400">
                      Circuit Passes
                    </span>
                  </div>
                </div>

                {/* Convergence Curve Chart */}
                <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <TrendingDown className="h-4 w-4 text-purple-600" />
                      <h3 className="font-display text-sm font-bold text-slate-800">
                        Convergence Telemetry (Loss vs Iteration)
                      </h3>
                    </div>
                    <span className="font-mono text-xs text-purple-700 bg-purple-50 px-2 py-0.5 rounded-lg border border-purple-200">
                      Final Loss: {trainingResult.final_train_loss.toFixed(4)}
                    </span>
                  </div>

                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={trainingResult.history}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis
                          dataKey="iteration"
                          stroke="#94a3b8"
                          fontSize={11}
                          tickLine={false}
                          label={{ value: "Iteration Step", position: "insideBottom", offset: -2, fontSize: 10, fill: "#64748b" }}
                        />
                        <YAxis
                          stroke="#94a3b8"
                          fontSize={11}
                          tickLine={false}
                          domain={["auto", "auto"]}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#ffffff",
                            borderColor: "#e2e8f0",
                            borderRadius: "0.75rem",
                            fontSize: "12px",
                            boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                          }}
                        />
                        <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
                        <Line
                          type="monotone"
                          dataKey="train_loss"
                          name="Train Loss"
                          stroke="#7c3aed"
                          strokeWidth={2.5}
                          dot={{ r: 2 }}
                        />
                        {trainingResult.history[0]?.val_loss !== undefined && (
                          <Line
                            type="monotone"
                            dataKey="val_loss"
                            name="Validation Loss"
                            stroke="#0ea5e9"
                            strokeWidth={2}
                            strokeDasharray="4 4"
                            dot={false}
                          />
                        )}
                        <Line
                          type="monotone"
                          dataKey="train_accuracy"
                          name="Train Accuracy"
                          stroke="#10b981"
                          strokeWidth={1.5}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Confusion Matrix & Detailed Metrics */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Confusion Matrix 2x2 */}
                  <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs">
                    <h4 className="text-xs font-bold text-slate-800 mb-3 flex items-center gap-1.5">
                      <Target className="h-3.5 w-3.5 text-purple-600" />
                      Test Confusion Matrix
                    </h4>
                    <div className="grid grid-cols-2 gap-2 text-center text-xs">
                      <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                        <div className="text-[10px] text-slate-500 uppercase font-bold">True Negative (TN)</div>
                        <div className="text-xl font-bold text-slate-800 font-mono mt-1">
                          {trainingResult.test_metrics.confusion_matrix.tn}
                        </div>
                        <div className="text-[10px] text-emerald-600 font-medium">Class 0 Correct</div>
                      </div>
                      <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                        <div className="text-[10px] text-slate-500 uppercase font-bold">False Positive (FP)</div>
                        <div className="text-xl font-bold text-slate-800 font-mono mt-1">
                          {trainingResult.test_metrics.confusion_matrix.fp}
                        </div>
                        <div className="text-[10px] text-rose-500 font-medium">Type I Error</div>
                      </div>
                      <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                        <div className="text-[10px] text-slate-500 uppercase font-bold">False Negative (FN)</div>
                        <div className="text-xl font-bold text-slate-800 font-mono mt-1">
                          {trainingResult.test_metrics.confusion_matrix.fn}
                        </div>
                        <div className="text-[10px] text-rose-500 font-medium">Type II Error</div>
                      </div>
                      <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                        <div className="text-[10px] text-slate-500 uppercase font-bold">True Positive (TP)</div>
                        <div className="text-xl font-bold text-slate-800 font-mono mt-1">
                          {trainingResult.test_metrics.confusion_matrix.tp}
                        </div>
                        <div className="text-[10px] text-emerald-600 font-medium">Class 1 Correct</div>
                      </div>
                    </div>
                  </div>

                  {/* Learned Weights Preview */}
                  <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs">
                    <h4 className="text-xs font-bold text-slate-800 mb-3 flex items-center gap-1.5">
                      <Binary className="h-3.5 w-3.5 text-purple-600" />
                      Learned Parameter Vector ({trainingResult.weights.length} Parameters)
                    </h4>
                    <div className="max-h-40 overflow-y-auto rounded-xl bg-slate-50 p-2 border border-slate-200 font-mono text-[11px] text-slate-700 space-y-1">
                      {trainingResult.weights.map((w, idx) => (
                        <div key={idx} className="flex justify-between px-2 py-0.5 rounded hover:bg-slate-100">
                          <span className="text-slate-400">θ[{idx}]:</span>
                          <span className="font-bold">{w.toFixed(5)} rad</span>
                        </div>
                      ))}
                    </div>
                    <div className="mt-3 text-[10px] text-slate-500 leading-tight">
                      Experiment ID: <span className="font-mono text-purple-700">{trainingResult.experiment_id}</span>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/50 p-12 text-center flex flex-col items-center justify-center my-auto min-h-[420px]">
                <BrainCircuit className="h-12 w-12 text-purple-300 mb-3 animate-pulse" />
                <h3 className="font-display text-base font-bold text-slate-700">No VQC Model Trained Yet</h3>
                <p className="text-xs text-slate-500 max-w-md mt-1">
                  Configure your dataset, feature map, parameterized ansatz, and classical optimizer on the left, then click <b>Train Variational Quantum Classifier</b> to execute the hybrid training loop.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── VIEW 2: HEAD-TO-HEAD BENCHMARK (7 MODELS) ────────────────────── */}
      {viewMode === "benchmark" && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200/90 bg-white p-5 sm:p-6 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h3 className="font-display text-base font-bold text-slate-900">
                  Head-to-Head Comparative Benchmark Suite
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Scientific evaluation of VQC vs 6 classical machine learning algorithms on identical train/test splits.
                </p>
              </div>
              <button
                onClick={handleRunBenchmark}
                disabled={isBenchmarking}
                className={cn(
                  "flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold text-white transition-all shadow-xs",
                  isBenchmarking
                    ? "bg-slate-400 cursor-not-allowed"
                    : "bg-purple-600 hover:bg-purple-700 active:scale-[0.99]"
                )}
              >
                {isBenchmarking ? (
                  <>
                    <span className="h-3.5 w-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
                    Executing Benchmark (7 Models)...
                  </>
                ) : (
                  <>
                    <RotateCcw className="h-3.5 w-3.5" />
                    Re-Run Full Benchmark
                  </>
                )}
              </button>
            </div>

            {benchmarkError && (
              <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
                <span>{benchmarkError}</span>
              </div>
            )}

            {benchmarkResult ? (
              <div className="mt-6 space-y-6">
                {/* Benchmark Comparison Table */}
                <div className="overflow-x-auto rounded-xl border border-slate-200">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="px-4 py-3">Model Architecture</th>
                        <th className="px-3 py-3">Paradigm</th>
                        <th className="px-3 py-3">Accuracy</th>
                        <th className="px-3 py-3">F1-Score</th>
                        <th className="px-3 py-3">ROC-AUC</th>
                        <th className="px-3 py-3">Train Time (ms)</th>
                        <th className="px-3 py-3">Inference Latency</th>
                        <th className="px-3 py-3">Parameters</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {benchmarkResult.models.map((m, idx) => (
                        <tr
                          key={idx}
                          className={cn(
                            "hover:bg-slate-50/60 transition-colors",
                            m.is_quantum ? "bg-purple-50/30 font-semibold" : ""
                          )}
                        >
                          <td className="px-4 py-3 flex items-center gap-2">
                            {m.is_quantum ? (
                              <BrainCircuit className="h-4 w-4 text-purple-600 shrink-0" />
                            ) : (
                              <Cpu className="h-4 w-4 text-slate-400 shrink-0" />
                            )}
                            <span className={m.is_quantum ? "text-purple-900 font-bold" : "text-slate-800"}>
                              {m.model_name}
                            </span>
                          </td>
                          <td className="px-3 py-3">
                            <span
                              className={cn(
                                "text-[10px] font-mono font-bold px-2 py-0.5 rounded-full",
                                m.is_quantum
                                  ? "bg-purple-100 text-purple-700 border border-purple-200"
                                  : "bg-slate-100 text-slate-600 border border-slate-200"
                              )}
                            >
                              {m.is_quantum ? "Quantum (PQC)" : "Classical ML"}
                            </span>
                          </td>
                          <td className="px-3 py-3 font-mono font-bold text-slate-900">
                            {(m.accuracy * 100).toFixed(1)}%
                          </td>
                          <td className="px-3 py-3 font-mono">{m.f1_score.toFixed(3)}</td>
                          <td className="px-3 py-3 font-mono">{m.roc_auc.toFixed(3)}</td>
                          <td className="px-3 py-3 font-mono text-slate-600">
                            {m.training_time_ms.toFixed(1)} ms
                          </td>
                          <td className="px-3 py-3 font-mono text-slate-600">
                            {m.inference_latency_ms.toFixed(2)} ms
                          </td>
                          <td className="px-3 py-3 font-mono text-slate-600">{m.num_parameters}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Summary Findings & Scientific Observations */}
                <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 space-y-2">
                  <div className="flex items-center gap-2 font-display text-xs font-bold text-slate-800">
                    <Info className="h-4 w-4 text-purple-600" />
                    Forensic Scientific Observations
                  </div>
                  <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-5">
                    {benchmarkResult.summary_findings.map((f, i) => (
                      <li key={i} className="leading-relaxed">
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500 text-xs">
                Click <b>Re-Run Full Benchmark</b> to execute the 7-model benchmark suite.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── VIEW 3: LIVE INFERENCE SANDBOX ───────────────────────────────── */}
      {viewMode === "inference" && (
        <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs max-w-3xl mx-auto">
          <div className="flex items-center gap-2 mb-4">
            <FlaskConical className="h-5 w-5 text-purple-600" />
            <div>
              <h3 className="font-display text-base font-bold text-slate-900">Live Single-Sample Quantum Inference</h3>
              <p className="text-xs text-slate-500">
                Evaluate single feature vectors through the trained parameterized circuit. Computes the expectation value ⟨Z₀⟩ and maps Born rule probabilities.
              </p>
            </div>
          </div>

          {!trainingResult ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" />
              <span>Please train a VQC model first in the "VQC Architecture & Training" tab before running live inference.</span>
            </div>
          ) : (
            <div className="space-y-5 text-xs">
              {/* Feature Inputs */}
              <div className="space-y-3">
                <label className="block text-xs font-bold text-slate-700">
                  Feature Vector Values ({inferFeatures.length} Dimensions)
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {inferFeatures.map((val, idx) => (
                    <div key={idx} className="p-3 rounded-xl border border-slate-200 bg-slate-50/50">
                      <label className="block text-[10px] font-bold text-slate-500 mb-1">
                        Feature x[{idx}]
                      </label>
                      <input
                        type="number"
                        step={0.1}
                        value={val}
                        onChange={(e) => {
                          const next = [...inferFeatures];
                          next[idx] = parseFloat(e.target.value) || 0;
                          setInferFeatures(next);
                        }}
                        className="w-full rounded-lg border border-slate-200 px-2 py-1 text-xs font-mono"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Threshold Slider */}
              <div>
                <div className="flex justify-between text-xs font-medium text-slate-600 mb-1">
                  <span>Decision Threshold</span>
                  <span className="font-mono text-purple-700 font-bold">{inferThreshold}</span>
                </div>
                <input
                  type="range"
                  min={0.1}
                  max={0.9}
                  step={0.05}
                  value={inferThreshold}
                  onChange={(e) => setInferThreshold(parseFloat(e.target.value))}
                  className="w-full accent-purple-600"
                />
              </div>

              {/* Predict Button */}
              <button
                onClick={handleRunInference}
                disabled={isInferring}
                className={cn(
                  "w-full flex items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold text-white transition-all shadow-xs",
                  isInferring
                    ? "bg-slate-400 cursor-not-allowed"
                    : "bg-purple-600 hover:bg-purple-700 active:scale-[0.99]"
                )}
              >
                {isInferring ? (
                  <>
                    <span className="h-3.5 w-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
                    Executing Quantum Forward Pass...
                  </>
                ) : (
                  <>
                    <Play className="h-3.5 w-3.5 fill-white" />
                    Execute Inference Pass
                  </>
                )}
              </button>

              {/* Inference Result Display */}
              {inferenceResult && (
                <div className="mt-4 rounded-xl border border-purple-200 bg-purple-50/40 p-4 grid grid-cols-2 sm:grid-cols-3 gap-3 text-center">
                  <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase">Predicted Class</div>
                    <div className="font-display text-2xl font-bold text-purple-700 mt-0.5">
                      Class {inferenceResult.predictions[0]}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase">Probability P(y=1)</div>
                    <div className="font-display text-2xl font-bold text-slate-800 mt-0.5 font-mono">
                      {(inferenceResult.probabilities[0][1] * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase">Latency</div>
                    <div className="font-display text-2xl font-bold text-slate-800 mt-0.5 font-mono">
                      {inferenceResult.inference_time_ms.toFixed(2)} ms
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── VIEW 4: EXPERIMENT REGISTRY ─────────────────────────────────── */}
      {viewMode === "experiments" && (
        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 sm:p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-display text-base font-bold text-slate-900">VQC Experiment Registry</h3>
              <p className="text-xs text-slate-500">
                Persisted session records of variational training runs, loss histories, and learned weights.
              </p>
            </div>
            <button
              onClick={handleLoadExperiments}
              className="flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-50"
            >
              <RotateCcw className="h-3 w-3" />
              Refresh
            </button>
          </div>

          {experiments.length === 0 ? (
            <div className="text-center p-8 text-xs text-slate-400">
              No training experiments recorded yet in this session.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-4 py-3">Experiment ID</th>
                    <th className="px-3 py-3">Dataset</th>
                    <th className="px-3 py-3">Ansatz</th>
                    <th className="px-3 py-3">Optimizer</th>
                    <th className="px-3 py-3">Test Accuracy</th>
                    <th className="px-3 py-3">Runtime</th>
                    <th className="px-3 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {experiments.map((exp) => (
                    <tr key={exp.experiment_id} className="hover:bg-slate-50/60">
                      <td className="px-4 py-2.5 font-mono text-purple-700 font-semibold">{exp.experiment_id}</td>
                      <td className="px-3 py-2.5 font-medium text-slate-800">{exp.dataset_name}</td>
                      <td className="px-3 py-2.5 text-slate-600">{exp.ansatz_type}</td>
                      <td className="px-3 py-2.5 text-slate-600">{exp.optimizer}</td>
                      <td className="px-3 py-2.5 font-mono font-bold text-slate-900">
                        {(exp.test_accuracy * 100).toFixed(1)}%
                      </td>
                      <td className="px-3 py-2.5 font-mono text-slate-500">
                        {(exp.training_time_ms / 1000).toFixed(2)}s
                      </td>
                      <td className="px-3 py-2.5">
                        <span className="font-mono text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                          {exp.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
