"""
hybrid_optimizer.py - Hybrid Classical-Quantum Workflow Orchestrator.

Orchestrates simultaneous classical solving (HiGHS MILP, Greedy, SA)
and quantum approximate solving (QAOA on Qiskit Aer), cross-validating solutions
and generating comprehensive research comparison payloads.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import time

from ..qubo.qubo_model import QUBOModel
from ..classical.milp_solver import HiGHSMILPSolver, MILPSolution
from ..classical.greedy_solver import GreedySolver, GreedySolution
from ..classical.simulated_annealing import SimulatedAnnealingSolver, AnnealingSolution
from ..quantum.qaoa_engine import QAOAEngine, QAOASolution
from .performance_metrics import BenchmarkMetricsCalculator


@dataclass
class HybridOptimizationResult:
    problem_name: str
    num_variables: int
    variable_names: List[str]
    classical_solution: Dict[str, Any]
    quantum_solution: Dict[str, Any]
    consensus_reached: bool
    optimality_gap_pct: float
    approximation_ratio: float
    total_execution_time_ms: float
    hardware_disclaimer: str = (
        "Quantum execution performed locally via classical simulation using Qiskit Aer 0.18.2. "
        "No quantum hardware advantage or supremacy claimed."
    )


class HybridOptimizer:
    """
    Orchestrates hybrid classical-quantum optimization runs.
    """

    def __init__(self, depth_p: int = 1, shots: int = 2048, seed: int = 42):
        self.depth_p = depth_p
        self.shots = shots
        self.seed = seed

    def solve(self, qubo: QUBOModel) -> HybridOptimizationResult:
        start_time = time.perf_counter()

        # Classical solve via HiGHS MILP
        milp_solver = HiGHSMILPSolver()
        milp_res = milp_solver.solve_qubo(qubo)

        # Quantum solve via QAOA on Qiskit Aer
        qaoa_engine = QAOAEngine(
            depth_p=self.depth_p,
            shots=self.shots,
            seed=self.seed
        )
        qaoa_res = qaoa_engine.solve(qubo, known_ground_energy=milp_res.objective_value)

        consensus = (milp_res.optimal_bitstring == qaoa_res.optimal_bitstring)
        gap = BenchmarkMetricsCalculator.calculate_gap(
            qaoa_res.best_sampled_energy,
            milp_res.objective_value
        )
        approx_ratio = BenchmarkMetricsCalculator.calculate_approx_ratio(
            qaoa_res.best_sampled_energy,
            milp_res.objective_value
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return HybridOptimizationResult(
            problem_name=qubo.problem_name,
            num_variables=qubo.num_variables,
            variable_names=qubo.variable_names,
            classical_solution={
                "solver": "SciPy HiGHS MILP",
                "bitstring": milp_res.optimal_bitstring,
                "vector": milp_res.optimal_vector,
                "objective_value": milp_res.objective_value,
                "solve_time_ms": milp_res.solve_time_ms,
                "status": milp_res.status,
            },
            quantum_solution={
                "solver": f"QAOA (p={self.depth_p}) on Qiskit Aer",
                "bitstring": qaoa_res.optimal_bitstring,
                "vector": qaoa_res.optimal_vector,
                "best_sampled_energy": qaoa_res.best_sampled_energy,
                "expected_energy": qaoa_res.expected_energy,
                "ground_state_probability": qaoa_res.ground_state_probability,
                "solve_time_ms": qaoa_res.solve_time_ms,
                "circuit_metadata": qaoa_res.circuit_metadata,
                "trajectory": [
                    {
                        "iteration": pt.iteration,
                        "energy": pt.energy,
                        "gammas": pt.gammas,
                        "betas": pt.betas,
                    }
                    for pt in qaoa_res.trajectory
                ],
                "top_measurements": qaoa_res.top_measurements,
            },
            consensus_reached=consensus,
            optimality_gap_pct=gap,
            approximation_ratio=approx_ratio,
            total_execution_time_ms=round(elapsed_ms, 2),
        )

