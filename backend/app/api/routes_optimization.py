"""
routes_optimization.py - Dedicated REST API Router for Quantum-Classical Optimization.

Mounts /api/optimization/* endpoints:
  - GET  /api/optimization/health
  - POST /api/optimization/problems/build
  - POST /api/optimization/qubo/validate
  - POST /api/optimization/qubo/convert
  - POST /api/optimization/solve/classical
  - POST /api/optimization/solve/qaoa
  - POST /api/optimization/solve/hybrid
  - POST /api/optimization/benchmark
"""

from typing import Dict, List, Optional, Any
import numpy as np
import scipy
import qiskit
import qiskit_aer
from fastapi import APIRouter, HTTPException, Query, status

from ..schemas.optimization import (
    QUBOPayload,
    ProblemBuildRequest,
    ProblemBuildResponse,
    QUBOValidateResponse,
    IsingConvertResponse,
    SolveClassicalRequest,
    ClassicalSolutionResponse,
    SolveQAOARequest,
    QAOASolutionResponse,
    QAOAIterationPointSchema,
    MeasurementItemSchema,
    SolveHybridRequest,
    HybridOptimizationResponse,
    BenchmarkRequest,
    BenchmarkResponse,
    BenchmarkSolverEntrySchema,
    OptimizationHealthResponse,
)
from ..engines.optimization.qubo.qubo_model import QUBOModel
from ..engines.optimization.qubo.qubo_validator import QUBOValidator
from ..engines.optimization.qubo.qubo_ising_converter import (
    qubo_to_ising,
    ising_to_qubo,
    verify_qubo_ising_equivalence,
)
from ..engines.optimization.classical import (
    HiGHSMILPSolver,
    BruteForceSolver,
    GreedySolver,
    SimulatedAnnealingSolver,
)
from ..engines.optimization.quantum import (
    QAOAEngine,
    ParameterStrategy,
)
from ..engines.optimization.problems import (
    KnapsackItem,
    KnapsackProblemBuilder,
    RealEstateAsset,
    RealEstatePortfolioBuilder,
    CandidateSite,
    DemandPoint,
    FacilityLocationBuilder,
    ConstructionSiteJob,
    EquipmentUnit,
    ResourceAllocationBuilder,
)
from ..engines.optimization.hybrid import (
    BenchmarkRunner,
    HybridOptimizer,
)


router = APIRouter(prefix="/api/optimization", tags=["Quantum-Classical Optimization"])


# =========================================================================
# Preset Problem Builders for Instant Demonstrations & Benchmarking
# =========================================================================

def _get_preset_portfolio_pune() -> QUBOModel:
    assets = [
        RealEstateAsset("hinj_1", "Hinjewadi Tech Parcel", 18.5, 4.2, 0.35, "Hinjewadi"),
        RealEstateAsset("wakad_1", "Wakad Commercial Hub", 16.0, 3.8, 0.25, "Wakad"),
        RealEstateAsset("baner_1", "Baner High Street", 14.5, 5.0, 0.20, "Baner"),
        RealEstateAsset("pcmc_1", "PCMC Industrial Park", 21.0, 6.5, 0.45, "PCMC"),
        RealEstateAsset("kharadi_1", "Kharadi Cyber Gateway", 17.0, 4.5, 0.30, "Kharadi"),
    ]
    builder = RealEstatePortfolioBuilder(assets=assets, total_budget_cr=10.0, risk_aversion=0.4)
    return builder.to_qubo()


def _get_preset_knapsack() -> QUBOModel:
    items = [
        KnapsackItem("k1", "Substation Transformer", 35.0, 10.0),
        KnapsackItem("k2", "EV DC Fast Charger Cluster", 25.0, 6.0),
        KnapsackItem("k3", "Smart Metering Hub", 18.0, 4.0),
        KnapsackItem("k4", "Rooftop Solar Battery", 28.0, 7.0),
        KnapsackItem("k5", "Stormwater Pump Unit", 15.0, 5.0),
    ]
    builder = KnapsackProblemBuilder(items=items, capacity=15.0)
    return builder.to_qubo()


