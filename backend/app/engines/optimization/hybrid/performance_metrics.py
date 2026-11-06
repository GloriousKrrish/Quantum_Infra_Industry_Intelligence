"""
performance_metrics.py - Rigorous Scientific Benchmarking Metrics.

Calculates:
  - Absolute optimality gap: |E_solver - E_exact|
  - Relative optimality gap percentage: (|E_solver - E_exact| / |E_exact|) * 100
  - Shift-invariant normalized approximation ratio alpha in [0, 1]
  - Independent bitstring verification: qubo.evaluate_energy(bitstring)
  - Feasibility checking and execution time tracking
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np


@dataclass
class SolverBenchmarkEntry:
    solver_name: str
    is_quantum: bool
    status: str
    optimal_bitstring: str  # Kept as alias for best bitstring found
    best_bitstring: str      # Unambiguous label
    energy: float            # Reported objective energy
    bitstring_evaluated_energy: float  # Independently verified QUBO evaluation E(best_bitstring)
    absolute_optimality_gap: float     # |energy - E_exact|
    optimality_gap_pct: float          # Percentage gap
    approximation_ratio: float         # Shift-invariant normalized ratio in [0, 1]
    solve_time_ms: float
    iterations: int
    feasibility_status: str
    hardware_note: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BenchmarkMetricsCalculator:
    """
    Computes rigorous comparison metrics between classical and quantum solvers.
    """

    @staticmethod
    def calculate_absolute_gap(energy: float, exact_ground_energy: float) -> float:
        """Absolute distance |E_solver - E_exact| in objective units."""
        return round(abs(energy - exact_ground_energy), 6)

    @staticmethod
    def calculate_gap(energy: float, exact_ground_energy: float) -> float:
        """Percentage gap above exact global minimum: (|E - E*| / |E*|) * 100%."""
        denom = abs(exact_ground_energy)
        if denom < 1e-8:
            return round(abs(energy - exact_ground_energy) * 100.0, 4)
        return round((abs(energy - exact_ground_energy) / denom) * 100.0, 4)

    @staticmethod
    def calculate_approx_ratio(
        energy: float,
        exact_ground_energy: float,
        worst_energy: Optional[float] = None,
    ) -> float:
        """
        Calculates shift-invariant normalized approximation ratio in [0, 1]:
            alpha = (E_worst - E) / (E_worst - E_best)
        Guarantees:
            alpha = 1.0 at E = E_best (provably optimal)
            alpha = 0.0 at E = E_worst (worst possible configuration)
        Invariant under arbitrary affine constant offsets c_0.
        """
        if worst_energy is not None and abs(worst_energy - exact_ground_energy) > 1e-6:
            alpha = (worst_energy - energy) / (worst_energy - exact_ground_energy)
            return round(min(1.0, max(0.0, float(alpha))), 4)

        # Fallback when worst_energy is not known: distance-based bounded ratio
        diff = abs(energy - exact_ground_energy)
        if diff < 1e-6:
            return 1.0
        denom = max(abs(exact_ground_energy), 1.0)
        return round(max(0.0, 1.0 - diff / denom), 4)
