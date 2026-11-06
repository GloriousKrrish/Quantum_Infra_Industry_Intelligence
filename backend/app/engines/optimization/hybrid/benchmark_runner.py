"""
benchmark_runner.py - Head-to-Head Quantum vs Classical Benchmark Runner.

Executes all solvers on the identical QUBO model under controlled seeds:
  1. SciPy HiGHS MILP (exact provable benchmark)
  2. Brute Force (exact combinatorial benchmark for n <= 18)
  3. Greedy Local Search (O(n log n) heuristic baseline)
  4. Simulated Annealing (Metropolis heuristic baseline)
  5. QAOA Depth p=1 (Qiskit Aer classical simulation)
  6. QAOA Depth p=2 (Qiskit Aer classical simulation)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np
import time

from ..qubo.qubo_model import QUBOModel
from ..classical.milp_solver import HiGHSMILPSolver
from ..classical.brute_force_solver import BruteForceSolver
from ..classical.greedy_solver import GreedySolver
from ..classical.simulated_annealing import SimulatedAnnealingSolver
from ..quantum.qaoa_engine import QAOAEngine
from .performance_metrics import BenchmarkMetricsCalculator, SolverBenchmarkEntry


@dataclass
class BenchmarkReport:
    problem_name: str
    num_variables: int
    exact_ground_energy: float
    exact_ground_bitstring: str
    solvers: List[SolverBenchmarkEntry]
    summary_findings: List[str]
    total_benchmark_time_ms: float
    scientific_disclaimer: str = (
        "Quantum results are obtained via local classical CPU simulation using Qiskit Aer 0.18.2. "
        "No quantum physical device or hardware advantage is claimed."
    )


class BenchmarkRunner:
    """
    Executes automated benchmarks across classical and quantum solvers.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed

    def run_benchmark(
        self,
        qubo: QUBOModel,
        run_qaoa_p2: bool = True,
        qaoa_shots: int = 2048,
        qaoa_maxiter: int = 40,
    ) -> BenchmarkReport:
        total_start = time.perf_counter()
        n = qubo.num_variables
        results: List[SolverBenchmarkEntry] = []

        # 1. Exact Ground Truth via HiGHS MILP
        milp_solver = HiGHSMILPSolver()
        milp_res = milp_solver.solve_qubo(qubo)
        exact_energy = milp_res.objective_value
        exact_bitstring = milp_res.optimal_bitstring

        results.append(
            SolverBenchmarkEntry(
                solver_name="SciPy HiGHS MILP (Exact)",
                is_quantum=False,
                status=milp_res.status,
                optimal_bitstring=milp_res.optimal_bitstring,
                energy=milp_res.objective_value,
                optimality_gap_pct=0.0,
                approximation_ratio=1.0,
                solve_time_ms=round(milp_res.solve_time_ms, 2),
                iterations=milp_res.iterations,
                feasibility_status="PROVABLY_OPTIMAL",
                hardware_note="Classical CPU (HiGHS Branch-and-Cut)",
                metadata={"simplex_iterations": milp_res.iterations},
            )
        )

        # 2. Brute Force (if n <= 18)
        if n <= 18:
            bf_solver = BruteForceSolver(max_variables=18)
            bf_res = bf_solver.solve(qubo)
            results.append(
                SolverBenchmarkEntry(
                    solver_name="Exact Brute Force",
                    is_quantum=False,
                    status="COMPLETED",
                    optimal_bitstring=bf_res.optimal_bitstring,
                    energy=bf_res.minimum_energy,
                    optimality_gap_pct=BenchmarkMetricsCalculator.calculate_gap(bf_res.minimum_energy, exact_energy),
                    approximation_ratio=BenchmarkMetricsCalculator.calculate_approx_ratio(bf_res.minimum_energy, exact_energy),
                    solve_time_ms=round(bf_res.solve_time_ms, 2),
                    iterations=bf_res.total_states_evaluated,
                    feasibility_status="PROVABLY_OPTIMAL",
                    hardware_note="Classical CPU (Exhaustive Search 2^n)",
                    metadata={"states_evaluated": bf_res.total_states_evaluated, "degeneracy": bf_res.degeneracy},
                )
            )

        # 3. Greedy Local Search
        greedy_solver = GreedySolver(n_restarts=10, seed=self.seed)
        greedy_res = greedy_solver.solve_qubo(qubo)
        results.append(
            SolverBenchmarkEntry(
                solver_name="Greedy Local Search",
                is_quantum=False,
                status="COMPLETED",
                optimal_bitstring=greedy_res.optimal_bitstring,
                energy=greedy_res.objective_value,
                optimality_gap_pct=BenchmarkMetricsCalculator.calculate_gap(greedy_res.objective_value, exact_energy),
                approximation_ratio=BenchmarkMetricsCalculator.calculate_approx_ratio(greedy_res.objective_value, exact_energy),
                solve_time_ms=round(greedy_res.solve_time_ms, 2),
                iterations=greedy_res.iterations,
                feasibility_status="HEURISTIC",
                hardware_note="Classical CPU (Multi-restart Coordinate Descent)",
                metadata={"restarts": greedy_res.restarts},
            )
        )

        # 4. Simulated Annealing
        sa_solver = SimulatedAnnealingSolver(seed=self.seed)
        sa_res = sa_solver.solve(qubo)
        results.append(
            SolverBenchmarkEntry(
                solver_name="Simulated Annealing",
                is_quantum=False,
                status="COMPLETED",
                optimal_bitstring=sa_res.optimal_bitstring,
                energy=sa_res.minimum_energy,
                optimality_gap_pct=BenchmarkMetricsCalculator.calculate_gap(sa_res.minimum_energy, exact_energy),
                approximation_ratio=BenchmarkMetricsCalculator.calculate_approx_ratio(sa_res.minimum_energy, exact_energy),
                solve_time_ms=round(sa_res.solve_time_ms, 2),
                iterations=sa_res.steps_total,
                feasibility_status="HEURISTIC",
                hardware_note="Classical CPU (Metropolis-Hastings)",
                metadata={"steps_accepted": sa_res.steps_accepted},
            )
        )

        # 5. QAOA (p=1)
        qaoa_p1 = QAOAEngine(depth_p=1, shots=qaoa_shots, maxiter=qaoa_maxiter, seed=self.seed)
        qaoa_p1_res = qaoa_p1.solve(qubo, known_ground_energy=exact_energy)
        results.append(
            SolverBenchmarkEntry(
                solver_name="QAOA (Depth p=1)",
                is_quantum=True,
                status=qaoa_p1_res.status,
                optimal_bitstring=qaoa_p1_res.optimal_bitstring,
                energy=qaoa_p1_res.best_sampled_energy,
                optimality_gap_pct=BenchmarkMetricsCalculator.calculate_gap(qaoa_p1_res.best_sampled_energy, exact_energy),
                approximation_ratio=BenchmarkMetricsCalculator.calculate_approx_ratio(qaoa_p1_res.best_sampled_energy, exact_energy),
                solve_time_ms=round(qaoa_p1_res.solve_time_ms, 2),
                iterations=qaoa_p1_res.iterations,
                feasibility_status="QUANTUM_APPROXIMATION",
                hardware_note="Qiskit Aer 0.18.2 CPU Simulation (Statevector + Shots)",
                metadata={
                    "expected_energy": qaoa_p1_res.expected_energy,
                    "ground_state_probability": qaoa_p1_res.ground_state_probability,
                    "shots": qaoa_p1_res.shots,
                },
            )
        )

        # 6. QAOA (p=2, if requested)
        if run_qaoa_p2:
            qaoa_p2 = QAOAEngine(depth_p=2, shots=qaoa_shots, maxiter=qaoa_maxiter, seed=self.seed)
            qaoa_p2_res = qaoa_p2.solve(qubo, known_ground_energy=exact_energy)
            results.append(
                SolverBenchmarkEntry(
                    solver_name="QAOA (Depth p=2)",
                    is_quantum=True,
                    status=qaoa_p2_res.status,
                    optimal_bitstring=qaoa_p2_res.optimal_bitstring,
                    energy=qaoa_p2_res.best_sampled_energy,
                    optimality_gap_pct=BenchmarkMetricsCalculator.calculate_gap(qaoa_p2_res.best_sampled_energy, exact_energy),
                    approximation_ratio=BenchmarkMetricsCalculator.calculate_approx_ratio(qaoa_p2_res.best_sampled_energy, exact_energy),
                    solve_time_ms=round(qaoa_p2_res.solve_time_ms, 2),
                    iterations=qaoa_p2_res.iterations,
                    feasibility_status="QUANTUM_APPROXIMATION",
                    hardware_note="Qiskit Aer 0.18.2 CPU Simulation (Statevector + Shots)",
                    metadata={
                        "expected_energy": qaoa_p2_res.expected_energy,
                        "ground_state_probability": qaoa_p2_res.ground_state_probability,
                        "shots": qaoa_p2_res.shots,
                    },
                )
            )

        total_elapsed_ms = (time.perf_counter() - total_start) * 1000.0

        # Scientific findings synthesis
        findings = [
            f"Exact global minimum is {exact_energy:.4f} found by SciPy HiGHS MILP.",
            f"QAOA (p=1) achieved best energy {qaoa_p1_res.best_sampled_energy:.4f} with ground-state probability {qaoa_p1_res.ground_state_probability * 100:.1f}%.",
        ]
        if run_qaoa_p2:
            p2_entry = results[-1]
            findings.append(
                f"QAOA (p=2) achieved best energy {p2_entry.energy:.4f} with ground-state probability {p2_entry.metadata['ground_state_probability'] * 100:.1f}%."
            )

        return BenchmarkReport(
            problem_name=qubo.problem_name,
            num_variables=n,
            exact_ground_energy=exact_energy,
            exact_ground_bitstring=exact_bitstring,
            solvers=results,
            summary_findings=findings,
            total_benchmark_time_ms=round(total_elapsed_ms, 2),
        )
