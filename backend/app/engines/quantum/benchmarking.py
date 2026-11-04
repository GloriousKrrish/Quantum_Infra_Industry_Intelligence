"""
Benchmarking Engine — QAOA vs Classical.

Runs the QAOA optimizer alongside brute-force and simulated annealing
on the same QUBO instance, then computes comparative metrics including
the approximation ratio.
"""

from __future__ import annotations

import numpy as np
from typing import List

from backend.app.models.schemas import (
    BenchmarkComparison,
    LandParcel,
    QUBOProblem,
)
from backend.app.engines.quantum.qaoa_optimizer import (
    build_qubo_matrix,
    run_qaoa,
    decode_solution,
    qubo_to_qubo_problem,
)
from backend.app.engines.classical_ai.classical_optimizer import (
    run_brute_force,
    run_simulated_annealing,
)


def run_benchmark(
    parcels: List[LandParcel],
    budget: float,
    qaoa_p: int = 2,
    qaoa_shots: int = 4096,
    lambda1: float = 10.0,
    lambda2: float = 1.0,
) -> tuple[BenchmarkComparison, QUBOProblem]:
    """
    Execute a full benchmark: QAOA + Brute Force + Simulated Annealing.

    Args:
        parcels:    Candidate parcels.
        budget:     Budget constraint in ₹ Crore.
        qaoa_p:     QAOA circuit depth parameter.
        qaoa_shots: Number of measurement shots.
        lambda1:    Budget penalty weight.
        lambda2:    Risk diversification weight.

    Returns:
        (BenchmarkComparison, QUBOProblem) tuple.
    """
    # ── 1. Build QUBO ─────────────────────────────────────────────────
    Q, offset, var_names = build_qubo_matrix(
        parcels, budget, lambda1=lambda1, lambda2=lambda2,
    )
    qubo_problem = qubo_to_qubo_problem(Q, offset, var_names)

    # ── 2. Run QAOA ───────────────────────────────────────────────────
    qaoa_result = run_qaoa(Q, p=qaoa_p, shots=qaoa_shots)

    # ── 3. Run classical baselines ────────────────────────────────────
    bf_result = run_brute_force(Q)
    sa_result = run_simulated_annealing(Q)

    # ── 4. Decode solutions ───────────────────────────────────────────
    qaoa_decoded = decode_solution(qaoa_result.optimal_bitstring, parcels, budget)
    bf_decoded = decode_solution(bf_result.optimal_solution, parcels, budget)

    # ── 5. Compute approximation ratio ────────────────────────────────
    # Ratio = E_qaoa / E_exact
    # For minimisation: ratio ≤ 1 means QAOA found same or worse (higher
    # energy).  We define it so 1.0 = exact match.
    exact_val = bf_result.optimal_value
    qaoa_val = qaoa_result.optimal_value

    if abs(exact_val) < 1e-12:
        # Edge case: exact solution is zero
        approx_ratio = 1.0 if abs(qaoa_val) < 1e-12 else 0.0
    else:
        # For minimisation problems with negative optima (utility max):
        # ratio = exact / qaoa if both negative (higher ratio = closer)
        approx_ratio = exact_val / qaoa_val if abs(qaoa_val) > 1e-12 else 0.0
        # Clamp to [0, 1]
        approx_ratio = max(0.0, min(1.0, approx_ratio))

    benchmark = BenchmarkComparison(
        qaoa_result=qaoa_result,
        classical_results=[bf_result, sa_result],
        qaoa_decoded=qaoa_decoded,
        classical_decoded=bf_decoded,
        approximation_ratio=round(approx_ratio, 6),
        budget_compliance=qaoa_decoded.budget_compliant,
    )

    return benchmark, qubo_problem
