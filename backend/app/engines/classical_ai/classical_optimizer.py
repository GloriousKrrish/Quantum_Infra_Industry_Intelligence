"""
Classical Optimization Baselines.

Provides brute-force exact solver and simulated annealing for QUBO
problems.  These serve as reference benchmarks against the quantum
QAOA approach.
"""

from __future__ import annotations

import time
from typing import Tuple

import numpy as np

from backend.app.models.schemas import ClassicalResult


# ═══════════════════════════════════════════════════════════════════════
# 1.  BRUTE-FORCE EXACT SOLVER
# ═══════════════════════════════════════════════════════════════════════


def run_brute_force(Q: np.ndarray) -> ClassicalResult:
    """
    Exhaustively evaluate all 2^n bitstrings to find the global minimum.

    Complexity: O(2^n · n²).  Only feasible for n ≤ 20.

    Args:
        Q: n×n QUBO matrix.

    Returns:
        ClassicalResult with the exact optimal solution.

    Raises:
        ValueError: If n > 20 (would require > 1M evaluations).
    """
    n = Q.shape[0]
    if n > 20:
        raise ValueError(
            f"Brute force is infeasible for n={n} variables (max 20)."
        )

    t_start = time.perf_counter()

    best_val = float("inf")
    best_bs = "0" * n

    for idx in range(2 ** n):
        x = np.array(
            [int(b) for b in format(idx, f"0{n}b")],
            dtype=np.float64,
        )
        val = float(x @ Q @ x)
        if val < best_val:
            best_val = val
            best_bs = format(idx, f"0{n}b")

    t_elapsed = (time.perf_counter() - t_start) * 1000.0

    return ClassicalResult(
        method="brute_force",
        optimal_value=round(best_val, 6),
        optimal_solution=best_bs,
        execution_time_ms=round(t_elapsed, 2),
    )


# ═══════════════════════════════════════════════════════════════════════
# 2.  SIMULATED ANNEALING
# ═══════════════════════════════════════════════════════════════════════


def _qubo_energy(x: np.ndarray, Q: np.ndarray) -> float:
    """Compute QUBO energy x^T Q x."""
    return float(x @ Q @ x)


def run_simulated_annealing(
    Q: np.ndarray,
    temp: float = 1000.0,
    cooling: float = 0.995,
    iterations: int = 10000,
    seed: int = 42,
) -> ClassicalResult:
    """
    Simulated annealing meta-heuristic for QUBO minimisation.

    Uses single-bit-flip neighbourhood with Metropolis acceptance
    criterion and geometric cooling schedule.

    Args:
        Q:          n×n QUBO matrix.
        temp:       Initial temperature.
        cooling:    Multiplicative cooling factor per step.
        iterations: Total number of SA steps.
        seed:       Random seed for reproducibility.

    Returns:
        ClassicalResult with the best solution found.
    """
    n = Q.shape[0]
    rng = np.random.default_rng(seed)

    t_start = time.perf_counter()

    # Random initial solution
    current = rng.integers(0, 2, size=n).astype(np.float64)
    current_energy = _qubo_energy(current, Q)

    best = current.copy()
    best_energy = current_energy

    T = temp
    for step in range(iterations):
        # Flip a random bit
        flip_idx = rng.integers(0, n)
        candidate = current.copy()
        candidate[flip_idx] = 1.0 - candidate[flip_idx]
        candidate_energy = _qubo_energy(candidate, Q)

        delta = candidate_energy - current_energy

        # Metropolis acceptance
        if delta < 0 or rng.random() < np.exp(-delta / max(T, 1e-10)):
            current = candidate
            current_energy = candidate_energy

            if current_energy < best_energy:
                best = current.copy()
                best_energy = current_energy

        T *= cooling

    t_elapsed = (time.perf_counter() - t_start) * 1000.0

    best_bs = "".join(str(int(b)) for b in best)

    return ClassicalResult(
        method="simulated_annealing",
        optimal_value=round(best_energy, 6),
        optimal_solution=best_bs,
        execution_time_ms=round(t_elapsed, 2),
    )
