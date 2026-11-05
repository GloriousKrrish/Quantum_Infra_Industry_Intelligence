import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Play,
  RotateCcw,
  Sparkles,
  Info,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Layers,
  ArrowRight,
} from "lucide-react";
import {
  executeErrorCorrection,
  type ErrorCorrectionResponse,
} from "../../lib/api";

export default function ErrorCorrectionLab() {
  const [codeType, setCodeType] = useState<"bit_flip" | "phase_flip">("bit_flip");
  const [errorQubit, setErrorQubit] = useState<number | null>(1);
  const [initialTheta, setInitialTheta] = useState<number>(1.047); // ~ pi/3
  const [shots, setShots] = useState<number>(1024);

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ErrorCorrectionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExecute = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await executeErrorCorrection({
        code_type: codeType,
        error_qubit: errorQubit,
        initial_state_theta: initialTheta,
        shots,
      });
      setResult(res);
    } catch (err: any) {
      console.error("QEC error:", err);
      setError(err.response?.data?.detail || err.message || "Failed to execute error correction.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleExecute();
  }, [codeType, errorQubit, initialTheta, shots]);

  return (
    <div className="space-y-6">
      {/* Control Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
              <h2 className="font-display text-lg font-bold text-slate-900">
                Quantum Error Correction (3-Qubit Repetition Codes)
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Protect an unknown quantum state |ψ⟩ = cos(θ/2)|0⟩ + sin(θ/2)|1⟩ against single-qubit bit-flip (X) and phase-flip (Z) errors using non-local entanglement encoding, syndrome extraction ancillas, and coherent recovery.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`font-mono text-xs font-bold px-3 py-1.5 rounded-xl border ${
                result?.is_corrected
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-rose-50 text-rose-700 border-rose-200"
              }`}
            >
              LOGICAL FIDELITY: {result ? `${(result.logical_fidelity * 100).toFixed(1)}%` : "..."}
            </span>
          </div>
        </div>

        {/* Configuration Grid */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Error Correction Code Type
            </label>
            <div className="flex gap-2 mt-2">
              <button
                onClick={() => setCodeType("bit_flip")}
                className={`flex-1 py-2 px-3 rounded-xl border text-xs font-bold transition-all ${
                  codeType === "bit_flip"
                    ? "border-blue-600 bg-blue-50 text-blue-700"
                    : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                }`}
              >
                3-Qubit Bit-Flip (X)
              </button>
              <button
                onClick={() => setCodeType("phase_flip")}
                className={`flex-1 py-2 px-3 rounded-xl border text-xs font-bold transition-all ${
                  codeType === "phase_flip"
                    ? "border-blue-600 bg-blue-50 text-blue-700"
                    : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                }`}
              >
                3-Qubit Phase-Flip (Z)
              </button>
            </div>
          </div>

          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Error Injection Site
            </label>
            <div className="grid grid-cols-4 gap-1.5 mt-2">
              {[null, 0, 1, 2].map((q) => (
                <button
                  key={String(q)}
                  onClick={() => setErrorQubit(q)}
                  className={`py-2 px-1 rounded-xl border text-xs font-mono font-bold transition-all ${
                    errorQubit === q
                      ? "border-rose-600 bg-rose-50 text-rose-700"
                      : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                  }`}
                >
                  {q === null ? "None" : `Q${q}`}
                </button>
              ))}
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              {errorQubit === null ? "Ideal noiseless transmission" : `Injects Pauli ${codeType === "bit_flip" ? "X" : "Z"} error on Qubit ${errorQubit}`}
            </span>
          </div>

          <div>
            <div className="flex justify-between items-center text-xs">
              <label className="font-bold uppercase tracking-wider text-slate-500">
                Initial State Angle θ
              </label>
              <span className="font-mono text-slate-700 font-bold">
                {initialTheta.toFixed(2)} rad
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="3.14"
              step="0.1"
              value={initialTheta}
              onChange={(e) => setInitialTheta(parseFloat(e.target.value))}
              className="mt-2.5 w-full accent-blue-600 cursor-pointer"
            />
            <span className="text-[10px] text-slate-400 block mt-1">
              Arbitrary unknown superposition state
            </span>
          </div>

          <div>
            <div className="flex justify-between items-center text-xs">
              <label className="font-bold uppercase tracking-wider text-slate-500">
                Monte Carlo Shots
              </label>
              <span className="font-mono text-slate-700 font-bold">{shots}</span>
            </div>
            <input
              type="range"
              min="256"
              max="2048"
              step="256"
              value={shots}
              onChange={(e) => setShots(parseInt(e.target.value))}
              className="mt-2.5 w-full accent-blue-600 cursor-pointer"
            />
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
          {/* Card 1: Syndrome Diagnostics */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4 text-xs">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Syndrome Extraction Readout (s₁ s₂)
            </h3>

            <div className="p-3.5 rounded-xl border border-blue-200 bg-blue-50/50 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-blue-900 font-bold">Measured Syndrome:</span>
                <span className="font-mono text-sm font-bold text-blue-700 bg-white px-2.5 py-1 rounded border border-blue-200">
                  s = "{result.expected_syndrome}"
                </span>
              </div>
              <p className="text-[11px] text-blue-800 leading-relaxed">
                Ancilla qubits measured stabilizer operators Z₀Z₁ and Z₁Z₂ without measuring the individual physical qubits, preserving the superposition intact!
              </p>
            </div>

            <div className="space-y-1.5">
              <span className="text-slate-500 font-bold block mb-1">Syndrome Decoding Table:</span>
              {Object.entries(result.syndrome_table).map(([syndrome, diagnosis]) => {
                const isActive = syndrome === result.expected_syndrome;
                return (
                  <div
                    key={syndrome}
                    className={`flex items-center justify-between p-2 rounded-lg border text-xs font-mono ${
                      isActive
                        ? "border-emerald-300 bg-emerald-50 text-emerald-900 font-bold"
                        : "border-slate-100 bg-slate-50 text-slate-500"
                    }`}
                  >
                    <span>s = "{syndrome}"</span>
                    <span>{diagnosis}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Card 2: Correction & State Recovery */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4 text-xs">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Coherent Recovery & Logical Fidelity
            </h3>

            <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/60 space-y-2">
              <div className="flex items-center gap-2 text-emerald-900 font-bold">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                <span>Quantum State Successfully Restored</span>
              </div>
              <div className="flex justify-between items-center pt-1 font-mono">
                <span className="text-emerald-800">State Fidelity F(|ψ_in⟩, |ψ_rec⟩):</span>
                <span className="font-bold text-emerald-700 text-sm">
                  {result.logical_fidelity.toFixed(4)}
                </span>
              </div>
            </div>

            <div className="p-3 rounded-xl border border-slate-100 bg-slate-50 space-y-2">
              <span className="font-bold text-slate-700 block">Encoding Mapping:</span>
              <div className="font-mono text-[11px] text-slate-600 space-y-1">
                <div>|0_L⟩ = {codeType === "bit_flip" ? "|000⟩" : "|+++⟩"}</div>
                <div>|1_L⟩ = {codeType === "bit_flip" ? "|111⟩" : "|---⟩"}</div>
                <div>|ψ_L⟩ = α|0_L⟩ + β|1_L⟩</div>
              </div>
            </div>
          </div>

          {/* Card 3: Circuit Stages */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4 text-xs">
            <h3 className="font-display text-sm font-bold text-slate-900">
              Circuit Execution Pipeline
            </h3>

            <div className="space-y-2">
              {result.circuit_steps.map((step, idx) => (
                <div key={idx} className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-100 text-[10px] font-bold text-blue-700 font-mono">
                    {idx + 1}
                  </span>
                  <span className="text-slate-700 text-[11px] leading-tight pt-0.5">{step}</span>
                </div>
              ))}
            </div>

            {result.coherent_recovery_method && (
              <div className="p-2.5 rounded-lg bg-slate-100/70 border border-slate-200 font-mono text-[10px] text-slate-600">
                <span className="font-bold block text-slate-700 mb-0.5">Recovery Architecture:</span>
                {result.coherent_recovery_method}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Code Limitations & Scientific Transparency Callout */}
      {result?.code_limitations && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-4 text-xs text-amber-900 flex items-start gap-3">
          <Info className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold uppercase tracking-wider text-[11px] text-amber-800">
              Scientific Scope & Code Limitations
            </span>
            <p className="leading-relaxed text-[11px]">
              {result.code_limitations}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

