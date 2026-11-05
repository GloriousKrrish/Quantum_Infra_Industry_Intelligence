"""
Quantum Information & Entropy Engine for Quantum Estate X.

Calculates mathematically rigorous quantum information measures:
- Von Neumann Entropy: S(ρ) = -Tr(ρ log₂ ρ) with zero-eigenvalue stability
- State Purity: γ = Tr(ρ²)
- Quantum Fidelity: F(ρ, σ) = (Tr √(√ρ σ √ρ))²
- Trace Distance: D(ρ, σ) = 1/2 ||ρ - σ||₁ = 1/2 Σ |λᵢ(ρ - σ)|
- Classical Shannon Entropy: H(X) = -Σ pᵢ log₂(pᵢ)
- Fuchs-van de Graaf inequality bounds: 1 - √F <= D <= √(1 - F)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.linalg as la

from backend.app.engines.quantum.density_matrix import (
    validate_density_matrix,
    compute_purity,
    analyze_density_matrix,
)


def compute_von_neumann_entropy(rho: np.ndarray) -> float:
    """
    Compute Von Neumann entropy S(ρ) = -Tr(ρ log₂ ρ) = -Σ λ_i log₂(λ_i).
    Safely handles zero and negative numerical eigenvalues via lim_{x->0} x log2(x) = 0.
    """
    eigvals = la.eigvalsh(rho)
    entropy = 0.0
    for ev in eigvals:
        if ev > 1e-12:
            entropy -= float(ev * math.log2(ev))
    return max(0.0, float(entropy))


def compute_shannon_entropy(probabilities: List[float]) -> float:
    """Compute classical Shannon entropy H(X) = -Σ p_i log₂(p_i)."""
    h = 0.0
    for p in probabilities:
        if p > 1e-12:
            h -= float(p * math.log2(p))
    return max(0.0, float(h))


def _matrix_sqrt_psd(mat: np.ndarray) -> np.ndarray:
    """Compute matrix square root for Hermitian positive-semidefinite matrices via spectral decomposition."""
    eigvals, eigvecs = la.eigh(mat)
    sqrt_eigs = np.sqrt(np.maximum(0.0, eigvals))
    return eigvecs @ np.diag(sqrt_eigs) @ eigvecs.conj().T


def compute_quantum_fidelity(rho: np.ndarray, sigma: np.ndarray) -> Dict[str, float]:
    """
    Calculate quantum fidelity between two states:
        F(ρ, σ) = (Tr √(√ρ σ √ρ))²   (Jozsa convention, squared fidelity)
        Root fidelity: √F = Tr √(√ρ σ √ρ)
    """
    if rho.shape != sigma.shape:
        raise ValueError(f"State dimensions do not match: {rho.shape} vs {sigma.shape}")

    sqrt_rho = _matrix_sqrt_psd(rho)
    inner = sqrt_rho @ sigma @ sqrt_rho
    sqrt_inner = _matrix_sqrt_psd(inner)

    # Trace of matrix square root
    root_fidelity = float(np.trace(sqrt_inner).real)
    root_fidelity = max(0.0, min(1.0, root_fidelity))
    squared_fidelity = float(root_fidelity ** 2)

    return {
        "squared_fidelity": round(squared_fidelity, 6),
        "root_fidelity": round(root_fidelity, 6),
    }


def compute_trace_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    """
    Calculate trace distance:
        D(ρ, σ) = 1/2 ||ρ - σ||₁ = 1/2 Tr |ρ - σ| = 1/2 Σ |λᵢ(ρ - σ)|
    """
    if rho.shape != sigma.shape:
        raise ValueError(f"State dimensions do not match: {rho.shape} vs {sigma.shape}")

    diff = rho - sigma
    diff_herm = (diff + diff.conj().T) / 2.0
    eigvals = la.eigvalsh(diff_herm)
    dist = 0.5 * float(np.sum(np.abs(eigvals)))
    return max(0.0, min(1.0, round(dist, 6)))


def analyze_quantum_information(
    state_a_preset: str = "pure_zero",
    state_b_preset: str = "pure_plus",
    custom_state_a: Optional[List[List[Dict[str, float]]]] = None,
    custom_state_b: Optional[List[List[Dict[str, float]]]] = None,
) -> Dict[str, Any]:
    """
    Comprehensive quantum information diagnostic comparing two states ρ and σ.
    """
    # 1. Resolve State A
    res_a = analyze_density_matrix(matrix_data=custom_state_a, preset=state_a_preset)
    dim_a = res_a["dimension"]
    rho_a = np.array([
        [complex(c["real"], c["imag"]) for c in row]
        for row in res_a["matrix"]
    ])

    # 2. Resolve State B
    res_b = analyze_density_matrix(matrix_data=custom_state_b, preset=state_b_preset)
    dim_b = res_b["dimension"]
    rho_b = np.array([
        [complex(c["real"], c["imag"]) for c in row]
        for row in res_b["matrix"]
    ])

    if dim_a != dim_b:
        raise ValueError(f"State dimensions must match: state A is {dim_a}x{dim_a}, state B is {dim_b}x{dim_b}")

    # Information metrics for State A
    s_a = compute_von_neumann_entropy(rho_a)
    purity_a = res_a["purity"]
    shannon_a = compute_shannon_entropy([float(rho_a[i, i].real) for i in range(dim_a)])

    # Information metrics for State B
    s_b = compute_von_neumann_entropy(rho_b)
    purity_b = res_b["purity"]
    shannon_b = compute_shannon_entropy([float(rho_b[i, i].real) for i in range(dim_b)])

    # Relational metrics
    fid = compute_quantum_fidelity(rho_a, rho_b)
    trace_dist = compute_trace_distance(rho_a, rho_b)

    # Fuchs-van de Graaf inequality bounds
    f_root = fid["root_fidelity"]
    fvdg_lower = round(1.0 - f_root, 6)
    fvdg_upper = round(math.sqrt(max(0.0, 1.0 - fid["squared_fidelity"])), 6)
    inequality_satisfied = bool(fvdg_lower - 1e-5 <= trace_dist <= fvdg_upper + 1e-5)

    return {
        "dimension": dim_a,
        "state_a": {
            "name": state_a_preset,
            "classification": res_a["classification"],
            "von_neumann_entropy": round(s_a, 6),
            "purity": round(purity_a, 6),
            "shannon_entropy_z": round(shannon_a, 6),
            "bloch_vector": res_a.get("bloch_vector"),
        },
        "state_b": {
            "name": state_b_preset,
            "classification": res_b["classification"],
            "von_neumann_entropy": round(s_b, 6),
            "purity": round(purity_b, 6),
            "shannon_entropy_z": round(shannon_b, 6),
            "bloch_vector": res_b.get("bloch_vector"),
        },
        "relational_metrics": {
            "squared_fidelity_F": fid["squared_fidelity"],
            "root_fidelity_sqrt_F": fid["root_fidelity"],
            "trace_distance_D": trace_dist,
            "orthogonality": bool(fid["squared_fidelity"] < 1e-6),
            "identical": bool(fid["squared_fidelity"] > 0.9999),
            "fuchs_van_de_graaf_bounds": {
                "lower_bound": fvdg_lower,
                "trace_distance": trace_dist,
                "upper_bound": fvdg_upper,
                "is_satisfied": inequality_satisfied,
                "formula": "1 - √F <= D(ρ, σ) <= √(1 - F)",
            },
        },
    }
