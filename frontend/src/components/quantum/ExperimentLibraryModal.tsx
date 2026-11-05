import { useState, useEffect } from "react";
import {
  X,
  BookOpen,
  Sparkles,
  ArrowRight,
  Play,
  CheckCircle2,
  Atom,
} from "lucide-react";
import type { ExperimentTemplate } from "../../lib/api";
import { fetchQuantumExperiments } from "../../lib/api";

interface ExperimentLibraryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectExperiment: (exp: ExperimentTemplate) => void;
}

export default function ExperimentLibraryModal({
  isOpen,
  onClose,
  onSelectExperiment,
}: ExperimentLibraryModalProps) {
  const [experiments, setExperiments] = useState<ExperimentTemplate[]>([]);
  const [selectedExpId, setSelectedExpId] = useState<string>("exp_hadamard_superposition");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!isOpen) return;
    async function load() {
      try {
        const data = await fetchQuantumExperiments();
        setExperiments(data);
        if (data.length > 0) setSelectedExpId(data[0].id);
      } catch (err) {
        console.error("Failed to load experiments:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [isOpen]);

  if (!isOpen) return null;

  const activeExp = experiments.find((e) => e.id === selectedExpId) || experiments[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="relative w-full max-w-4xl rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 bg-slate-50/80">
          <div className="flex items-center gap-2.5">
            <BookOpen className="h-5 w-5 text-blue-600" />
            <div>
              <h2 className="font-display text-base font-bold text-slate-900">
                Reproducible Quantum Experiment Library
              </h2>
              <span className="text-xs text-slate-500 font-mono">
                10 Canonical Quantum Foundations, Entanglement, and Algorithm Experiments
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-xl p-1.5 text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100 overflow-y-auto flex-1">
          {/* Left Column: Experiment List */}
          <div className="p-4 space-y-1.5 overflow-y-auto max-h-[500px]">
            {experiments.map((exp) => (
              <button
                key={exp.id}
                onClick={() => setSelectedExpId(exp.id)}
                className={`w-full flex flex-col text-left rounded-xl p-3 border transition-all ${
                  selectedExpId === exp.id
                    ? "border-blue-600 bg-blue-50/60 shadow-2xs"
                    : "border-transparent hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-slate-900">{exp.name}</span>
                  <span className="text-[10px] font-mono text-slate-500 bg-slate-200/60 px-1.5 py-0.2 rounded">
                    {exp.num_qubits}Q
                  </span>
                </div>
                <span className="text-[10px] text-blue-700 font-medium mt-0.5">{exp.category}</span>
              </button>
            ))}
          </div>

          {/* Right Column: Detailed Experiment Profile */}
          <div className="md:col-span-2 p-6 space-y-4 overflow-y-auto">
            {activeExp && (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="font-display text-base font-bold text-slate-900">
                    {activeExp.name}
                  </h3>
                  <span className="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-mono font-bold text-blue-700">
                    {activeExp.num_qubits} Qubit Circuit
                  </span>
                </div>

                <div className="rounded-xl bg-slate-50 p-4 border border-slate-200/80 space-y-2">
                  <span className="text-[10px] font-bold uppercase text-slate-500 block">Scientific Objective:</span>
                  <p className="text-xs text-slate-800 font-medium leading-relaxed">
                    {activeExp.objective}
                  </p>
                </div>

                <div className="space-y-1">
                  <span className="text-xs font-bold text-slate-800">Mathematical Formulation:</span>
                  <div className="rounded-xl bg-blue-50/30 p-3 border border-blue-100 font-mono text-xs text-blue-900">
                    {activeExp.formula}
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-xs font-bold text-slate-800">Expected Quantum State:</span>
                  <p className="text-xs font-mono text-slate-700 bg-slate-100/70 p-2.5 rounded-lg border border-slate-200">
                    {activeExp.expected_state}
                  </p>
                </div>

                <div className="space-y-1">
                  <span className="text-xs font-bold text-slate-800">Theoretical Explanation:</span>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {activeExp.explanation}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-3">
                  <button
                    onClick={onClose}
                    className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Close
                  </button>
                  <button
                    onClick={() => {
                      onSelectExperiment(activeExp);
                      onClose();
                    }}
                    className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-blue-700 transition-colors"
                  >
                    <Play className="h-3.5 w-3.5" />
                    Load into Quantum Playground
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
