"""
optimization.py - Pydantic v2 Schemas for Optimization & Quantum Research Engine.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class QUBOPayload(BaseModel):
    matrix: List[List[float]] = Field(..., description="Square 2D QUBO matrix Q")
    offset: float = Field(0.0, description="Scalar constant offset c_0")
    variable_names: List[str] = Field(default_factory=list, description="Labels for decision variables")
    problem_name: str = Field("QUBO Problem", description="Descriptive identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary domain metadata")


class ProblemBuildRequest(BaseModel):
    problem_type: str = Field(
        ...,
        description="'knapsack', 'portfolio', 'facility_location', or 'resource_allocation'"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Domain parameters specific to problem type"
    )


class ProblemBuildResponse(BaseModel):
    problem_type: str
    qubo: QUBOPayload
    num_variables: int
    variable_names: List[str]
    linear_coefficients: Dict[str, float]
    quadratic_interactions: List[Dict[str, Any]]
    milp_summary: Optional[Dict[str, Any]] = None


class QUBOValidateResponse(BaseModel):
    is_valid: bool
    num_variables: int
    is_symmetric: bool
    is_finite: bool
    condition_number: Optional[float] = None
    min_eigenvalue: Optional[float] = None
    max_eigenvalue: Optional[float] = None
    dynamic_range_db: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)


class IsingConvertResponse(BaseModel):
    num_spins: int
    h_linear: List[float]
    J_quadratic: List[List[float]]
    offset: float
    variable_names: List[str]
    pauli_terms: List[Dict[str, Any]]
    verified_equivalent: bool


class SolveClassicalRequest(BaseModel):
    qubo: QUBOPayload
    solver: str = Field(
        "milp",
        description="'milp', 'brute_force', 'greedy', or 'simulated_annealing'"
    )
    seed: Optional[int] = Field(42, description="Random seed for stochastic solvers")


class ClassicalSolutionResponse(BaseModel):
    solver_name: str
    status: str
    optimal_bitstring: str
    optimal_vector: List[int]
    objective_value: float
    solve_time_ms: float
    iterations: int
    optimality_gap: Optional[float] = 0.0
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class SolveQAOARequest(BaseModel):
    qubo: QUBOPayload
    depth_p: int = Field(1, ge=1, le=5, description="QAOA circuit layer depth (1 to 5)")
    shots: int = Field(2048, ge=100, le=10000, description="Measurement shots on simulator")
    optimizer_name: str = Field("COBYLA", description="COBYLA, Nelder-Mead, or SLSQP")
    strategy: str = Field("linear_ramp", description="linear_ramp, random, or fourier")
    maxiter: int = Field(50, ge=5, le=200, description="Classical optimizer max iterations")
    seed: Optional[int] = Field(42, description="Seed for simulator and parameter initialization")


class QAOAIterationPointSchema(BaseModel):
    iteration: int
    energy: float
    gammas: List[float]
    betas: List[float]


class MeasurementItemSchema(BaseModel):
    bitstring: str
    counts: int
    probability: float
    energy: float
    is_ground_state: bool


class QAOASolutionResponse(BaseModel):
    status: str
    success: bool
    depth_p: int
    shots: int
    optimizer_name: str
    iterations: int
    optimal_gammas: List[float]
    optimal_betas: List[float]
    optimal_bitstring: str
    optimal_vector: List[int]
    best_sampled_bitstring: Optional[str] = None
    most_frequent_bitstring: Optional[str] = None
    best_sampled_energy: float
    most_frequent_energy: Optional[float] = None
    expected_energy: float
    ground_state_probability: float
    is_verified_ground_state: Optional[bool] = False
    approximation_ratio: Optional[float] = None
    solve_time_ms: float
    circuit_metadata: Dict[str, Any]
    trajectory: List[QAOAIterationPointSchema]
    top_measurements: List[MeasurementItemSchema]
    hardware_disclaimer: str


class SolveHybridRequest(BaseModel):
    qubo: QUBOPayload
    depth_p: int = Field(1, ge=1, le=3)
    shots: int = Field(2048, ge=100, le=8192)
    seed: Optional[int] = Field(42)


class HybridOptimizationResponse(BaseModel):
    problem_name: str
    num_variables: int
    variable_names: List[str]
    classical_solution: Dict[str, Any]
    quantum_solution: Dict[str, Any]
    consensus_reached: bool
    optimality_gap_pct: float
    approximation_ratio: float
    total_execution_time_ms: float
    hardware_disclaimer: str


class BenchmarkRequest(BaseModel):
    qubo: Optional[QUBOPayload] = None
    problem_preset: Optional[str] = Field(
        None,
        description="Optional problem preset: 'portfolio_pune', 'knapsack_infra', or 'facility_pune'"
    )
    run_qaoa_p2: bool = Field(True, description="Whether to include depth p=2 QAOA")
    shots: int = Field(2048, ge=500, le=8192)
    maxiter: int = Field(40, ge=10, le=100)
    seed: Optional[int] = Field(42)


class BenchmarkSolverEntrySchema(BaseModel):
    solver_name: str
    is_quantum: bool
    status: str
    optimal_bitstring: str
    best_bitstring: Optional[str] = None
    energy: float
    bitstring_evaluated_energy: Optional[float] = None
    absolute_optimality_gap: Optional[float] = None
    optimality_gap_pct: float
    approximation_ratio: float
    solve_time_ms: float
    iterations: int
    feasibility_status: str
    hardware_note: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BenchmarkResponse(BaseModel):
    problem_name: str
    num_variables: int
    exact_ground_energy: float
    exact_ground_bitstring: str
    solvers: List[BenchmarkSolverEntrySchema]
    summary_findings: List[str]
    total_benchmark_time_ms: float
    scientific_disclaimer: str


class OptimizationHealthResponse(BaseModel):
    status: str
    qiskit_version: str
    qiskit_aer_version: str
    scipy_version: str
    numpy_version: str
    supported_solvers: List[str]
    supported_problem_types: List[str]
    simulation_backend: str
    hardware_disclaimer: str

