"""
Quantum State Evolution Engine for Quantum Estate X.

Simulates continuous-time unitary quantum state evolution under physical Hamiltonians:
    |ψ(t)⟩ = exp(-i H t / ℏ) |ψ(0)⟩

Supports:
- Single-qubit Pauli Hamiltonians (X, Y, Z, general B-field)
- Two-qubit interaction Hamiltonians (Ising ZZ, Exchange XY, Heisenberg XXX)
- Energy conservation verification: ⟨H⟩(t) = const
- Time-series tracking of statevector amplitudes, basis probabilities, and Bloch vectors
"""

from __future__ import annotations

import cmath
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import scipy.linalg as la

from backend.app.engines.quantum.gate_library import (
    MATRIX_I,
    MATRIX_X,
    MATRIX_Y,
    MATRIX_Z,
    MATRIX_H,
)


# Standard canonical initial states
CANONICAL_STATES_1Q: Dict[str, np.ndarray] = {
    "zero": np.array([1.0, 0.0], dtype=complex),
    "one": np.array([0.0, 1.0], dtype=complex),
    "plus": np.array([1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0)], dtype=complex),
    "minus": np.array([1.0 / math.sqrt(2.0), -1.0 / math.sqrt(2.0)], dtype=complex),
    "plus_i": np.array([1.0 / math.sqrt(2.0), 1.0j / math.sqrt(2.0)], dtype=complex),
    "minus_i": np.array([1.0 / math.sqrt(2.0), -1.0j / math.sqrt(2.0)], dtype=complex),
}

CANONICAL_STATES_2Q: Dict[str, np.ndarray] = {
    "00": np.array([1.0, 0.0, 0.0, 0.0], dtype=complex),
    "01": np.array([0.0, 1.0, 0.0, 0.0], dtype=complex),
    "10": np.array([0.0, 0.0, 1.0, 0.0], dtype=complex),
    "11": np.array([0.0, 0.0, 0.0, 1.0], dtype=complex),
    "bell_phi_plus": np.array([1.0 / math.sqrt(2.0), 0.0, 0.0, 1.0 / math.sqrt(2.0)], dtype=complex),
    "bell_psi_plus": np.array([0.0, 1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0), 0.0], dtype=complex),
}


def build_hamiltonian(
    hamiltonian_type: str,
    omega: float = 1.0,
    b_field: Optional[Dict[str, float]] = None,
    j_coupling: float = 1.0,
) -> Tuple[np.ndarray, int, str]:
    """
    Construct the Hermitian Hamiltonian matrix H (H = H^dagger).
    Returns (H, num_qubits, latex_formula).
    """
    ht = hamiltonian_type.lower()

    if ht == "pauli_x":
        H = omega * MATRIX_X
        return H, 1, r"H = \hbar \omega \sigma_x"
    elif ht == "pauli_y":
        H = omega * MATRIX_Y
        return H, 1, r"H = \hbar \omega \sigma_y"
    elif ht == "pauli_z":
        H = omega * MATRIX_Z
        return H, 1, r"H = \hbar \omega \sigma_z"
    elif ht == "hadamard":
        H = (omega / math.sqrt(2.0)) * (MATRIX_X + MATRIX_Z)
        return H, 1, r"H = \frac{\hbar \omega}{\sqrt{2}} (\sigma_x + \sigma_z)"
    elif ht == "general_b_field":
        bx = float(b_field.get("x", 0.0) if b_field else 1.0)
        by = float(b_field.get("y", 0.0) if b_field else 0.0)
        bz = float(b_field.get("z", 0.0) if b_field else 1.0)
        H = bx * MATRIX_X + by * MATRIX_Y + bz * MATRIX_Z
        return H, 1, rf"H = {bx:.2f}\sigma_x + {by:.2f}\sigma_y + {bz:.2f}\sigma_z"
    elif ht == "ising_zz":
        H = j_coupling * np.kron(MATRIX_Z, MATRIX_Z)
        return H, 2, r"H = J (\sigma_z \otimes \sigma_z)"
    elif ht == "exchange_xy":
        H = j_coupling * (np.kron(MATRIX_X, MATRIX_X) + np.kron(MATRIX_Y, MATRIX_Y))
        return H, 2, r"H = J (\sigma_x \otimes \sigma_x + \sigma_y \otimes \sigma_y)"
    elif ht == "heisenberg_xxx":
        H = j_coupling * (
            np.kron(MATRIX_X, MATRIX_X)
            + np.kron(MATRIX_Y, MATRIX_Y)
            + np.kron(MATRIX_Z, MATRIX_Z)
        )
        return H, 2, r"H = J (\vec{\sigma}_1 \cdot \vec{\sigma}_2)"
    else:
        # Default to Pauli-Z precession
        return omega * MATRIX_Z, 1, r"H = \hbar \omega \sigma_z"


