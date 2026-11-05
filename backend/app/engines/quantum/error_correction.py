"""
Quantum Error Correction Engine for Quantum Estate X.

Implements foundational stabilizer quantum error-correcting codes:
- 3-Qubit Bit-Flip Repetition Code (detects & corrects single X error)
- 3-Qubit Phase-Flip Repetition Code (detects & corrects single Z error)
- Syndrome extraction via ancilla stabilizer measurements (Z_0 Z_1, Z_1 Z_2)
- Autonomous error decoding and conditional recovery
- Demonstration of No-Cloning theorem compatibility via non-local entanglement
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np

from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from backend.app.engines.quantum.quantum_information import compute_quantum_fidelity


def simulate_3qubit_bit_flip_code(
    initial_state_theta: float = 1.04719755,  # pi/3 -> alpha=sqrt(3)/2, beta=1/2
    error_qubit: Optional[int] = 1,          # Which qubit suffers bit-flip (0, 1, 2, or None)
    shots: int = 1024,
) -> Dict[str, Any]:
    """
    Execute 3-qubit bit-flip error correction code:
    1. Encode: |ψ⟩|00⟩ -> α|000⟩ + β|111⟩
    2. Inject error: X on error_qubit
    3. Syndrome extraction: Measure Z₀Z₁ and Z₁Z₂ using 2 ancillae
    4. Recovery: Conditionally flip corrupted qubit
    5. Decode: Uncompute encoding to recover original |ψ⟩ on q0
    """
    # 3 data qubits + 2 syndrome ancillae
    qr_data = QuantumRegister(3, "data")
    qr_anc = QuantumRegister(2, "syndrome")
    cr_syndrome = ClassicalRegister(2, "s")
    cr_logical = ClassicalRegister(1, "logical")

    qc = QuantumCircuit(qr_data, qr_anc, cr_syndrome, cr_logical)

    # 1. State preparation on q0: Ry(theta)|0⟩
    qc.ry(initial_state_theta, qr_data[0])

    # 2. Encoding into 3-qubit repetition code
    qc.cx(qr_data[0], qr_data[1])
    qc.cx(qr_data[0], qr_data[2])

    # 3. Error Injection
    injected_desc = "No error injected (clean channel)."
    if error_qubit in (0, 1, 2):
        qc.x(qr_data[error_qubit])
        injected_desc = f"Pauli-X (bit-flip) injected on data qubit q_{error_qubit}."

    # 4. Syndrome Extraction via Ancilla Stabilizers
    # Stabilizer S₁ = Z₀ Z₁ (parity of q0 and q1)
    qc.cx(qr_data[0], qr_anc[0])
    qc.cx(qr_data[1], qr_anc[0])
    qc.measure(qr_anc[0], cr_syndrome[0])

    # Stabilizer S₂ = Z₁ Z₂ (parity of q1 and q2)
    qc.cx(qr_data[1], qr_anc[1])
    qc.cx(qr_data[2], qr_anc[1])
    qc.measure(qr_anc[1], cr_syndrome[1])

    # 5. Deferred Coherent Recovery (Principle of Deferred Measurement)
    # Syndrome decoding:
    # (s0, s1) = (1, 0) -> error on q0
    # (s0, s1) = (1, 1) -> error on q1
    # (s0, s1) = (0, 1) -> error on q2
    # (s0, s1) = (0, 0) -> no error
    # Coherent recovery using multi-controlled X gates:
    # Correction on q0: active when s0=1, s1=0 (i.e., flip s1, Toffoli, flip s1)
    qc.x(qr_anc[1])
    qc.ccx(qr_anc[0], qr_anc[1], qr_data[0])
    qc.x(qr_anc[1])

    # Correction on q1: active when s0=1, s1=1
    qc.ccx(qr_anc[0], qr_anc[1], qr_data[1])

    # Correction on q2: active when s0=0, s1=1
    qc.x(qr_anc[0])
    qc.ccx(qr_anc[0], qr_anc[1], qr_data[2])
    qc.x(qr_anc[0])

    # 6. Decoding to verify logical state on q0
    qc.cx(qr_data[0], qr_data[2])
    qc.cx(qr_data[0], qr_data[1])

    # 7. Measure logical qubit
    qc.measure(qr_data[0], cr_logical[0])

    # Simulate on Aer
    sim = AerSimulator()
    job = sim.run(qc, shots=shots)
    counts = dict(job.result().get_counts())

    # Calculate logical outcome probabilities
    # Output bitstrings in Qiskit: 'logical_bit syndrome_bits' e.g. '0 01'
    logical_0_count = sum(cnt for k, cnt in counts.items() if k.split()[0] == "0")
    logical_1_count = sum(cnt for k, cnt in counts.items() if k.split()[0] == "1")

    p0_measured = logical_0_count / shots
    p1_measured = logical_1_count / shots

    # Expected theoretical probabilities from initial state Ry(theta)|0⟩
    expected_p0 = math.cos(initial_state_theta / 2.0) ** 2
    expected_p1 = math.sin(initial_state_theta / 2.0) ** 2

    # Fidelity calculation
    fidelity_retained = 1.0 - abs(p0_measured - expected_p0)

    # Syndrome diagnosis
    expected_syndrome = "00"
    if error_qubit == 0:
        expected_syndrome = "01"  # in binary s1 s0
    elif error_qubit == 1:
        expected_syndrome = "11"
    elif error_qubit == 2:
        expected_syndrome = "10"

    return {
        "code_type": "3-Qubit Bit-Flip Code",
        "injected_error": injected_desc,
        "error_qubit": error_qubit,
        "expected_syndrome": expected_syndrome,
        "theoretical_input_probabilities": {
            "p0": round(expected_p0, 4),
            "p1": round(expected_p1, 4),
        },
        "recovered_logical_probabilities": {
            "p0": round(p0_measured, 4),
            "p1": round(p1_measured, 4),
        },
        "logical_fidelity": round(max(0.0, min(1.0, fidelity_retained)), 4),
        "is_corrected": bool(abs(p0_measured - expected_p0) < 0.08),
        "explanation": (
            "The 3-qubit bit-flip code protects against arbitrary single X errors by encoding "
            "the logical qubit non-locally into 3 entangled data qubits (α|000⟩ + β|111⟩). "
            "Syndrome measurement checks joint parities Z₀Z₁ and Z₁Z₂ without measuring the individual "
            "amplitudes, thereby preserving quantum superposition and bypassing the No-Cloning theorem."
        ),
    }


def simulate_3qubit_phase_flip_code(
    initial_state_theta: float = 1.04719755,
    error_qubit: Optional[int] = 0,
    shots: int = 1024,
) -> Dict[str, Any]:
    """
    Execute 3-qubit phase-flip error correction code:
    Encodes in the Hadamard basis |0_L⟩ = |+++⟩, |1_L⟩ = |--->.
    Pauli-Z phase error in Z-basis acts as Pauli-X bit flip in X-basis.
    """
    qr_data = QuantumRegister(3, "data")
    qr_anc = QuantumRegister(2, "syndrome")
    cr_syndrome = ClassicalRegister(2, "s")
    cr_logical = ClassicalRegister(1, "logical")

    qc = QuantumCircuit(qr_data, qr_anc, cr_syndrome, cr_logical)

    # State prep
    qc.ry(initial_state_theta, qr_data[0])

    # Encode: bit flip encoding followed by transversal Hadamards
    qc.cx(qr_data[0], qr_data[1])
    qc.cx(qr_data[0], qr_data[2])
    for q in range(3):
        qc.h(qr_data[q])

    # Inject Phase Error Z
    injected_desc = "No phase error injected."
    if error_qubit in (0, 1, 2):
        qc.z(qr_data[error_qubit])
        injected_desc = f"Pauli-Z (phase-flip) injected on data qubit q_{error_qubit}."

    # Transform to X-basis to convert phase errors into bit flips
    for q in range(3):
        qc.h(qr_data[q])

    # Standard bit-flip syndrome extraction
    qc.cx(qr_data[0], qr_anc[0])
    qc.cx(qr_data[1], qr_anc[0])
    qc.measure(qr_anc[0], cr_syndrome[0])

    qc.cx(qr_data[1], qr_anc[1])
    qc.cx(qr_data[2], qr_anc[1])
    qc.measure(qr_anc[1], cr_syndrome[1])

    # Coherent correction in bit-flip basis
    qc.x(qr_anc[1])
    qc.ccx(qr_anc[0], qr_anc[1], qr_data[0])
    qc.x(qr_anc[1])

    qc.ccx(qr_anc[0], qr_anc[1], qr_data[1])

    qc.x(qr_anc[0])
    qc.ccx(qr_anc[0], qr_anc[1], qr_data[2])
    qc.x(qr_anc[0])

    # Decode
    qc.cx(qr_data[0], qr_data[2])
    qc.cx(qr_data[0], qr_data[1])

    qc.measure(qr_data[0], cr_logical[0])

    sim = AerSimulator()
    job = sim.run(qc, shots=shots)
    counts = dict(job.result().get_counts())

    logical_0_count = sum(cnt for k, cnt in counts.items() if k.split()[0] == "0")
    p0_measured = logical_0_count / shots
    expected_p0 = math.cos(initial_state_theta / 2.0) ** 2

    return {
        "code_type": "3-Qubit Phase-Flip Code",
        "injected_error": injected_desc,
        "error_qubit": error_qubit,
        "expected_p0": round(expected_p0, 4),
        "recovered_p0": round(p0_measured, 4),
        "is_corrected": bool(abs(p0_measured - expected_p0) < 0.08),
        "explanation": (
            "The 3-qubit phase-flip code rotates the basis via transversal Hadamard gates, "
            "mapping phase errors Z into bit-flip errors X (H Z H = X), which are then "
            "diagnosed and corrected using the standard syndrome extraction circuit."
        ),
    }
