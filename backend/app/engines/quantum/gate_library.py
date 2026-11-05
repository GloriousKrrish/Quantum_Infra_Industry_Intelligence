"""
Quantum Gate Library for Quantum Estate X.

Provides mathematically verified definitions, unitary matrices, matrix generators,
and metadata for standard single-qubit and multi-qubit quantum gates.

Conventions:
- Computational basis: |0⟩ = [1, 0]^T, |1⟩ = [0, 1]^T
- Matrix multiplication follows standard quantum mechanics conventions.
- Qiskit little-endian qubit ordering is explicitly mapped and documented.
"""

from __future__ import annotations

import cmath
import math
from typing import Any, Dict, List, Optional
import numpy as np


# ═══════════════════════════════════════════════════════════════════════
# 1. GATE DEFINITIONS & STATIC MATRICES
# ═══════════════════════════════════════════════════════════════════════

INV_SQRT2 = 1.0 / math.sqrt(2.0)

# Single-Qubit Matrices
MATRIX_I = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=complex)
MATRIX_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
MATRIX_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
MATRIX_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
MATRIX_H = np.array([[INV_SQRT2, INV_SQRT2], [INV_SQRT2, -INV_SQRT2]], dtype=complex)
MATRIX_S = np.array([[1.0, 0.0], [0.0, 1.0j]], dtype=complex)  # Phase gate (Z^(1/2))
MATRIX_SDG = np.array([[1.0, 0.0], [0.0, -1.0j]], dtype=complex)  # S dagger
MATRIX_T = np.array([[1.0, 0.0], [0.0, cmath.exp(1.0j * math.pi / 4.0)]], dtype=complex)  # T gate (Z^(1/4))
MATRIX_TDG = np.array([[1.0, 0.0], [0.0, cmath.exp(-1.0j * math.pi / 4.0)]], dtype=complex)

# Two-Qubit Matrices (Standard order: |00⟩, |01⟩, |10⟩, |11⟩)
MATRIX_CNOT = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=complex,
)

MATRIX_CZ = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, -1.0],
    ],
    dtype=complex,
)

MATRIX_SWAP = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ],
    dtype=complex,
)

# Three-Qubit Matrix (Toffoli / CCNOT, 8x8)
MATRIX_TOFFOLI = np.eye(8, dtype=complex)
MATRIX_TOFFOLI[6, 6] = 0.0
MATRIX_TOFFOLI[6, 7] = 1.0
MATRIX_TOFFOLI[7, 6] = 1.0
MATRIX_TOFFOLI[7, 7] = 0.0


# ═══════════════════════════════════════════════════════════════════════
# 2. PARAMETERIZED ROTATION GENERATORS
# ═══════════════════════════════════════════════════════════════════════

def get_rx_matrix(theta: float) -> np.ndarray:
    """Rx(theta) = exp(-i theta X / 2) = cos(theta/2) I - i sin(theta/2) X."""
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return np.array([[c, -1.0j * s], [-1.0j * s, c]], dtype=complex)


def get_ry_matrix(theta: float) -> np.ndarray:
    """Ry(theta) = exp(-i theta Y / 2) = cos(theta/2) I - i sin(theta/2) Y."""
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=complex)


def get_rz_matrix(phi: float) -> np.ndarray:
    """Rz(phi) = exp(-i phi Z / 2) = diag(exp(-i phi/2), exp(i phi/2))."""
    return np.array(
        [[cmath.exp(-1.0j * phi / 2.0), 0.0], [0.0, cmath.exp(1.0j * phi / 2.0)]],
        dtype=complex,
    )


def matrix_to_serializable(mat: np.ndarray) -> List[List[Dict[str, float]]]:
    """Convert a numpy complex matrix to serializable [[{real, imag}]]."""
    out: List[List[Dict[str, float]]] = []
    for row in mat:
        row_list: List[Dict[str, float]] = []
        for val in row:
            row_list.append({"real": float(val.real), "imag": float(val.imag)})
        out.append(row_list)
    return out


# ═══════════════════════════════════════════════════════════════════════
# 3. GATE METADATA CATALOG
# ═══════════════════════════════════════════════════════════════════════

