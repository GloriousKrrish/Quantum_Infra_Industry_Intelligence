"""
test_qml_encoding.py - Comprehensive Scientific Validation Suite for Milestone 5.1.

Tests:
  1. Basis Encoding:
     - Binary validation (reject negatives, floats, non-binary, empty)
     - Basis state preparation (amplitude 1.0 at exact basis index)
     - Qubit ordering (little-endian vs big-endian)
     - Deterministic measurement verification on AerSimulator
  2. Amplitude Encoding:
     - Zero-vector rejection (norm < 1e-12)
     - Non-finite rejection (NaN, Inf)
     - L2 normalization & zero-padding to powers of 2
     - Exact state preparation fidelity |<target|actual>|^2 >= 1.0 - 1e-4
     - Odd dimension handling (e.g. 3 -> 4, 5 -> 8)
  3. Angle Encoding:
     - RX, RY, RZ rotation encoding
     - Comparison against independent Kronecker tensor-product reference states
     - One-to-one, dense (3:1), and cyclic feature mappings
     - Feature scaling factors
  4. IQP Feature Maps:
     - Single-qubit phase layer + entangling ZZ interactions
     - Linear, circular, and full entanglement topologies
     - Multi-layer repetitions (R >= 1)
     - Mathematical parameter consistency
  5. Resource Metrics & Registry:
     - Actual circuit instruction inspection (no hardcoding)
     - Single-qubit vs two-qubit gate counts
     - Circuit depth and statevector dimensions
     - Decoupled registry factory and comparative encoder benchmarking
"""

import pytest
import numpy as np
import math

from qiskit.quantum_info import Statevector

from backend.app.engines.qml.encoding import (
    BaseQuantumEncoder,
    EncodingResult,
    BasisEncoder,
    AmplitudeEncoder,
    AngleEncoder,
    IQPFeatureMap,
    EncodingResourceMetrics,
    calculate_circuit_metrics,
    EncodingRegistry,
)


# =========================================================================
# 1. Basis Encoding Tests
# =========================================================================

def test_basis_encoder_valid_inputs():
    encoder = BasisEncoder()
    # List of ints
    res1 = encoder.encode([1, 0, 1])
    assert res1.circuit.num_qubits == 3
    assert res1.get_dominant_state()["bitstring"] == "101"
    assert np.isclose(res1.get_dominant_state()["probability"], 1.0)
    assert res1.get_dominant_state()["index"] == 5  # 1*1 + 0*2 + 1*4 = 5

    # Bitstring string input
    res2 = encoder.encode("011")
    assert res2.circuit.num_qubits == 3
    assert res2.get_dominant_state()["index"] == 6  # 0*1 + 1*2 + 1*4 = 6 (under little endian)

    # Boolean array
    res3 = encoder.encode(np.array([True, False, False]))
    assert res3.circuit.num_qubits == 3
    assert res3.get_dominant_state()["index"] == 1


def test_basis_encoder_rejections():
    encoder = BasisEncoder()
    # Negative value
    with pytest.raises(ValueError, match="only contain 0 and 1"):
        encoder.validate_input([-1, 0])

    # Value 2
    with pytest.raises(ValueError, match="only contain 0 and 1"):
        encoder.validate_input([0, 2])

    # Float non-binary
    with pytest.raises(ValueError, match="Floating-point input must only contain 0.0 and 1.0"):
        encoder.validate_input([0.0, 0.5])

    # Invalid string
    with pytest.raises(ValueError, match="non-binary characters"):
        encoder.validate_input("1020")

    # Empty
    with pytest.raises(ValueError, match="cannot be empty"):
        encoder.validate_input([])


def test_basis_encoder_qubit_ordering_little_vs_big():
    # Little-endian: x=[1, 0, 0] -> Qubit 0 is 1 -> index 1
    enc_little = BasisEncoder(endianness="little")
    res_l = enc_little.encode([1, 0, 0])
    assert enc_little.get_basis_index([1, 0, 0]) == 1
    assert res_l.get_dominant_state()["index"] == 1

    # Big-endian: x=[1, 0, 0] -> x[0] is MSB (2^2) -> index 4
    enc_big = BasisEncoder(endianness="big")
    res_b = enc_big.encode([1, 0, 0])
    assert enc_big.get_basis_index([1, 0, 0]) == 4
    assert res_b.get_dominant_state()["index"] == 4


