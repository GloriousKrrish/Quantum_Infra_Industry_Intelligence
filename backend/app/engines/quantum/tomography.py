"""
Quantum State Tomography Engine for Quantum Estate X.

Reconstructs quantum density matrices from statistical Pauli basis measurements:
- Pauli basis measurements: ⟨σ_x⟩, ⟨σ_y⟩, ⟨σ_z⟩
- Physical density operator reconstruction: ρ = 1/2 (I + r_x σ_x + r_y σ_y + r_z σ_z)
- Physical state projection (guarantees positive semidefiniteness under shot noise)
- Statistical reconstruction error and quantum state fidelity
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
    """
    # 1. Theoretical true statevector & density matrix
    qc_base = build_qiskit_circuit(1, circuit_ops, with_measurements=False)
    sv = Statevector.from_instruction(qc_base)
    psi_true = np.array(sv.data, dtype=complex)
    rho_true = np.outer(psi_true, psi_true.conj())

    # Theoretical Pauli expectation values
    rx_true = float(np.trace(MATRIX_X @ rho_true).real)
    ry_true = float(np.trace(MATRIX_Y @ rho_true).real)
    rz_true = float(np.trace(MATRIX_Z @ rho_true).real)

    sim = AerSimulator()

    # 2. Measure in Z basis (Computational basis)
    qc_z = qc_base.copy()
    qc_z.measure_all()
    res_z = sim.run(qc_z, shots=shots).result().get_counts()
    c0_z = res_z.get("0", 0)
    c1_z = res_z.get("1", 0)
    rz_measured = (c0_z - c1_z) / shots

    # 3. Measure in X basis (H before measurement)
    qc_x = qc_base.copy()
    qc_x.h(0)
    qc_x.measure_all()
    res_x = sim.run(qc_x, shots=shots).result().get_counts()
    c0_x = res_x.get("0", 0)
    c1_x = res_x.get("1", 0)
    rx_measured = (c0_x - c1_x) / shots

    # 4. Measure in Y basis (S^dagger then H before measurement)
    qc_y = qc_base.copy()
    qc_y.sdg(0)
    qc_y.h(0)
    qc_y.measure_all()
    res_y = sim.run(qc_y, shots=shots).result().get_counts()
    c0_y = res_y.get("0", 0)
    c1_y = res_y.get("1", 0)
    ry_measured = (c0_y - c1_y) / shots

    # 5. Reconstruct Density Matrix & Apply Physical Projection
    r_len = math.sqrt(rx_measured ** 2 + ry_measured ** 2 + rz_measured ** 2)
    # If statistical noise drives length outside Bloch sphere, project to surface
    if r_len > 1.0:
        scale = 1.0 / r_len
        rx_phys = rx_measured * scale
        ry_phys = ry_measured * scale
        rz_phys = rz_measured * scale
    else:
        rx_phys = rx_measured
        ry_phys = ry_measured
        rz_phys = rz_measured

    rho_reconstructed = 0.5 * (
        MATRIX_I
        + rx_phys * MATRIX_X
        + ry_phys * MATRIX_Y
        + rz_phys * MATRIX_Z
    )

    # 6. Evaluation metrics
    fid = compute_quantum_fidelity(rho_true, rho_reconstructed)
    dist = compute_trace_distance(rho_true, rho_reconstructed)

    # Serialized matrices
    true_matrix_cells = [
        [{"real": round(float(rho_true[r, c].real), 4), "imag": round(float(rho_true[r, c].imag), 4)} for c in range(2)]
        for r in range(2)
    ]
    rec_matrix_cells = [
        [{"real": round(float(rho_reconstructed[r, c].real), 4), "imag": round(float(rho_reconstructed[r, c].imag), 4)} for c in range(2)]
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
            "length": round(math.sqrt(rx_true ** 2 + ry_true ** 2 + rz_true ** 2), 4),
        },
        "reconstructed_bloch_vector": {
            "x": round(rx_phys, 4),
            "y": round(ry_phys, 4),
            "z": round(rz_phys, 4),
            "length": round(math.sqrt(rx_phys ** 2 + ry_phys ** 2 + rz_phys ** 2), 4),
        },
        "pauli_measurements": {
            "sigma_x": {"expectation": round(rx_measured, 4), "counts_plus": c0_x, "counts_minus": c1_x},
            "sigma_y": {"expectation": round(ry_measured, 4), "counts_plus_i": c0_y, "counts_minus_i": c1_y},
            "sigma_z": {"expectation": round(rz_measured, 4), "counts_0": c0_z, "counts_1": c1_z},
        },
        "fidelity_reconstructed": fid["squared_fidelity"],
        "trace_distance_error": dist,
        "true_density_matrix": true_matrix_cells,
        "reconstructed_density_matrix": rec_matrix_cells,
    }
