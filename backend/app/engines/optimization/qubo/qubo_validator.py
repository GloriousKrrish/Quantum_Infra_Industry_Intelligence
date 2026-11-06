"""
QUBO Validation & Diagnostic Engine.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

from backend.app.engines.optimization.qubo.qubo_model import QUBOModel


class QUBOValidationError(ValueError):
    """Raised when QUBO matrix or parameters violate mathematical constraints."""
    pass


@dataclass
class QUBOValidationResult:
    is_valid: bool
    num_variables: int
    is_symmetric: bool
    is_finite: bool
    condition_number: Optional[float] = None
    min_eigenvalue: Optional[float] = None
    max_eigenvalue: Optional[float] = None
    dynamic_range_db: Optional[float] = None
    warnings: List[str] = field(default_factory=list)


class QUBOValidator:
    """Wrapper class for QUBO validation."""

    @staticmethod
    def validate(model: QUBOModel) -> QUBOValidationResult:
        try:
            info = validate_qubo_model(model)
            Q = model.to_symmetric_matrix()
            eigs = np.linalg.eigvalsh(Q)
            cond = float(np.linalg.cond(Q)) if np.all(np.isfinite(Q)) and np.linalg.matrix_rank(Q) == len(Q) else None
            
            return QUBOValidationResult(
                is_valid=True,
                num_variables=info["num_variables"],
                is_symmetric=info["is_symmetric"],
                is_finite=True,
                condition_number=cond,
                min_eigenvalue=round(float(np.min(eigs)), 4),
                max_eigenvalue=round(float(np.max(eigs)), 4),
                dynamic_range_db=round(info["dynamic_range_orders"] * 20.0, 2),
                warnings=info["warnings"],
            )
        except Exception as e:
            return QUBOValidationResult(
                is_valid=False,
                num_variables=model.num_variables,
                is_symmetric=False,
                is_finite=False,
                warnings=[str(e)],
            )


def validate_qubo_model(model: QUBOModel) -> Dict[str, Any]:
    """
    Perform thorough numerical, structural, and algebraic validation on a QUBOModel.
    Returns diagnostic summary dict.
    """
    Q = model.matrix
    n = model.num_variables

    # 1. Structural checks
    if Q.ndim != 2:
        raise QUBOValidationError(f"QUBO matrix must have dimension 2, got {Q.ndim}")
    if Q.shape[0] != Q.shape[1]:
        raise QUBOValidationError(f"QUBO matrix must be square, got {Q.shape}")
    if n == 0:
        raise QUBOValidationError("QUBO matrix cannot have zero variables")

    # 2. Numerical finiteness
    if not np.all(np.isfinite(Q)):
        raise QUBOValidationError("QUBO matrix contains NaN or Inf values")
    if not np.isfinite(model.offset):
        raise QUBOValidationError(f"QUBO offset must be finite, got {model.offset}")

    # 3. Symmetry check
    is_symmetric = bool(np.allclose(Q, Q.T, atol=1e-10))
    is_upper_triangular = bool(np.allclose(np.tril(Q, -1), 0.0, atol=1e-10))

    # 4. Coefficient statistics
    diag_vals = np.diag(Q)
    off_diag_vals = Q[~np.eye(n, dtype=bool)]

    min_coeff = float(np.min(np.abs(Q[Q != 0]))) if np.any(Q != 0) else 0.0
    max_coeff = float(np.max(np.abs(Q))) if np.any(Q != 0) else 0.0

    dynamic_range_orders = 0.0
    if min_coeff > 0:
        dynamic_range_orders = float(np.log10(max_coeff / min_coeff))

    warnings: List[str] = []
    if dynamic_range_orders > 6.0:
        warnings.append(
            f"Wide coefficient dynamic range ({dynamic_range_orders:.1f} orders of magnitude). "
            "Consider rescaling penalties to improve QAOA gradient conditioning."
        )

    # 5. Energy equivalence test (sample random binary vectors)
    model_upper = model.to_upper_triangular()
    model_sym = model.to_symmetric()
    rng = np.random.default_rng(42)
    sample_tests_passed = True
    for _ in range(min(16, 2**n)):
        x_rand = rng.integers(0, 2, size=n)
        e_orig = model.evaluate_energy(x_rand)
        e_up = model_upper.evaluate_energy(x_rand)
        e_sym = model_sym.evaluate_energy(x_rand)
        if not (np.isclose(e_orig, e_up, atol=1e-9) and np.isclose(e_orig, e_sym, atol=1e-9)):
            sample_tests_passed = False
            raise QUBOValidationError(
                f"Algebraic canonicalization mismatch: E_orig={e_orig}, E_upper={e_up}, E_sym={e_sym}"
            )

    return {
        "is_valid": True,
        "num_variables": n,
        "is_symmetric": is_symmetric,
        "is_upper_triangular": is_upper_triangular,
        "canonicalization_verified": sample_tests_passed,
        "min_nonzero_abs_coeff": round(min_coeff, 6),
        "max_abs_coeff": round(max_coeff, 6),
        "dynamic_range_orders": round(dynamic_range_orders, 2),
        "diagonal_min": round(float(np.min(diag_vals)), 6) if len(diag_vals) > 0 else 0.0,
        "diagonal_max": round(float(np.max(diag_vals)), 6) if len(diag_vals) > 0 else 0.0,
        "warnings": warnings,
    }
