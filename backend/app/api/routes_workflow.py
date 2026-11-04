"""
Full 9-step Pune Development Workflow endpoint.

Orchestrates the entire pipeline from parcel intelligence through
quantum optimization to final recommendation.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.models.schemas import (
    WorkflowRequest,
    WorkflowResponse,
)
from backend.app.engines.real_estate.land_intelligence import (
    get_all_parcels,
    compute_utility_score,
)
from backend.app.engines.real_estate.infrastructure_calc import (
    generate_infrastructure_report,
)
from backend.app.engines.quantum.qaoa_optimizer import (
    build_qubo_matrix,
    decode_solution,
    qubo_to_qubo_problem,
)
from backend.app.engines.quantum.benchmarking import run_benchmark

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])


@router.post(
    "/pune-development",
    response_model=WorkflowResponse,
    summary="Execute the full 9-step Pune development workflow",
    description=(
        "Step 1: Load parcel data\n"
        "Step 2: Compute infrastructure reports\n"
        "Step 3: Calculate utility scores\n"
        "Step 4: Build QUBO matrix\n"
        "Step 5: Run QAOA optimization\n"
        "Step 6: Run classical baselines\n"
        "Step 7: Compare & benchmark\n"
        "Step 8: Decode optimal portfolio\n"
        "Step 9: Generate recommendation"
    ),
)
async def pune_development_workflow(
    req: WorkflowRequest,
) -> WorkflowResponse:
    """
    Execute the full quantum-optimized Pune development workflow.

    This endpoint orchestrates every engine module in sequence:
    land intelligence → infrastructure calculation → QUBO formulation →
    QAOA solving → classical benchmarking → recommendation.
    """
    # ── Step 1: Load parcels ──────────────────────────────────────────
    parcels = get_all_parcels()
    if req.zone_filter:
        parcels = [p for p in parcels if p.zone_type == req.zone_filter]

    # ── Step 2: Infrastructure reports ────────────────────────────────
    infra_reports = [generate_infrastructure_report(p) for p in parcels]

    # ── Step 3: Utility scores (used internally by QUBO) ──────────────
    utility_scores = {p.name: compute_utility_score(p) for p in parcels}

    # ── Steps 4-7: QUBO + QAOA + Classical + Benchmark ────────────────
    benchmark, qubo_problem = run_benchmark(
        parcels,
        req.budget_crore,
        qaoa_p=req.qaoa_p,
        qaoa_shots=req.qaoa_shots,
    )

    # ── Step 8: Decode (already done in benchmark) ────────────────────
    qaoa_decoded = benchmark.qaoa_decoded
    classical_decoded = benchmark.classical_decoded

    # ── Step 9: Generate recommendation ───────────────────────────────
    recommendation = {
        "budget_requested_cr": req.budget_crore,
        "method": "QAOA (Quantum Approximate Optimization Algorithm)",
        "selected_parcels": qaoa_decoded.selected_parcels,
        "total_investment_crore": qaoa_decoded.total_cost_crore,
        "budget_remaining_crore": round(
            req.budget_crore - qaoa_decoded.total_cost_crore, 2
        ),
        "portfolio_utility_score": qaoa_decoded.total_utility,
        "budget_compliant": qaoa_decoded.budget_compliant,
        "approximation_ratio": benchmark.approximation_ratio,
        "quantum_advantage_note": (
            "QAOA achieved {:.1%} approximation ratio vs exact solution. "
            "For {} parcels, quantum approach scales polynomially while "
            "brute force scales exponentially (2^n)."
        ).format(benchmark.approximation_ratio, len(parcels)),
        "utility_breakdown": utility_scores,
        "classical_comparison": {
            "brute_force_parcels": classical_decoded.selected_parcels,
            "brute_force_cost": classical_decoded.total_cost_crore,
            "same_solution": (
                set(qaoa_decoded.selected_parcels) == set(classical_decoded.selected_parcels)
            ),
        },
    }

    return WorkflowResponse(
        parcels_evaluated=parcels,
        infrastructure_reports=infra_reports,
        qubo_formulation=qubo_problem,
        benchmark=benchmark,
        recommendation=recommendation,
    )
