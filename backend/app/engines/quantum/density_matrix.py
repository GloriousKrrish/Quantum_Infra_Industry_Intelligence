"""
Density Matrix Laboratory Engine for Quantum Estate X.

Performs rigorous density operator construction, spectral decomposition,
partial trace operations, and mathematical validation:
- Hermiticity: ρ = ρ†
- Trace normalization: Tr(ρ) = 1.0
- Positive semidefiniteness: λ_i >= 0
- Purity: γ = Tr(ρ²)
- Subsystem partial trace over arbitrary partitions
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import scipy.linalg as la


class DensityMatrixValidationError(ValueError):
    """Raised when a user-supplied matrix fails quantum physical validity."""
    pass


def validate_density_matrix(rho: np.ndarray, tolerance: float = 1e-6) -> Dict[str, Any]:
    """
    Validate that a square matrix is a legitimate physical quantum density operator.
    Checks:
    1. Square dimension d x d
    2. Hermiticity: ||rho - rho^dagger||_inf < tol
    3. Unit trace: |Tr(rho) - 1.0| < tol
    4. Positive semidefiniteness: all eigenvalues >= -tol
    """
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise DensityMatrixValidationError(f"Matrix must be square 2D array, got shape {rho.shape}")

    d = rho.shape[0]

    # 1. Hermiticity
    hermitian_diff = np.max(np.abs(rho - rho.conj().T))
    is_hermitian = bool(hermitian_diff < tolerance)
    if not is_hermitian:
        raise DensityMatrixValidationError(
            f"Matrix is not Hermitian (max deviation {hermitian_diff:.2e} > {tolerance:.2e})"
        )

    # 2. Trace normalization
    tr = float(np.trace(rho).real)
    is_trace_one = bool(abs(tr - 1.0) < tolerance)
    if not is_trace_one:
        raise DensityMatrixValidationError(
            f"Matrix trace must equal 1.0, got Tr(ρ) = {tr:.6f}"
        )

    # 3. Eigenvalues & Positive Semidefiniteness
    # For Hermitian matrices, use eigh
    eigvals, eigvecs = la.eigh(rho)
    min_eig = float(np.min(eigvals))
    is_positive_semidefinite = bool(min_eig >= -tolerance)
    if not is_positive_semidefinite:
        raise DensityMatrixValidationError(
            f"Matrix has negative eigenvalue {min_eig:.6f}; violates positive semidefiniteness."
        )

    # Clean small numerical noise in eigenvalues
    clean_eigs = [max(0.0, float(ev)) for ev in sorted(eigvals, reverse=True)]
    sum_eigs = sum(clean_eigs)
    if sum_eigs > 0:
        clean_eigs = [ev / sum_eigs for ev in clean_eigs]

    return {
        "dimension": d,
        "is_hermitian": is_hermitian,
        "trace": round(tr, 6),
        "min_eigenvalue": round(min_eig, 6),
        "is_positive_semidefinite": is_positive_semidefinite,
        "eigenvalues": [round(ev, 6) for ev in clean_eigs],
        "rank": int(sum(1 for ev in clean_eigs if ev > 1e-5)),
    }


def compute_purity(rho: np.ndarray) -> float:
    """Calculate state purity: γ = Tr(ρ²)."""
    purity = float(np.trace(rho @ rho).real)
    return max(0.0, min(1.0, purity))


def partial_trace_2qubit(rho_ab: np.ndarray, trace_out: str = "B") -> np.ndarray:
    """
    Compute partial trace of a 4x4 2-qubit density matrix.
    trace_out='B' traces out qubit 1, returning 2x2 rho_A.
    trace_out='A' traces out qubit 0, returning 2x2 rho_B.
    """
    if rho_ab.shape != (4, 4):
        raise ValueError(f"Expected 4x4 matrix, got {rho_ab.shape}")

    # Reshape to tensor: rho(i_A, i_B, j_A, j_B)
    tensor = rho_ab.reshape(2, 2, 2, 2)

    if trace_out.upper() == "B":
        # Sum over i_B == j_B
        rho_a = np.trace(tensor, axis1=1, axis2=3)
        return rho_a
    else:
        # Sum over i_A == j_A
        rho_b = np.trace(tensor, axis1=0, axis2=2)
        return rho_b


def analyze_density_matrix(
    matrix_data: Optional[List[List[Dict[str, float]]]] = None,
    preset: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Full diagnostic report of a density matrix.
    """
    if matrix_data:
        dim = len(matrix_data)
        rho = np.zeros((dim, dim), dtype=complex)
        for r in range(dim):
            for c in range(dim):
                cell = matrix_data[r][c]
                rho[r, c] = complex(cell.get("real", 0.0), cell.get("imag", 0.0))
    elif preset:
        p = preset.lower()
        if p == "pure_zero":
            rho = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
        elif p == "pure_plus":
            rho = 0.5 * np.array([[1.0, 1.0], [1.0, 1.0]], dtype=complex)
        elif p == "maximally_mixed_1q":
            rho = 0.5 * np.eye(2, dtype=complex)
        elif p == "bell_phi_plus":
            psi = np.array([1.0 / math.sqrt(2), 0, 0, 1.0 / math.sqrt(2)], dtype=complex)
            rho = np.outer(psi, psi.conj())
        elif p == "maximally_mixed_2q":
            rho = 0.25 * np.eye(4, dtype=complex)
        else:
            rho = 0.5 * np.eye(2, dtype=complex)
    else:
        # Default pure |0⟩
        rho = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)

    # Validate
    val = validate_density_matrix(rho)
    d = val["dimension"]
    purity = compute_purity(rho)

    # Classification
    if abs(purity - 1.0) < 1e-4:
        classification = "PURE"
        desc = "Pure quantum state: Tr(ρ²) = 1.0, represents a single statevector in Hilbert space."
    elif abs(purity - (1.0 / d)) < 1e-4:
        classification = "MAXIMALLY_MIXED"
        desc = f"Maximally mixed state: Tr(ρ²) = 1/{d} = {1.0/d:.3f}, complete lack of quantum state knowledge."
    else:
        classification = "MIXED"
        desc = f"Partially mixed quantum state: Purity γ = {purity:.4f} lies strictly between 1/{d} and 1.0."

    # Serialized matrix elements
    matrix_cells: List[List[Dict[str, float]]] = []
    for r in range(d):
        row_cells = []
        for c in range(d):
            val_c = rho[r, c]
            row_cells.append({
                "real": round(float(val_c.real), 6),
                "imag": round(float(val_c.imag), 6),
            })
        matrix_cells.append(row_cells)

    # 1-Qubit Bloch representation if d == 2
    bloch = None
    if d == 2:
        rx = float(2.0 * rho[0, 1].real)
        ry = float(-2.0 * rho[0, 1].imag)
        rz = float(rho[0, 0].real - rho[1, 1].real)
        bloch = {
            "x": round(rx, 4),
            "y": round(ry, 4),
            "z": round(rz, 4),
            "length": round(math.sqrt(rx ** 2 + ry ** 2 + rz ** 2), 4),
        }

    # Subsystems if 2-qubits (d == 4)
    reduced_a_cells = None
    reduced_b_cells = None
    if d == 4:
        rho_a = partial_trace_2qubit(rho, trace_out="B")
        rho_b = partial_trace_2qubit(rho, trace_out="A")
        reduced_a_cells = [
            [{"real": round(float(rho_a[r, c].real), 4), "imag": round(float(rho_a[r, c].imag), 4)} for c in range(2)]
            for r in range(2)
        ]
        reduced_b_cells = [
            [{"real": round(float(rho_b[r, c].real), 4), "imag": round(float(rho_b[r, c].imag), 4)} for c in range(2)]
            for r in range(2)
        ]

    return {
        "dimension": d,
        "is_valid": True,
        "trace": val["trace"],
        "purity": round(purity, 6),
        "mixedness": round(1.0 - purity, 6),
        "classification": classification,
        "description": desc,
        "eigenvalues": val["eigenvalues"],
        "rank": val["rank"],
        "matrix": matrix_cells,
        "bloch_vector": bloch,
        "reduced_subsystem_a": reduced_a_cells,
        "reduced_subsystem_b": reduced_b_cells,
    }