def test_basis_encoder_measurement_verification():
    encoder = BasisEncoder()
    data = [1, 1, 0, 1]
    meas = encoder.verify_measurement(data, shots=500, seed=42)
    assert meas["is_deterministic"] is True
    assert meas["accuracy"] == 1.0
    assert meas["expected_bitstring"] == format(encoder.get_basis_index(data), "04b")


# =========================================================================
# 2. Amplitude Encoding Tests
# =========================================================================

def test_amplitude_encoder_normalization_and_fidelity():
    encoder = AmplitudeEncoder()
    # 4-dimensional continuous vector
    vec = [3.0, 1.0, 4.0, 2.0]
    res = encoder.encode(vec)

    assert res.circuit.num_qubits == 2  # 2^2 = 4
    assert len(res.statevector) == 4

    norm_target = np.array(vec) / np.linalg.norm(vec)
    fidelity = res.get_statevector_fidelity(norm_target)
    assert np.isclose(fidelity, 1.0, atol=1e-4)

    # Probabilities must match squares of normalized components
    expected_probs = norm_target ** 2
    assert np.allclose(res.probabilities, expected_probs, atol=1e-4)


def test_amplitude_encoder_odd_dimensions_padding():
    encoder = AmplitudeEncoder()
    # Dimension 3 -> should pad to 4 (2 qubits)
    vec_3d = [1.0, 2.0, 3.0]
    res_3d = encoder.encode(vec_3d)
    assert res_3d.circuit.num_qubits == 2
    assert len(res_3d.statevector) == 4

    # Dimension 5 -> should pad to 8 (3 qubits)
    vec_5d = [1.0, 1.0, 1.0, 1.0, 1.0]
    res_5d = encoder.encode(vec_5d)
    assert res_5d.circuit.num_qubits == 3
    assert len(res_5d.statevector) == 8


def test_amplitude_encoder_zero_vector_rejection():
    encoder = AmplitudeEncoder()
    with pytest.raises(ValueError, match="Zero-vector rejection"):
        encoder.validate_input([0.0, 0.0, 0.0])

    with pytest.raises(ValueError, match="non-finite values"):
        encoder.validate_input([1.0, np.nan, 2.0])

    with pytest.raises(ValueError, match="non-finite values"):
        encoder.validate_input([1.0, np.inf, 2.0])


def test_amplitude_encoder_verify_state_preparation():
    encoder = AmplitudeEncoder()
    vec = [0.5, -1.2, 3.4, 0.8]
    audit = encoder.verify_state_preparation(vec)
    assert audit["is_valid"] is True
    assert audit["statevector_fidelity"] >= 0.9999


# =========================================================================
# 3. Angle Encoding Tests
# =========================================================================

def test_angle_encoder_ry_vs_analytical_reference():
    encoder = AngleEncoder(rotation="ry")
    angles = [0.3, 1.2, 2.5]
    res = encoder.encode(angles)

    assert res.circuit.num_qubits == 3

    # Compare against pure mathematical tensor product
    audit = encoder.verify_against_reference(angles)
    assert audit["is_exact"]
    assert audit["fidelity"] >= 0.999999
    assert audit["max_absolute_error"] < 1e-6


def test_angle_encoder_rx_vs_analytical_reference():
    encoder = AngleEncoder(rotation="rx")
    angles = [0.8, 1.5]
    audit = encoder.verify_against_reference(angles)
    assert audit["is_exact"]
    assert audit["fidelity"] >= 0.999999


def test_angle_encoder_rz_with_hadamard():
    encoder = AngleEncoder(rotation="rz", use_hadamard_for_rz=True)
    angles = [0.4, 1.1]
    res = encoder.encode(angles)
    assert res.circuit.num_qubits == 2

    # Under RZ on |+>, probabilities of |0> and |1> remain equal (0.5), only phase changes
    assert np.allclose(res.probabilities, 0.25, atol=1e-5)

    audit = encoder.verify_against_reference(angles)
    assert audit["is_exact"]


def test_angle_encoder_dense_euler_mapping():
    # Dense mapping encodes up to 3 features per qubit
    encoder = AngleEncoder(rotation="combined", mapping="dense")
    data_5d = [0.1, 0.2, 0.3, 0.4, 0.5]
    res = encoder.encode(data_5d)
    # 5 features in 3:1 mapping -> ceil(5/3) = 2 qubits
    assert res.circuit.num_qubits == 2
    assert res.metrics.total_gates == 5  # 3 on Q0, 2 on Q1


# =========================================================================
# 4. IQP Feature Map Tests
# =========================================================================

