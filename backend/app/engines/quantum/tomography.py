"""
Quantum State Tomography Engine for Quantum Estate X.

Reconstructs single-qubit quantum density matrices from statistical Pauli basis measurements:
- Pauli basis measurements: ⟨σ_x⟩, ⟨σ_y⟩, ⟨σ_z⟩
- Raw density operator reconstruction: ρ_raw = 1/2 (I + r_x σ_x + r_y σ_y + r_z σ_z)
- Physical state projection (guarantees positive semidefiniteness under statistical shot noise)
- Distinguishes ideal theoretical reconstruction from finite-shot statistical reconstruction
- Reports statistical uncertainty bounds: σ / √N
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from backend.app.engines.quantum.circuit_engine import build_qiskit_circuit
from backend.app.engines.quantum.gate_library import (
    MATRIX_I,
    MATRIX_X,
    MATRIX_Y,
    MATRIX_Z,
)
from backend.app.engines.quantum.quantum_information import (
    compute_quantum_fidelity,
    compute_trace_distance,
)


def perform_single_qubit_tomography(
    circuit_ops: List[Dict[str, Any]],
    shots: int = 2048,
) -> Dict[str, Any]:
    """
    Perform complete state tomography on a single-qubit quantum circuit.
    Measures ⟨σ_z⟩, ⟨σ_x⟩, and ⟨σ_y⟩ to reconstruct ρ.
    Preserves raw reconstruction, projected physical reconstruction, and statistical uncertainties.
    """
    shots = max(100, shots)

    # 1. Theoretical true statevector & density matrix
    qc_base = build_qiskit_circuit(1, circuit_ops, with_measurements=False)
    sv = Statevector.from_instruction(qc_base)
    psi_true = np.array(sv.data, dtype=complex)
    rho_true = np.outer(psi_true, psi_true.conj())

    # Theoretical Pauli expectation values (exact analytical)
    rx_true = float(np.trace(MATRIX_X @ rho_true).real)
    ry_true = float(np.trace(MATRIX_Y @ rho_true).real)
    rz_true = float(np.trace(MATRIX_Z @ rho_true).real)
    true_bloch_len = math.sqrt(rx_true ** 2 + ry_true ** 2 + rz_true ** 2)

    sim = AerSimulator()

    # 2. Measure in Z basis (Computational basis)
    qc_z = qc_base.copy()
    qc_z.measure_all()
    res_z = sim.run(qc_z, shots=shots).result().get_counts()
    c0_z = res_z.get("0", 0)
    c1_z = res_z.get("1", 0)
    rz_measured = (c0_z - c1_z) / shots
    # Standard error of mean: sqrt((1 - <sigma_z>^2) / N)
    std_err_z = math.sqrt(max(0.0, 1.0 - rz_measured ** 2) / shots)

    # 3. Measure in X basis (H before measurement)
    qc_x = qc_base.copy()
    qc_x.h(0)
    qc_x.measure_all()
    res_x = sim.run(qc_x, shots=shots).result().get_counts()
    c0_x = res_x.get("0", 0)
    c1_x = res_x.get("1", 0)
    rx_measured = (c0_x - c1_x) / shots
    std_err_x = math.sqrt(max(0.0, 1.0 - rx_measured ** 2) / shots)

    # 4. Measure in Y basis (S^dagger then H before measurement)
    qc_y = qc_base.copy()
    qc_y.sdg(0)
    qc_y.h(0)
    qc_y.measure_all()
    res_y = sim.run(qc_y, shots=shots).result().get_counts()
    c0_y = res_y.get("0", 0)
    c1_y = res_y.get("1", 0)
    ry_measured = (c0_y - c1_y) / shots
    std_err_y = math.sqrt(max(0.0, 1.0 - ry_measured ** 2) / shots)

    # 5. Raw Reconstruction
    r_raw_len = math.sqrt(rx_measured ** 2 + ry_measured ** 2 + rz_measured ** 2)
    rho_raw = 0.5 * (
        MATRIX_I
        + rx_measured * MATRIX_X
        + ry_measured * MATRIX_Y
        + rz_measured * MATRIX_Z
    )

    # Check positive semidefiniteness of raw reconstruction
    eigvals_raw = np.linalg.eigvalsh(rho_raw)
    is_raw_psd = bool(np.min(eigvals_raw) >= -1e-7)

    # 6. Physical PSD Projection
    # If statistical noise drives |r| > 1, the raw matrix has negative eigenvalue: (1 - |r|)/2 < 0.
    # We project the Bloch vector to the surface: r_phys = r / |r|, which restores PSD (min eig = 0).
    is_projected = False
    if r_raw_len > 1.0:
        is_projected = True
        scale = 1.0 / r_raw_len
        rx_phys = rx_measured * scale
        ry_phys = ry_measured * scale
        rz_phys = rz_measured * scale
    else:
        rx_phys = rx_measured
        ry_phys = ry_measured
        rz_phys = rz_measured

    rho_projected = 0.5 * (
        MATRIX_I
        + rx_phys * MATRIX_X
        + ry_phys * MATRIX_Y
        + rz_phys * MATRIX_Z
    )

    # 7. Evaluation Metrics
    fid_raw = compute_quantum_fidelity(rho_true, rho_raw)
    fid_projected = compute_quantum_fidelity(rho_true, rho_projected)
    dist = compute_trace_distance(rho_true, rho_projected)

    purity_raw = float(np.trace(rho_raw @ rho_raw).real)
    purity_projected = float(np.trace(rho_projected @ rho_projected).real)

    # Helper serialization
    def _serialize_matrix(mat: np.ndarray) -> List[List[Dict[str, float]]]:
        return [
            [{"real": round(float(mat[r, c].real), 4), "imag": round(float(mat[r, c].imag), 4)} for c in range(2)]
            for r in range(2)
        ]

    return {
        "num_qubits": 1,
        "shots_per_basis": shots,
        "total_shots": shots * 3,
        "true_bloch_vector": {
            "x": round(rx_true, 4),
            "y": round(ry_true, 4),
            "z": round(rz_true, 4),
            "length": round(true_bloch_len, 4),
        },
        "raw_bloch_vector": {
            "x": round(rx_measured, 4),
            "y": round(ry_measured, 4),
            "z": round(rz_measured, 4),
            "length": round(r_raw_len, 4),
        },
        "reconstructed_bloch_vector": {
            "x": round(rx_phys, 4),
            "y": round(ry_phys, 4),
            "z": round(rz_phys, 4),
            "length": round(math.sqrt(rx_phys ** 2 + ry_phys ** 2 + rz_phys ** 2), 4),
        },
        "pauli_measurements": {
            "x": {
                "expected_val": round(rx_measured, 4),
                "std_error": round(std_err_x, 4),
                "prob_plus": round(c0_x / shots, 4),
                "prob_minus": round(c1_x / shots, 4),
            },
            "y": {
                "expected_val": round(ry_measured, 4),
                "std_error": round(std_err_y, 4),
                "prob_plus_i": round(c0_y / shots, 4),
                "prob_minus_i": round(c1_y / shots, 4),
            },
            "z": {
                "expected_val": round(rz_measured, 4),
                "std_error": round(std_err_z, 4),
                "prob_0": round(c0_z / shots, 4),
                "prob_1": round(c1_z / shots, 4),
            },
            "sigma_x": {"expectation": round(rx_measured, 4), "counts_plus": c0_x, "counts_minus": c1_x},
            "sigma_y": {"expectation": round(ry_measured, 4), "counts_plus_i": c0_y, "counts_minus_i": c1_y},
            "sigma_z": {"expectation": round(rz_measured, 4), "counts_0": c0_z, "counts_1": c1_z},
        },
        "is_raw_psd": is_raw_psd,
        "is_psd_projected": is_projected,
        "fidelity_raw": fid_raw["squared_fidelity"],
        "fidelity_reconstructed": fid_projected["squared_fidelity"],
        "fidelity_projected": fid_projected["squared_fidelity"],
        "purity_reconstructed": round(purity_projected, 4),
        "purity_raw": round(purity_raw, 4),
        "trace_distance": dist,
        "trace_distance_error": dist,
        "true_density_matrix": _serialize_matrix(rho_true),
        "raw_density_matrix": _serialize_matrix(rho_raw),
        "reconstructed_density_matrix": _serialize_matrix(rho_projected),
        "statistical_notice": (
            "Tomography accuracy is subject to finite-shot statistical fluctuations (standard error ~ 1/√N). "
            "Under finite sampling, raw inversion may yield non-PSD operators (|r| > 1), which are projected "
            "back onto the valid Bloch sphere. High fidelity (> 0.95) is expected for N ≥ 2048, but not guaranteed under low shot counts."
        ),
    }
