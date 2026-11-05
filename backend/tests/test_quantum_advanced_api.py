"""
Integration Test Suite for Phase 03 Advanced Quantum API Endpoints.
Verifies all 11 new REST endpoints via TestClient.
"""

import math
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_api_evolution_simulate():
    """POST /api/quantum/evolution/simulate returns continuous time trajectory."""
    payload = {
        "hamiltonian_type": "pauli_x",
        "initial_state_name": "zero",
        "omega": 1.0,
        "total_time": 3.14159,
        "num_steps": 10,
    }
    resp = client.post("/api/quantum/evolution/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["num_qubits"] == 1
    assert len(data["trajectory"]) == 10
    assert "energy_expectation" in data


def test_api_density_analyze():
    """POST /api/quantum/density/analyze validates and inspects matrix."""
    payload = {"preset": "bell_phi_plus"}
    resp = client.post("/api/quantum/density/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["dimension"] == 4
    assert data["classification"] == "PURE"
    assert math.isclose(data["purity"], 1.0, abs_tol=1e-4)


def test_api_density_analyze_invalid_rejected():
    """Non-Hermitian matrix returns HTTP 422."""
    payload = {
        "matrix_data": [
            [{"real": 1.0, "imag": 0.0}, {"real": 1.0, "imag": 1.0}],
            [{"real": 0.0, "imag": 0.0}, {"real": 0.0, "imag": 0.0}],
        ]
    }
    resp = client.post("/api/quantum/density/analyze", json=payload)
    assert resp.status_code == 422


def test_api_measurement_execute():
    """POST /api/quantum/measurement/execute executes basis measurement."""
    payload = {
        "num_qubits": 1,
        "operations": [{"gate": "H", "targets": [0]}],
        "basis": "X",
        "shots": 500,
    }
    resp = client.post("/api/quantum/measurement/execute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["basis"] == "X"
    assert len(data["theoretical_outcomes"]) == 2


def test_api_interference_simulate():
    """POST /api/quantum/interference/simulate returns fringe curve."""
    payload = {
        "phase_theta": 0.0,
        "shots": 500,
        "include_sweep": True,
        "sweep_steps": 15,
    }
    resp = client.post("/api/quantum/interference/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["interference_regime"] == "CONSTRUCTIVE"
    assert len(data["sweep_curve"]) == 15


def test_api_information_analyze():
    """POST /api/quantum/information/analyze calculates Von Neumann entropy and fidelity."""
    payload = {
        "state_a_preset": "pure_zero",
        "state_b_preset": "pure_plus",
    }
    resp = client.post("/api/quantum/information/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "squared_fidelity_F" in data["relational_metrics"]
    assert data["relational_metrics"]["fuchs_van_de_graaf_bounds"]["is_satisfied"] is True


def test_api_entanglement_analyze():
    """POST /api/quantum/entanglement/analyze returns concurrence and PPT negativity."""
    payload = {"preset": "bell_phi_plus"}
    resp = client.post("/api/quantum/entanglement/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert math.isclose(data["concurrence"], 1.0, abs_tol=1e-4)
    assert data["entanglement_classification"] == "ENTANGLED"


def test_api_noise_simulate():
    """POST /api/quantum/noise/simulate compares ideal and noisy circuit."""
    payload = {
        "num_qubits": 1,
        "operations": [{"gate": "X", "targets": [0]}],
        "noise_type": "amplitude_damping",
        "gamma": 0.2,
        "shots": 1000,
    }
    resp = client.post("/api/quantum/noise/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["noise_type"] == "amplitude_damping"
    assert len(data["distribution_comparison"]) == 2


def test_api_decoherence_simulate():
    """POST /api/quantum/decoherence/simulate calculates Bloch vector decay."""
    payload = {
        "initial_state_name": "plus",
        "t1_us": 40.0,
        "t2_us": 25.0,
        "total_time_us": 50.0,
        "num_steps": 10,
    }
    resp = client.post("/api/quantum/decoherence/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["physical_constraint_satisfied"] is True
    assert len(data["trajectory"]) == 10


def test_api_error_correction_execute():
    """POST /api/quantum/error-correction/execute corrects single bit-flip."""
    payload = {
        "code_type": "bit_flip",
        "error_qubit": 2,
        "shots": 1000,
    }
    resp = client.post("/api/quantum/error-correction/execute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_corrected"] is True
    assert data["expected_syndrome"] == "10"


def test_api_channel_apply():
    """POST /api/quantum/channel/apply verifies CPTP trace preservation."""
    payload = {
        "channel_type": "depolarizing",
        "input_state_preset": "pure_plus",
        "param_p": 0.2,
    }
    resp = client.post("/api/quantum/channel/apply", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_trace_preserving"] is True
    assert data["output_purity"] < data["input_purity"]


def test_api_tomography_reconstruct():
    """POST /api/quantum/tomography/reconstruct performs state tomography."""
    payload = {
        "operations": [{"gate": "H", "targets": [0]}, {"gate": "S", "targets": [0]}],
        "shots": 2000,
    }
    resp = client.post("/api/quantum/tomography/reconstruct", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["fidelity_reconstructed"] > 0.95
    assert "pauli_measurements" in data
