"""
Advanced Entanglement Analysis Engine for Quantum Estate X.

Performs rigorous bipartite and multipartite entanglement quantification:
- Schmidt decomposition: |ψ_AB⟩ = Σ λ_k |u_k⟩_A |v_k⟩_B
- Schmidt rank and Schmidt coefficients (λ_k >= 0, Σ λ_k² = 1)
- Entanglement entropy: E(ψ) = -Σ λ_k² log₂(λ_k²)
- Wootters' Concurrence: C(ρ) = max(0, μ₁ - μ₂ - μ₃ - μ₄) for general 2-qubit states
- Peres-Horodecki PPT criterion: Negativity N(ρ) and Logarithmic Negativity E_N(ρ)
- Robust classification distinguishing quantum entanglement from classical correlation
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.linalg as la

from backend.app.engines.quantum.gate_library import MATRIX_Y
from backend.app.engines.quantum.density_matrix import (
    validate_density_matrix,
    compute_purity,
    partial_trace_2qubit,
)
from backend.app.engines.quantum.quantum_information import compute_von_neumann_entropy


def schmidt_decomposition_pure_state(psi: np.ndarray, dim_a: int = 2, dim_b: int = 2) -> Dict[str, Any]:
    """
    Compute Schmidt decomposition of a pure bipartite statevector |ψ_AB⟩:
        |ψ_AB⟩ = Σ_k λ_k |u_k⟩_A |v_k⟩_B
    via Singular Value Decomposition (SVD).
    """
    if len(psi) != dim_a * dim_b:
        raise ValueError(f"State length {len(psi)} does not match dim_A * dim_B = {dim_a * dim_b}")

    # Reshape statevector into dim_a x dim_b matrix
    mat_c = psi.reshape(dim_a, dim_b)

    # SVD: mat_c = U @ diag(s) @ Vh
    U, s, Vh = la.svd(mat_c)

    # Schmidt coefficients are the singular values
    schmidt_coeffs = [float(val) for val in s if val > 1e-9]
    schmidt_rank = len(schmidt_coeffs)

    # Entanglement entropy S(ρ_A) = -Σ λ_k² log₂(λ_k²)
    ent_entropy = 0.0
    for lam in schmidt_coeffs:
        lam_sq = lam ** 2
        if lam_sq > 1e-12:
            ent_entropy -= lam_sq * math.log2(lam_sq)

    return {
        "schmidt_rank": schmidt_rank,
        "is_entangled": bool(schmidt_rank > 1),
        "schmidt_coefficients": [round(c, 4) for c in schmidt_coeffs],
        "schmidt_probabilities": [round(c ** 2, 4) for c in schmidt_coeffs],
        "entanglement_entropy_ebits": round(ent_entropy, 4),
    }


def _matrix_sqrt_psd(mat: np.ndarray) -> np.ndarray:
    """Compute matrix square root for Hermitian positive-semidefinite matrices via spectral decomposition."""
    eigvals, eigvecs = la.eigh(mat)
    sqrt_eigs = np.sqrt(np.maximum(0.0, eigvals))
    return eigvecs @ np.diag(sqrt_eigs) @ eigvecs.conj().T


def compute_concurrence_2qubit(rho: np.ndarray) -> float:
    """
    Calculate Wootters' concurrence C(ρ) for an arbitrary 2-qubit state (pure or mixed):
        ρ̃ = (σ_y ⊗ σ_y) ρ* (σ_y ⊗ σ_y)
        R = √(√ρ ρ̃ √ρ)
        C(ρ) = max(0, μ₁ - μ₂ - μ₃ - μ₄) where μ_i are eigenvalues of R in decreasing order.
    """
    if rho.shape != (4, 4):
        raise ValueError(f"Concurrence is defined for 4x4 2-qubit states, got {rho.shape}")

    # Spin-flipped state: (σ_y ⊗ σ_y)
    sy_sy = np.kron(MATRIX_Y, MATRIX_Y)
    rho_tilde = sy_sy @ rho.conj() @ sy_sy

    # R = sqrtm(sqrtm(rho) @ rho_tilde @ sqrtm(rho))
    sqrt_rho = _matrix_sqrt_psd(rho)
    inner = sqrt_rho @ rho_tilde @ sqrt_rho
    sqrt_inner = _matrix_sqrt_psd((inner + inner.conj().T) / 2.0)

    # Eigenvalues of sqrt_inner
    eigvals = la.eigvals(sqrt_inner).real
    eigvals = sorted([max(0.0, float(ev)) for ev in eigvals], reverse=True)

    c = eigvals[0] - eigvals[1] - eigvals[2] - eigvals[3]
    return max(0.0, min(1.0, round(float(c), 6)))


def compute_negativity_and_ppt(rho: np.ndarray) -> Dict[str, Any]:
    """
    Compute Peres-Horodecki PPT criterion, Negativity, and Logarithmic Negativity:
        Partial transpose with respect to subsystem B:
        (ρ^T_B)_{(i, μ), (j, ν)} = ρ_{(i, ν), (j, μ)}
        Negativity N(ρ) = (||ρ^T_B||₁ - 1) / 2 = Σ_{λ < 0} |λ|
        Logarithmic Negativity E_N(ρ) = log₂(||ρ^T_B||₁)
    """
    if rho.shape != (4, 4):
        raise ValueError(f"Expected 4x4 matrix, got {rho.shape}")

    # Partial transpose on subsystem B (qubit 1)
    # Tensor representation: rho[iA, iB, jA, jB] -> transpose indices 1 and 3
    tensor = rho.reshape(2, 2, 2, 2)
    rho_pt = np.transpose(tensor, (0, 3, 2, 1)).reshape(4, 4)

    # Eigenvalues of partial transpose
    eigvals_pt = la.eigvalsh(rho_pt)
    negative_eigs = [float(ev) for ev in eigvals_pt if ev < -1e-6]

    negativity = sum(abs(ev) for ev in negative_eigs)
    trace_norm = float(np.sum(np.abs(eigvals_pt)))
    log_negativity = math.log2(max(1.0, trace_norm))

    is_npt = len(negative_eigs) > 0

    return {
        "is_ppt_separable": not is_npt,
        "is_entangled_npt": is_npt,
        "negativity": round(negativity, 6),
        "logarithmic_negativity": round(log_negativity, 6),
        "min_pt_eigenvalue": round(float(np.min(eigvals_pt)), 6),
    }


def analyze_entanglement_state(
    preset: str = "bell_phi_plus",
    custom_statevector: Optional[List[Dict[str, float]]] = None,
    custom_matrix: Optional[List[List[Dict[str, float]]]] = None,
    werner_parameter_p: float = 1.0,
) -> Dict[str, Any]:
    """
    Comprehensive diagnostic of quantum entanglement vs. classical correlation.
    """
    p_name = preset.lower()
    is_pure = True
    psi: Optional[np.ndarray] = None
    rho: np.ndarray

    if custom_matrix:
        d = len(custom_matrix)
        rho = np.zeros((d, d), dtype=complex)
        for r in range(d):
            for c in range(d):
                cell = custom_matrix[r][c]
                rho[r, c] = complex(cell.get("real", 0.0), cell.get("imag", 0.0))
        is_pure = False
    elif custom_statevector:
        psi = np.array(
            [complex(c.get("real", 0.0), c.get("imag", 0.0)) for c in custom_statevector],
            dtype=complex,
        )
        psi = psi / np.linalg.norm(psi)
        rho = np.outer(psi, psi.conj())
        is_pure = True
    elif p_name == "bell_phi_plus":
        psi = np.array([1.0 / math.sqrt(2), 0.0, 0.0, 1.0 / math.sqrt(2)], dtype=complex)
        rho = np.outer(psi, psi.conj())
    elif p_name == "bell_psi_minus":
        # Singlet state S=0
        psi = np.array([0.0, 1.0 / math.sqrt(2), -1.0 / math.sqrt(2), 0.0], dtype=complex)
        rho = np.outer(psi, psi.conj())
    elif p_name == "w_state_3q":
        # 3-qubit W-state: (|001> + |010> + |100>)/√3
        psi = np.zeros(8, dtype=complex)
        psi[1] = 1.0 / math.sqrt(3.0)  # 001
        psi[2] = 1.0 / math.sqrt(3.0)  # 010
        psi[4] = 1.0 / math.sqrt(3.0)  # 100
        rho = np.outer(psi, psi.conj())
    elif p_name == "ghz_state_3q":
        psi = np.zeros(8, dtype=complex)
        psi[0] = 1.0 / math.sqrt(2.0)
        psi[7] = 1.0 / math.sqrt(2.0)
        rho = np.outer(psi, psi.conj())
    elif p_name == "werner_state":
        # Werner state: p |Phi+><Phi+| + (1-p)/4 * I_4
        # Entangled if and only if p > 1/3 ~ 0.333
        p = max(0.0, min(1.0, werner_parameter_p))
        psi_bell = np.array([1.0 / math.sqrt(2), 0.0, 0.0, 1.0 / math.sqrt(2)], dtype=complex)
        rho_bell = np.outer(psi_bell, psi_bell.conj())
        rho = p * rho_bell + ((1.0 - p) / 4.0) * np.eye(4, dtype=complex)
        is_pure = bool(abs(p - 1.0) < 1e-4)
    elif p_name == "classical_correlated_separable":
        # 0.5 |00><00| + 0.5 |11><11| (strictly separable, zero entanglement!)
        rho = np.zeros((4, 4), dtype=complex)
        rho[0, 0] = 0.5
        rho[3, 3] = 0.5
        is_pure = False
    else:
        # Default separable product state |00⟩
        psi = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        rho = np.outer(psi, psi.conj())

    d = rho.shape[0]
    purity = compute_purity(rho)

    # 1. Concurrence & PPT for 2-qubit states
    concurrence = None
    ppt_analysis = None
    if d == 4:
        concurrence = compute_concurrence_2qubit(rho)
        ppt_analysis = compute_negativity_and_ppt(rho)

    # 2. Schmidt decomposition if pure state and bipartite
    schmidt = None
    if is_pure and psi is not None and d == 4:
        schmidt = schmidt_decomposition_pure_state(psi, dim_a=2, dim_b=2)

    # 3. Subsystem reduced density matrices (for d=4)
    subsystem_metrics = None
    if d == 4:
        rho_a = partial_trace_2qubit(rho, trace_out="B")
        rho_b = partial_trace_2qubit(rho, trace_out="A")
        subsystem_metrics = {
            "purity_subsystem_A": round(compute_purity(rho_a), 4),
            "purity_subsystem_B": round(compute_purity(rho_b), 4),
            "entropy_subsystem_A": round(compute_von_neumann_entropy(rho_a), 4),
            "entropy_subsystem_B": round(compute_von_neumann_entropy(rho_b), 4),
        }

    # Classification logic
    if concurrence is not None and concurrence > 0.01:
        ent_classification = "ENTANGLED"
        ent_desc = f"Quantum entangled state (Concurrence C = {concurrence:.3f}, Negativity N = {ppt_analysis['negativity']:.3f})."
    elif p_name == "classical_correlated_separable":
        ent_classification = "SEPARABLE_CLASSICAL_CORRELATION"
        ent_desc = "Classically correlated but unentangled mixture (C = 0.000, PPT-separable, local hidden variables suffice)."
    elif p_name in ("w_state_3q", "ghz_state_3q"):
        ent_classification = "MULTIPARTITE_ENTANGLED"
        ent_desc = f"Multipartite entangled 3-qubit state ({p_name.upper()})."
    else:
        ent_classification = "SEPARABLE"
        ent_desc = "Separable product state (C = 0.000, zero quantum entanglement)."

    return {
        "preset_name": p_name,
        "dimension": d,
        "is_pure": is_pure,
        "global_purity": round(purity, 4),
        "entanglement_classification": ent_classification,
        "description": ent_desc,
        "concurrence": concurrence,
        "ppt_negativity": ppt_analysis,
        "schmidt_decomposition": schmidt,
        "subsystem_metrics": subsystem_metrics,
    }
