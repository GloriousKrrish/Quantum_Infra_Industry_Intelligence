"""
Verification Suite for Phase 03 Group C:
- Quantum Noise Models (Depolarizing, Amplitude Damping, Thermal Relaxation)
- Decoherence & Open Quantum Systems (T1, T2, Bloch Trajectory)
- Quantum Channels (Kraus representations, CPTP verification, purity degradation)
"""

import math
import numpy as np
import pytest

from backend.app.engines.quantum.noise_models import (
    build_noise_model,
    simulate_noisy_circuit,
)
from backend.app.engines.quantum.decoherence import (
    simulate_decoherence_trajectory,
)
from backend.app.engines.quantum.quantum_channels import (
    get_channel_kraus_operators,
    apply_quantum_channel,
)


# ═══════════════════════════════════════════════════════════════════════
# 1. NOISE MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_noise_model_depolarizing_tvd():
    """Depolarizing noise increases total variation distance between ideal and noisy execution."""
    ops = [{"gate": "H", "targets": [0]}, {"gate": "CX", "targets": [1], "controls": [0]}]
    res = simulate_noisy_circuit(circuit_ops=ops, num_qubits=2, noise_type="depolarizing", error_prob=0.15, shots=2000)
    assert res["total_variation_distance"] > 0.05
    assert len(res["distribution_comparison"]) == 4


def test_noise_model_amplitude_damping_bias():
    """Amplitude damping decays excited states |1> towards |0>."""
    ops = [{"gate": "X", "targets": [0]}]  # Prepares |1>
    res = simulate_noisy_circuit(circuit_ops=ops, num_qubits=1, noise_type="amplitude_damping", gamma=0.30, shots=2000)
    noisy_0 = next(d["noisy_count"] for d in res["distribution_comparison"] if d["bitstring"] == "0")
    # Without noise, 0 count is 0; with amplitude damping gamma=0.3, ~30% decay to 0
    assert noisy_0 > 200


# ═══════════════════════════════════════════════════════════════════════
# 2. DECOHERENCE TRAJECTORY TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_decoherence_physical_t2_bound():
    """Engine enforces physical constraint T2 <= 2 * T1."""
    res = simulate_decoherence_trajectory(t1_us=20.0, t2_us=100.0)  # Input invalid T2 > 2*T1
    assert res["physical_constraint_satisfied"] is True
    assert res["t2_dephasing_us"] <= 2.0 * res["t1_relaxation_us"]


def test_decoherence_purity_decay_to_ground_state():
    """State |+> dephases: purity initially drops from 1.0, then relaxes to ground state |0> (purity -> 1.0)."""
    res = simulate_decoherence_trajectory(initial_state_name="plus", t1_us=20.0, t2_us=10.0, total_time_us=80.0, num_steps=20)
    traj = res["trajectory"]
    # Initial state |+> at t=0 has purity 1.0, bloch_x = 1.0
    assert math.isclose(traj[0]["purity"], 1.0, abs_tol=1e-3)
    assert math.isclose(traj[0]["bloch_x"], 1.0, abs_tol=1e-3)

    # Late time t >> T1, T2: state relaxes to north pole |0> (bloch_z -> 1.0, bloch_x -> 0)
    final_pt = traj[-1]
    assert math.isclose(final_pt["bloch_x"], 0.0, abs_tol=1e-2)
    assert final_pt["bloch_z"] > 0.95


# ═══════════════════════════════════════════════════════════════════════
# 3. QUANTUM CHANNEL TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_quantum_channel_trace_preservation_completeness():
    """All standard quantum channels satisfy Kraus completeness Σ E_k† E_k = I."""
    for ch in ("identity", "bit_flip", "phase_flip", "depolarizing", "amplitude_damping", "phase_damping"):
        kraus_ops, _ = get_channel_kraus_operators(ch, param_p=0.2, gamma=0.2, lambda_param=0.2)
        completeness = sum(k.conj().T @ k for k in kraus_ops)
        assert np.allclose(completeness, np.eye(2), atol=1e-6), f"Channel {ch} violates trace preservation!"


def test_depolarizing_channel_bloch_shrinkage():
    """Depolarizing channel isotropically shrinks the Bloch vector."""
    res = apply_quantum_channel(channel_type="depolarizing", input_state_preset="pure_plus", param_p=0.4)
    assert res["is_trace_preserving"] is True
    assert res["bloch_out"]["length"] < res["bloch_in"]["length"]
    # Depolarizing shrinks radius to (1 - p) = 0.6
    assert math.isclose(res["bloch_out"]["length"], 0.60, abs_tol=1e-2)
    assert res["fidelity_retained"] < 1.0