def _get_preset_facility_pune() -> QUBOModel:
    sites = [
        CandidateSite("s1", "Baner Depot", 18.5590, 73.7868, 20.0, 100.0),
        CandidateSite("s2", "Wakad Depot", 18.5987, 73.7634, 18.0, 100.0),
        CandidateSite("s3", "Hinjewadi Depot", 18.5913, 73.7389, 22.0, 100.0),
        CandidateSite("s4", "PCMC Depot", 18.6275, 73.8131, 19.0, 100.0),
    ]
    demands = [
        DemandPoint("d1", "Aundh Demand", 18.5626, 73.8087, 1.5),
        DemandPoint("d2", "Balewadi Demand", 18.5756, 73.7712, 2.0),
        DemandPoint("d3", "Pimple Saudagar", 18.5987, 73.7997, 1.8),
        DemandPoint("d4", "Tathawade Demand", 18.6186, 73.7538, 1.2),
    ]
    builder = FacilityLocationBuilder(sites, demands, num_facilities_to_open=2)
    return builder.to_qubo()


# =========================================================================
# 1. Health and Capabilities
# =========================================================================

@router.get("/health", response_model=OptimizationHealthResponse)
async def optimization_health():
    """Returns software versions, supported solvers, and physical hardware disclosures."""
    return OptimizationHealthResponse(
        status="OPERATIONAL",
        qiskit_version=qiskit.__version__,
        qiskit_aer_version=qiskit_aer.__version__,
        scipy_version=scipy.__version__,
        numpy_version=np.__version__,
        supported_solvers=[
            "scipy_highs_milp",
            "brute_force",
            "greedy_local_search",
            "simulated_annealing",
            "qaoa_aer_simulator",
        ],
        supported_problem_types=[
            "knapsack",
            "portfolio",
            "facility_location",
            "resource_allocation",
        ],
        simulation_backend="Qiskit Aer CPU Statevector & Shot Simulator",
        hardware_disclaimer=(
            "Quantum optimization is simulated locally using classical CPU execution via Qiskit Aer. "
            "No quantum physical device was accessed, and no claim of quantum advantage or supremacy is made."
        ),
    )


# =========================================================================
# 2. Problem Builder
# =========================================================================

@router.post("/problems/build", response_model=ProblemBuildResponse)
async def build_problem(request: ProblemBuildRequest):
    """
    Formulates domain optimization problems into verified QUBO and MILP representations.
    """
    ptype = request.problem_type.lower()
    params = request.parameters

    try:
        if ptype == "knapsack":
            raw_items = params.get("items", [])
            if not raw_items:
                qubo = _get_preset_knapsack()
                milp_summary = {"model": "0/1 Knapsack", "capacity": 15.0}
            else:
                items = [
                    KnapsackItem(
                        id=str(it.get("id", i)),
                        name=str(it.get("name", f"Item_{i}")),
                        value=float(it["value"]),
                        weight=float(it["weight"]),
                    )
                    for i, it in enumerate(raw_items)
                ]
                builder = KnapsackProblemBuilder(
                    items=items,
                    capacity=float(params.get("capacity", 20.0)),
                    penalty_multiplier=params.get("penalty_multiplier"),
                )
                qubo = builder.to_qubo()
                milp_summary = builder.to_milp_matrices()

        elif ptype == "portfolio":
            raw_assets = params.get("assets", [])
            if not raw_assets:
                qubo = _get_preset_portfolio_pune()
                milp_summary = {"model": "Real Estate Portfolio", "budget": 10.0}
            else:
                assets = [
                    RealEstateAsset(
                        id=str(a.get("id", i)),
                        name=str(a.get("name", f"Asset_{i}")),
                        expected_roi_pct=float(a.get("expected_roi_pct", 15.0)),
                        cost_cr=float(a.get("cost_cr", 2.0)),
                        risk_score=float(a.get("risk_score", 0.3)),
                        micro_market=str(a.get("micro_market", "Pune")),
                    )
                    for i, a in enumerate(raw_assets)
                ]
                builder = RealEstatePortfolioBuilder(
                    assets=assets,
                    total_budget_cr=float(params.get("budget_cr", 10.0)),
                    risk_aversion=float(params.get("risk_aversion", 0.5)),
                    diversification_penalty=float(params.get("diversification_penalty", 2.0)),
                )
                qubo = builder.to_qubo()
                milp_summary = builder.to_milp_matrices()

        elif ptype == "facility_location":
            qubo = _get_preset_facility_pune()
            milp_summary = {"model": "Facility Location", "k_facilities": 2}

        elif ptype == "resource_allocation":
            jobs = [
                ConstructionSiteJob("j1", "Tower A Foundation", "piling_rig", 3.0, 10, 1.5),
                ConstructionSiteJob("j2", "Commercial Core Wall", "tower_crane", 2.0, 15, 2.0),
                ConstructionSiteJob("j3", "Road Grading Wakad", "excavator", 1.5, 7, 0.8),
            ]
            units = [
                EquipmentUnit("u1", "piling_rig", 1.0, 1.2),
                EquipmentUnit("u2", "tower_crane", 1.2, 1.8),
                EquipmentUnit("u3", "excavator", 1.0, 0.7),
            ]
            builder = ResourceAllocationBuilder(jobs, units)
            qubo = builder.to_qubo()
            milp_summary = {"model": "Resource Allocation", "n_jobs": 3, "n_units": 3}

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported problem type: {ptype}. Supported: knapsack, portfolio, facility_location, resource_allocation",
            )

        return ProblemBuildResponse(
            problem_type=ptype,
            qubo=QUBOPayload(
                matrix=qubo.matrix.tolist(),
                offset=qubo.offset,
                variable_names=qubo.variable_names,
                problem_name=qubo.problem_name,
                metadata=qubo.metadata,
            ),
            num_variables=qubo.num_variables,
            variable_names=qubo.variable_names,
            linear_coefficients=qubo.get_linear_coefficients(),
            quadratic_interactions=qubo.get_quadratic_interactions(),
            milp_summary={"variables_count": qubo.num_variables},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to build problem: {str(e)}",
        )


