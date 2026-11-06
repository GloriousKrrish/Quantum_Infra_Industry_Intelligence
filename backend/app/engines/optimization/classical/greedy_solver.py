"""
greedy_solver.py - Fast Greedy Heuristic and 1-Bit Flip Coordinate Descent Solver.

Provides rapid O(n log n) heuristic approximations for combinatorial problems
and multi-restart local search for QUBO models.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import time

from ..qubo.qubo_model import QUBOModel


@dataclass
class GreedySolution:
    """Result of greedy heuristic or multi-restart local search."""
    optimal_bitstring: str
    optimal_vector: List[int]
    objective_value: float
    iterations: int
    restarts: int
    solve_time_ms: float
    solver_name: str = "Greedy Local Search"
    extra_metadata: Dict[str, Any] = field(default_factory=dict)


class GreedySolver:
    """
    Greedy coordinate-descent and multi-start local search solver.
    """

    def __init__(self, n_restarts: int = 10, seed: Optional[int] = 42):
        self.n_restarts = n_restarts
        self.seed = seed

    def solve_qubo(self, qubo: QUBOModel) -> GreedySolution:
        start_time = time.perf_counter()
        rng = np.random.default_rng(self.seed)
        n = qubo.n_variables
        Q_sym = qubo.to_symmetric_matrix()
        c0 = qubo.constant_offset

        best_energy = float("inf")
        best_bitstring = "0" * n
        total_flips = 0

        # Always include all-zeros and all-ones seeds
        initial_configs = [
            np.zeros(n, dtype=int),
            np.ones(n, dtype=int),
        ]
        # Additional random starts
        for _ in range(max(1, self.n_restarts - 2)):
            initial_configs.append(rng.integers(0, 2, size=n, dtype=int))

        for x in initial_configs:
            current_x = x.copy()
            improved = True
            iter_count = 0

            while improved and iter_count < 100:
                iter_count += 1
                improved = False
                best_delta = 0.0
                best_flip_idx = -1

                # Evaluate delta for flipping each bit i:
                # Delta E = E(x with x_i flipped) - E(x)
                # When x_i flips from 0 to 1: Delta E = Q_ii + 2 * sum_{j != i} Q_ij x_j
                # When x_i flips from 1 to 0: Delta E = -Q_ii - 2 * sum_{j != i} Q_ij x_j
                # In general: Delta E = (1 - 2*x_i) * (Q_ii + 2 * sum_{j != i} Q_ij x_j)
                for i in range(n):
                    s_i = 1 - 2 * current_x[i]  # +1 if 0->1, -1 if 1->0
                    interaction = np.dot(Q_sym[i, :], current_x) - Q_sym[i, i] * current_x[i]
                    delta = s_i * (Q_sym[i, i] + 2.0 * interaction)

                    if delta < best_delta - 1e-9:
                        best_delta = delta
                        best_flip_idx = i

                if best_flip_idx >= 0 and best_delta < -1e-9:
                    current_x[best_flip_idx] = 1 - current_x[best_flip_idx]
                    improved = True
                    total_flips += 1

            # Compute current configuration energy
            curr_energy = float(current_x @ Q_sym @ current_x + c0)
            if curr_energy < best_energy:
                best_energy = curr_energy
                best_bitstring = "".join(str(b) for b in current_x)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        best_vec = [int(b) for b in best_bitstring]

        return GreedySolution(
            optimal_bitstring=best_bitstring,
            optimal_vector=best_vec,
            objective_value=best_energy,
            iterations=total_flips,
            restarts=len(initial_configs),
            solve_time_ms=elapsed_ms,
            extra_metadata={"seed": self.seed}
        )

    @staticmethod
    def solve_knapsack_ratio(
        values: List[float],
        weights: List[float],
        capacity: float
    ) -> GreedySolution:
        """
        Classic O(n log n) knapsack solver based on value-to-weight ratio.
        """
        start_time = time.perf_counter()
        n = len(values)
        ratios = [(values[i] / max(weights[i], 1e-6), i) for i in range(n)]
        ratios.sort(key=lambda item: item[0], reverse=True)

        selected = [0] * n
        accum_weight = 0.0
        accum_value = 0.0

        for r, idx in ratios:
            if accum_weight + weights[idx] <= capacity:
                selected[idx] = 1
                accum_weight += weights[idx]
                accum_value += values[idx]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        bitstring = "".join(str(b) for b in selected)

        return GreedySolution(
            optimal_bitstring=bitstring,
            optimal_vector=selected,
            objective_value=-accum_value,  # minimization convention
            iterations=n,
            restarts=1,
            solve_time_ms=elapsed_ms,
            solver_name="Greedy Ratio Knapsack",
            extra_metadata={
                "accumulated_value": accum_value,
                "accumulated_weight": accum_weight,
                "capacity": capacity
            }
        )

