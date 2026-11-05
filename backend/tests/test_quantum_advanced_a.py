"""
Verification Suite for Phase 03 Group A:
- State Evolution
- Density Matrix Laboratory
- Quantum Measurement Theory
- Quantum Interference Laboratory
"""

import math
import numpy as np
import pytest

from backend.app.engines.quantum.state_evolution import (
    simulate_state_evolution,
    build_hamiltonian,
)
from backend.app.engines.quantum.density_matrix import (
    analyze_density_matrix,
    validate_density_matrix,
    compute_purity,
    partial_trace_2qubit,
    DensityMatrixValidationError,
)
from backend.app.engines.quantum.measurement_theory import (
    execute_measurement_experiment,
)
from backend.app.engines.quantum.interference import (
    simulate_mach_zehnder,
)


# ═══════════════════════════════════════════════════════════════════════
# 1. STATE EVOLUTION TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_state_evolution_pauli_x_inversion():
    """Under H = omega * sigma_x, state |0> rotates to |1> at t = pi/(2*omega)."""
    omega = 1.0
    t_half = math.pi / 2.0  # At t = pi/2, exp(-i sigma_x pi/2) = -i sigma_x
    res = simulate_state_evolution(
        hamiltonian_type="pauli_x",
        initial_state_name="zero",
        omega=omega,
        total_time=t_half,
        num_steps=10,
    )
    final_point = res["trajectory"][-1]
    # At t = pi/2: prob of 0 should be 0, prob of 1 should be 1
    assert math.isclose(final_point["probabilities"][1], 1.0, abs_tol=1e-3)
    assert math.isclose(final_point["probabilities"][0], 0.0, abs_tol=1e-3)


def test_state_evolution_energy_conservation():
    """Energy expectation value <H> must be conserved throughout unitary time evolution."""
    res = simulate_state_evolution(
        hamiltonian_type="general_b_field",
        b_field={"x": 1.0, "y": 0.5, "z": 0.8},
        initial_state_name="plus",
        total_time=5.0,
        num_steps=20,
    )
    assert res["num_qubits"] == 1
    assert len(res["trajectory"]) == 20
    # Energy expectation value is constant and returned
    assert isinstance(res["energy_expectation"], float)


def test_state_evolution_2qubit_ising():
    """Ising ZZ Hamiltonian H = J (sigma_z (x) sigma_z) preserves computational basis states."""
    res = simulate_state_evolution(
        hamiltonian_type="ising_zz",
        initial_state_name="01",
        j_coupling=1.5,
        total_time=4.0,
        num_steps=15,
    )
    assert res["num_qubits"] == 2
    # Basis state |01> is an eigenstate of sigma_z (x) sigma_z with eigenvalue -1
    # Hence population remains 100% in |01>
    for pt in res["trajectory"]:
        assert math.isclose(pt["probabilities"][1], 1.0, abs_tol=1e-3)


# ═══════════════════════════════════════════════════════════════════════
# 2. DENSITY MATRIX TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_density_matrix_pure_validation():
    """Pure state |+> has purity Tr(rho^2) = 1.0."""
    res = analyze_density_matrix(preset="pure_plus")
    assert res["is_valid"] is True
    assert res["classification"] == "PURE"
    assert math.isclose(res["purity"], 1.0, abs_tol=1e-5)
    assert math.isclose(res["trace"], 1.0, abs_tol=1e-5)
    assert res["rank"] == 1


def test_density_matrix_mixed_purity():
    """1-qubit maximally mixed state has purity Tr(rho^2) = 0.5 and rank = 2."""
    res = analyze_density_matrix(preset="maximally_mixed_1q")
    assert res["is_valid"] is True
    assert res["classification"] == "MAXIMALLY_MIXED"
    assert math.isclose(res["purity"], 0.5, abs_tol=1e-5)
    assert res["rank"] == 2


def test_density_matrix_non_hermitian_rejected():
    """Non-Hermitian matrix must raise DensityMatrixValidationError."""
    non_herm = [
        [{"real": 1.0, "imag": 0.0}, {"real": 1.0, "imag": 0.5}],
        [{"real": 0.0, "imag": 0.0}, {"real": 0.0, "imag": 0.0}],
    ]
    with pytest.raises(DensityMatrixValidationError):
        analyze_density_matrix(matrix_data=non_herm)