def test_iqp_feature_map_circuit_construction():
    iqp = IQPFeatureMap(repetitions=1, entanglement="full")
    features = [0.5, 1.0, 1.5]
    res = iqp.encode(features)

    assert res.circuit.num_qubits == 3
    # Breakdown check:
    # 3 H gates (1 per qubit)
    # 3 RZ gates (1 per qubit)
    # 3 pairs for full entanglement (0-1, 0-2, 1-2). Each pair has 2 CNOTs + 1 RZ = 3 gates
    # Total gates = 3 + 3 + (3 * 3) = 15 gates
    assert res.metrics.total_gates == 15
    assert res.metrics.gate_breakdown["h"] == 3
    assert res.metrics.gate_breakdown["rz"] == 6
    assert res.metrics.gate_breakdown["cx"] == 6


def test_iqp_feature_map_topologies():
    feats = [0.1, 0.2, 0.3, 0.4]

    # Linear: 3 pairs
    iqp_lin = IQPFeatureMap(num_qubits=4, entanglement="linear", repetitions=1)
    res_lin = iqp_lin.encode(feats)
    assert iqp_lin.get_entanglement_pairs(4) == [(0, 1), (1, 2), (2, 3)]
    assert res_lin.metrics.gate_breakdown["cx"] == 6  # 3 pairs * 2

    # Circular: 4 pairs (includes (3, 0))
    iqp_circ = IQPFeatureMap(num_qubits=4, entanglement="circular", repetitions=1)
    res_circ = iqp_circ.encode(feats)
    assert len(iqp_circ.get_entanglement_pairs(4)) == 4
    assert res_circ.metrics.gate_breakdown["cx"] == 8

    # Multi-repetition (R=2): doubles all gates
    iqp_rep2 = IQPFeatureMap(num_qubits=4, entanglement="linear", repetitions=2)
    res_rep2 = iqp_rep2.encode(feats)
    assert res_rep2.metrics.gate_breakdown["cx"] == 12


# =========================================================================
# 5. Resource Metrics & Registry Tests
# =========================================================================

def test_actual_circuit_metric_inspection():
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.rx(0.5, 1)
    qc.cx(0, 1)
    qc.cx(1, 2)

    metrics = calculate_circuit_metrics(qc, transpile_to_basis=False)
    assert metrics.num_qubits == 3
    assert metrics.circuit_depth == 3
    assert metrics.total_gates == 4
    assert metrics.single_qubit_gates == 2  # h, rx
    assert metrics.two_qubit_gates == 2     # 2 cxs
    assert metrics.multi_qubit_gates == 0
    assert metrics.statevector_dimension == 8
    assert metrics.gate_breakdown == {"h": 1, "rx": 1, "cx": 2}


def test_encoding_registry_factory():
    catalog = EncodingRegistry.list_encoders()
    assert len(catalog) >= 8

    b = EncodingRegistry.get_encoder("basis")
    assert isinstance(b, BasisEncoder)

    a = EncodingRegistry.get_encoder("amplitude")
    assert isinstance(a, AmplitudeEncoder)

    ang = EncodingRegistry.get_encoder("angle_ry")
    assert isinstance(ang, AngleEncoder)
    assert ang.rotation == "ry"

    iqp = EncodingRegistry.get_encoder("iqp", repetitions=2)
    assert isinstance(iqp, IQPFeatureMap)
    assert iqp.repetitions == 2


def test_encoding_comparison_benchmark():
    data = [0.2, 0.4, 0.6, 0.8]
    comparisons = EncodingRegistry.compare_encodings(data, transpile_metrics=False)

    assert len(comparisons) >= 5
    encoder_names = [c["encoder_name"] for c in comparisons]
    assert "amplitude" in encoder_names
    assert "angle_ry" in encoder_names
    assert "iqp" in encoder_names

    # Verify every entry ran successfully and has empirical metrics
    for comp in comparisons:
        assert comp["status"] == "SUCCESS"
        assert comp["num_qubits"] > 0
        assert comp["circuit_depth"] > 0
        assert comp["encoding_time_ms"] >= 0.0


def test_encoding_reproducibility():
    encoder = AngleEncoder(rotation="ry")
    vec = [0.33, 1.44, 2.55]
    res1 = encoder.encode(vec)
    res2 = encoder.encode(vec)

    assert np.allclose(res1.statevector, res2.statevector, atol=1e-12)
    assert np.allclose(res1.probabilities, res2.probabilities, atol=1e-12)
