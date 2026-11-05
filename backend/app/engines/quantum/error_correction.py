"""
Quantum Error Correction Engine for Quantum Estate X.

Implements foundational stabilizer quantum error-correcting codes:
- 3-Qubit Bit-Flip Repetition Code (detects & corrects single X error)
- 3-Qubit Phase-Flip Repetition Code (detects & corrects single Z error)
- Syndrome extraction via ancilla stabilizer measurements (Z_0 Z_1, Z_1 Z_2 or X_0 X_1, X_1 X_2)
- Coherent error decoding and multi-controlled unitary recovery (Principle of Deferred Measurement)
- Demonstration of No-Cloning theorem compatibility via non-local entanglement

SCIENTIFIC LIMITATIONS & ASSUMPTIONS:
1. The 3-qubit bit-flip code corrects a single bit-flip (X) error only; it CANNOT correct phase-flip (Z)
   or combined (Y = iXZ) errors.
2. The 3-qubit phase-flip code corrects a single phase-flip (Z) error only; it CANNOT correct bit-flip (X)
   or combined (Y) errors.
3. Neither 3-qubit code independently corrects an arbitrary unknown single-qubit error. Full single-qubit
   error correction requires at least a distance-3 code such as the 9-qubit Shor code or 7-qubit Steane code.
4. Coherent recovery uses quantum feedback via multi-controlled Toffoli gates conditioned on syndrome ancillae,
   assuming instantaneous noiseless feedforward gates.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np

from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit_aer import AerSimulator


def simulate_3qubit_bit_flip_code(
    initial_state_theta: float = 1.04719755,  # pi/3 -> alpha=cos(pi/6)=sqrt(3)/2, beta=sin(pi/6)=1/2
    error_qubit: Optional[int] = 1,          # Which qubit suffers bit-flip (0, 1, 2, or None)
    shots: int = 1024,
) -> Dict[str, Any]:
    """
    Execute 3-qubit bit-flip error correction code:
    1. Encode: |ψ⟩|00⟩ -> α|000⟩ + β|111⟩
    2. Inject error: Pauli-X on error_qubit (or clean channel if None)
    3. Syndrome extraction: Measure Z₀Z₁ and Z₁Z₂ using 2 ancillae
    4. Recovery: Coherent Toffoli correction on corrupted qubit
    5. Decode: Uncompute encoding to recover original |ψ⟩ on q0
    """
    if error_qubit is not None and error_qubit not in (0, 1, 2):
        raise ValueError(f"Invalid error_qubit {error_qubit}. Must be 0, 1, 2, or None.")

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
    injected_desc = "No error injected (clean transmission)."
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

    # 5. Coherent Recovery via Multi-Controlled Unitaries (Deferred Measurement)
    # Syndrome decoding:
    # (s0, s1) = (1, 0) -> error on q0
    # (s0, s1) = (1, 1) -> error on q1
    # (s0, s1) = (0, 1) -> error on q2
    # (s0, s1) = (0, 0) -> no error
    qc.x(qr_anc[1])
    qc.ccx(qr_anc[0], qr_anc[1], qr_data[0])
    qc.x(qr_anc[1])

    qc.ccx(qr_anc[0], qr_anc[1], qr_data[1])

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
    logical_0_count = sum(cnt for k, cnt in counts.items() if k.split()[0] == "0")
    logical_1_count = sum(cnt for k, cnt in counts.items() if k.split()[0] == "1")

    p0_measured = logical_0_count / shots
    p1_measured = logical_1_count / shots

    # Expected theoretical probabilities from initial state Ry(theta)|0⟩
    expected_p0 = math.cos(initial_state_theta / 2.0) ** 2
    expected_p1 = math.sin(initial_state_theta / 2.0) ** 2

    fidelity_retained = 1.0 - abs(p0_measured - expected_p0)

    # Syndrome diagnosis
    expected_syndrome = "00"
    if error_qubit == 0:
        expected_syndrome = "01"  # binary s1 s0
    elif error_qubit == 1:
        expected_syndrome = "11"
    elif error_qubit == 2:
        expected_syndrome = "10"

    syndrome_table = {
        "00": "No error detected across stabilizers Z₀Z₁ and Z₁Z₂.",
        "01": "Error detected on data qubit q₀ (Z₀Z₁ violated, Z₁Z₂ satisfied).",
        "11": "Error detected on data qubit q₁ (both Z₀Z₁ and Z₁Z₂ violated).",
        "10": "Error detected on data qubit q₂ (Z₀Z₁ satisfied, Z₁Z₂ violated).",
    }

    circuit_steps = [
        "1. State Preparation: Apply Ry(θ) to encode arbitrary unknown state on data qubit q₀.",
        "2. Stabilizer Encoding: Apply CNOT(q₀→q₁) and CNOT(q₀→q₂) to prepare non-local codeword α|000⟩ + β|111⟩.",
        f"3. Error Channel: {injected_desc}",
        "4. Syndrome Extraction: Non-demolition parity measurements into ancilla registers without state collapse.",
        "5. Coherent Recovery: Apply multi-controlled Toffoli correction to restore corrupted qubit.",
        "6. Logical Verification: Uncompute entanglement to extract recovered state on q₀.",
    ]

    return {
        "code_type": "3-Qubit Bit-Flip Code",
        "initial_state_theta_rad": round(initial_state_theta, 4),
        "injected_error": injected_desc,
        "error_qubit": error_qubit,
        "error_qubit_injected": error_qubit,
        "expected_syndrome": expected_syndrome,
        "syndrome_table": syndrome_table,
        "syndrome_measurements": counts,
        "circuit_steps": circuit_steps,
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
        "code_limitations": (
            "LIMITATION: Corrects single-qubit bit-flip (X) errors only. "
            "Cannot correct phase-flip (Z) or combined (Y = iXZ) errors. "
            "Arbitrary single-qubit error correction requires distance-3 codes (e.g. 9-qubit Shor code)."
        ),
        "coherent_recovery_mechanism": (
            "Uses coherent quantum feedback via multi-controlled Toffoli gates conditioned on ancilla registers. "
            "Relies on the Principle of Deferred Measurement, assuming ideal noiseless recovery gates."
        ),
        "explanation": (
            "The 3-qubit bit-flip code protects against single X errors by encoding "
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
    Pauli-Z phase error in computational basis acts as Pauli-X bit flip in Hadamard basis (H Z H = X).
    """
    if error_qubit is not None and error_qubit not in (0, 1, 2):
        raise ValueError(f"Invalid error_qubit {error_qubit}. Must be 0, 1, 2, or None.")

    qr_data = QuantumRegister(3, "data")
    qr_anc = QuantumRegister(2, "syndrome")
    cr_syndrome = ClassicalRegister(2, "s")
    cr_logical = ClassicalRegister(1, "logical")

    qc = QuantumCircuit(qr_data, qr_anc, cr_syndrome, cr_logical)

    # 1. State prep on q0
    qc.ry(initial_state_theta, qr_data[0])

    # 2. Encode: bit-flip encoding followed by transversal Hadamards
    qc.cx(qr_data[0], qr_data[1])
    qc.cx(qr_data[0], qr_data[2])
    for q in range(3):
        qc.h(qr_data[q])

    # 3. Inject Phase Error Z
    injected_desc = "No phase error injected (clean transmission)."
    if error_qubit in (0, 1, 2):
        qc.z(qr_data[error_qubit])
        injected_desc = f"Pauli-Z (phase-flip) injected on data qubit q_{error_qubit}."

    # 4. Transform to X-basis to convert phase errors into bit flips (H Z H = X)
    for q in range(3):
        qc.h(qr_data[q])

    # 5. Syndrome extraction in rotated basis
    qc.cx(qr_data[0], qr_anc[0])
    qc.cx(qr_data[1], qr_anc[0])
    qc.measure(qr_anc[0], cr_syndrome[0])

    qc.cx(qr_data[1], qr_anc[1])
    qc.cx(qr_data[2], qr_anc[1])
    qc.measure(qr_anc[1], cr_syndrome[1])

    # 6. Coherent correction in rotated basis
    qc.x(qr_anc[1])
    qc.ccx(qr_anc[0], qr_anc[1], qr_data[0])
    qc.x(qr_anc[1])

    qc.ccx(qr_anc[0], qr_anc[1], qr_data[1])

    qc.x(qr_anc[0])
    qc.ccx(qr_anc[0], qr_anc[1], qr_data[2])
    qc.x(qr_anc[0])

    # 7. Decode back to computational basis
    qc.cx(qr_data[0], qr_data[2])
    qc.cx(qr_data[0], qr_data[1])

    qc.measure(qr_data[0], cr_logical[0])

    sim = AerSimulator()
    job = sim.run(qc, shots=shots)
    counts = dict(job.result().get_counts())

    logical_0_count = sum(cnt for k, cnt in counts.items() if k.split()[0] == "0")
    logical_1_count = sum(cnt for k, cnt in counts.items() if k.split()[0] == "1")

    p0_measured = logical_0_count / shots
    p1_measured = logical_1_count / shots
    expected_p0 = math.cos(initial_state_theta / 2.0) ** 2
    expected_p1 = math.sin(initial_state_theta / 2.0) ** 2

    fidelity_retained = 1.0 - abs(p0_measured - expected_p0)

    # Syndrome diagnosis
    expected_syndrome = "00"
    if error_qubit == 0:
        expected_syndrome = "01"
    elif error_qubit == 1:
        expected_syndrome = "11"
    elif error_qubit == 2:
        expected_syndrome = "10"

    syndrome_table = {
        "00": "No phase error detected across stabilizers X₀X₁ and X₁X₂.",
        "01": "Phase error detected on data qubit q₀ (X₀X₁ violated, X₁X₂ satisfied).",
        "11": "Phase error detected on data qubit q₁ (both X₀X₁ and X₁X₂ violated).",
        "10": "Phase error detected on data qubit q₂ (X₀X₁ satisfied, X₁X₂ violated).",
    }

    circuit_steps = [
        "1. State Preparation: Apply Ry(θ) to prepare arbitrary initial state on data qubit q₀.",
        "2. Stabilizer Encoding: CNOT gates + transversal Hadamards to prepare |ψ_L⟩ = α|+++⟩ + β|---⟩.",
        f"3. Error Channel: {injected_desc}",
        "4. Basis Transformation: Transversal Hadamards rotate phase flips into bit flips (H Z H = X).",
        "5. Syndrome Extraction & Recovery: Extract parities into ancillae and apply coherent Toffoli correction.",
        "6. Decoding & Measurement: Disentangle code to recover original state on q₀.",
    ]

    return {
        "code_type": "3-Qubit Phase-Flip Code",
        "initial_state_theta_rad": round(initial_state_theta, 4),
        "injected_error": injected_desc,
        "error_qubit": error_qubit,
        "error_qubit_injected": error_qubit,
        "expected_syndrome": expected_syndrome,
        "syndrome_table": syndrome_table,
        "syndrome_measurements": counts,
        "circuit_steps": circuit_steps,
        "theoretical_input_probabilities": {
            "p0": round(expected_p0, 4),
            "p1": round(expected_p1, 4),
        },
        "recovered_logical_probabilities": {
            "p0": round(p0_measured, 4),
            "p1": round(p1_measured, 4),
        },
        "expected_p0": round(expected_p0, 4),
        "recovered_p0": round(p0_measured, 4),
        "logical_fidelity": round(max(0.0, min(1.0, fidelity_retained)), 4),
        "is_corrected": bool(abs(p0_measured - expected_p0) < 0.08),
        "code_limitations": (
            "LIMITATION: Corrects single-qubit phase-flip (Z) errors only. "
            "Cannot correct bit-flip (X) or combined (Y) errors. "
            "Arbitrary single-qubit error correction requires distance-3 codes (e.g. 9-qubit Shor code)."
        ),
        "coherent_recovery_mechanism": (
            "Uses coherent quantum feedback via multi-controlled Toffoli gates conditioned on ancilla registers. "
            "Relies on the Principle of Deferred Measurement, assuming ideal noiseless recovery gates."
        ),
        "explanation": (
            "The 3-qubit phase-flip code rotates the basis via transversal Hadamard gates, "
            "mapping phase errors Z into bit-flip errors X (H Z H = X), which are then "
            "diagnosed and corrected using the standard syndrome extraction circuit."
        ),
    }
