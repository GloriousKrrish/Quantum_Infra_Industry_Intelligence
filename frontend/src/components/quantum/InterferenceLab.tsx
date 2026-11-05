import React, { useState, useEffect } from "react";
import {
  Waves,
  Play,
  RotateCcw,
  Sparkles,
  Info,
  CheckCircle2,
  Sliders,
  TrendingUp,
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
  simulateInterference,
  type InterferenceSimulateResponse,
} from "../../lib/api";

const PRESET_PHASES = [
  { label: "0 (Constructive)", value: 0.0, desc: "P(|0⟩) = 1.0, P(|1⟩) = 0.0" },
  { label: "π/2 (50/50 Split)", value: 1.5707963, desc: "P(|0⟩) = 0.5, P(|1⟩) = 0.5" },
  { label: "π (Destructive)", value: 3.1415926, desc: "P(|0⟩) = 0.0, P(|1⟩) = 1.0" },
  { label: "3π/2 (Balanced)", value: 4.712389, desc: "P(|0⟩) = 0.5, P(|1⟩) = 0.5" },
  { label: "2π (Full Cycle)", value: 6.283185, desc: "P(|0⟩) = 1.0, P(|1⟩) = 0.0" },
];

export default function InterferenceLab() {
  const [phaseTheta, setPhaseTheta] = useState<number>(0.0);
  const [shots, setShots] = useState<number>(1024);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<InterferenceSimulateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSimulate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await simulateInterference({
        phase_theta: phaseTheta,
        shots,
        include_sweep: true,
        sweep_steps: 36,
      });
      setResult(res);
    } catch (err: any) {
      console.error("Interference simulation failed:", err);
      setError(err.response?.data?.detail || err.message || "Failed to simulate interference.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSimulate();
  }, [phaseTheta, shots]);

  return (
    <div className="space-y-6">
      {/* Control Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Waves className="h-5 w-5 text-blue-600" />
              <h2 className="font-display text-lg font-bold text-slate-900">
                Mach-Zehnder Quantum Wave Interferometer
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Observe quantum wave-particle duality and amplitude interference in the sequence |0⟩ → H → P(θ) → H → Measure. Contrast the continuous sinusoidal quantum fringe curve against classical particle statistics.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSimulate}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-xs"
            >
              <Play className="h-3.5 w-3.5" />
              {loading ? "Sweeping..." : "Recompute Fringe"}
            </button>
          </div>
        </div>

        {/* Phase Controls & Presets */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="flex justify-between items-center text-xs">
              <label className="font-bold uppercase tracking-wider text-slate-500">
                Phase Shift Parameter θ
              </label>
              <span className="font-mono text-blue-700 font-bold bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {phaseTheta.toFixed(3)} rad ({(phaseTheta * (180 / Math.PI)).toFixed(1)}°)
              </span>
            </div>
            <input
              type="range"
              min="0"
              max={6.283185}
              step="0.05"
              value={phaseTheta}
              onChange={(e) => setPhaseTheta(parseFloat(e.target.value))}
              className="w-full accent-blue-600 mt-2.5 cursor-pointer"
            />

            <div className="flex flex-wrap gap-1.5 mt-3">
              {PRESET_PHASES.map((p) => (
                <button
                  key={p.label}
                  onClick={() => setPhaseTheta(p.value)}
                  className={`px-2.5 py-1 rounded-lg border text-[11px] font-mono transition-all ${
                    Math.abs(phaseTheta - p.value) < 0.1
                      ? "border-blue-600 bg-blue-50 text-blue-700 font-bold"
                      : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center text-xs">
              <label className="font-bold uppercase tracking-wider text-slate-500">
                Aer Monte Carlo Shots
              </label>
              <span className="font-mono text-slate-700 font-bold">
                {shots} shots
              </span>
            </div>
            <input
              type="range"
              min="256"
              max="4096"
              step="256"
              value={shots}
              onChange={(e) => setShots(parseInt(e.target.value))}
              className="w-full accent-blue-600 mt-2.5 cursor-pointer"
            />
            <span className="text-[10px] text-slate-400 block mt-1">
              Controls statistical variance of sampled detector counts
            </span>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Cols: Continuous Sinusoidal Fringe Curve */}
          <div className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <h3 className="font-display text-sm font-bold text-slate-900">
                  Continuous Interference Fringe: P(|0⟩, θ) = cos²(θ / 2)
                </h3>
                <span className="text-[11px] text-slate-500 font-mono">
                  Theoretical curve (blue line) vs Qiskit Aer shot-sampled counts (green dots)
                </span>
              </div>
              <span
                className={`font-mono text-xs font-bold px-2.5 py-1 rounded-lg border ${
                  result.interference_regime === "CONSTRUCTIVE"
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : result.interference_regime === "DESTRUCTIVE"
                    ? "bg-rose-50 text-rose-700 border-rose-200"
                    : "bg-blue-50 text-blue-700 border-blue-200"
                }`}
              >
                {result.interference_regime} INTERFERENCE
              </span>
            </div>

            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={result.sweep_curve || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey="theta_deg"
                    tick={{ fill: "#64748b", fontSize: 10, fontFamily: "monospace" }}
                    unit="°"
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
                  <Line
                    type="monotone"
                    dataKey="theoretical_p0"
                    name="Theoretical P(|0⟩)"
                    stroke="#2563eb"
                    strokeWidth={2.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="sampled_p0"
                    name="Sampled Frequency"
                    stroke="#059669"
                    strokeWidth={1}
                    dot={{ r: 2 }}
                    strokeDasharray="2 2"
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Right Col: Quantum vs Classical Contrast Analysis */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Interference Metrics & Contrast
            </h3>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl border border-slate-100 bg-slate-50 space-y-1">
                <span className="text-slate-500 block">Detector Counts (|0⟩ vs |1⟩)</span>
                <div className="flex justify-between font-mono font-bold text-slate-800 text-sm">
                  <span className="text-blue-700">|0⟩: {result.sampled_counts["0"]} ({((result.sampled_counts["0"] / shots) * 100).toFixed(1)}%)</span>
                  <span className="text-rose-700">|1⟩: {result.sampled_counts["1"]} ({((result.sampled_counts["1"] / shots) * 100).toFixed(1)}%)</span>
                </div>
              </div>

              <div className="p-3 rounded-xl border border-blue-100 bg-blue-50/50 space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-blue-900 font-bold">Quantum Contrast (2·Re[α₁*α₂]):</span>
                  <span className="font-mono font-bold text-blue-700">
                    {result.quantum_interference_contrast.toFixed(3)}
                  </span>
                </div>
                <p className="text-[10px] text-blue-800 leading-relaxed">
                  Quantum probability includes the cross-term 2·Re(α₁*α₂) = cos(θ). Without this phase-dependent interference term, the detectors would register flat 50/50 classical probabilities.
                </p>
              </div>

              <div className="p-3 rounded-xl border border-slate-100 bg-slate-50 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Classical Flat Expectation:</span>
                  <span className="font-mono font-bold text-slate-700">
                    {result.classical_expectation_p0.toFixed(2)} (0.50)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Theoretical P(|0⟩) = cos²(θ/2):</span>
                  <span className="font-mono font-bold text-slate-900">
                    {result.theoretical_probabilities["0"].toFixed(4)}
                  </span>
                </div>
              </div>

              <div className="rounded-xl border border-amber-100 bg-amber-50/60 p-3 text-[11px] text-amber-900 space-y-1">
                <span className="font-bold block">Interferometer Topology</span>
                <p className="text-[10px] text-amber-800">
                  |0⟩ ➔ Beam Splitter 1 (H) ➔ Phase Shifter (Rz/P(θ)) ➔ Beam Splitter 2 (H) ➔ Photodetector (Z-measure)
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
