"""
simulated_annealing.py - Metropolis-Hastings Classical Simulated Annealing Solver.

Provides probabilistic escaping from local minima for QUBO models,
generating full convergence trajectories over temperature annealing schedules.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import time
import math

from ..qubo.qubo_model import QUBOModel


@dataclass
class AnnealingTrajectoryPoint:
    step: int
    temperature: float
    current_energy: float
    best_energy: float
    acceptance_rate: float


@dataclass
class AnnealingSolution:
    """Result of simulated annealing optimization."""
    optimal_bitstring: str
    optimal_vector: List[int]
    minimum_energy: float
    steps_total: int
    steps_accepted: int
    solve_time_ms: float
    trajectory: List[AnnealingTrajectoryPoint]
    solver_name: str = "Simulated Annealing"
    extra_metadata: Dict[str, Any] = field(default_factory=dict)


class SimulatedAnnealingSolver:
    """
    Classical simulated annealing solver for QUBO models.
    """

    def __init__(
        self,
        initial_temp: float = 100.0,
        final_temp: float = 0.01,
        cooling_rate: float = 0.99,
        steps_per_temp: int = 10,
        seed: Optional[int] = 42,
    ):
        self.initial_temp = initial_temp
        self.final_temp = final_temp
        self.cooling_rate = cooling_rate
        self.steps_per_temp = steps_per_temp
        self.seed = seed

    def solve(self, qubo: QUBOModel) -> AnnealingSolution:
        start_time = time.perf_counter()
        rng = np.random.default_rng(self.seed)
        n = qubo.n_variables
        Q_sym = qubo.to_symmetric_matrix()
        c0 = qubo.constant_offset

        # Initial state: random bitstring
        current_x = rng.integers(0, 2, size=n, dtype=int)
        current_energy = float(current_x @ Q_sym @ current_x + c0)

        best_x = current_x.copy()
        best_energy = current_energy

        temp = self.initial_temp
        trajectory: List[AnnealingTrajectoryPoint] = []
        step_count = 0
        accepted_count = 0

        # Precompute initial trajectory point
        trajectory.append(
            AnnealingTrajectoryPoint(
                step=0,
                temperature=temp,
                current_energy=current_energy,
                best_energy=best_energy,
                acceptance_rate=1.0,
            )
        )

        while temp > self.final_temp:
            temp_accepted = 0
            for _ in range(self.steps_per_temp):
                step_count += 1
                # Pick a random bit to flip
                i = rng.integers(0, n)
                s_i = 1 - 2 * current_x[i]

                # Fast delta E calculation
                interaction = np.dot(Q_sym[i, :], current_x) - Q_sym[i, i] * current_x[i]
                delta_E = s_i * (Q_sym[i, i] + 2.0 * interaction)

                accept = False
                if delta_E < 0.0:
                    accept = True
                else:
                    prob = math.exp(-delta_E / max(temp, 1e-12))
                    if rng.random() < prob:
                        accept = True

                if accept:
                    current_x[i] = 1 - current_x[i]
                    current_energy += delta_E
                    temp_accepted += 1
                    accepted_count += 1

                    if current_energy < best_energy:
                        best_energy = current_energy
                        best_x = current_x.copy()

            # Record downsampled trajectory (every 5 temp steps or if log is small)
            if len(trajectory) < 50 or temp <= self.final_temp:
                trajectory.append(
                    AnnealingTrajectoryPoint(
                        step=step_count,
                        temperature=temp,
                        current_energy=current_energy,
                        best_energy=best_energy,
                        acceptance_rate=temp_accepted / max(1, self.steps_per_temp),
                    )
                )

            temp *= self.cooling_rate

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        best_bitstring = "".join(str(b) for b in best_x)

        return AnnealingSolution(
            optimal_bitstring=best_bitstring,
            optimal_vector=best_x.tolist(),
            minimum_energy=best_energy,
            steps_total=step_count,
            steps_accepted=accepted_count,
            solve_time_ms=elapsed_ms,
            trajectory=trajectory,
            extra_metadata={
                "initial_temp": self.initial_temp,
                "final_temp": self.final_temp,
                "cooling_rate": self.cooling_rate,
                "seed": self.seed,
            }
        )

