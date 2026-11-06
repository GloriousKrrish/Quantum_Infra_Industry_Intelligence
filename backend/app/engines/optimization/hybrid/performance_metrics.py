"""
performance_metrics.py - Rigorous Scientific Benchmarking Metrics.

Calculates:
  - Optimality gap: |E_solver - E_exact| / |E_exact|
  - Approximation ratio: alpha
  - Constraint violation / feasibility checking
  - Speedup and execution time statistics
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import numpy as np


@dataclass
class SolverBenchmarkEntry:
    solver_name: str
    is_quantum: bool
    status: str
    optimal_bitstring: str
    energy: float
    optimality_gap_pct: float
    approximation_ratio: float
    solve_time_ms: float
    iterations: int
    feasibility_status: str
    hardware_note: str
    metadata: Dict[str, Any]


class BenchmarkMetricsCalculator:
    """
    Computes rigorous comparison metrics between classical and quantum solvers.
    """

    @staticmethod
    def calculate_gap(energy: float, exact_ground_energy: float) -> float:
        """Percentage gap above the exact global minimum."""
        denom = abs(exact_ground_energy)
        if denom < 1e-8:
            return round(abs(energy - exact_ground_energy) * 100.0, 4)
        return round(abs(energy - exact_ground_energy) / denom * 100.0, 4)

    @staticmethod
    def calculate_approx_ratio(energy: float, exact_ground_energy: float) -> float:
        """Approximation ratio alpha in [0, 1] for minimization with negative costs or relative."""
        if abs(exact_ground_energy) < 1e-8:
            return 1.0 if abs(energy - exact_ground_energy) < 1e-6 else 0.0

        if exact_ground_energy < 0:
            # For minimization of negative values (e.g. profit maximization):
            # energy is more negative = better.
            ratio = energy / exact_ground_energy
            return round(min(1.0, max(0.0, ratio)), 4)
        else:
            ratio = exact_ground_energy / max(energy, 1e-8)
            return round(min(1.0, max(0.0, ratio)), 4)