# =========================================================================
# 3. QUBO Validator
# =========================================================================

@router.post("/qubo/validate", response_model=QUBOValidateResponse)
async def validate_qubo(payload: QUBOPayload):
    """
    Validates QUBO matrix symmetry, conditioning, finiteness, and dynamic range.
    """
    qubo = QUBOModel(
        matrix=np.array(payload.matrix, dtype=float),
        offset=payload.offset,
        variable_names=payload.variable_names,
        problem_name=payload.problem_name,
        metadata=payload.metadata,
    )
    res = QUBOValidator.validate(qubo)
    return QUBOValidateResponse(
        is_valid=res.is_valid,
        num_variables=res.num_variables,
        is_symmetric=res.is_symmetric,
        is_finite=res.is_finite,
        condition_number=res.condition_number,
        min_eigenvalue=res.min_eigenvalue,
        max_eigenvalue=res.max_eigenvalue,
        dynamic_range_db=res.dynamic_range_db,
        warnings=res.warnings,
    )


# =========================================================================
# 4. QUBO to Ising Bidirectional Converter
# =========================================================================

@router.post("/qubo/convert", response_model=IsingConvertResponse)
async def convert_qubo_to_ising(payload: QUBOPayload):
    """
    Bidirectional algebraic conversion between QUBO and Ising model with Qiskit Pauli string generation.
    """
    qubo = QUBOModel(
        matrix=np.array(payload.matrix, dtype=float),
        offset=payload.offset,
        variable_names=payload.variable_names,
        problem_name=payload.problem_name,
        metadata=payload.metadata,
    )
    ising = qubo_to_ising(qubo)
    is_equiv = verify_qubo_ising_equivalence(qubo, ising, samples=16)

    # Extract non-zero Pauli terms
    op = ising.to_sparse_pauli_op()
    pauli_terms = [
        {"pauli": label, "coefficient": round(float(coeff.real), 6)}
        for label, coeff in op.to_list()
    ]

    return IsingConvertResponse(
        num_spins=ising.num_spins,
        h_linear=ising.h.tolist(),
        J_quadratic=ising.J.tolist(),
        offset=ising.offset,
        variable_names=ising.variable_names,
        pauli_terms=pauli_terms,
        verified_equivalent=is_equiv,
    )


# =========================================================================
# 5. Solve Classical
# =========================================================================

