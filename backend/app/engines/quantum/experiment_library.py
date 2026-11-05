"""
Pre-Loaded Reproducible Quantum Experiments for Quantum Estate X.

Contains 10 mathematically verified quantum computing experiments covering single-qubit
transformations, phase rotations, quantum wave interference, all 4 Bell states,
3-qubit GHZ state, and the Quantum Teleportation protocol.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


EXPERIMENT_CATALOG: Dict[str, Dict[str, Any]] = {
    "exp_single_qubit_x": {
        "id": "exp_single_qubit_x",
        "name": "Single-Qubit Initialization & Pauli-X Bit Flip",
        "category": "Foundations",
        "num_qubits": 1,
        "objective": "Demonstrate computational basis states |0⟩ and |1⟩ using the Pauli-X operator.",
        "formula": "X|0⟩ = \\begin{pmatrix} 0 & 1 \\\\ 1 & 0 \\end{pmatrix}\\begin{pmatrix} 1 \\\\ 0 \\end{pmatrix} = \\begin{pmatrix} 0 \\\\ 1 \\end{pmatrix} = |1⟩",
        "circuit": [
            {"gate": "X", "targets": [0], "controls": []}
        ],
        "expected_state": "|1⟩ with 100% measurement probability",
        "explanation": (
            "The Pauli-X gate acts as a quantum NOT gate. It flips the ground state |0⟩ into the excited state |1⟩. "
            "On the Bloch sphere, this corresponds to a 180° (π radians) rotation about the X-axis from the north pole to the south pole."
        ),
    },

    "exp_hadamard_superposition": {
        "id": "exp_hadamard_superposition",
        "name": "Hadamard Equal Superposition",
        "category": "Superposition",
        "num_qubits": 1,
        "objective": "Transform a definite computational basis state into an equal quantum superposition |+⟩.",
        "formula": "H|0⟩ = \\frac{1}{\\sqrt{2}}(|0⟩ + |1⟩) = |+⟩, \\quad P(|0⟩) = |\\frac{1}{\\sqrt{2}}|^2 = 0.50",
        "circuit": [
            {"gate": "H", "targets": [0], "controls": []}
        ],
        "expected_state": "|+⟩ = 0.7071|0⟩ + 0.7071|1⟩ (50% / 50% measurement distribution)",
        "explanation": (
            "The Hadamard operator creates an unbiased superposition. Crucially, before measurement, the qubit is NOT 'either 0 or 1'; "
            "it exists simultaneously in both states with equal real probability amplitudes (1/√2). Measurement collapses the state to |0⟩ or |1⟩ with equal probability."
        ),
    },

    "exp_phase_shift_s_t": {
        "id": "exp_phase_shift_s_t",
        "name": "Phase Rotation with S and T Gates",
        "category": "Phase",
        "num_qubits": 1,
        "objective": "Demonstrate relative phase rotation on the Bloch sphere equator without altering measurement probabilities.",
        "formula": "T H |0⟩ = \\frac{1}{\\sqrt{2}}|0⟩ + \\frac{e^{i\\pi/4}}{\\sqrt{2}}|1⟩, \\quad |\\frac{e^{i\\pi/4}}{\\sqrt{2}}|^2 = 0.50",
        "circuit": [
            {"gate": "H", "targets": [0], "controls": []},
            {"gate": "T", "targets": [0], "controls": []},
            {"gate": "S", "targets": [0], "controls": []}
        ],
        "expected_state": "Equal magnitudes (0.7071) with relative phase φ = 3π/4 (135°)",
        "explanation": (
            "Phase gates (S, T, Rz) rotate the statevector around the Z-axis of the Bloch sphere. Notice that applying S and T to |+⟩ "
            "changes the quantum phase from 0 to 3π/4, but the measurement probabilities remain exactly 50% for |0⟩ and 50% for |1⟩. "
            "Quantum phase is invisible to computational basis measurement until converted to amplitude differences via interference."
        ),
    },

    "exp_quantum_interference": {
        "id": "exp_quantum_interference",
        "name": "Quantum Wave Interference (H-Z-H)",
        "category": "Interference",
        "num_qubits": 1,
        "objective": "Demonstrate destructive wave interference collapsing amplitudes back to a deterministic state.",
        "formula": "H Z H |0⟩ = H Z |+⟩ = H |-⟩ = |1⟩",
        "circuit": [
            {"gate": "H", "targets": [0], "controls": []},
            {"gate": "Z", "targets": [0], "controls": []},
            {"gate": "H", "targets": [0], "controls": []}
        ],
        "expected_state": "|1⟩ with 100% probability via destructive interference on |0⟩",
        "explanation": (
            "In step 1, H creates (|0⟩ + |1⟩)/√2. In step 2, Z flips the phase of |1⟩ to obtain |-⟩ = (|0⟩ - |1⟩)/√2. "
            "In step 3, the second H gate recombines the probability amplitudes. The amplitudes for |0⟩ cancel destructively "
            "((1/√2)(1/√2) + (1/√2)(-1/√2) = 0), while amplitudes for |1⟩ add constructively to 1.0! This proves quantum computation operates on complex wave amplitudes, not classical probabilities."
        ),
    },

    "exp_bell_phi_plus": {
        "id": "exp_bell_phi_plus",
        "name": "Bell State |Φ+⟩ (Canonical EPR Pair)",
        "category": "Entanglement",
        "num_qubits": 2,
        "objective": "Prepare maximally entangled Bell pair |Φ+⟩ = (|00⟩ + |11⟩)/√2.",
        "formula": "|\\Phi^+\\rangle = \\text{CNOT}_{0,1}(H_0 \\otimes I_1)|00\\rangle = \\frac{|00\\rangle + |11\\rangle}{\\sqrt{2}}",
        "circuit": [
            {"gate": "H", "targets": [0], "controls": []},
            {"gate": "CX", "targets": [1], "controls": [0]}
        ],
        "expected_state": "Amplitudes on |00⟩ (0.7071) and |11⟩ (0.7071); 0% for |01⟩ and |10⟩",
        "explanation": (
            "|Φ+⟩ is the prototypical entangled Bell state. Measurement on either qubit alone yields 0 or 1 with 50% probability, "
            "meaning the reduced density matrix of each qubit is maximally mixed (Bloch vector length = 0). "
            "Yet, whenever qubit 0 is measured as 0, qubit 1 is guaranteed to be 0; whenever qubit 0 is 1, qubit 1 is guaranteed to be 1."
        ),
    },

    "exp_bell_phi_minus": {
        "id": "exp_bell_phi_minus",
        "name": "Bell State |Φ−⟩ (Phase Inverted Bell Pair)",
        "category": "Entanglement",
        "num_qubits": 2,
        "objective": "Prepare Bell state |Φ−⟩ = (|00⟩ − |11⟩)/√2.",
        "formula": "|\\Phi^-\\rangle = \\frac{|00\\rangle - |11\\rangle}{\\sqrt{2}}",
        "circuit": [
            {"gate": "X", "targets": [0], "controls": []},
            {"gate": "H", "targets": [0], "controls": []},
            {"gate": "CX", "targets": [1], "controls": [0]}
        ],
        "expected_state": "+0.7071 on |00⟩ and -0.7071 on |11⟩",
        "explanation": (
            "By starting qubit 0 in state |1⟩ (via X), the Hadamard gate prepares |-⟩ = (|0⟩ - |1⟩)/√2. "
            "Applying CNOT entangles the qubits with a negative relative phase between |00⟩ and |11⟩."
        ),
    },

    "exp_bell_psi_plus": {
        "id": "exp_bell_psi_plus",
        "name": "Bell State |Ψ+⟩ (Anti-Correlated Bell Pair)",
        "category": "Entanglement",
        "num_qubits": 2,
        "objective": "Prepare anti-correlated Bell state |Ψ+⟩ = (|01⟩ + |10⟩)/√2.",
        "formula": "|\\Psi^+\\rangle = \\frac{|01\\rangle + |10\\rangle}{\\sqrt{2}}",
        "circuit": [
            {"gate": "H", "targets": [0], "controls": []},
            {"gate": "X", "targets": [1], "controls": []},
            {"gate": "CX", "targets": [1], "controls": [0]}
        ],
        "expected_state": "+0.7071 on |01⟩ and +0.7071 on |10⟩ (perfect anti-correlation)",
        "explanation": (
            "In |Ψ+⟩, the qubits are perfectly anti-correlated. If qubit 0 is measured as |0⟩, qubit 1 is guaranteed to be |1⟩; "
            "if qubit 0 is |1⟩, qubit 1 is guaranteed to be |0⟩."
        ),
    },

    "exp_bell_psi_minus": {
        "id": "exp_bell_psi_minus",
        "name": "Bell State |Ψ−⟩ (Singlet State)",
        "category": "Entanglement",
        "num_qubits": 2,
        "objective": "Prepare the singlet state |Ψ−⟩ = (|01⟩ − |10⟩)/√2.",
        "formula": "|\\Psi^-\\rangle = \\frac{|01\\rangle - |10\\rangle}{\\sqrt{2}}",
        "circuit": [
            {"gate": "X", "targets": [0], "controls": []},
            {"gate": "H", "targets": [0], "controls": []},
            {"gate": "X", "targets": [1], "controls": []},
            {"gate": "CX", "targets": [1], "controls": [0]}
        ],
        "expected_state": "+0.7071 on |01⟩ and -0.7071 on |10⟩",
        "explanation": (
            "The singlet state |Ψ−⟩ possesses total spin S = 0 and is invariant under arbitrary identical rotations on both qubits. "
            "It is fundamental to tests of Bell's theorem and quantum non-locality."
        ),
    },

    "exp_ghz_state": {
        "id": "exp_ghz_state",
        "name": "3-Qubit Greenberger–Horne–Zeilinger (GHZ) State",
        "category": "Entanglement",
        "num_qubits": 3,
        "objective": "Demonstrate multi-partite macroscopic quantum entanglement across 3 qubits.",
        "formula": "|\\text{GHZ}\\rangle = \\frac{|000\\rangle + |111\\rangle}{\\sqrt{2}}",
        "circuit": [
            {"gate": "H", "targets": [0], "controls": []},
            {"gate": "CX", "targets": [1], "controls": [0]},
            {"gate": "CX", "targets": [2], "controls": [1]}
        ],
        "expected_state": "50% |000⟩ and 50% |111⟩; zero probability for all 6 intermediate states",
        "explanation": (
            "The GHZ state represents non-local multi-particle entanglement. Measuring any single qubit immediately collapses all three qubits "
            "to either |000⟩ or |111⟩. GHZ states are central to quantum error correction codes and multi-party quantum communication."
        ),
    },

    "exp_quantum_teleportation": {
        "id": "exp_quantum_teleportation",
        "name": "Quantum Teleportation Protocol",
        "category": "Algorithms",
        "num_qubits": 3,
        "objective": "Teleport unknown qubit state |ψ⟩ from Alice (q0) to Bob (q2) using an EPR pair (q1, q2) and Bell measurement.",
        "formula": "|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle \\xrightarrow{\\text{teleport}} \\text{Bob's } q_2 = \\alpha|0\\rangle + \\beta|1\\rangle",
        "circuit": [
            # Prepare arbitrary state on qubit 0: Ry(pi/3) -> alpha ~ 0.866, beta ~ 0.500
            {"gate": "RY", "targets": [0], "controls": [], "params": {"theta": math.pi / 3.0}},
            # Create shared Bell pair between q1 (Alice) and q2 (Bob)
            {"gate": "H", "targets": [1], "controls": []},
            {"gate": "CX", "targets": [2], "controls": [1]},
            # Alice performs Bell basis change on q0 and q1
            {"gate": "CX", "targets": [1], "controls": [0]},
            {"gate": "H", "targets": [0], "controls": []},
            # Bob applies conditional recovery operations based on measurement outcomes.
            # Under the Principle of Deferred Measurement (Nielsen & Chuang, Sec 4.4),
            # classical feedforward X^(c1) and Z^(c0) is executed as coherent CX(1->2) and CZ(0->2)
            # gates, preserving full statevector coherence while reproducing Bob's exact state.
            {"gate": "CX", "targets": [2], "controls": [1]},
            {"gate": "CZ", "targets": [2], "controls": [0]}
        ],
        "expected_state": "Bob's qubit q2 reproduces the initial state Ry(π/3)|0⟩ with fidelity = 1.0",
        "explanation": (
            "The Quantum Teleportation protocol (Bennett et al. 1993) transmits an unknown quantum state using "
            "an entangled EPR pair and 2 classical bits of information. "
            "Alice couples the unknown state |ψ⟩ (q0) with her EPR half (q1) and performs a Bell measurement. "
            "Under the Principle of Deferred Measurement (Nielsen & Chuang, Theorem 4.4), classical feedforward "
            "(applying Pauli-X if q1=1 and Pauli-Z if q0=1) is executed coherently via CX(1→2) and CZ(0→2) gates. "
            "Tracing out Alice's qubits (q0, q1) proves Bob's reduced density matrix on q2 matches the exact "
            "input state Ry(π/3)|0⟩ with fidelity F = 1.000, purity γ = 1.000, and identical Bloch vector."
        ),
    },
}


def get_all_experiments() -> List[Dict[str, Any]]:
    """Return all pre-loaded experiment templates."""
    return list(EXPERIMENT_CATALOG.values())


def get_experiment_by_id(exp_id: str) -> Optional[Dict[str, Any]]:
    """Return a single experiment template by ID."""
    return EXPERIMENT_CATALOG.get(exp_id)

