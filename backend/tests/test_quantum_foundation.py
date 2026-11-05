"""
Scientific Validation Suite for Phase 02 — Quantum Computing Foundation.

Tests:
1. Gate Library Unitary Properties (U^dagger U = I)
2. Single-Qubit State Evolution (X, Y, Z, H, S, T, Rotations)
3. Multi-Qubit Entanglement (4 Bell States, 3-Qubit GHZ State)
4. Statevector Probability Normalization (sum |alpha_i|^2 = 1.0)
5. Reduced Density Matrix & Bloch Vector Calculations (Pure vs Entangled Mixed States)
6. Quantum Teleportation Protocol (Deferred Measurement Fidelity & Equivalence)
7. Qubit Ordering Consistency (Qiskit Little-Endian |q_{n-1} ... q_0>)
8. Complex Amplitudes & Phase Angles (Re, Im, Magnitude, Phase)
9. FastAPI API Endpoints & Circuit Validation Guardrails
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.engines.quantum.gate_library import (
    GATE_CATALOG,
    MATRIX_I,
    MATRIX_X,
    MATRIX_Y,
    MATRIX_Z,
    MATRIX_H,
    MATRIX_S,
    MATRIX_T,
    MATRIX_CNOT,
    MATRIX_CZ,
    MATRIX_SWAP,
    MATRIX_TOFFOLI,
    get_rx_matrix,
    get_ry_matrix,
    get_rz_matrix,
)
from backend.app.engines.quantum.circuit_engine import (
    build_qiskit_circuit,
    CircuitValidationError,
)
from backend.app.engines.quantum.simulation_engine import simulate_circuit
from backend.app.engines.quantum.experiment_library import (
    get_all_experiments,
    get_experiment_by_id,
)

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════
# 1. UNITARY MATRIX VERIFICATION (U^dagger U = I)
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "name, mat",
    [
        ("I", MATRIX_I),
        ("X", MATRIX_X),
        ("Y", MATRIX_Y),
        ("Z", MATRIX_Z),
        ("H", MATRIX_H),
        ("S", MATRIX_S),
        ("T", MATRIX_T),
        ("CNOT", MATRIX_CNOT),
        ("CZ", MATRIX_CZ),
        ("SWAP", MATRIX_SWAP),
        ("TOFFOLI", MATRIX_TOFFOLI),
    ],
)
def test_static_gate_unitarity(name: str, mat: np.ndarray):
    """Every quantum gate matrix must be strictly unitary: U^dagger @ U = I."""
    identity = np.eye(mat.shape[0], dtype=complex)
    product = mat.conj().T @ mat
    assert np.allclose(product, identity, atol=1e-10), f"Gate {name} violates unitarity."


@pytest.mark.parametrize("angle", [0.0, math.pi / 4.0, math.pi / 2.0, math.pi, 2.5])
def test_rotation_gates_unitarity(angle: float):
    """Parameterized rotation matrices Rx, Ry, Rz must be unitary for all angles."""
    for fn in (get_rx_matrix, get_ry_matrix, get_rz_matrix):
        mat = fn(angle)
        identity = np.eye(2, dtype=complex)
        product = mat.conj().T @ mat
        assert np.allclose(product, identity, atol=1e-10)


# ═══════════════════════════════════════════════════════════════════════
# 2. SINGLE-QUBIT BASIS TRANSFORMATIONS
# ═══════════════════════════════════════════════════════════════════════

def test_pauli_x_inversion():
    """Pauli-X transforms |0> -> |1>."""
    res = simulate_circuit(num_qubits=1, operations=[{"gate": "X", "targets": [0]}], shots=500)
    # State 1 has 100% probability
    assert math.isclose(res["statevector"][1]["probability"], 1.0, abs_tol=1e-5)
    assert math.isclose(res["statevector"][0]["probability"], 0.0, abs_tol=1e-5)
    # Bloch vector is south pole: (0, 0, -1)
    bv = res["qubit_bloch_vectors"][0]["bloch_vector"]
    assert math.isclose(bv["z"], -1.0, abs_tol=1e-4)


def test_hadamard_superposition():
    """Hadamard transforms |0> -> |+> = (|0> + |1>)/sqrt(2)."""
    res = simulate_circuit(num_qubits=1, operations=[{"gate": "H", "targets": [0]}], shots=1000)
    p0 = res["statevector"][0]["probability"]
    p1 = res["statevector"][1]["probability"]
    assert math.isclose(p0, 0.50, abs_tol=1e-5)
    assert math.isclose(p1, 0.50, abs_tol=1e-5)
    # Bloch vector points along +X axis: (1, 0, 0)
    bv = res["qubit_bloch_vectors"][0]["bloch_vector"]
    assert math.isclose(bv["x"], 1.0, abs_tol=1e-4)
    assert math.isclose(bv["z"], 0.0, abs_tol=1e-4)


def test_quantum_interference_hz_h():
    """H-Z-H on |0> causes destructive interference on |0>, yielding |1> deterministically."""
    ops = [
        {"gate": "H", "targets": [0]},
        {"gate": "Z", "targets": [0]},
        {"gate": "H", "targets": [0]},
    ]
    res = simulate_circuit(num_qubits=1, operations=ops, shots=500)
    assert math.isclose(res["statevector"][1]["probability"], 1.0, abs_tol=1e-5)
    assert math.isclose(res["statevector"][0]["probability"], 0.0, abs_tol=1e-5)


# ═══════════════════════════════════════════════════════════════════════
# 3. ENTANGLEMENT & BELL STATES
# ═══════════════════════════════════════════════════════════════════════

def test_bell_state_phi_plus():
    """|Phi+> = (|00> + |11>)/sqrt(2)."""
    ops = [
        {"gate": "H", "targets": [0]},
        {"gate": "CX", "targets": [1], "controls": [0]},
    ]
    res = simulate_circuit(num_qubits=2, operations=ops, shots=2048)
    amplitudes = {s["bitstring"]: s["probability"] for s in res["statevector"]}

    assert math.isclose(amplitudes["00"], 0.50, abs_tol=1e-4)
    assert math.isclose(amplitudes["11"], 0.50, abs_tol=1e-4)
    assert amplitudes["01"] < 1e-6
    assert amplitudes["10"] < 1e-6

    # Reduced density matrix check: for Bell state, individual qubits are MAXIMALLY MIXED!
    q0_bloch = res["qubit_bloch_vectors"][0]
    q1_bloch = res["qubit_bloch_vectors"][1]
    assert q0_bloch["state_classification"] == "MAXIMALLY_MIXED"
    assert q1_bloch["state_classification"] == "MAXIMALLY_MIXED"
    assert math.isclose(q0_bloch["purity"], 0.50, abs_tol=1e-4)
    assert math.isclose(q0_bloch["bloch_vector"]["length"], 0.0, abs_tol=1e-4)


def test_bell_state_psi_plus():
    """|Psi+> = (|01> + |10>)/sqrt(2)."""
    ops = [
        {"gate": "H", "targets": [0]},
        {"gate": "X", "targets": [1]},
        {"gate": "CX", "targets": [1], "controls": [0]},
    ]
    res = simulate_circuit(num_qubits=2, operations=ops, shots=1024)
    amplitudes = {s["bitstring"]: s["probability"] for s in res["statevector"]}

    assert math.isclose(amplitudes["01"], 0.50, abs_tol=1e-4)
    assert math.isclose(amplitudes["10"], 0.50, abs_tol=1e-4)
    assert amplitudes["00"] < 1e-6
    assert amplitudes["11"] < 1e-6


def test_ghz_state():
    """3-qubit GHZ state = (|000> + |111>)/sqrt(2)."""
    ops = [
        {"gate": "H", "targets": [0]},
        {"gate": "CX", "targets": [1], "controls": [0]},
        {"gate": "CX", "targets": [2], "controls": [1]},
    ]
    res = simulate_circuit(num_qubits=3, operations=ops, shots=2048)
    amplitudes = {s["bitstring"]: s["probability"] for s in res["statevector"]}

    assert math.isclose(amplitudes["000"], 0.50, abs_tol=1e-4)
    assert math.isclose(amplitudes["111"], 0.50, abs_tol=1e-4)

    # All three individual qubits are maximally mixed
    for q_info in res["qubit_bloch_vectors"]:
        assert q_info["state_classification"] == "MAXIMALLY_MIXED"
        assert math.isclose(q_info["purity"], 0.50, abs_tol=1e-4)


# ═══════════════════════════════════════════════════════════════════════
# 4. PROBABILITY NORMALIZATION, ORDERING & TELEPORTATION
# ═══════════════════════════════════════════════════════════════════════

def test_probability_normalization():
    """Sum of all computational basis probabilities must equal 1.0."""
    ops = [
        {"gate": "H", "targets": [0]},
        {"gate": "RY", "targets": [1], "params": {"theta": 1.2}},
        {"gate": "CX", "targets": [2], "controls": [0]},
        {"gate": "RZ", "targets": [2], "params": {"phi": 0.8}},
    ]
    res = simulate_circuit(num_qubits=3, operations=ops, shots=1000)
    total_prob = sum(s["probability"] for s in res["statevector"])
    assert math.isclose(total_prob, 1.0, abs_tol=1e-5)


def test_qubit_ordering_little_endian():
    """Verify Qiskit little-endian ordering |q_{n-1} ... q_0> across statevector and measurements."""
    # Applying X only on qubit 0 should yield bitstring '001' (rightmost bit = 1)
    res_q0 = simulate_circuit(num_qubits=3, operations=[{"gate": "X", "targets": [0]}], shots=100)
    assert res_q0["statevector"][1]["bitstring"] == "001"
    assert math.isclose(res_q0["statevector"][1]["probability"], 1.0, abs_tol=1e-6)
    assert res_q0["measurements"][0]["bitstring"] == "001"

    # Applying X only on qubit 2 should yield bitstring '100' (leftmost bit = 1)
    res_q2 = simulate_circuit(num_qubits=3, operations=[{"gate": "X", "targets": [2]}], shots=100)
    assert res_q2["statevector"][4]["bitstring"] == "100"
    assert math.isclose(res_q2["statevector"][4]["probability"], 1.0, abs_tol=1e-6)
    assert res_q2["measurements"][0]["bitstring"] == "100"


def test_complex_amplitudes_and_phase_angles():
    """Verify complex amplitude extraction (Re, Im, magnitude, phase)."""
    # Create |+i> = (|0> + i|1>)/sqrt(2) via H then S on qubit 0
    res = simulate_circuit(num_qubits=1, operations=[{"gate": "H", "targets": [0]}, {"gate": "S", "targets": [0]}])
    s0 = res["statevector"][0]  # |0>
    s1 = res["statevector"][1]  # |1>

    assert math.isclose(s0["real"], 1.0 / math.sqrt(2), abs_tol=1e-4)
    assert math.isclose(s0["imag"], 0.0, abs_tol=1e-4)
    assert math.isclose(s0["magnitude"], 1.0 / math.sqrt(2), abs_tol=1e-4)
    assert math.isclose(s0["phase_rad"], 0.0, abs_tol=1e-4)

    assert math.isclose(s1["real"], 0.0, abs_tol=1e-4)
    assert math.isclose(s1["imag"], 1.0 / math.sqrt(2), abs_tol=1e-4)
    assert math.isclose(s1["magnitude"], 1.0 / math.sqrt(2), abs_tol=1e-4)
    assert math.isclose(s1["phase_rad"], math.pi / 2.0, abs_tol=1e-4)
    assert math.isclose(s1["phase_deg"], 90.0, abs_tol=1e-2)


def test_reduced_density_matrix_mixed_vs_pure():
    """Verify purity gamma = Tr(rho^2) = 1.0 for product states and gamma = 0.5 for Bell pairs."""
    # Separable product state: |+> (x) |0>
    res_sep = simulate_circuit(num_qubits=2, operations=[{"gate": "H", "targets": [0]}])
    for q in res_sep["qubit_bloch_vectors"]:
        assert q["state_classification"] == "PURE"
        assert math.isclose(q["purity"], 1.0, abs_tol=1e-4)
        assert math.isclose(q["bloch_vector"]["length"], 1.0, abs_tol=1e-4)

    # Entangled Bell pair: (|00> + |11>)/sqrt(2)
    res_ent = simulate_circuit(num_qubits=2, operations=[{"gate": "H", "targets": [0]}, {"gate": "CX", "targets": [1], "controls": [0]}])
    for q in res_ent["qubit_bloch_vectors"]:
        assert q["state_classification"] == "MAXIMALLY_MIXED"
        assert math.isclose(q["purity"], 0.5, abs_tol=1e-4)
        assert math.isclose(q["bloch_vector"]["length"], 0.0, abs_tol=1e-4)
        assert math.isclose(q["prob_0"], 0.5, abs_tol=1e-4)
        assert math.isclose(q["prob_1"], 0.5, abs_tol=1e-4)


def test_quantum_teleportation_experiment():
    """Verify teleportation reproduces Bob's qubit state with fidelity = 1.0."""
    exp = get_experiment_by_id("exp_quantum_teleportation")
    assert exp is not None
    res = simulate_circuit(
        num_qubits=exp["num_qubits"],
        operations=exp["circuit"],
        shots=2048,
    )
    assert res["num_qubits"] == 3
    assert len(res["statevector"]) == 8

    # Bob's qubit is index 2
    bob_bloch = res["qubit_bloch_vectors"][2]
    assert bob_bloch["state_classification"] == "PURE"
    assert math.isclose(bob_bloch["purity"], 1.0, abs_tol=1e-3)
    assert math.isclose(bob_bloch["bloch_vector"]["length"], 1.0, abs_tol=1e-3)

    # Input state was Ry(pi/3)|0> -> rx = sin(pi/3) = sqrt(3)/2 ~ 0.8660, rz = cos(pi/3) = 0.5
    assert math.isclose(bob_bloch["bloch_vector"]["x"], math.sin(math.pi / 3.0), abs_tol=1e-3)
    assert math.isclose(bob_bloch["bloch_vector"]["y"], 0.0, abs_tol=1e-3)
    assert math.isclose(bob_bloch["bloch_vector"]["z"], math.cos(math.pi / 3.0), abs_tol=1e-3)

    # Bob's measurement probabilities: P(0) = cos^2(pi/6) = 0.75, P(1) = sin^2(pi/6) = 0.25
    assert math.isclose(bob_bloch["prob_0"], 0.75, abs_tol=1e-3)
    assert math.isclose(bob_bloch["prob_1"], 0.25, abs_tol=1e-3)