@router.post("/solve/classical", response_model=ClassicalSolutionResponse)
async def solve_classical(request: SolveClassicalRequest):
    """
    Solves QUBO using SciPy HiGHS MILP, Brute-Force, Greedy, or Simulated Annealing.
    """
    qubo = QUBOModel(
        matrix=np.array(request.qubo.matrix, dtype=float),
        offset=request.qubo.offset,
        variable_names=request.qubo.variable_names,
        problem_name=request.qubo.problem_name,
        metadata=request.qubo.metadata,
    )
    solver_choice = request.solver.lower()

    if solver_choice == "milp":
        solver = HiGHSMILPSolver()
        sol = solver.solve_qubo(qubo)
        return ClassicalSolutionResponse(
            solver_name=sol.solver_name,
            status=sol.status,
            optimal_bitstring=sol.optimal_bitstring,
            optimal_vector=sol.optimal_vector,
            objective_value=sol.objective_value,
            solve_time_ms=sol.solve_time_ms,
            iterations=sol.iterations,
            optimality_gap=sol.optimality_gap,
            extra_metadata=sol.extra_metadata,
        )

    elif solver_choice == "brute_force":
        if qubo.num_variables > 18:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brute force is restricted to n <= 18 variables (requested n={qubo.num_variables})",
            )
        solver = BruteForceSolver(max_variables=18)
        sol = solver.solve(qubo)
        return ClassicalSolutionResponse(
            solver_name=sol.solver_name,
            status="COMPLETED",
            optimal_bitstring=sol.optimal_bitstring,
            optimal_vector=sol.optimal_vector,
            objective_value=sol.minimum_energy,
            solve_time_ms=sol.solve_time_ms,
            iterations=sol.total_states_evaluated,
            optimality_gap=0.0,
            extra_metadata={"degeneracy": sol.degeneracy},
        )

    elif solver_choice == "greedy":
        solver = GreedySolver(seed=request.seed)
        sol = solver.solve_qubo(qubo)
        return ClassicalSolutionResponse(
            solver_name=sol.solver_name,
            status="COMPLETED",
            optimal_bitstring=sol.optimal_bitstring,
            optimal_vector=sol.optimal_vector,
            objective_value=sol.objective_value,
            solve_time_ms=sol.solve_time_ms,
            iterations=sol.iterations,
            optimality_gap=None,
            extra_metadata=sol.extra_metadata,
        )

    elif solver_choice == "simulated_annealing":
        solver = SimulatedAnnealingSolver(seed=request.seed)
        sol = solver.solve(qubo)
        return ClassicalSolutionResponse(
            solver_name=sol.solver_name,
            status="COMPLETED",
            optimal_bitstring=sol.optimal_bitstring,
            optimal_vector=sol.optimal_vector,
            objective_value=sol.minimum_energy,
            solve_time_ms=sol.solve_time_ms,
            iterations=sol.steps_total,
            optimality_gap=None,
            extra_metadata=sol.extra_metadata,
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown solver: {solver_choice}. Allowed: milp, brute_force, greedy, simulated_annealing",
        )


# =========================================================================
# 6. Solve QAOA
# =========================================================================

@router.post("/solve/qaoa", response_model=QAOASolutionResponse)
async def solve_qaoa(request: SolveQAOARequest):
    """
    Solves QUBO using parameterized QAOA on Qiskit Aer classical simulator.
    """
    qubo = QUBOModel(
        matrix=np.array(request.qubo.matrix, dtype=float),
        offset=request.qubo.offset,
        variable_names=request.qubo.variable_names,
        problem_name=request.qubo.problem_name,
        metadata=request.qubo.metadata,
    )

    strat_map = {
        "linear_ramp": ParameterStrategy.LINEAR_RAMP,
        "random": ParameterStrategy.RANDOM,
        "fourier": ParameterStrategy.FOURIER,
    }
    chosen_strategy = strat_map.get(request.strategy.lower(), ParameterStrategy.LINEAR_RAMP)

    # First find exact ground state via fast HiGHS MILP to compute approximation ratio
    milp = HiGHSMILPSolver()
    milp_sol = milp.solve_qubo(qubo)
    ground_truth_energy = milp_sol.objective_value

    engine = QAOAEngine(
        depth_p=request.depth_p,
        shots=request.shots,
        optimizer_name=request.optimizer_name,
        maxiter=request.maxiter,
        strategy=chosen_strategy,
        seed=request.seed,
    )
    sol = engine.solve(qubo, known_ground_energy=ground_truth_energy)

    return QAOASolutionResponse(
        status=sol.status,
        success=sol.success,
        depth_p=sol.depth_p,
        shots=sol.shots,
        optimizer_name=sol.optimizer_name,
        iterations=sol.iterations,
        optimal_gammas=sol.optimal_gammas,
        optimal_betas=sol.optimal_betas,
        optimal_bitstring=sol.optimal_bitstring,
        optimal_vector=sol.optimal_vector,
        best_sampled_energy=sol.best_sampled_energy,
        expected_energy=sol.expected_energy,
        ground_state_probability=sol.ground_state_probability,
        approximation_ratio=sol.approximation_ratio,
        solve_time_ms=sol.solve_time_ms,
        circuit_metadata=sol.circuit_metadata,
        trajectory=[
            QAOAIterationPointSchema(
                iteration=pt.iteration,
                energy=pt.energy,
                gammas=pt.gammas,
                betas=pt.betas,
            )
            for pt in sol.trajectory
        ],
        top_measurements=[
            MeasurementItemSchema(
                bitstring=m["bitstring"],
                counts=m["counts"],
                probability=m["probability"],
                energy=m["energy"],
                is_ground_state=m["is_ground_state"],
            )
            for m in sol.top_measurements
        ],
        hardware_disclaimer=sol.hardware_disclaimer,
    )


