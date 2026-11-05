"""
API routes for quantum optimization and benchmarking.
"""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np
from fastapi import APIRouter, HTTPException, Path

from backend.app.models.schemas import (
    BenchmarkComparison,
    CircuitSimulateRequest,
    CircuitSimulateResponse,
    ExperimentTemplate,
    GateSpec,
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
from backend.app.engines.quantum.gate_library import (
    get_all_gate_specs,
    get_gate_spec,
)
from backend.app.engines.quantum.circuit_engine import CircuitValidationError
from backend.app.engines.quantum.simulation_engine import simulate_circuit
from backend.app.engines.quantum.experiment_library import (
    get_all_experiments,
    get_experiment_by_id,
)

router = APIRouter(prefix="/api/quantum", tags=["Quantum Computing & Optimization"])


# ═══════════════════════════════════════════════════════════════════════
# 1. PHASE 02: QUANTUM COMPUTING FOUNDATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.get(
    "/gates",
    response_model=List[GateSpec],
    summary="Get library of supported quantum gates",
    description="Returns mathematical matrices, LaTeX representations, and metadata for single and multi-qubit gates.",
)
async def list_quantum_gates() -> List[Dict[str, Any]]:
    """Return all registered quantum gates."""
    return get_all_gate_specs()


@router.get(
    "/gates/{gate_id}",
    response_model=GateSpec,
    summary="Get specification for a single quantum gate",
    description="Returns unitary matrix and physical action for a single gate by ID (e.g. 'H', 'CX', 'RX').",
)
async def get_quantum_gate(
    gate_id: str = Path(..., description="Unique gate symbol (e.g. 'H', 'CX', 'RZ')"),
) -> Dict[str, Any]:
    """Return specification for a single gate."""
    spec = get_gate_spec(gate_id)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Quantum gate '{gate_id}' not found in gate library.")
    return spec


@router.post(
    "/circuit/simulate",
    response_model=CircuitSimulateResponse,
    summary="Simulate quantum circuit on Qiskit Aer",
    description=(
        "Executes a user-defined circuit on Qiskit Aer. Returns full complex statevector amplitudes, "
        "shot-based measurement counts, and scientifically accurate per-qubit reduced density matrices & Bloch vectors."
    ),
)
async def simulate_user_circuit(
    req: CircuitSimulateRequest,
) -> Dict[str, Any]:
    """Execute quantum circuit and return statevector and measurements."""
    try:
        raw_ops = [op.model_dump() for op in req.operations]
        result = simulate_circuit(
            num_qubits=req.num_qubits,
            operations=raw_ops,
            shots=req.shots,
        )
        return result
    except CircuitValidationError as cve:
        raise HTTPException(status_code=422, detail=str(cve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Quantum simulation error: {str(exc)}")


@router.get(
    "/experiments",
    response_model=List[ExperimentTemplate],
    summary="List pre-loaded reproducible quantum experiments",
    description="Returns catalog of 10 verified experiments including Bell states, GHZ state, interference, and teleportation.",
)
async def list_quantum_experiments() -> List[Dict[str, Any]]:
    """Return catalog of pre-loaded experiments."""
    return get_all_experiments()


@router.get(
    "/experiments/{exp_id}",
    response_model=ExperimentTemplate,
    summary="Get single experiment details and circuit",
    description="Returns the circuit operations, mathematical formula, and expected state for a given experiment ID.",
)
async def get_quantum_experiment(
    exp_id: str = Path(..., description="Experiment identifier (e.g. 'exp_bell_phi_plus')"),
) -> Dict[str, Any]:
    """Return a single experiment by ID."""
    exp = get_experiment_by_id(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{exp_id}' not found.")
    return exp


# ═══════════════════════════════════════════════════════════════════════
# 2. EXISTING QAOA REAL ESTATE OPTIMIZATION ENDPOINTS (PRESERVED)
# ═══════════════════════════════════════════════════════════════════════


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