# ═══════════════════════════════════════════════════════════════════════
# 5. CIRCUIT VALIDATION & ERROR GUARDS
# ═══════════════════════════════════════════════════════════════════════

def test_circuit_out_of_bounds_qubit_rejected():
    """Qubit index >= num_qubits raises CircuitValidationError."""
    with pytest.raises(CircuitValidationError):
        simulate_circuit(num_qubits=2, operations=[{"gate": "X", "targets": [5]}])


def test_circuit_qubit_count_exceeded_rejected():
    """Qubit count > 8 raises CircuitValidationError."""
    with pytest.raises(CircuitValidationError):
        simulate_circuit(num_qubits=12, operations=[{"gate": "H", "targets": [0]}])


def test_circuit_overlapping_control_target_rejected():
    """Same qubit cannot be both control and target."""
    with pytest.raises(CircuitValidationError):
        simulate_circuit(
            num_qubits=2,
            operations=[{"gate": "CX", "targets": [0], "controls": [0]}],
        )


# ═══════════════════════════════════════════════════════════════════════
# 6. API ENDPOINTS INTEGRATION
# ═══════════════════════════════════════════════════════════════════════

def test_api_list_gates():
    """GET /api/quantum/gates returns complete gate specifications."""
    resp = client.get("/api/quantum/gates")
    assert resp.status_code == 200
    gates = resp.json()
    assert len(gates) >= 12
    gate_ids = [g["id"] for g in gates]
    assert "H" in gate_ids
    assert "CX" in gate_ids
    assert "RX" in gate_ids


