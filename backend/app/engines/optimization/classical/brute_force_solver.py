"""
brute_force_solver.py - Exhaustive Exact QUBO and Combinatorial Solver.

Computes exact global minimum across all 2^n configurations for n <= 20.
Guarantees provable ground state finding for benchmarking heuristics and QAOA.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np
import time

from ..qubo.qubo_model import QUBOModel


@dataclass
class BruteForceSolution:
    """Result of exhaustive combinatorial search."""
    optimal_bitstring: str
    optimal_vector: List[int]
    minimum_energy: float
    total_states_evaluated: int
    degeneracy: int
    all_optimal_bitstrings: List[str]
    solve_time_ms: float
    solver_name: str = "Exact Brute Force"
    energy_percentiles: Dict[str, float] = field(default_factory=dict)


class BruteForceSolver:
    """
    Exhaustive exact solver for QUBO models up to 20 variables (2^20 ~ 1,048,576 configurations).
    """

    def __init__(self, max_variables: int = 20):
        self.max_variables = max_variables

    def solve(self, qubo: QUBOModel) -> BruteForceSolution:
        start_time = time.perf_counter()
        n = qubo.n_variables

        if n > self.max_variables:
            raise ValueError(
                f"BruteForceSolver is limited to n <= {self.max_variables} variables "
                f"to prevent memory exhaustion. Requested problem has n = {n}."
            )

        total_states = 1 << n
        Q_sym = qubo.to_symmetric_matrix()
        c0 = qubo.constant_offset

        # Vectorized bit-array evaluation for speed
        # Construct matrix of shape (2^n, n)
        # Using NumPy bit unpacking
        indices = np.arange(total_states, dtype=np.uint32)
        # Unpack bits: shape (2^n, n)
        bits = ((indices[:, None] >> np.arange(n)[None, :]) & 1).astype(np.float64)

        # Vectorized energy evaluation:
        # E = sum_j (X Q)_j * X_j + c0
        # X @ Q has shape (2^n, n)
        XQ = bits @ Q_sym
        energies = np.sum(XQ * bits, axis=1) + c0

        min_energy = float(np.min(energies))
        min_indices = np.where(np.isclose(energies, min_energy, atol=1e-8))[0]
        degeneracy = len(min_indices)

        optimal_idx = min_indices[0]
        optimal_vec = bits[optimal_idx].astype(int).tolist()
        optimal_bitstring = "".join(str(b) for b in optimal_vec)

        all_optimal_bitstrings = [
            "".join(str(int(b)) for b in bits[idx])
            for idx in min_indices[:10]  # top 10 degenerate ground states
        ]

        percentiles = {
            "p0_min": min_energy,
            "p25": float(np.percentile(energies, 25)),
            "p50_median": float(np.median(energies)),
            "p75": float(np.percentile(energies, 75)),
            "p100_max": float(np.max(energies)),
            "mean": float(np.mean(energies)),
            "std": float(np.std(energies)),
        }

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return BruteForceSolution(
            optimal_bitstring=optimal_bitstring,
            optimal_vector=optimal_vec,
            minimum_energy=min_energy,
            total_states_evaluated=total_states,
            degeneracy=degeneracy,
            all_optimal_bitstrings=all_optimal_bitstrings,
            solve_time_ms=elapsed_ms,
            energy_percentiles=percentiles
        )

