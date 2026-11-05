"""
Verification Suite for Phase 03 Group D:
- Quantum Error Correction (3-Qubit Bit-Flip and Phase-Flip Codes)
- Quantum State Tomography (Pauli X, Y, Z Reconstruction, Fidelity)
"""

import math
import numpy as np
import pytest

from backend.app.engines.quantum.error_correction import (
    simulate_3qubit_bit_flip_code,
    simulate_3qubit_phase_flip_code,
)
from backend.app.engines.quantum.tomography import (
    perform_single_qubit_tomography,
)


# ═══════════════════════════════════════════════════════════════════════
# 1. ERROR CORRECTION TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_error_correction_bit_flip_q1():
    """Bit-flip code detects and corrects single X error on data qubit 1 with high fidelity."""
    res = simulate_3qubit_bit_flip_code(initial_state_theta=math.pi / 3.0, error_qubit=1, shots=2000)
    assert res["is_corrected"] is True
    assert res["logical_fidelity"] > 0.90
    assert res["expected_syndrome"] == "11"


def test_error_correction_bit_flip_clean():
    """Clean channel (no error) produces syndrome 00 and preserves logical state."""
    res = simulate_3qubit_bit_flip_code(initial_state_theta=math.pi / 3.0, error_qubit=None, shots=2000)
    assert res["is_corrected"] is True
    assert res["expected_syndrome"] == "00"
    assert res["logical_fidelity"] > 0.95


def test_error_correction_phase_flip_q0():
    """Phase-flip code corrects single Z error on qubit 0 via Hadamard basis rotation."""
    res = simulate_3qubit_phase_flip_code(initial_state_theta=math.pi / 3.0, error_qubit=0, shots=2000)
    assert res["is_corrected"] is True
    assert abs(res["recovered_p0"] - res["expected_p0"]) < 0.08


# ═══════════════════════════════════════════════════════════════════════
# 2. STATE TOMOGRAPHY TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_single_qubit_tomography_plus_i():
    """Tomography on |+i> reconstructs ⟨σ_x⟩≈0, ⟨σ_y⟩≈1, ⟨σ_z⟩≈0 with high fidelity."""
    ops = [{"gate": "H", "targets": [0]}, {"gate": "S", "targets": [0]}]
    res = perform_single_qubit_tomography(circuit_ops=ops, shots=3000)

    # Theoretical Bloch vector: (0, 1, 0)
    rec_bloch = res["reconstructed_bloch_vector"]
    assert math.isclose(rec_bloch["x"], 0.0, abs_tol=0.08)
    assert math.isclose(rec_bloch["y"], 1.0, abs_tol=0.08)
    assert math.isclose(rec_bloch["z"], 0.0, abs_tol=0.08)
    assert res["fidelity_reconstructed"] > 0.98


def test_single_qubit_tomography_ground_state():
    """Tomography on ground state |0> reconstructs north pole ⟨σ_z⟩≈1 with high fidelity."""
    ops = []  # Ground state |0>
    res = perform_single_qubit_tomography(circuit_ops=ops, shots=2000)

    rec_bloch = res["reconstructed_bloch_vector"]
    assert math.isclose(rec_bloch["z"], 1.0, abs_tol=0.05)
    assert res["fidelity_reconstructed"] > 0.99
