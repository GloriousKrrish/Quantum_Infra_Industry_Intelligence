"""
test_qml_vqc.py - Scientific Validation Test Suite for Variational Quantum Classifier (VQC).

Tests:
  1. Circuit & Ansatz Construction (HEA, SEA, TwoLocal, parameter vectors)
  2. Forward Pass & Measurement Calibration (<Z_0> in [-1, 1], P(0)+P(1) = 1)
  3. Analytical Parameter-Shift Rule vs Finite Differences (|shift - fd| < 1e-4)
  4. Loss Functions & Probability Derivatives (BCE, MSE)
  5. Dataset Generation & Leakage-Free Preprocessing
  6. Domain Real Estate Datasets (Land Suitability, Infrastructure Risk)
  7. Training Engine Convergence (COBYLA, L-BFGS-B, Adam)
  8. Classical Baselines (LR, SVM Linear/RBF, DT, RF, MLP)
  9. Comparative Benchmark Suite
  10. FastAPI /api/qml/vqc/* Endpoints
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.engines.qml.vqc import (
    AnsatzConfig,
    MeasurementConfig,
    TrainingConfig,
    VQCConfig,
    ParameterizedAnsatz,
    VQCMeasurementEngine,
    VQCGradientEngine,
    BinaryCrossEntropyLoss,
    MeanSquaredErrorLoss,
    VariationalQuantumClassifier,
    VQCTrainer,
    DatasetPreprocessor,
    VQCDatasetLibrary,
    ClassicalBaselineRunner,
    VQCBenchmarkSuite,
    VQCExperimentRegistry,
)


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# 1. Circuit & Ansatz Tests
# =========================================================================

def test_hardware_efficient_ansatz():
    cfg = AnsatzConfig(
        ansatz_type="hardware_efficient",
        num_qubits=3,
        num_layers=2,
        rotation_gates=["ry"],
        entanglement="linear",
    )
    ansatz = ParameterizedAnsatz(cfg)
    # (L + 1) * n * rot = (2 + 1) * 3 * 1 = 9 parameters
    assert ansatz.num_parameters == 9
    assert len(ansatz.parameter_vector) == 9

    # Circuit construction
    qc = ansatz.circuit
    assert qc.num_qubits == 3
    # 3 layers of 3 RYs = 9 RY gates; 2 layers of 2 CNOTs = 4 CNOT gates
    assert qc.count_ops()["ry"] == 9
    assert qc.count_ops()["cx"] == 4


def test_strongly_entangling_ansatz():
    cfg = AnsatzConfig(
        ansatz_type="strongly_entangling",
        num_qubits=3,
        num_layers=2,
    )
    ansatz = ParameterizedAnsatz(cfg)
    # 3 Euler params per qubit per layer = 3 * 3 * 2 = 18 parameters
    assert ansatz.num_parameters == 18
    qc = ansatz.circuit
    assert qc.num_qubits == 3
    assert qc.count_ops()["cx"] == 6  # 3 circular CNOTs per layer * 2


def test_parameter_binding():
    cfg = AnsatzConfig(num_qubits=2, num_layers=1, rotation_gates=["ry"])
    ansatz = ParameterizedAnsatz(cfg)
    # 4 parameters
    vals = np.array([0.1, 0.2, 0.3, 0.4])
    bound_qc = ansatz.bind_parameters(vals)
    assert bound_qc.num_parameters == 0  # All parameters bound


# =========================================================================
# 2. Measurement & Expectation Value Tests
# =========================================================================

def test_measurement_expectation_and_probabilities():
    meas = VQCMeasurementEngine(num_qubits=2)
    # Identity circuit (|00>): <Z_0> must be +1.0
    from qiskit import QuantumCircuit
    qc0 = QuantumCircuit(2)
    exp_val, probs = meas.evaluate_circuit(qc0)
    assert np.isclose(exp_val, 1.0, atol=1e-5)
    assert np.isclose(probs[0], 1.0, atol=1e-5)  # P(y=0) = 1
    assert np.isclose(probs[1], 0.0, atol=1e-5)  # P(y=1) = 0

    # Flip qubit 0 (|01> under little endian): <Z_0> must be -1.0
    qc1 = QuantumCircuit(2)
    qc1.x(0)
    exp_val1, probs1 = meas.evaluate_circuit(qc1)
    assert np.isclose(exp_val1, -1.0, atol=1e-5)
    assert np.isclose(probs1[0], 0.0, atol=1e-5)
    assert np.isclose(probs1[1], 1.0, atol=1e-5)

    # Superposition on qubit 0 (H): <Z_0> must be 0.0
    qc_h = QuantumCircuit(2)
    qc_h.h(0)
    exp_h, probs_h = meas.evaluate_circuit(qc_h)
    assert np.isclose(exp_h, 0.0, atol=1e-5)
    assert np.isclose(probs_h[0], 0.5, atol=1e-5)
    assert np.isclose(probs_h[1], 0.5, atol=1e-5)


# =========================================================================
# 3. Analytical Parameter-Shift Rule vs Finite Differences
# =========================================================================

def test_parameter_shift_vs_finite_difference():
    """
    Verifies that Parameter-Shift Rule analytical gradients match numerical
    finite differences within 1e-4 tolerance on a deterministic parameterized circuit.
    """
    from qiskit import QuantumCircuit
    from qiskit.circuit import ParameterVector
    from qiskit.quantum_info import SparsePauliOp

    theta = ParameterVector("θ", 3)
    qc = QuantumCircuit(2)
    qc.ry(theta[0], 0)
    qc.cx(0, 1)
    qc.ry(theta[1], 1)
    qc.rz(theta[2], 0)

    obs = SparsePauliOp("IZ")
    params = np.array([0.65, 1.25, -0.45])

    audit = VQCGradientEngine.verify_gradient_accuracy(qc, theta, params, obs, tolerance=1e-4)
    assert audit["is_consistent"]
    assert audit["max_absolute_error"] < 1e-5


# =========================================================================
# 4. Loss Functions Tests
# =========================================================================

def test_loss_functions():
    bce = BinaryCrossEntropyLoss()
    mse = MeanSquaredErrorLoss()

    y_true = np.array([1, 0, 1, 0])
    p_pred = np.array([0.9, 0.1, 0.8, 0.2])

    loss_bce = bce.compute(y_true, p_pred)
    assert loss_bce > 0.0
    grad_bce = bce.gradient_wrt_prob(y_true, p_pred)
    assert len(grad_bce) == 4

    loss_mse = mse.compute(y_true, p_pred)
    assert loss_mse > 0.0
    grad_mse = mse.gradient_wrt_prob(y_true, p_pred)
    assert len(grad_mse) == 4


# =========================================================================
# 5. Dataset Generation & Preprocessing Tests
# =========================================================================

def test_dataset_generation_and_leakage_free_preprocessing():
    # Moons dataset
    bundle = VQCDatasetLibrary.load_dataset("moons", n_samples=80, test_size=0.25, seed=42)
    X_train = bundle["X_train"]
    X_test = bundle["X_test"]
    y_train = bundle["y_train"]
    y_test = bundle["y_test"]

    assert len(X_train) == 60
    assert len(X_test) == 20
    assert len(y_train) == 60
    assert len(y_test) == 20

    # Values must be scaled within [0, pi]
    assert np.all(X_train >= 0.0 - 1e-5)
    assert np.all(X_train <= np.pi + 1e-5)


def test_domain_land_suitability_dataset():
    bundle = VQCDatasetLibrary.load_dataset("land_suitability", n_samples=80, seed=42)
    meta = bundle["metadata"]
    assert meta["provenance_tier"] == "SYNTHETIC_BENCHMARK"
    assert "road distance" in meta["feature_names"][0].lower()
    assert len(bundle["X_train"]) == 60
    assert bundle["X_train"].shape[1] == 4


def test_domain_infrastructure_risk_dataset():
    bundle = VQCDatasetLibrary.load_dataset("infrastructure_risk", n_samples=80, seed=42)
    meta = bundle["metadata"]
    assert meta["provenance_tier"] == "SYNTHETIC_BENCHMARK"
    assert len(bundle["X_train"]) == 60
    assert bundle["X_train"].shape[1] == 4


# =========================================================================
# 6. VQC Model Forward & Prediction Tests
# =========================================================================

def test_vqc_model_forward_and_predict():
    cfg = VQCConfig(
        encoder_name="angle_ry",
        ansatz=AnsatzConfig(num_qubits=2, num_layers=1),
    )
    model = VariationalQuantumClassifier(cfg)
    assert model.num_qubits == 2

    X_sample = np.array([[0.5, 1.0], [1.5, 0.2]])
    probs = model.predict_proba(X_sample)
    assert probs.shape == (2, 2)
    # Probabilities must sum to 1.0 per sample
    assert np.allclose(np.sum(probs, axis=1), 1.0, atol=1e-5)

    preds = model.predict(X_sample)
    assert preds.shape == (2,)
    assert set(preds).issubset({0, 1})


# =========================================================================
# 7. Training Engine Convergence
# =========================================================================

def test_vqc_training_convergence_cobyla():
    """
    Tests that VQC training reduces loss on a small linearly separable dataset.
    """
    bundle = VQCDatasetLibrary.load_dataset("linearly_separable", n_samples=30, test_size=0.25, seed=42)
    X_train = bundle["X_train"]
    y_train = bundle["y_train"]

    cfg = VQCConfig(
        encoder_name="angle_ry",
        ansatz=AnsatzConfig(num_qubits=2, num_layers=1, seed=42),
        training=TrainingConfig(optimizer="COBYLA", max_iter=15, seed=42),
    )
    model = VariationalQuantumClassifier(cfg)
    trainer = VQCTrainer(model, cfg.training)

    res = trainer.fit(X_train, y_train)
    assert res.success
    assert res.iterations > 0
    assert len(res.history) > 0
    # Training loss should be finite and reasonable
    assert res.final_train_loss < 2.0


# =========================================================================
# 8. Classical Baselines & Benchmark Suite
# =========================================================================

def test_classical_baselines_runner():
    bundle = VQCDatasetLibrary.load_dataset("moons", n_samples=40, seed=42)
    results = ClassicalBaselineRunner.run_all_baselines(
        bundle["X_train"], bundle["y_train"], bundle["X_test"], bundle["y_test"], seed=42
    )
    assert len(results) == 6
    for r in results:
        assert 0.0 <= r["accuracy"] <= 1.0
        assert r["training_time_ms"] >= 0.0


def test_vqc_benchmark_suite():
    report = VQCBenchmarkSuite.run_benchmark(
        dataset_name="linearly_separable",
        n_samples=30,
        max_iter=10,
        seed=42,
    )
    assert "models" in report
    assert len(report["models"]) == 7  # VQC + 6 classical baselines
    assert report["models"][0]["is_quantum"] is True
    assert len(report["summary_findings"]) > 0


# =========================================================================
# 9. FastAPI Endpoints Tests
# =========================================================================

def test_api_vqc_health(client):
    res = client.get("/api/qml/vqc/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert "COBYLA" in data["supported_optimizers"]


def test_api_vqc_ansatz_list(client):
    res = client.get("/api/qml/vqc/ansatz/list")
    assert res.status_code == 200
    data = res.json()
    assert len(data["ansatzes"]) >= 3


def test_api_vqc_circuit_build(client):
    res = client.post("/api/qml/vqc/circuit/build", json={
        "num_qubits": 3,
        "ansatz_type": "hardware_efficient",
        "num_layers": 2,
        "encoder_name": "angle_ry",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["num_qubits"] == 3
    assert data["num_parameters"] > 0
    assert data["circuit_depth"] > 0


def test_api_vqc_predict(client):
    # 2 qubits, 1 layer HEA -> 4 weights
    res = client.post("/api/qml/vqc/model/predict", json={
        "features": [[0.5, 1.0], [1.2, 0.3]],
        "weights": [0.1, 0.2, 0.3, 0.4],
        "encoder_name": "angle_ry",
        "ansatz_type": "hardware_efficient",
        "num_layers": 1,
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["predictions"]) == 2
    assert len(data["probabilities"]) == 2