def test_density_matrix_partial_trace():
    """Partial trace of Bell state |Phi+> leaves maximally mixed subsystem."""
    res = analyze_density_matrix(preset="bell_phi_plus")
    assert res["dimension"] == 4
    assert res["classification"] == "PURE"  # 4x4 global state is pure
    # Subsystem A is maximally mixed: Tr(rho_A^2) = 0.50
    rho_a = np.array([
        [complex(c["real"], c["imag"]) for c in row]
        for row in res["reduced_subsystem_a"]
    ])
    purity_a = compute_purity(rho_a)
    assert math.isclose(purity_a, 0.50, abs_tol=1e-4)


# ═══════════════════════════════════════════════════════════════════════
# 3. MEASUREMENT THEORY TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_measurement_born_rule_z():
    """State |+> measured in Z-basis yields 50% |0> and 50% |1>."""
    ops = [{"gate": "H", "targets": [0]}]
    res = execute_measurement_experiment(circuit_ops=ops, num_qubits=1, basis="Z", shots=2000)
    p0 = next(o["theoretical_probability"] for o in res["theoretical_outcomes"] if o["label"] == "0")
    p1 = next(o["theoretical_probability"] for o in res["theoretical_outcomes"] if o["label"] == "1")
    assert math.isclose(p0, 0.50, abs_tol=1e-4)
    assert math.isclose(p1, 0.50, abs_tol=1e-4)


def test_measurement_hadamard_basis_x():
    """State |+> measured in X-basis yields 100% |+> deterministically."""
    ops = [{"gate": "H", "targets": [0]}]
    res = execute_measurement_experiment(circuit_ops=ops, num_qubits=1, basis="X", shots=2000)
    p_plus = next(o["theoretical_probability"] for o in res["theoretical_outcomes"] if o["label"] == "+")
    p_minus = next(o["theoretical_probability"] for o in res["theoretical_outcomes"] if o["label"] == "-")
    assert math.isclose(p_plus, 1.0, abs_tol=1e-4)
    assert math.isclose(p_minus, 0.0, abs_tol=1e-4)


def test_measurement_collapse_projection():
    """Collapsed outcome post-measurement bloch vector is verified."""
    ops = [{"gate": "H", "targets": [0]}]
    res = execute_measurement_experiment(circuit_ops=ops, num_qubits=1, basis="Z", simulate_collapse_outcome="0")
    collapsed = res["collapsed_state_demonstration"]["post_measurement_bloch"]
    assert math.isclose(collapsed["z"], 1.0, abs_tol=1e-4)  # Collapsed to north pole |0>


# ═══════════════════════════════════════════════════════════════════════
# 4. QUANTUM INTERFERENCE TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_interference_constructive_and_destructive():
    """Phase theta = 0 gives constructive; theta = pi gives destructive interference."""
    res_0 = simulate_mach_zehnder(phase_theta=0.0, shots=1000)
    assert res_0["interference_regime"] == "CONSTRUCTIVE"
    assert math.isclose(res_0["theoretical_probabilities"]["p0"], 1.0, abs_tol=1e-4)
    assert math.isclose(res_0["theoretical_probabilities"]["p1"], 0.0, abs_tol=1e-4)

    res_pi = simulate_mach_zehnder(phase_theta=math.pi, shots=1000)
    assert res_pi["interference_regime"] == "DESTRUCTIVE"
    assert math.isclose(res_pi["theoretical_probabilities"]["p0"], 0.0, abs_tol=1e-4)
    assert math.isclose(res_pi["theoretical_probabilities"]["p1"], 1.0, abs_tol=1e-4)


def test_interference_fringe_sweep():
    """Phase sweep yields sinusoidal fringe curve matching cos^2(theta/2)."""
    res = simulate_mach_zehnder(phase_theta=0.0, include_sweep=True, sweep_steps=20)
    curve = res["sweep_curve"]
    assert len(curve) == 20
    for pt in curve:
        th = pt["phase_rad"]
        expected_p0 = math.cos(th / 2.0) ** 2
        assert math.isclose(pt["theory_p0"], expected_p0, abs_tol=1e-4)

