import React, { useState, useEffect } from "react";
import {
  Activity,
  Sliders,
  Play,
  RotateCcw,
  Sparkles,
  Info,
  Layers,
  Zap,
  TrendingDown,
  ShieldAlert,
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
  Legend,
} from "recharts";
import {
  simulateNoise,
  simulateDecoherence,
  applyQuantumChannel,
  type NoiseSimulateResponse,
  type DecoherenceSimulateResponse,
  type QuantumChannelResponse,
} from "../../lib/api";

export default function NoiseDecoherenceLab() {
  const [subTab, setSubTab] = useState<"noise_models" | "decoherence_trajectory" | "kraus_channels">("noise_models");

  // Tab 1: Circuit Noise State
  const [noiseType, setNoiseType] = useState<string>("depolarizing");
  const [errorProb, setErrorProb] = useState<number>(0.05);
  const [noiseShots, setNoiseShots] = useState<number>(2048);
  const [noiseResult, setNoiseResult] = useState<NoiseSimulateResponse | null>(null);
  const [noiseLoading, setNoiseLoading] = useState<boolean>(false);

  // Tab 2: Decoherence Trajectory State
  const [initialStateName, setInitialStateName] = useState<string>("plus");
  const [t1Us, setT1Us] = useState<number>(50.0);
  const [t2Us, setT2Us] = useState<number>(30.0);
  const [totalTimeUs, setTotalTimeUs] = useState<number>(100.0);
  const [decoResult, setDecoResult] = useState<DecoherenceSimulateResponse | null>(null);
  const [decoLoading, setDecoLoading] = useState<boolean>(false);

  // Tab 3: Kraus Channels State
  const [channelType, setChannelType] = useState<string>("depolarizing");
  const [channelPreset, setChannelPreset] = useState<string>("pure_plus");
  const [channelP, setChannelP] = useState<number>(0.15);
  const [channelResult, setChannelResult] = useState<QuantumChannelResponse | null>(null);
  const [channelLoading, setChannelLoading] = useState<boolean>(false);

  // Run Noise Sim
  const handleRunNoise = async () => {
    setNoiseLoading(true);
    try {
      const res = await simulateNoise({
        operations: [
          { gate: "H", targets: [0], controls: [] },
          { gate: "CX", targets: [1], controls: [0] },
        ],
        num_qubits: 2,
        noise_type: noiseType,
        error_prob: errorProb,
        gamma: errorProb,
        lambda_param: errorProb,
        shots: noiseShots,
      });
      setNoiseResult(res);
    } catch (e) {
      console.error("Noise sim error:", e);
    } finally {
      setNoiseLoading(false);
    }
  };

  // Run Decoherence Sim
  const handleRunDecoherence = async () => {
    setDecoLoading(true);
    try {
      const res = await simulateDecoherence({
        initial_state_name: initialStateName,
        t1_us: t1Us,
        t2_us: Math.min(t2Us, 2 * t1Us), // Enforce T2 <= 2T1 physically
        total_time_us: totalTimeUs,
        num_steps: 40,
      });
      setDecoResult(res);
    } catch (e) {
      console.error("Decoherence sim error:", e);
    } finally {
      setDecoLoading(false);
    }
  };

  // Run Kraus Channel
  const handleRunChannel = async () => {
    setChannelLoading(true);
    try {
      const res = await applyQuantumChannel({
        channel_type: channelType,
        input_state_preset: channelPreset,
        param_p: channelP,
        gamma: channelP,
        lambda_param: channelP,
      });
      setChannelResult(res);
    } catch (e) {
      console.error("Channel error:", e);
    } finally {
      setChannelLoading(false);
    }
  };

  useEffect(() => {
    if (subTab === "noise_models") handleRunNoise();
    if (subTab === "decoherence_trajectory") handleRunDecoherence();
    if (subTab === "kraus_channels") handleRunChannel();
  }, [subTab, noiseType, errorProb, noiseShots, initialStateName, t1Us, t2Us, totalTimeUs, channelType, channelPreset, channelP]);

  return (
    <div className="space-y-6">
      {/* Top Card & Subtab Navigation */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-amber-600" />
              <h2 className="font-display text-lg font-bold text-slate-900">
                Quantum Noise, Decoherence & Open Quantum Systems
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Model environmental noise, T1 thermal relaxation, T2 dephasing, and completely positive trace-preserving (CPTP) Kraus maps to understand decoherence in realistic quantum architectures.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800">
              Qiskit Aer Noise Engine (Classical C++)
            </span>
          </div>
        </div>

        {/* Sub-tabs */}
        <div className="mt-6 flex border-b border-slate-100 gap-2 overflow-x-auto text-xs font-bold">
          <button
            onClick={() => setSubTab("noise_models")}
            className={`border-b-2 px-4 py-2.5 transition-all ${
              subTab === "noise_models"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            Circuit Noise Simulation (Aer)
          </button>
          <button
            onClick={() => setSubTab("decoherence_trajectory")}
            className={`border-b-2 px-4 py-2.5 transition-all ${
              subTab === "decoherence_trajectory"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            T₁ / T₂ Decoherence Trajectory
          </button>
          <button
            onClick={() => setSubTab("kraus_channels")}
            className={`border-b-2 px-4 py-2.5 transition-all ${
              subTab === "kraus_channels"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            CPTP Quantum Channels (Kraus)
          </button>
        </div>
      </div>

      {/* ── SUBTAB 1: CIRCUIT NOISE SIMULATION ────────────────────────────── */}
      {subTab === "noise_models" && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Noise Channel Model
                </label>
                <select
                  value={noiseType}
                  onChange={(e) => setNoiseType(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:bg-white focus:outline-none"
                >
                  <option value="depolarizing">Depolarizing Channel (Isotropic Noise)</option>
                  <option value="bit_flip">Bit-Flip Channel (Pauli X)</option>
                  <option value="phase_flip">Phase-Flip Channel (Pauli Z)</option>
                  <option value="amplitude_damping">Amplitude Damping (Energy Loss)</option>
                  <option value="phase_damping">Phase Damping (Pure Dephasing)</option>
                  <option value="thermal_relaxation">Thermal Relaxation (T1/T2)</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between items-center text-xs">
                  <label className="font-bold uppercase tracking-wider text-slate-500">
                    Error Probability / Parameter
                  </label>
                  <span className="font-mono text-slate-700 font-bold">
                    {(errorProb * 100).toFixed(1)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="0.4"
                  step="0.01"
                  value={errorProb}
                  onChange={(e) => setErrorProb(parseFloat(e.target.value))}
                  className="mt-2.5 w-full accent-blue-600 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between items-center text-xs">
                  <label className="font-bold uppercase tracking-wider text-slate-500">
                    Measurement Shots
                  </label>
                  <span className="font-mono text-slate-700 font-bold">
                    {noiseShots}
                  </span>
                </div>
                <input
                  type="range"
                  min="512"
                  max="4096"
                  step="512"
                  value={noiseShots}
                  onChange={(e) => setNoiseShots(parseInt(e.target.value))}
                  className="mt-2.5 w-full accent-blue-600 cursor-pointer"
                />
              </div>
            </div>
          </div>

          {noiseResult && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Histogram Side-by-side */}
              <div className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-display text-sm font-bold text-slate-900">
                    Ideal (Noiseless) vs. Noisy Bell State |Φ+⟩ Measurement Distribution
                  </h3>
                  <span className="text-xs font-mono text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200 font-bold">
                    TVD: {noiseResult.total_variation_distance.toFixed(4)}
                  </span>
                </div>

                <div className="h-[280px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={noiseResult.distribution_comparison}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="bitstring" tick={{ fill: "#334155", fontSize: 11, fontFamily: "monospace" }} />
                      <YAxis tick={{ fill: "#64748b", fontSize: 10 }} unit="%" />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                      />
                      <Legend wrapperStyle={{ fontSize: "11px", fontFamily: "monospace" }} />
                      <Bar dataKey="ideal_frequency" name="Ideal Noiseless (%)" fill="#2563eb" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="noisy_frequency" name="Noisy Simulated (%)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Degradation Card */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4 text-xs">
                <h3 className="font-display text-sm font-bold text-slate-900">
                  Fidelity & Purity Degradation
                </h3>

                <div className="p-3 rounded-xl border border-amber-200 bg-amber-50/50 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-amber-900 font-bold">Total Variation Distance (TVD):</span>
                    <span className="font-mono font-bold text-amber-700">
                      {noiseResult.total_variation_distance.toFixed(4)}
                    </span>
                  </div>
                  <p className="text-[10px] text-amber-800 leading-relaxed">
                    TVD measures statistical divergence between ideal and noisy output distributions: 0 = identical, 1 = completely disjoint.
                  </p>
                </div>

                <div className="p-3 rounded-xl border border-slate-100 bg-slate-50 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Estimated Noisy Purity Tr(ρ²):</span>
                    <span className="font-mono font-bold text-slate-800">
                      {noiseResult.noisy_purity_estimate.toFixed(4)}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 block">
                    Ideal Bell state purity is exactly 1.000. Noise reduces pure states into mixed statistical ensembles.
                  </span>
                </div>

                <div className="p-3 rounded-xl border border-slate-100 bg-slate-50 space-y-1">
                  <span className="text-slate-600 block font-bold">Unwanted Error Leakage:</span>
                  <div className="space-y-1 pt-1 font-mono text-[11px]">
                    {noiseResult.distribution_comparison.map((item) => (
                      <div key={item.bitstring} className="flex justify-between">
                        <span className="text-slate-500">|{item.bitstring}⟩:</span>
                        <span className={item.delta > 0.01 ? "text-amber-700 font-bold" : "text-slate-700"}>
                          Δ = {item.delta >= 0 ? "+" : ""}{item.delta.toFixed(2)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── SUBTAB 2: DECOHERENCE TRAJECTORY ─────────────────────────────── */}
      {subTab === "decoherence_trajectory" && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Initial State |ψ(0)⟩
                </label>
                <select
                  value={initialStateName}
                  onChange={(e) => setInitialStateName(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:bg-white focus:outline-none"
                >
                  <option value="plus">|+⟩ Superposition (X-axis)</option>
                  <option value="one">|1⟩ Excited State (Z-pole)</option>
                  <option value="plus_i">|+i⟩ Phase State (Y-axis)</option>
                  <option value="zero">|0⟩ Ground State (Relaxation Target)</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between items-center text-xs">
                  <label className="font-bold uppercase tracking-wider text-slate-500">
                    T₁ Relaxation Time
                  </label>
                  <span className="font-mono text-slate-700 font-bold">{t1Us.toFixed(1)} µs</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="150"
                  step="5"
                  value={t1Us}
                  onChange={(e) => setT1Us(parseFloat(e.target.value))}
                  className="mt-2.5 w-full accent-blue-600 cursor-pointer"
                />
                <span className="text-[10px] text-slate-400 block mt-1">Energy decay: |1⟩ → |0⟩</span>
              </div>

              <div>
                <div className="flex justify-between items-center text-xs">
                  <label className="font-bold uppercase tracking-wider text-slate-500">
                    T₂ Dephasing Time
                  </label>
                  <span className="font-mono text-slate-700 font-bold">{t2Us.toFixed(1)} µs</span>
                </div>
                <input
                  type="range"
                  min="2"
                  max={2 * t1Us}
                  step="2"
                  value={t2Us}
                  onChange={(e) => setT2Us(parseFloat(e.target.value))}
                  className="mt-2.5 w-full accent-blue-600 cursor-pointer"
                />
                <span className="text-[10px] text-slate-400 block mt-1">Bound: T₂ ≤ 2T₁</span>
              </div>

              <div>
                <div className="flex justify-between items-center text-xs">
                  <label className="font-bold uppercase tracking-wider text-slate-500">
                    Total Simulation Time
                  </label>
                  <span className="font-mono text-slate-700 font-bold">{totalTimeUs.toFixed(1)} µs</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="300"
                  step="10"
                  value={totalTimeUs}
                  onChange={(e) => setTotalTimeUs(parseFloat(e.target.value))}
                  className="mt-2.5 w-full accent-blue-600 cursor-pointer"
                />
              </div>
            </div>
          </div>

          {decoResult && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-display text-sm font-bold text-slate-900">
                    Continuous Open-System Trajectory: Population & Coherence Decay
                  </h3>
                  <span className="text-xs font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-bold">
                    T₂ ≤ 2T₁ Constraint Verified
                  </span>
                </div>

                <div className="h-[280px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={decoResult.trajectory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="time_us" tick={{ fill: "#64748b", fontSize: 10, fontFamily: "monospace" }} unit="µs" />
                      <YAxis tick={{ fill: "#64748b", fontSize: 10 }} domain={[0, 1]} />
                      <Tooltip contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0" }} />
                      <Legend wrapperStyle={{ fontSize: "11px", fontFamily: "monospace" }} />
                      <Line type="monotone" dataKey="rho_00" name="Ground Population ρ₀₀" stroke="#2563eb" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="rho_11" name="Excited Population ρ₁₁" stroke="#dc2626" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="abs_rho_01" name="Coherence |ρ₀₁|" stroke="#059669" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="purity" name="Purity Tr(ρ²)" stroke="#7c3aed" strokeWidth={1.5} strokeDasharray="3 3" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Bloch Vector Shrinkage Card */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4 text-xs">
                <h3 className="font-display text-sm font-bold text-slate-900">
                  Bloch Sphere Trajectory
                </h3>

                <div className="p-3 rounded-xl border border-slate-100 bg-slate-50 space-y-2">
                  <span className="text-slate-600 block font-bold">Final State at t = {totalTimeUs} µs:</span>
                  {decoResult.trajectory.length > 0 && (
                    <div className="font-mono text-xs space-y-1">
                      <div className="flex justify-between">
                        <span>Purity Tr(ρ²):</span>
                        <span className="font-bold text-purple-700">
                          {decoResult.trajectory[decoResult.trajectory.length - 1].purity.toFixed(4)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Entropy S(ρ):</span>
                        <span className="font-bold text-slate-800">
                          {decoResult.trajectory[decoResult.trajectory.length - 1].von_neumann_entropy.toFixed(4)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Bloch Vector Length |r|:</span>
                        <span className="font-bold text-blue-700">
                          {decoResult.trajectory[decoResult.trajectory.length - 1].bloch_vector.length.toFixed(4)}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="p-3 rounded-xl border border-blue-100 bg-blue-50/50 space-y-1">
                  <span className="text-blue-900 font-bold block">Physical Mechanism:</span>
                  <p className="text-[10px] text-blue-800 leading-relaxed">
                    Transverse coherence |ρ₀₁| decays as exp(-t/T₂), causing the Bloch vector to shrink inward. Longitudinal population ρ₁₁ decays toward the ground state as exp(-t/T₁).
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── SUBTAB 3: KRAUS CHANNELS ─────────────────────────────────────── */}
      {subTab === "kraus_channels" && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  CPTP Quantum Channel
                </label>
                <select
                  value={channelType}
                  onChange={(e) => setChannelType(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:bg-white focus:outline-none"
                >
                  <option value="depolarizing">Depolarizing Channel (4 Kraus operators)</option>
                  <option value="amplitude_damping">Amplitude Damping (2 Kraus operators)</option>
                  <option value="phase_damping">Phase Damping (2 Kraus operators)</option>
                  <option value="bit_flip">Bit-Flip Channel (2 Kraus operators)</option>
                  <option value="phase_flip">Phase-Flip Channel (2 Kraus operators)</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Input State ρ
                </label>
                <select
                  value={channelPreset}
                  onChange={(e) => setChannelPreset(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:bg-white focus:outline-none"
                >
                  <option value="pure_plus">|+⟩ Superposition State</option>
                  <option value="pure_zero">|0⟩ Ground State</option>
                  <option value="pure_one">|1⟩ Excited State</option>
                  <option value="pure_plus_i">|+i⟩ Circular State</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between items-center text-xs">
                  <label className="font-bold uppercase tracking-wider text-slate-500">
                    Channel Parameter (p / γ / λ)
                  </label>
                  <span className="font-mono text-slate-700 font-bold">{channelP.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="0.8"
                  step="0.05"
                  value={channelP}
                  onChange={(e) => setChannelP(parseFloat(e.target.value))}
                  className="mt-2.5 w-full accent-blue-600 cursor-pointer"
                />
              </div>
            </div>
          </div>

          {channelResult && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Properties Card */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4 text-xs">
                <h3 className="font-display text-sm font-bold text-slate-900">
                  Channel Axioms & Kraus Completeness
                </h3>

                <div className="flex items-center justify-between p-3 rounded-xl border border-slate-100 bg-slate-50">
                  <span className="font-bold text-slate-700">Trace Preservation Σ E_k† E_k = I:</span>
                  <span className="font-mono font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
                    {channelResult.is_trace_preserving ? "VERIFIED (CPTP)" : "VIOLATED"}
                  </span>
                </div>

                <div className="flex justify-between p-3 rounded-xl border border-slate-100 bg-slate-50 font-mono">
                  <span className="text-slate-600">Kraus Operators Count:</span>
                  <span className="font-bold text-slate-900">{channelResult.num_kraus_operators}</span>
                </div>

                <div className="flex justify-between p-3 rounded-xl border border-slate-100 bg-slate-50 font-mono">
                  <span className="text-slate-600">Purity Degradation:</span>
                  <span className="font-bold text-blue-700">
                    {channelResult.input_purity.toFixed(3)} ➔ {channelResult.output_purity.toFixed(3)}
                  </span>
                </div>

                <div className="flex justify-between p-3 rounded-xl border border-slate-100 bg-slate-50 font-mono">
                  <span className="text-slate-600">Output State Fidelity F:</span>
                  <span className="font-bold text-slate-900">{channelResult.state_fidelity.toFixed(4)}</span>
                </div>
              </div>

              {/* Bloch Shrinkage Card */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4 text-xs">
                <h3 className="font-display text-sm font-bold text-slate-900">
                  Affine Bloch Sphere Shrinkage Matrix
                </h3>
                <p className="text-slate-500 text-[11px]">
                  Any CPTP single-qubit channel transforms the Bloch vector via an affine map: r⃗' = M r⃗ + c⃗.
                </p>

                <div className="grid grid-cols-3 gap-2 text-center font-mono">
                  <div className="p-2.5 bg-blue-50 rounded-xl border border-blue-100">
                    <span className="text-[10px] text-blue-600 block">X Scale (η_x)</span>
                    <span className="font-bold text-blue-900">{channelResult.bloch_shrinkage.x_scale.toFixed(3)}</span>
                  </div>
                  <div className="p-2.5 bg-emerald-50 rounded-xl border border-emerald-100">
                    <span className="text-[10px] text-emerald-600 block">Y Scale (η_y)</span>
                    <span className="font-bold text-emerald-900">{channelResult.bloch_shrinkage.y_scale.toFixed(3)}</span>
                  </div>
                  <div className="p-2.5 bg-purple-50 rounded-xl border border-purple-100">
                    <span className="text-[10px] text-purple-600 block">Z Scale (η_z)</span>
                    <span className="font-bold text-purple-900">{channelResult.bloch_shrinkage.z_scale.toFixed(3)}</span>
                  </div>
                </div>

                <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 font-mono text-center">
                  <span className="text-[10px] text-slate-500 block">Z Shift Translation (c_z)</span>
                  <span className="font-bold text-slate-800">{channelResult.bloch_shrinkage.z_shift.toFixed(3)}</span>
                </div>
              </div>

              {/* Kraus Operators Display */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4 text-xs">
                <h3 className="font-display text-sm font-bold text-slate-900">
                  Kraus Operators E_k
                </h3>
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {channelResult.kraus_operators.map((op, idx) => (
                    <div key={idx} className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 font-mono text-[11px]">
                      <span className="font-bold text-slate-700 block mb-1">E_{idx}:</span>
                      <div className="grid grid-cols-2 gap-1 text-center">
                        <span className="bg-white p-1 rounded border border-slate-200">{op[0][0].real.toFixed(3)}</span>
                        <span className="bg-white p-1 rounded border border-slate-200">{op[0][1].real.toFixed(3)}</span>
                        <span className="bg-white p-1 rounded border border-slate-200">{op[1][0].real.toFixed(3)}</span>
                        <span className="bg-white p-1 rounded border border-slate-200">{op[1][1].real.toFixed(3)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