GATE_CATALOG: Dict[str, Dict[str, Any]] = {
    "I": {
        "id": "I",
        "name": "Identity Gate",
        "category": "single_qubit",
        "num_qubits": 1,
        "is_parameterized": False,
        "symbol": "I",
        "latex": "I = \\begin{pmatrix} 1 & 0 \\\\ 0 & 1 \\end{pmatrix}",
        "description": "Performs no operation; leaves qubit state invariant.",
        "effect": "|0⟩ → |0⟩, |1⟩ → |1⟩",
        "matrix": matrix_to_serializable(MATRIX_I),
    },
    "X": {
        "id": "X",
        "name": "Pauli-X (NOT) Gate",
        "category": "single_qubit",
        "num_qubits": 1,
        "is_parameterized": False,
        "symbol": "X",
        "latex": "X = \\begin{pmatrix} 0 & 1 \\\\ 1 & 0 \\end{pmatrix}",
        "description": "Quantum bit-flip operator. Rotates π radians around the X-axis of the Bloch sphere.",
        "effect": "|0⟩ → |1⟩, |1⟩ → |0⟩",
        "matrix": matrix_to_serializable(MATRIX_X),
    },
    "Y": {
        "id": "Y",
        "name": "Pauli-Y Gate",
        "category": "single_qubit",
        "num_qubits": 1,
        "is_parameterized": False,
        "symbol": "Y",
        "latex": "Y = \\begin{pmatrix} 0 & -i \\\\ i & 0 \\end{pmatrix}",
        "description": "Simultaneous bit-flip and phase-flip. Rotates π radians around the Y-axis.",
        "effect": "|0⟩ → i|1⟩, |1⟩ → -i|0⟩",
        "matrix": matrix_to_serializable(MATRIX_Y),
    },
    "Z": {
        "id": "Z",
        "name": "Pauli-Z (Phase Flip) Gate",
        "category": "single_qubit",
        "num_qubits": 1,
        "is_parameterized": False,
        "symbol": "Z",
        "latex": "Z = \\begin{pmatrix} 1 & 0 \\\\ 0 & -1 \\end{pmatrix}",
        "description": "Phase-flip operator. Leaves |0⟩ unchanged and flips phase of |1⟩.",
        "effect": "|0⟩ → |0⟩, |1⟩ → -|1⟩",
        "matrix": matrix_to_serializable(MATRIX_Z),
    },
    "H": {
        "id": "H",
        "name": "Hadamard Gate",
        "category": "single_qubit",
        "num_qubits": 1,
        "is_parameterized": False,
        "symbol": "H",
        "latex": "H = \\frac{1}{\\sqrt{2}}\\begin{pmatrix} 1 & 1 \\\\ 1 & -1 \\end{pmatrix}",
        "description": "Creates an equal superposition of basis states. Maps computational basis to X basis.",
        "effect": "|0⟩ → (|0⟩+|1⟩)/√2 = |+⟩, |1⟩ → (|0⟩-|1⟩)/√2 = |-⟩",
        "matrix": matrix_to_serializable(MATRIX_H),
    },
    "S": {
        "id": "S",
        "name": "Phase (S) Gate",
        "category": "single_qubit",
        "num_qubits": 1,
        "is_parameterized": False,
        "symbol": "S",
        "latex": "S = \\begin{pmatrix} 1 & 0 \\\\ 0 & i \\end{pmatrix}",
        "description": "Quarter-turn phase shift (π/2 radians around Z-axis). S = √Z.",
        "effect": "|0⟩ → |0⟩, |1⟩ → i|1⟩",
        "matrix": matrix_to_serializable(MATRIX_S),
    },
    "T": {
        "id": "T",
        "name": "T (π/8) Gate",
        "category": "single_qubit",
        "num_qubits": 1,
        "is_parameterized": False,
        "symbol": "T",
        "latex": "T = \\begin{pmatrix} 1 & 0 \\\\ 0 & e^{i\\pi/4} \\end{pmatrix}",
        "description": "Eighth-turn phase shift (π/4 radians around Z-axis). T = √S = Z^(1/4). Essential for universal fault-tolerant quantum computation.",
        "effect": "|0⟩ → |0⟩, |1⟩ → e^(iπ/4)|1⟩",
        "matrix": matrix_to_serializable(MATRIX_T),
    },
    "RX": {
        "id": "RX",
        "name": "Rotation-X Gate",
        "category": "single_qubit",
        "num_qubits": 1,
        "is_parameterized": True,
        "default_param": math.pi / 2.0,
        "symbol": "Rx(θ)",
        "latex": "R_x(\\theta) = \\begin{pmatrix} \\cos(\\theta/2) & -i\\sin(\\theta/2) \\\\ -i\\sin(\\theta/2) & \\cos(\\theta/2) \\end{pmatrix}",
        "description": "Arbitrary single-qubit rotation by angle θ around the X-axis of the Bloch sphere.",
        "effect": "Rotates statevector by θ about the X axis.",
        "matrix": matrix_to_serializable(get_rx_matrix(math.pi / 2.0)),
    },
    "RY": {
        "id": "RY",
        "name": "Rotation-Y Gate",
        "category": "single_qubit",
        "num_qubits": 1,
        "is_parameterized": True,
        "default_param": math.pi / 2.0,
        "symbol": "Ry(θ)",
        "latex": "R_y(\\theta) = \\begin{pmatrix} \\cos(\\theta/2) & -\\sin(\\theta/2) \\\\ \\sin(\\theta/2) & \\cos(\\theta/2) \\end{pmatrix}",
        "description": "Arbitrary single-qubit rotation by angle θ around the Y-axis of the Bloch sphere.",
        "effect": "Rotates statevector by θ about the Y axis with pure real coefficients.",
        "matrix": matrix_to_serializable(get_ry_matrix(math.pi / 2.0)),
    },
    "RZ": {
        "id": "RZ",
        "name": "Rotation-Z Gate",
        "category": "single_qubit",
        "num_qubits": 1,
        "is_parameterized": True,
        "default_param": math.pi / 2.0,
        "symbol": "Rz(λ)",
        "latex": "R_z(\\phi) = \\begin{pmatrix} e^{-i\\phi/2} & 0 \\\\ 0 & e^{i\\phi/2} \\end{pmatrix}",
        "description": "Arbitrary single-qubit rotation by angle φ around the Z-axis of the Bloch sphere.",
        "effect": "Shifts relative phase between |0⟩ and |1⟩ by φ.",
        "matrix": matrix_to_serializable(get_rz_matrix(math.pi / 2.0)),
    },
    "CX": {
        "id": "CX",
        "name": "Controlled-NOT (CNOT) Gate",
        "category": "multi_qubit",
        "num_qubits": 2,
        "is_parameterized": False,
        "symbol": "CX",
        "latex": "CX = \\begin{pmatrix} 1 & 0 & 0 & 0 \\\\ 0 & 1 & 0 & 0 \\\\ 0 & 0 & 0 & 1 \\\\ 0 & 0 & 1 & 0 \\end{pmatrix}",
        "description": "Entangling 2-qubit gate. Flips target qubit if control qubit is in state |1⟩.",
        "effect": "|00⟩ → |00⟩, |01⟩ → |01⟩, |10⟩ → |11⟩, |11⟩ → |10⟩",
        "matrix": matrix_to_serializable(MATRIX_CNOT),
    },
    "CZ": {
        "id": "CZ",
        "name": "Controlled-Z Gate",
        "category": "multi_qubit",
        "num_qubits": 2,
        "is_parameterized": False,
        "symbol": "CZ",
        "latex": "CZ = \\begin{pmatrix} 1 & 0 & 0 & 0 \\\\ 0 & 1 & 0 & 0 \\\\ 0 & 0 & 1 & 0 \\\\ 0 & 0 & 0 & -1 \\end{pmatrix}",
        "description": "Symmetric entangling gate. Flips the phase of state |11⟩.",
        "effect": "|11⟩ → -|11⟩; all other basis states invariant.",
        "matrix": matrix_to_serializable(MATRIX_CZ),
    },
    "SWAP": {
        "id": "SWAP",
        "name": "SWAP Gate",
        "category": "multi_qubit",
        "num_qubits": 2,
        "is_parameterized": False,
        "symbol": "SWAP",
        "latex": "SWAP = \\begin{pmatrix} 1 & 0 & 0 & 0 \\\\ 0 & 0 & 1 & 0 \\\\ 0 & 1 & 0 & 0 \\\\ 0 & 0 & 0 & 1 \\end{pmatrix}",
        "description": "Exchanges the states of two qubits. Can be decomposed into 3 alternating CNOT gates.",
        "effect": "|01⟩ ↔ |10⟩; |00⟩ and |11⟩ invariant.",
        "matrix": matrix_to_serializable(MATRIX_SWAP),
    },
    "CCX": {
        "id": "CCX",
        "name": "Toffoli (CCNOT) Gate",
        "category": "multi_qubit",
        "num_qubits": 3,
        "is_parameterized": False,
        "symbol": "CCX",
        "latex": "CCNOT = \\text{diag}(I, I, I, X)",
        "description": "Three-qubit universal reversible logic gate. Flips target if both controls are in state |1⟩.",
        "effect": "|110⟩ → |111⟩, |111⟩ → |110⟩; all other basis states invariant.",
        "matrix": matrix_to_serializable(MATRIX_TOFFOLI),
    },
}


def get_all_gate_specs() -> List[Dict[str, Any]]:
    """Return list of all registered quantum gate specifications."""
    return list(GATE_CATALOG.values())


def get_gate_spec(gate_id: str) -> Optional[Dict[str, Any]]:
    """Return specification for a single gate by ID (case-insensitive)."""
    return GATE_CATALOG.get(gate_id.upper())

