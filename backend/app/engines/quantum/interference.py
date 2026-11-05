"""
Quantum Interference Engine for Quantum Estate X.

Simulates wave interference phenomena, the Mach-Zehnder interferometer,
phase-dependent probability fringes, and the mathematical contrast between
classical probability addition and quantum probability amplitude addition:
- Quantum superposition: |ψ⟩ = ( |0⟩ + e^(iθ)|1⟩ ) / √2
- Amplitude addition: P(0) = |α₁ + α₂|² = |α₁|² + |α₂|² + 2 Re(α₁* α₂)
- Classical particle addition: P_class = P₁ + P₂ (zero interference fringes)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator


def simulate_mach_zehnder(
    phase_theta: float = 0.0,
    shots: int = 1024,
    include_sweep: bool = True,
    sweep_steps: int = 36,
) -> Dict[str, Any]:
    """
    Simulate the canonical Mach-Zehnder quantum interferometer:
        |0⟩ ──[ H ]──[ Rz(θ) ]──[ H ]──[ M ]
    """
    # 1. Exact Single Phase Point Calculation
    # Physical beam splitter H followed by phase shift theta on arm 1:
    # State before second beam splitter: (|0⟩ + e^(iθ)|1⟩)/√2
    # After second beam splitter H:
    # Amplitude 0 = (1 + e^(iθ))/2 = e^(iθ/2) * cos(θ/2)
    # Amplitude 1 = (1 - e^(iθ))/2 = -i * e^(iθ/2) * sin(θ/2)
    p0_theory = math.cos(phase_theta / 2.0) ** 2
    p1_theory = math.sin(phase_theta / 2.0) ** 2

    # Classical expectation without interference
    p0_classical = 0.50
    p1_classical = 0.50

    # Cross-term (pure quantum interference term): 2 * Re(alpha_0* * alpha_1)
    # For equal split: 2 * (1/√2) * (e^(iθ)/√2) -> cos(θ)
    interference_cross_term = math.cos(phase_theta)

    # 2. Qiskit Aer Circuit Execution for the single point
    qc = QuantumCircuit(1)
    qc.h(0)
    qc.p(phase_theta, 0)
    qc.h(0)
    qc.measure_all()

    sim = AerSimulator()
    job = sim.run(qc, shots=shots)
    counts = dict(job.result().get_counts())

    sampled_c0 = counts.get("0", 0)
    sampled_c1 = counts.get("1", 0)
    sampled_p0 = sampled_c0 / shots
    sampled_p1 = sampled_c1 / shots

    # Classification of interference regime
    if p0_theory > 0.98:
        regime = "CONSTRUCTIVE"
        regime_desc = "Complete constructive interference in Detector 0 (P₀ ≈ 1.00); destructive in Detector 1."
    elif p0_theory < 0.02:
        regime = "DESTRUCTIVE"
        regime_desc = "Complete destructive interference in Detector 0 (P₀ ≈ 0.00); constructive in Detector 1."
    else:
        regime = "INTERMEDIATE"
        regime_desc = f"Intermediate wave interference: P₀ = {p0_theory*100:.1f}%, P₁ = {p1_theory*100:.1f}%."

    # 3. Phase Sweep Fringes (0 to 2*pi)
    sweep_curve: List[Dict[str, Any]] = []
    if include_sweep:
        steps = max(10, min(sweep_steps, 72))
        thetas = np.linspace(0.0, 2.0 * math.pi, steps)
        for th in thetas:
            p0_th = math.cos(th / 2.0) ** 2
            p1_th = math.sin(th / 2.0) ** 2
            sweep_curve.append({
                "phase_rad": round(float(th), 4),
                "phase_deg": round(math.degrees(float(th)), 1),
                "theory_p0": round(p0_th, 4),
                "theory_p1": round(p1_th, 4),
                "classical_baseline": 0.50,
                "interference_term": round(math.cos(float(th)), 4),
            })

    return {
        "phase_theta_rad": round(phase_theta, 4),
        "phase_theta_deg": round(math.degrees(phase_theta), 1),
        "shots_requested": shots,
        "interference_regime": regime,
        "description": regime_desc,
        "theoretical_probabilities": {
            "p0": round(p0_theory, 4),
            "p1": round(p1_theory, 4),
        },
        "sampled_results": {
            "count_0": sampled_c0,
            "count_1": sampled_c1,
            "frequency_0": round(sampled_p0, 4),
            "frequency_1": round(sampled_p1, 4),
        },
        "quantum_cross_term": round(interference_cross_term, 4),
        "classical_baseline": {
            "p0": p0_classical,
            "p1": p1_classical,
            "explanation": "If light/matter behaved as classical particles, probabilities would sum without phase fringes (P = 0.50 constant).",
        },
        "sweep_curve": sweep_curve,
    }

