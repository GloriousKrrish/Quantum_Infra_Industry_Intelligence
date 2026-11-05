"""
Quantum Channel Engine for Quantum Estate X.

Implements Completely Positive Trace-Preserving (CPTP) quantum operations
via Kraus operator sum representations:
    E(ρ) = Σ_k E_k ρ E_k†, with Σ_k E_k† E_k = I

Channels:
- Identity Channel
- Bit-Flip Channel
- Phase-Flip Channel
- Bit-Phase-Flip Channel
- Depolarizing Channel
- Amplitude Damping Channel (photon emission decay)
- Phase Damping Channel (pure dephasing)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.app.engines.quantum.gate_library import (
    MATRIX_I,
    MATRIX_X,
    MATRIX_Y,
    MATRIX_Z,
)
from backend.app.engines.quantum.density_matrix import (
    analyze_density_matrix,
    compute_purity,
)
from backend.app.engines.quantum.quantum_information import compute_quantum_fidelity


def get_channel_kraus_operators(
    channel_type: str = "depolarizing",
    param_p: float = 0.1,
    gamma: float = 0.1,
    lambda_param: float = 0.1,
) -> Tuple[List[np.ndarray], str]:
    """
    Construct Kraus matrices {E_k} satisfying Σ_k E_k† E_k = I.
    """
    ct = channel_type.lower()
    p = max(0.0, min(1.0, param_p))

    if ct == "identity":
        return [MATRIX_I], "Identity channel (no distortion)."

    elif ct == "bit_flip":
        e0 = math.sqrt(1.0 - p) * MATRIX_I
        e1 = math.sqrt(p) * MATRIX_X
        return [e0, e1], f"Bit-Flip channel (p = {p:.3f}): applies Pauli-X with probability p."

    elif ct == "phase_flip":
        e0 = math.sqrt(1.0 - p) * MATRIX_I
        e1 = math.sqrt(p) * MATRIX_Z
        return [e0, e1], f"Phase-Flip channel (p = {p:.3f}): applies Pauli-Z with probability p."

    elif ct == "bit_phase_flip":
        e0 = math.sqrt(1.0 - p) * MATRIX_I
        e1 = math.sqrt(p) * MATRIX_Y
        return [e0, e1], f"Bit-Phase-Flip channel (p = {p:.3f}): applies Pauli-Y with probability p."

    elif ct == "depolarizing":
        # E_0 = √(1 - 3p/4) I, E_i = √(p/4) σ_i
        p_depol = min(1.0, p)
        e0 = math.sqrt(max(0.0, 1.0 - 0.75 * p_depol)) * MATRIX_I
        factor = math.sqrt(0.25 * p_depol)
        e1 = factor * MATRIX_X
        e2 = factor * MATRIX_Y
        e3 = factor * MATRIX_Z
        return [e0, e1, e2, e3], f"Depolarizing channel (p = {p_depol:.3f}): isotropic decoherence to I/2."

    elif ct == "amplitude_damping":
        # E_0 = [[1, 0], [0, √(1-γ)]], E_1 = [[0, √γ], [0, 0]]
        g = max(0.0, min(1.0, gamma))
        e0 = np.array([[1.0, 0.0], [0.0, math.sqrt(1.0 - g)]], dtype=complex)
        e1 = np.array([[0.0, math.sqrt(g)], [0.0, 0.0]], dtype=complex)
        return [e0, e1], f"Amplitude Damping channel (γ = {g:.3f}): non-unital energy dissipation |1⟩ → |0⟩."

    elif ct == "phase_damping":
        # E_0 = [[1, 0], [0, √(1-λ)]], E_1 = [[0, 0], [0, √λ]]
        l_val = max(0.0, min(1.0, lambda_param))
        e0 = np.array([[1.0, 0.0], [0.0, math.sqrt(1.0 - l_val)]], dtype=complex)
        e1 = np.array([[0.0, 0.0], [0.0, math.sqrt(l_val)]], dtype=complex)
        return [e0, e1], f"Phase Damping channel (λ = {l_val:.3f}): unital pure dephasing."

    else:
        return [MATRIX_I], "Identity channel."


def apply_quantum_channel(
    channel_type: str = "depolarizing",
    input_state_preset: str = "pure_plus",
    param_p: float = 0.1,
    gamma: float = 0.1,
    lambda_param: float = 0.1,
) -> Dict[str, Any]:
    """
    Apply CPTP quantum channel E(ρ_in) = Σ E_k ρ_in E_k†.
    """
    # 1. Resolve input state
    in_analysis = analyze_density_matrix(preset=input_state_preset)
    rho_in = np.array([
        [complex(c["real"], c["imag"]) for c in row]
        for row in in_analysis["matrix"]
    ])
    purity_in = in_analysis["purity"]
    bloch_in = in_analysis.get("bloch_vector")

    # 2. Get Kraus operators
    kraus_ops, desc = get_channel_kraus_operators(
        channel_type=channel_type,
        param_p=param_p,
        gamma=gamma,
        lambda_param=lambda_param,
    )

    # 3. Verify completeness condition: Σ E_k† E_k = I
    completeness_sum = sum(k.conj().T @ k for k in kraus_ops)
    completeness_err = float(np.max(np.abs(completeness_sum - np.eye(2))))
    is_trace_preserving = bool(completeness_err < 1e-6)

    # 4. Apply channel: ρ_out = Σ E_k ρ_in E_k†
    rho_out = sum(k @ rho_in @ k.conj().T for k in kraus_ops)
    rho_out = (rho_out + rho_out.conj().T) / 2.0  # Numerical symmetrization
    rho_out = rho_out / np.trace(rho_out).real     # Strict normalization

    purity_out = compute_purity(rho_out)
    fid = compute_quantum_fidelity(rho_in, rho_out)

    # Output Bloch vector
    rx_out = float(2.0 * rho_out[0, 1].real)
    ry_out = float(-2.0 * rho_out[0, 1].imag)
    rz_out = float(rho_out[0, 0].real - rho_out[1, 1].real)
    bloch_out = {
        "x": round(rx_out, 4),
        "y": round(ry_out, 4),
        "z": round(rz_out, 4),
        "length": round(math.sqrt(rx_out ** 2 + ry_out ** 2 + rz_out ** 2), 4),
    }

    # Serialized matrix output
    matrix_cells = [
        [{"real": round(float(rho_out[r, c].real), 4), "imag": round(float(rho_out[r, c].imag), 4)} for c in range(2)]
        for r in range(2)
    ]

    return {
        "channel_type": channel_type,
        "description": desc,
        "input_state": input_state_preset,
        "is_trace_preserving": is_trace_preserving,
        "completeness_error": round(completeness_err, 8),
        "input_purity": purity_in,
        "output_purity": round(purity_out, 4),
        "fidelity_retained": fid["squared_fidelity"],
        "bloch_in": bloch_in,
        "bloch_out": bloch_out,
        "output_density_matrix": matrix_cells,
        "kraus_operator_count": len(kraus_ops),
    }
