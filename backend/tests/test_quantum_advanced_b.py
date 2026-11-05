"""
Verification Suite for Phase 03 Group B:
- Quantum Information & Entropy (Von Neumann, Shannon, Fidelity, Trace Distance)
- Advanced Entanglement Analysis (Schmidt, Concurrence, PPT Negativity, Werner States)
"""

import math
import numpy as np
import pytest

from backend.app.engines.quantum.quantum_information import (
    compute_von_neumann_entropy,
    compute_shannon_entropy,
    compute_quantum_fidelity,
    compute_trace_distance,
    analyze_quantum_information,
)
from backend.app.engines.quantum.entanglement_analysis import (
    schmidt_decomposition_pure_state,
    compute_concurrence_2qubit,
    compute_negativity_and_ppt,
    analyze_entanglement_state,
)


# ═══════════════════════════════════════════════════════════════════════
# 1. QUANTUM INFORMATION & ENTROPY TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_von_neumann_entropy_pure_state_zero():
    """Pure states have exact zero Von Neumann entropy: S(|ψ⟩) = 0.0."""
    rho_pure = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    s = compute_von_neumann_entropy(rho_pure)
    assert math.isclose(s, 0.0, abs_tol=1e-7)


def test_von_neumann_entropy_maximally_mixed_log2d():
    """Maximally mixed 2-qubit state (d=4) has S = log2(4) = 2.0 ebits."""
    rho_mixed_4 = 0.25 * np.eye(4, dtype=complex)
    s = compute_von_neumann_entropy(rho_mixed_4)
    assert math.isclose(s, 2.0, abs_tol=1e-7)


def test_fidelity_identical_states_one():
    """Fidelity of any state with itself is identically 1.0."""
    rho = 0.5 * np.array([[1.0, 1.0], [1.0, 1.0]], dtype=complex)
    fid = compute_quantum_fidelity(rho, rho)
    assert math.isclose(fid["squared_fidelity"], 1.0, abs_tol=1e-6)
    assert math.isclose(fid["root_fidelity"], 1.0, abs_tol=1e-6)


def test_fidelity_orthogonal_states_zero():
    """Fidelity of orthogonal states |0⟩ and |1⟩ is identically 0.0."""
    rho_0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    rho_1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
    fid = compute_quantum_fidelity(rho_0, rho_1)
    assert math.isclose(fid["squared_fidelity"], 0.0, abs_tol=1e-6)


def test_trace_distance_orthogonal_states_one():
    """Trace distance between orthogonal states |0⟩ and |1⟩ is D = 1.0."""
    rho_0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    rho_1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
    d = compute_trace_distance(rho_0, rho_1)
    assert math.isclose(d, 1.0, abs_tol=1e-6)


def test_fuchs_van_de_graaf_inequality():
    """Fuchs-van de Graaf bounds 1 - √F <= D <= √(1 - F) hold for non-orthogonal states."""
    res = analyze_quantum_information(state_a_preset="pure_zero", state_b_preset="pure_plus")
    bounds = res["relational_metrics"]["fuchs_van_de_graaf_bounds"]
    assert bounds["is_satisfied"] is True
    # For |0⟩ and |+⟩: F = 1/2 = 0.5, √F ~ 0.7071
    # Trace distance D = 1/√2 ~ 0.7071
    assert math.isclose(res["relational_metrics"]["squared_fidelity_F"], 0.5, abs_tol=1e-4)


# ═══════════════════════════════════════════════════════════════════════
# 2. ENTANGLEMENT ANALYSIS TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_schmidt_decomposition_bell_state():
    """Bell state |Phi+> has Schmidt rank 2, equal coefficients 1/√2, and E = 1.0 ebit."""
    psi_bell = np.array([1.0 / math.sqrt(2), 0.0, 0.0, 1.0 / math.sqrt(2)], dtype=complex)
    schmidt = schmidt_decomposition_pure_state(psi_bell, dim_a=2, dim_b=2)
    assert schmidt["schmidt_rank"] == 2
    assert schmidt["is_entangled"] is True
    assert math.isclose(schmidt["entanglement_entropy_ebits"], 1.0, abs_tol=1e-4)
    for c in schmidt["schmidt_coefficients"]:
        assert math.isclose(c, 1.0 / math.sqrt(2), abs_tol=1e-4)


def test_schmidt_decomposition_separable_state():
    """Separable product state |00> has Schmidt rank 1 and E = 0.0 ebit."""
    psi_sep = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
    schmidt = schmidt_decomposition_pure_state(psi_sep, dim_a=2, dim_b=2)
    assert schmidt["schmidt_rank"] == 1
    assert schmidt["is_entangled"] is False
    assert math.isclose(schmidt["entanglement_entropy_ebits"], 0.0, abs_tol=1e-4)


def test_wootters_concurrence_bell_state():
    """Bell state has maximum concurrence C(ρ) = 1.0."""
    res = analyze_entanglement_state(preset="bell_phi_plus")
    assert math.isclose(res["concurrence"], 1.0, abs_tol=1e-4)
    assert res["ppt_negativity"]["is_entangled_npt"] is True
    assert math.isclose(res["ppt_negativity"]["negativity"], 0.5, abs_tol=1e-4)


def test_classical_correlated_state_has_zero_concurrence():
    """Classically correlated mixture 0.5|00><00| + 0.5|11><11| has ZERO concurrence."""
    res = analyze_entanglement_state(preset="classical_correlated_separable")
    assert math.isclose(res["concurrence"], 0.0, abs_tol=1e-5)
    assert res["ppt_negativity"]["is_ppt_separable"] is True
    assert res["entanglement_classification"] == "SEPARABLE_CLASSICAL_CORRELATION"


def test_werner_state_entanglement_transition():
    """Werner state is entangled if and only if p > 1/3 ~ 0.333."""
    # At p = 0.8: strongly entangled
    res_ent = analyze_entanglement_state(preset="werner_state", werner_parameter_p=0.8)
    assert res_ent["concurrence"] > 0.0
    assert res_ent["ppt_negativity"]["is_entangled_npt"] is True
    assert res_ent["entanglement_classification"] == "ENTANGLED"

    # Near boundary: at p = 0.34 (p > 1/3 ~ 0.3333), state is weakly entangled
    res_boundary_ent = analyze_entanglement_state(preset="werner_state", werner_parameter_p=0.34)
    assert res_boundary_ent["concurrence"] > 0.0
    assert res_boundary_ent["entanglement_classification"] == "ENTANGLED"

    # Near boundary: at p = 0.33 (p <= 1/3), state is strictly separable
    res_boundary_sep = analyze_entanglement_state(preset="werner_state", werner_parameter_p=0.33)
    assert math.isclose(res_boundary_sep["concurrence"], 0.0, abs_tol=1e-5)
    assert res_boundary_sep["entanglement_classification"] == "SEPARABLE"

    # At p = 0.2: separable
    res_sep = analyze_entanglement_state(preset="werner_state", werner_parameter_p=0.2)
    assert math.isclose(res_sep["concurrence"], 0.0, abs_tol=1e-5)
    assert res_sep["ppt_negativity"]["is_ppt_separable"] is True
    assert res_sep["entanglement_classification"] == "SEPARABLE"

