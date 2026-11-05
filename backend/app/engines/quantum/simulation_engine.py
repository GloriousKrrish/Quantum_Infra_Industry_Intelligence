"""
Quantum Simulation Engine for Quantum Estate X.

Executes quantum circuits on Qiskit Aer, extracts statevector amplitudes,
computational basis probabilities, shot-based sampling, and computes the
scientifically accurate reduced density matrices and Bloch vectors for every qubit.
"""

from __future__ import annotations

import cmath
import math
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, Statevector, partial_trace
from qiskit_aer import AerSimulator

from backend.app.engines.quantum.circuit_engine import (
    build_qiskit_circuit,
    get_circuit_metrics,
)


def simulate_circuit(
    num_qubits: int,
    operations: List[Dict[str, Any]],
    shots: int = 1024,
) -> Dict[str, Any]:
    """
    Execute full statevector simulation and shot-based measurement sampling.

    Returns:
    - Statevector with complex amplitudes, magnitudes, phases, probabilities.
    - Shot-based measurement count distribution.
    - Per-qubit reduced density matrix and Bloch vector (supporting mixed/entangled states).
    - Circuit structural metrics (depth, gate count, ops).
    """
    t_start = time.perf_counter()

    # 1. Build circuit without measurements for exact pure statevector simulation
    qc_unitary = build_qiskit_circuit(num_qubits, operations, with_measurements=False)
    metrics = get_circuit_metrics(qc_unitary)

    # 2. Compute exact statevector
    statevector = Statevector.from_instruction(qc_unitary)
    state_arr = np.array(statevector.data, dtype=complex)

    # 3. Format statevector basis states (|00...0> to |11...1>)
    # Qiskit Statevector indices correspond to standard little-endian integer values
    basis_amplitudes: List[Dict[str, Any]] = []
    total_dim = 2 ** num_qubits

    for i in range(total_dim):
        amp = state_arr[i]
        mag_sq = float(abs(amp) ** 2)
        phase_rad = float(cmath.phase(amp))
        phase_deg = float(math.degrees(phase_rad))

        # Format binary string with leading zeros matching num_qubits
        bitstring = format(i, f"0{num_qubits}b")

        basis_amplitudes.append({
            "index": i,
            "bitstring": bitstring,
            "ket": f"|{bitstring}⟩",
            "real": float(amp.real),
            "imag": float(amp.imag),
            "magnitude": float(abs(amp)),
            "probability": round(mag_sq, 6),
            "phase_rad": round(phase_rad, 4),
            "phase_deg": round(phase_deg, 2),
        })

    # Sort amplitudes by probability descending for clear inspection
    sorted_amplitudes = sorted(basis_amplitudes, key=lambda a: a["probability"], reverse=True)
    top_states = [s for s in sorted_amplitudes if s["probability"] > 1e-4]

    # 4. Shot-based measurement simulation via AerSimulator
    qc_meas = qc_unitary.copy()
    qc_meas.measure_all()

    sim = AerSimulator()
    job = sim.run(qc_meas, shots=shots)
    counts = dict(job.result().get_counts())

    # Format measurement distribution
    measurements: List[Dict[str, Any]] = []
    for bitstr, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        measurements.append({
            "bitstring": bitstr,
            "count": int(cnt),
            "frequency": round(cnt / shots, 4),
            "percentage": round((cnt / shots) * 100.0, 2),
        })

    # 5. Compute per-qubit Reduced Density Matrix and Bloch Vector
    # Scientific requirement: for an entangled state, individual qubits are mixed states!
    rho_full = DensityMatrix(statevector)
    qubit_bloch_vectors: List[Dict[str, Any]] = []

    for q_idx in range(num_qubits):
        # Trace out all other qubits: q_others = [j for j in range(num_qubits) if j != q_idx]
        q_others = [j for j in range(num_qubits) if j != q_idx]
        if q_others:
            rho_q = partial_trace(rho_full, q_others)
            rho_mat = np.array(rho_q.data, dtype=complex)
        else:
            rho_mat = np.array(rho_full.data, dtype=complex)

        # Elements of 2x2 density matrix
        # rho = [[rho00, rho01], [rho10, rho11]]
        rho00 = float(rho_mat[0, 0].real)
        rho11 = float(rho_mat[1, 1].real)
        rho01 = rho_mat[0, 1]

        # Bloch vector components:
        # rx = 2 * Re(rho01)
        # ry = -2 * Im(rho01) = 2 * Im(rho10)
        # rz = rho00 - rho11
        rx = float(2.0 * rho01.real)
        ry = float(-2.0 * rho01.imag)
        rz = float(rho00 - rho11)
        r_length = math.sqrt(rx ** 2 + ry ** 2 + rz ** 2)

        # State purity: Tr(rho^2) in [0.5, 1.0]
        # Purity = 1.0 for pure state, 0.5 for maximally mixed state
        purity = float(np.trace(rho_mat @ rho_mat).real)

        # Classification
        if abs(r_length - 1.0) < 1e-3 and abs(purity - 1.0) < 1e-3:
            state_classification = "PURE"
            state_desc = "Pure single-qubit quantum state (on Bloch surface)"
        elif r_length < 1e-3 or abs(purity - 0.5) < 1e-3:
            state_classification = "MAXIMALLY_MIXED"
            state_desc = "Maximally mixed state due to complete quantum entanglement (center of Bloch sphere)"
        else:
            state_classification = "MIXED"
            state_desc = f"Partially mixed state due to entanglement (length {r_length:.2f} < 1)"

        # Spherical coordinates (theta, phi)
        if r_length > 1e-5:
            norm_rz = max(-1.0, min(1.0, rz / r_length))
            theta_rad = math.acos(norm_rz)
            phi_rad = math.atan2(ry, rx)
        else:
            theta_rad = 0.0
            phi_rad = 0.0

        qubit_bloch_vectors.append({
            "qubit_index": q_idx,
            "bloch_vector": {
                "x": round(rx, 4),
                "y": round(ry, 4),
                "z": round(rz, 4),
                "length": round(r_length, 4),
            },
            "spherical_coords": {
                "theta_rad": round(theta_rad, 4),
                "theta_pi": round(theta_rad / math.pi, 4),
                "phi_rad": round(phi_rad, 4),
                "phi_pi": round(phi_rad / math.pi, 4),
            },
            "purity": round(purity, 4),
            "state_classification": state_classification,
            "description": state_desc,
            "prob_0": round(rho00, 4),
            "prob_1": round(rho11, 4),
            "density_matrix": [
                [{"real": float(rho_mat[0, 0].real), "imag": float(rho_mat[0, 0].imag)},
                 {"real": float(rho_mat[0, 1].real), "imag": float(rho_mat[0, 1].imag)}],
                [{"real": float(rho_mat[1, 0].real), "imag": float(rho_mat[1, 0].imag)},
                 {"real": float(rho_mat[1, 1].real), "imag": float(rho_mat[1, 1].imag)}],
            ],
        })

    execution_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    return {
        "num_qubits": num_qubits,
        "num_clbits": metrics["num_clbits"],
        "circuit_depth": metrics["circuit_depth"],
        "total_gate_count": metrics["total_gate_count"],
        "ops_breakdown": metrics["ops_breakdown"],
        "is_entangled": metrics["is_entangled"],
        "shots_requested": shots,
        "execution_time_ms": execution_ms,
        "simulator_backend": "Qiskit AerSimulator (C++)",
        "statevector": basis_amplitudes,
        "top_states": top_states,
        "measurements": measurements,
        "qubit_bloch_vectors": qubit_bloch_vectors,
    }

