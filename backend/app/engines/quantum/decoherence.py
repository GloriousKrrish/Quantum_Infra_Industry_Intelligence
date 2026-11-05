"""
Quantum Decoherence & Open Systems Engine for Quantum Estate X.

Simulates environmental interaction, T1 relaxation, and T2 dephasing:
- Physical relaxation bound: T2 <= 2 * T1 (under standard Markovian weak-coupling assumptions)
- Pure dephasing relationship: 1/T2 = 1/(2*T1) + 1/T_phi
- Analytic Kraus trajectory for amplitude + phase damping
- Lindblad master equation:
    dρ/dt = -i/ℏ [H, ρ] + (1/T₁) (σ₋ ρ σ₊ - 1/2 {σ₊ σ₋, ρ}) + (1/2T_φ) (σ_z ρ σ_z - ρ)
- Time-series tracking of Bloch vector shrinkage, purity loss, and von Neumann entropy
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np

from backend.app.engines.quantum.quantum_information import compute_von_neumann_entropy


def simulate_decoherence_trajectory(
    initial_state_name: str = "plus",
    t1_us: float = 50.0,
    t2_us: float = 30.0,
    total_time_us: float = 100.0,
    num_steps: int = 50,
) -> Dict[str, Any]:
    """
    Simulate continuous decoherence trajectory over time t in [0, total_time_us].
    Validates physical relaxation bounds and returns comprehensive population, coherence, and Bloch data.
    """
    if t1_us <= 0.0 or t2_us <= 0.0 or total_time_us <= 0.0:
        raise ValueError("Decoherence parameters t1_us, t2_us, and total_time_us must be strictly positive.")

    # Physical consistency check: T2 <= 2 * T1
    t1 = float(t1_us)
    t2_max = 2.0 * t1
    t2 = min(t2_max, float(t2_us))

    # Pure dephasing time T_phi: 1/T2 = 1/(2*T1) + 1/T_phi
    inv_t_phi = (1.0 / t2) - (1.0 / (2.0 * t1))
    t_phi = (1.0 / inv_t_phi) if inv_t_phi > 1e-9 else float("inf")

    # Initial density matrix
    init_name = initial_state_name.lower()
    if init_name == "plus":  # |+⟩
        rho_0 = 0.5 * np.array([[1.0, 1.0], [1.0, 1.0]], dtype=complex)
    elif init_name == "one":  # |1⟩ (fully excited state, max T1 decay)
        rho_0 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
    elif init_name == "plus_i":  # |+i⟩
        rho_0 = 0.5 * np.array([[1.0, -1.0j], [1.0j, 1.0]], dtype=complex)
    else:  # Default |0⟩ (ground state, no T1 decay)
        rho_0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)

    steps = max(10, min(num_steps, 200))
    time_points = np.linspace(0.0, total_time_us, steps)
    trajectory: List[Dict[str, Any]] = []

    for t in time_points:
        decay_1 = math.exp(-t / t1)
        decay_2 = math.exp(-t / t2)

        # Analytic Kraus solution for amplitude + phase damping on single qubit
        # rho_11(t) decays exponentially to 0 (ground state |0⟩)
        rho_11_t = float(rho_0[1, 1].real) * decay_1
        rho_00_t = 1.0 - rho_11_t
        # Off-diagonal coherence decays with T2
        rho_01_t = rho_0[0, 1] * decay_2
        rho_10_t = rho_0[1, 0] * decay_2

        rho_t = np.array([
            [rho_00_t, rho_01_t],
            [rho_10_t, rho_11_t]
        ], dtype=complex)

        # Bloch coordinates:
        # |0⟩ is north pole (z = +1), |1⟩ is south pole (z = -1)
        rx = float(2.0 * rho_01_t.real)
        ry = float(-2.0 * rho_01_t.imag)
        rz = float(rho_00_t - rho_11_t)
        r_len = math.sqrt(rx ** 2 + ry ** 2 + rz ** 2)

        purity = float(np.trace(rho_t @ rho_t).real)
        entropy = compute_von_neumann_entropy(rho_t)

        trajectory.append({
            "time_us": round(float(t), 2),
            "rho_00": round(float(rho_00_t), 4),
            "rho_11": round(float(rho_11_t), 4),
            "abs_rho_01": round(float(abs(rho_01_t)), 4),
            "purity": round(purity, 4),
            "entropy": round(entropy, 4),
            "von_neumann_entropy": round(entropy, 4),
            "excited_state_population": round(rho_11_t, 4),
            "bloch_vector": {
                "x": round(rx, 4),
                "y": round(ry, 4),
                "z": round(rz, 4),
                "length": round(r_len, 4),
            },
            "bloch_x": round(rx, 4),
            "bloch_y": round(ry, 4),
            "bloch_z": round(rz, 4),
            "bloch_length": round(r_len, 4),
        })

    return {
        "initial_state": init_name,
        "t1_us": t1,
        "t2_us": t2,
        "t1_relaxation_us": t1,
        "t2_dephasing_us": t2,
        "t_phi_pure_dephasing_us": round(t_phi, 2) if not math.isinf(t_phi) else "Infinity",
        "physical_constraint_satisfied": bool(t2 <= 2.0 * t1 + 1e-6),
        "input_was_clamped": bool(t2_us > 2.0 * t1_us),
        "total_time_us": total_time_us,
        "trajectory": trajectory,
        "lindblad_formulation": (
            "dρ/dt = -i/ℏ [H, ρ] + (1/T₁) (σ₋ ρ σ₊ - 1/2 {σ₊ σ₋, ρ}) + "
            "(1/2T_φ) (σ_z ρ σ_z - ρ)"
        ),
        "disclaimer": (
            "Mathematical Markovian weak-coupling master equation model. "
            "Assumes zero-temperature thermal bath (asymptotic ground state |0⟩) and frequency-independent decay rates."
        ),
    }