def test_api_get_single_gate():
    """GET /api/quantum/gates/H returns Hadamard gate."""
    resp = client.get("/api/quantum/gates/H")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Hadamard Gate"
    assert data["num_qubits"] == 1


def test_api_simulate_circuit():
    """POST /api/quantum/circuit/simulate executes circuit and returns statevector & Bloch info."""
    payload = {
        "num_qubits": 2,
        "operations": [
            {"gate": "H", "targets": [0], "controls": []},
            {"gate": "CX", "targets": [1], "controls": [0]},
        ],
        "shots": 500,
    }
    resp = client.post("/api/quantum/circuit/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["num_qubits"] == 2
    assert len(data["statevector"]) == 4
    assert len(data["qubit_bloch_vectors"]) == 2
    assert data["qubit_bloch_vectors"][0]["state_classification"] == "MAXIMALLY_MIXED"


def test_api_list_experiments():
    """GET /api/quantum/experiments returns catalog of 10 experiments."""
    resp = client.get("/api/quantum/experiments")
    assert resp.status_code == 200
    experiments = resp.json()
    assert len(experiments) >= 10
    exp_ids = [e["id"] for e in experiments]
    assert "exp_bell_phi_plus" in exp_ids
    assert "exp_ghz_state" in exp_ids
    assert "exp_quantum_teleportation" in exp_ids


def test_api_get_single_experiment():
    """GET /api/quantum/experiments/exp_bell_phi_plus returns single experiment."""
    resp = client.get("/api/quantum/experiments/exp_bell_phi_plus")
    assert resp.status_code == 200
    data = resp.json()
    assert "Bell State" in data["name"]
    assert len(data["circuit"]) == 2