# =========================================================================
# 7. Solve Hybrid (Classical + QAOA Orchestrated)
# =========================================================================

@router.post("/solve/hybrid", response_model=HybridOptimizationResponse)
async def solve_hybrid(request: SolveHybridRequest):
    """
    Executes SciPy HiGHS MILP and QAOA side-by-side, providing direct cross-validation.
    """
    qubo = QUBOModel(
        matrix=np.array(request.qubo.matrix, dtype=float),
        offset=request.qubo.offset,
        variable_names=request.qubo.variable_names,
        problem_name=request.qubo.problem_name,
        metadata=request.qubo.metadata,
    )
    optimizer = HybridOptimizer(depth_p=request.depth_p, shots=request.shots, seed=request.seed)
    res = optimizer.solve(qubo)

    return HybridOptimizationResponse(
        problem_name=res.problem_name,
        num_variables=res.num_variables,
        variable_names=res.variable_names,
        classical_solution=res.classical_solution,
        quantum_solution=res.quantum_solution,
        consensus_reached=res.consensus_reached,
        optimality_gap_pct=res.optimality_gap_pct,
        approximation_ratio=res.approximation_ratio,
        total_execution_time_ms=res.total_execution_time_ms,
        hardware_disclaimer=res.hardware_disclaimer,
    )


# =========================================================================
# 8. Benchmark All Solvers
# =========================================================================

@router.post("/benchmark", response_model=BenchmarkResponse)
async def run_benchmark(request: BenchmarkRequest):
    """
    Runs comprehensive 5-way benchmark across MILP, Brute-Force, Greedy, SA, and QAOA.
    """
    if request.qubo is not None:
        qubo = QUBOModel(
            matrix=np.array(request.qubo.matrix, dtype=float),
            offset=request.qubo.offset,
            variable_names=request.qubo.variable_names,
            problem_name=request.qubo.problem_name,
            metadata=request.qubo.metadata,
        )
    elif request.problem_preset == "portfolio_pune":
        qubo = _get_preset_portfolio_pune()
    elif request.problem_preset == "facility_pune":
        qubo = _get_preset_facility_pune()
    else:
        qubo = _get_preset_knapsack()

    runner = BenchmarkRunner(seed=request.seed or 42)
    report = runner.run_benchmark(
        qubo=qubo,
        run_qaoa_p2=request.run_qaoa_p2,
        qaoa_shots=request.shots,
        qaoa_maxiter=request.maxiter,
    )

    return BenchmarkResponse(
        problem_name=report.problem_name,
        num_variables=report.num_variables,
        exact_ground_energy=report.exact_ground_energy,
        exact_ground_bitstring=report.exact_ground_bitstring,
        solvers=[
            BenchmarkSolverEntrySchema(
                solver_name=s.solver_name,
                is_quantum=s.is_quantum,
                status=s.status,
                optimal_bitstring=s.optimal_bitstring,
                energy=s.energy,
                optimality_gap_pct=s.optimality_gap_pct,
                approximation_ratio=s.approximation_ratio,
                solve_time_ms=s.solve_time_ms,
                iterations=s.iterations,
                feasibility_status=s.feasibility_status,
                hardware_note=s.hardware_note,
                metadata=s.metadata,
            )
            for s in report.solvers
        ],
        summary_findings=report.summary_findings,
        total_benchmark_time_ms=report.total_benchmark_time_ms,
        scientific_disclaimer=report.scientific_disclaimer,
    )