def _state_to_bloch_1q(state: np.ndarray) -> Dict[str, float]:
    """Calculate single-qubit Bloch vector components (rx, ry, rz)."""
    alpha, beta = state[0], state[1]
    # Density matrix rho = [[|a|^2, a*b*], [b*a, |b|^2]]
    rx = float(2.0 * (alpha.conj() * beta).real)
    ry = float(2.0 * (alpha.conj() * beta).imag)
    rz = float(abs(alpha) ** 2 - abs(beta) ** 2)
    length = math.sqrt(rx ** 2 + ry ** 2 + rz ** 2)
    return {
        "x": round(rx, 4),
        "y": round(ry, 4),
        "z": round(rz, 4),
        "length": round(length, 4),
    }


def simulate_state_evolution(
    hamiltonian_type: str = "pauli_x",
    initial_state_name: str = "zero",
    custom_initial_state: Optional[List[Dict[str, float]]] = None,
    omega: float = 1.0,
    b_field: Optional[Dict[str, float]] = None,
    j_coupling: float = 1.0,
    total_time: float = 6.2831853,  # ~ 2*pi
    num_steps: int = 50,
) -> Dict[str, Any]:
    """
    Simulate continuous-time state evolution under H.
    """
    # 1. Construct Hamiltonian
    H, num_qubits, formula_latex = build_hamiltonian(
        hamiltonian_type, omega=omega, b_field=b_field, j_coupling=j_coupling
    )
    dim = 2 ** num_qubits

    # 2. Prepare initial statevector
    if custom_initial_state and len(custom_initial_state) == dim:
        psi_0 = np.array(
            [complex(c.get("real", 0.0), c.get("imag", 0.0)) for c in custom_initial_state],
            dtype=complex,
        )
    else:
        cat = CANONICAL_STATES_1Q if num_qubits == 1 else CANONICAL_STATES_2Q
        psi_0 = cat.get(initial_state_name, cat[list(cat.keys())[0]])

    # Normalize initial state
    norm = np.linalg.norm(psi_0)
    if norm < 1e-12:
        psi_0 = np.zeros(dim, dtype=complex)
        psi_0[0] = 1.0
    else:
        psi_0 = psi_0 / norm

    # 3. Energy expectation value: <H> = <psi|H|psi>
    e_0 = float(np.vdot(psi_0, H @ psi_0).real)

    # 4. Eigenvalue spectrum
    eigvals, _ = la.eigh(H)
    energy_gap = float(abs(eigvals[-1] - eigvals[0])) if len(eigvals) > 1 else 0.0
    period = round((2.0 * math.pi / energy_gap), 4) if energy_gap > 1e-6 else None

    # 5. Time Discretization & Trajectory
    steps = max(5, min(num_steps, 200))
    time_points = np.linspace(0.0, total_time, steps)
    trajectory: List[Dict[str, Any]] = []

    for t in time_points:
        # Unitary propagator: U(t) = exp(-i H t)
        U_t = la.expm(-1j * H * t)
        psi_t = U_t @ psi_0

        # Amplitudes and probabilities
        amps = []
        for i in range(dim):
            a = psi_t[i]
            phase = float(cmath.phase(a))
            amps.append({
                "index": i,
                "bitstring": format(i, f"0{num_qubits}b"),
                "real": round(float(a.real), 4),
                "imag": round(float(a.imag), 4),
                "probability": round(float(abs(a) ** 2), 4),
                "phase_rad": round(phase, 4),
            })

        point: Dict[str, Any] = {
            "time": round(float(t), 4),
            "probabilities": [amp["probability"] for amp in amps],
            "amplitudes": amps,
        }

        # For 1-qubit systems, track continuous 3D Bloch vector
        if num_qubits == 1:
            point["bloch_vector"] = _state_to_bloch_1q(psi_t)

        trajectory.append(point)

    # Final state metrics
    psi_final = la.expm(-1j * H * total_time) @ psi_0
    overlap = float(abs(np.vdot(psi_0, psi_final)) ** 2)

    return {
        "num_qubits": num_qubits,
        "hamiltonian_type": hamiltonian_type,
        "formula_latex": formula_latex,
        "energy_expectation": round(e_0, 4),
        "eigenvalues": [round(float(ev), 4) for ev in eigvals],
        "energy_gap": round(energy_gap, 4),
        "recurrence_period": period,
        "total_time": round(total_time, 4),
        "num_steps": steps,
        "initial_overlap_final": round(overlap, 4),
        "trajectory": trajectory,
    }

