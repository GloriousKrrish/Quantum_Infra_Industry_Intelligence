"""
Verification Suite for Phase 03 Group D:
- Quantum Error Correction (3-Qubit Bit-Flip and Phase-Flip Codes across all qubits, syndromes, and error bounds)
- Quantum State Tomography (Multi-state Pauli X, Y, Z Reconstruction, Raw vs. Projected PSD, Uncertainties)
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

def test_error_correction_bit_flip_clean():
    """Clean channel (no error) produces syndrome 00 and preserves logical state."""
    res = simulate_3qubit_bit_flip_code(initial_state_theta=math.pi / 3.0, error_qubit=None, shots=2000)
    assert res["is_corrected"] is True
    assert res["expected_syndrome"] == "00"
    assert res["logical_fidelity"] > 0.95
    assert "LIMITATION" in res["code_limitations"]


def test_error_correction_bit_flip_q0():
    """Bit-flip code detects and corrects single X error on data qubit 0 (syndrome 01)."""
    res = simulate_3qubit_bit_flip_code(initial_state_theta=math.pi / 3.0, error_qubit=0, shots=2000)
    assert res["is_corrected"] is True
    assert res["logical_fidelity"] > 0.90
    assert res["expected_syndrome"] == "01"


def test_error_correction_bit_flip_q1():
    """Bit-flip code detects and corrects single X error on data qubit 1 (syndrome 11)."""
    res = simulate_3qubit_bit_flip_code(initial_state_theta=math.pi / 3.0, error_qubit=1, shots=2000)
    assert res["is_corrected"] is True
    assert res["logical_fidelity"] > 0.90
    assert res["expected_syndrome"] == "11"


def test_error_correction_bit_flip_q2():
    """Bit-flip code detects and corrects single X error on data qubit 2 (syndrome 10)."""
    res = simulate_3qubit_bit_flip_code(initial_state_theta=math.pi / 3.0, error_qubit=2, shots=2000)
    assert res["is_corrected"] is True
    assert res["logical_fidelity"] > 0.90
    assert res["expected_syndrome"] == "10"


def test_error_correction_bit_flip_invalid_qubit():
    """Invalid error qubit index raises ValueError."""
    with pytest.raises(ValueError, match="Invalid error_qubit"):
        simulate_3qubit_bit_flip_code(error_qubit=5)


def test_error_correction_phase_flip_clean():
    """Phase-flip clean channel produces syndrome 00 and preserves state."""
    res = simulate_3qubit_phase_flip_code(initial_state_theta=math.pi / 3.0, error_qubit=None, shots=2000)
    assert res["is_corrected"] is True
    assert res["expected_syndrome"] == "00"
    assert res["logical_fidelity"] > 0.95


def test_error_correction_phase_flip_q0():
    """Phase-flip code corrects single Z error on qubit 0 (syndrome 01) via Hadamard basis rotation."""
    res = simulate_3qubit_phase_flip_code(initial_state_theta=math.pi / 3.0, error_qubit=0, shots=2000)
    assert res["is_corrected"] is True
    assert res["expected_syndrome"] == "01"
    assert res["logical_fidelity"] > 0.90


def test_error_correction_phase_flip_q1():
    """Phase-flip code corrects single Z error on qubit 1 (syndrome 11)."""
    res = simulate_3qubit_phase_flip_code(initial_state_theta=math.pi / 3.0, error_qubit=1, shots=2000)
    assert res["is_corrected"] is True
    assert res["expected_syndrome"] == "11"
    assert res["logical_fidelity"] > 0.90


def test_error_correction_phase_flip_q2():
    """Phase-flip code corrects single Z error on qubit 2 (syndrome 10)."""
    res = simulate_3qubit_phase_flip_code(initial_state_theta=math.pi / 3.0, error_qubit=2, shots=2000)
    assert res["is_corrected"] is True
    assert res["expected_syndrome"] == "10"
    assert res["logical_fidelity"] > 0.90


def test_error_correction_phase_flip_invalid_qubit():
    """Invalid error qubit index raises ValueError for phase-flip code."""
    with pytest.raises(ValueError, match="Invalid error_qubit"):
        simulate_3qubit_phase_flip_code(error_qubit=-1)


# ═══════════════════════════════════════════════════════════════════════
# 2. STATE TOMOGRAPHY TESTS (Multi-State & PSD Reconstruction)
# ═══════════════════════════════════════════════════════════════════════

def test_single_qubit_tomography_ground_state():
    """Tomography on ground state |0> reconstructs north pole ⟨σ_z⟩≈+1."""
    ops = []  # Ground state |0>
    res = perform_single_qubit_tomography(circuit_ops=ops, shots=3000)

    rec_bloch = res["reconstructed_bloch_vector"]
    assert math.isclose(rec_bloch["z"], 1.0, abs_tol=0.06)
    assert math.isclose(rec_bloch["x"], 0.0, abs_tol=0.06)
    assert math.isclose(rec_bloch["y"], 0.0, abs_tol=0.06)
    assert res["fidelity_reconstructed"] > 0.98


def test_single_qubit_tomography_excited_state():
    """Tomography on excited state |1> reconstructs south pole ⟨σ_z⟩≈-1."""
    ops = [{"gate": "X", "targets": [0]}]
    res = perform_single_qubit_tomography(circuit_ops=ops, shots=3000)

    rec_bloch = res["reconstructed_bloch_vector"]
    assert math.isclose(rec_bloch["z"], -1.0, abs_tol=0.06)
    assert math.isclose(rec_bloch["x"], 0.0, abs_tol=0.06)
    assert math.isclose(rec_bloch["y"], 0.0, abs_tol=0.06)
    assert res["fidelity_reconstructed"] > 0.98


def test_single_qubit_tomography_plus_state():
    """Tomography on |+> reconstructs positive X pole ⟨σ_x⟩≈+1."""
    ops = [{"gate": "H", "targets": [0]}]
    res = perform_single_qubit_tomography(circuit_ops=ops, shots=3000)

    rec_bloch = res["reconstructed_bloch_vector"]
    assert math.isclose(rec_bloch["x"], 1.0, abs_tol=0.06)
    assert math.isclose(rec_bloch["z"], 0.0, abs_tol=0.06)
    assert math.isclose(rec_bloch["y"], 0.0, abs_tol=0.06)
    assert res["fidelity_reconstructed"] > 0.98


def test_single_qubit_tomography_minus_state():
    """Tomography on |-> reconstructs negative X pole ⟨σ_x⟩≈-1."""
    ops = [{"gate": "X", "targets": [0]}, {"gate": "H", "targets": [0]}]
    res = perform_single_qubit_tomography(circuit_ops=ops, shots=3000)

    rec_bloch = res["reconstructed_bloch_vector"]
    assert math.isclose(rec_bloch["x"], -1.0, abs_tol=0.06)
    assert math.isclose(rec_bloch["z"], 0.0, abs_tol=0.06)
    assert math.isclose(rec_bloch["y"], 0.0, abs_tol=0.06)
    assert res["fidelity_reconstructed"] > 0.98


def test_single_qubit_tomography_plus_i():
    """Tomography on |+i> reconstructs positive Y pole ⟨σ_y⟩≈+1."""
    ops = [{"gate": "H", "targets": [0]}, {"gate": "S", "targets": [0]}]
    res = perform_single_qubit_tomography(circuit_ops=ops, shots=3000)

    rec_bloch = res["reconstructed_bloch_vector"]
    assert math.isclose(rec_bloch["x"], 0.0, abs_tol=0.08)
    assert math.isclose(rec_bloch["y"], 1.0, abs_tol=0.08)
    assert math.isclose(rec_bloch["z"], 0.0, abs_tol=0.08)
    assert res["fidelity_reconstructed"] > 0.97


def test_single_qubit_tomography_complex_superposition_t_gate():
    """Tomography on non-Clifford state (H + T) preserves raw & projected PSD and statistical errors."""
    ops = [{"gate": "H", "targets": [0]}, {"gate": "T", "targets": [0]}]
    res = perform_single_qubit_tomography(circuit_ops=ops, shots=3000)

    assert "raw_bloch_vector" in res
    assert "fidelity_raw" in res
    assert "fidelity_projected" in res
    assert "std_error" in res["pauli_measurements"]["x"]
    assert "statistical_notice" in res
    assert res["fidelity_reconstructed"] > 0.95
