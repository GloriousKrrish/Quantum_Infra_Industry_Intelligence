"""
Quantum Measurement Theory Engine for Quantum Estate X.

Simulates generalized projective quantum measurements, state collapse,
basis rotations (Z, X, Y), repeated measurements, and statistical shot sampling:
- Theoretical Born rule: P(m) = ⟨ψ|Π_m|ψ⟩ = Tr(Π_m ρ)
- Lüders / Von Neumann projection postulate: ρ → Π_m ρ Π_m / P(m)
- Measurement complementarity & repeated idempotent measurements
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from backend.app.engines.quantum.circuit_engine import build_qiskit_circuit
from backend.app.engines.quantum.gate_library import (
    MATRIX_X,
    MATRIX_Y,
    MATRIX_Z,
    MATRIX_H,
)


# Single-qubit projective measurement operators
PROJECTORS_1Q: Dict[str, Dict[str, np.ndarray]] = {
    "Z": {
        "0": np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex),  # |0⟩⟨0|
        "1": np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex),  # |1⟩⟨1|
    },
    "X": {
        "+": 0.5 * np.array([[1.0, 1.0], [1.0, 1.0]], dtype=complex),  # |+⟩⟨+|
        "-": 0.5 * np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=complex), # |-⟩⟨-|
    },
    "Y": {
        "+i": 0.5 * np.array([[1.0, -1.0j], [1.0j, 1.0]], dtype=complex), # |+i⟩⟨+i|
        "-i": 0.5 * np.array([[1.0, 1.0j], [-1.0j, 1.0]], dtype=complex), # |-i⟩⟨-i|
    },
}


def execute_measurement_experiment(
    circuit_ops: List[Dict[str, Any]],
    num_qubits: int = 1,
    basis: str = "Z",
    shots: int = 1024,
    simulate_collapse_outcome: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute quantum measurement in specified basis (Z, X, Y).
    Returns theoretical Born probabilities, collapsed post-measurement state,
    and sampled Qiskit Aer measurement histogram.
    """
    # 1. Build circuit and compute pure pre-measurement statevector
    qc_base = build_qiskit_circuit(num_qubits, circuit_ops, with_measurements=False)
    sv_pre = Statevector.from_instruction(qc_base)
    psi_pre = np.array(sv_pre.data, dtype=complex)

    basis_upper = basis.upper()
    if basis_upper not in ("Z", "X", "Y"):
        basis_upper = "Z"

    # 2. Compute theoretical probabilities in chosen basis
    outcomes: List[Dict[str, Any]] = []

    if num_qubits == 1:
        projectors = PROJECTORS_1Q[basis_upper]
        rho_pre = np.outer(psi_pre, psi_pre.conj())

        for label, proj in projectors.items():
            prob = float(np.trace(proj @ rho_pre).real)
            prob_clean = max(0.0, min(1.0, prob))

            # Collapsed post-measurement state if this outcome occurs
            if prob_clean > 1e-9:
                rho_collapsed = (proj @ rho_pre @ proj) / prob_clean
                collapsed_bloch = {
                    "x": round(float(2.0 * rho_collapsed[0, 1].real), 4),
                    "y": round(float(-2.0 * rho_collapsed[0, 1].imag), 4),
                    "z": round(float(rho_collapsed[0, 0].real - rho_collapsed[1, 1].real), 4),
                }
            else:
                rho_collapsed = np.zeros((2, 2), dtype=complex)
                collapsed_bloch = {"x": 0.0, "y": 0.0, "z": 0.0}

            outcomes.append({
                "label": label,
                "basis": basis_upper,
                "theoretical_probability": round(prob_clean, 4),
                "collapsed_bloch": collapsed_bloch,
            })
    else:
        # Multi-qubit computational basis
        dim = 2 ** num_qubits
        for i in range(dim):
            prob = float(abs(psi_pre[i]) ** 2)
            bitstring = format(i, f"0{num_qubits}b")
            outcomes.append({
                "label": bitstring,
                "basis": "Z",
                "theoretical_probability": round(prob, 4),
            })

    # 3. Finite-shot sampling with basis rotation
    qc_meas = qc_base.copy()

    # Rotate basis before computational measurement
    if basis_upper == "X":
        # H rotates X-basis into Z-basis
        for q in range(num_qubits):
            qc_meas.h(q)
    elif basis_upper == "Y":
        # S^dagger then H rotates Y-basis into Z-basis: Sdg then H
        for q in range(num_qubits):
            qc_meas.sdg(q)
            qc_meas.h(q)

    qc_meas.measure_all()
    sim = AerSimulator()
    job = sim.run(qc_meas, shots=shots)
    counts_raw = dict(job.result().get_counts())

    # Map counts to basis labels
    sampled_distribution: List[Dict[str, Any]] = []
    for bitstr, cnt in sorted(counts_raw.items(), key=lambda x: x[1], reverse=True):
        if num_qubits == 1 and basis_upper == "X":
            label = "+" if bitstr == "0" else "-"
        elif num_qubits == 1 and basis_upper == "Y":
            label = "+i" if bitstr == "0" else "-i"
        else:
            label = bitstr

        freq = cnt / shots
        sampled_distribution.append({
            "label": label,
            "count": int(cnt),
            "frequency": round(freq, 4),
            "percentage": round(freq * 100.0, 2),
        })

    # 4. Collapse demonstration
    # Pick target outcome for state collapse inspection
    chosen_label = simulate_collapse_outcome or (outcomes[0]["label"] if outcomes else "0")
    matching_outcome = next((o for o in outcomes if o["label"] == chosen_label), outcomes[0] if outcomes else None)

    return {
        "num_qubits": num_qubits,
        "basis": basis_upper,
        "shots_requested": shots,
        "theoretical_outcomes": outcomes,
        "sampled_distribution": sampled_distribution,
        "collapsed_state_demonstration": {
            "selected_outcome": chosen_label,
            "probability": matching_outcome["theoretical_probability"] if matching_outcome else 0.0,
            "post_measurement_bloch": matching_outcome.get("collapsed_bloch") if matching_outcome else None,
            "repeated_measurement_note": (
                "Under the projection postulate (Lüders theorem), immediately re-measuring in the same "
                f"{basis_upper}-basis will return outcome '{chosen_label}' with 100% certainty (P = 1.000)."
            ),
        },
    }

