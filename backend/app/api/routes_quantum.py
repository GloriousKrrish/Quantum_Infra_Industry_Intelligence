"""
API routes for quantum optimization and benchmarking.
"""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter, Path

from backend.app.models.schemas import (
    BenchmarkComparison,
    OptimizeRequest,
    QAOAResult,
    QUBOProblem,
    SolutionDecoding,
)
from backend.app.engines.real_estate.land_intelligence import get_all_parcels
from backend.app.engines.quantum.qaoa_optimizer import (
    build_qubo_matrix,
    decode_solution,
    qubo_to_qubo_problem,
    run_qaoa,
)
from backend.app.engines.quantum.benchmarking import run_benchmark

router = APIRouter(prefix="/api/quantum", tags=["Quantum Optimization"])


@router.post(
    "/optimize",
    summary="Run QAOA optimization on parcel portfolio",
    description=(
        "Formulates the parcel selection QUBO and solves it with QAOA. "
        "Returns optimal bitstring, decoded portfolio, and QUBO details."
    ),
)
async def optimize_portfolio(
    req: OptimizeRequest,
) -> dict:
    """
    Run QAOA-based portfolio optimization.

    Steps:
    1. Fetch parcels within budget
    2. Build QUBO matrix
    3. Run QAOA
    4. Decode solution
    """
    parcels = get_all_parcels()
    if req.max_parcels:
        parcels = parcels[: req.max_parcels]

    Q, offset, var_names = build_qubo_matrix(
        parcels,
        req.budget_crore,
        lambda1=req.lambda_budget,
        lambda2=req.lambda_risk,
    )
    qubo_problem = qubo_to_qubo_problem(Q, offset, var_names)
    qaoa_result = run_qaoa(Q, p=req.qaoa_p, shots=req.qaoa_shots)
    decoded = decode_solution(qaoa_result.optimal_bitstring, parcels, req.budget_crore)

    return {
        "qaoa_result": qaoa_result,
        "qubo_formulation": qubo_problem,
        "decoded_solution": decoded,
        "budget_crore": req.budget_crore,
    }


@router.get(
    "/benchmark/{budget_crore}",
    response_model=BenchmarkComparison,
    summary="Run full QAOA vs Classical benchmark",
    description=(
        "Runs QAOA, brute-force, and simulated annealing on the same "
        "QUBO instance and returns comparative metrics."
    ),
)
async def benchmark(
    budget_crore: float = Path(..., gt=0, description="Total budget in ₹ Crore"),
) -> BenchmarkComparison:
    """Run the full benchmark suite."""
    parcels = get_all_parcels()
    comparison, _ = run_benchmark(parcels, budget_crore)
    return comparison
