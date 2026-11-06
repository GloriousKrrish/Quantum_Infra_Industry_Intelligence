"""
test_optimization_engine.py - Comprehensive Scientific Test Suite for Phase 04.

Tests:
  - QUBO Model and canonicalization
  - QUBO Validator
  - QUBO ⇄ Ising Bidirectional Converter and SparsePauliOp mapping
  - Classical Solvers (HiGHS MILP, Brute-Force, Greedy, Simulated Annealing)
  - QAOA Engine (Qiskit Aer classical CPU simulation, depth p=1,2, convergence trajectory)
  - Optimization Problem Library (Knapsack, Portfolio, Facility Location, Resource Allocation)
  - Hybrid Runner and Benchmarking Suite
  - FastAPI /api/optimization/* REST Endpoints
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.engines.optimization.qubo.qubo_model import QUBOModel
from backend.app.engines.optimization.qubo.qubo_validator import QUBOValidator
from backend.app.engines.optimization.qubo.qubo_ising_converter import (
    qubo_to_ising,
    ising_to_qubo,
    verify_qubo_ising_equivalence,
    IsingModel,
)
from backend.app.engines.optimization.classical import (
    HiGHSMILPSolver,
    BruteForceSolver,
    GreedySolver,
    SimulatedAnnealingSolver,
)
from backend.app.engines.optimization.quantum import (
    QAOAEngine,
    QAOACircuitBuilder,
    ParameterStrategy,
    MeasurementDecoder,
)
from backend.app.engines.optimization.problems import (
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
from backend.app.engines.optimization.hybrid import (
    BenchmarkRunner,
    HybridOptimizer,
    BenchmarkMetricsCalculator,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_qubo_2var():
    # Min at x=[0, 1] with E = -4 + 5 = 1.0
    # x=[0, 0] -> 5.0
    # x=[1, 0] -> -3 + 5 = 2.0
    # x=[1, 1] -> -3 - 4 + 4 + 5 = 2.0
    Q = np.array([[-3.0, 2.0], [2.0, -4.0]])
    return QUBOModel(matrix=Q, offset=5.0, variable_names=["x0", "x1"])


@pytest.fixture
def sample_qubo_4var():
    # 4-variable problem
    Q = np.array([
        [-5.0,  2.0,  1.0,  0.0],
        [ 0.0, -4.0,  3.0,  1.0],
        [ 0.0,  0.0, -6.0,  2.0],
        [ 0.0,  0.0,  0.0, -3.0],
    ])
    return QUBOModel(matrix=Q, offset=10.0)


# =========================================================================
# 1. QUBO Model & Validator Tests
# =========================================================================

def test_qubo_canonicalization(sample_qubo_2var):
    qubo = sample_qubo_2var
    upper = qubo.to_upper_triangular()
    sym = qubo.to_symmetric()

    assert np.allclose(np.tril(upper.matrix, -1), 0.0)
    assert np.allclose(sym.matrix, sym.matrix.T)

    for bstr in ["00", "01", "10", "11"]:
        e_orig = qubo.evaluate_energy(bstr)
        e_up = upper.evaluate_energy(bstr)
        e_sym = sym.evaluate_energy(bstr)
        assert np.isclose(e_orig, e_up)
        assert np.isclose(e_orig, e_sym)


def test_qubo_validator(sample_qubo_4var):
    val = QUBOValidator.validate(sample_qubo_4var)
    assert val.is_valid is True
    assert val.num_variables == 4
    assert val.is_finite is True
    assert val.min_eigenvalue is not None


# =========================================================================
# 2. Bidirectional Ising Converter Tests
# =========================================================================

def test_qubo_ising_conversion_and_equivalence(sample_qubo_4var):
    qubo = sample_qubo_4var
    ising = qubo_to_ising(qubo)
    assert ising.num_spins == 4

    # Mathematical equivalence check
    is_equiv = verify_qubo_ising_equivalence(qubo, ising, samples=16)
    assert is_equiv is True

    # Round trip conversion
    qubo_rec = ising_to_qubo(ising)
    assert qubo_rec.num_variables == 4
    for _ in range(10):
        x = np.random.randint(0, 2, size=4)
        assert np.isclose(qubo.evaluate_energy(x), qubo_rec.evaluate_energy(x))


def test_ising_sparse_pauli_op(sample_qubo_2var):
    ising = qubo_to_ising(sample_qubo_2var)
    op = ising.to_sparse_pauli_op()
    assert op.num_qubits == 2
    pauli_list = op.to_list()
    assert len(pauli_list) > 0


# =========================================================================
# 3. Classical Solvers Suite Tests
# =========================================================================

def test_highs_milp_solver(sample_qubo_2var):
    solver = HiGHSMILPSolver()
    res = solver.solve_qubo(sample_qubo_2var)

    assert res.success is True
    assert res.optimal_bitstring == "01"
    assert np.isclose(res.objective_value, 1.0)
    assert res.solve_time_ms > 0


def test_brute_force_solver(sample_qubo_2var):
    solver = BruteForceSolver(max_variables=10)
    res = solver.solve(sample_qubo_2var)

    assert res.optimal_bitstring == "01"
    assert np.isclose(res.minimum_energy, 1.0)
    assert res.total_states_evaluated == 4


def test_greedy_solver(sample_qubo_4var):
    solver = GreedySolver(n_restarts=5, seed=42)
    res = solver.solve_qubo(sample_qubo_4var)

    assert len(res.optimal_bitstring) == 4
    assert np.isfinite(res.objective_value)


def test_simulated_annealing_solver(sample_qubo_4var):
    solver = SimulatedAnnealingSolver(seed=42)
    res = solver.solve(sample_qubo_4var)

    assert len(res.optimal_bitstring) == 4
    assert len(res.trajectory) > 0
    assert np.isfinite(res.minimum_energy)


# =========================================================================
# 4. QAOA Engine Tests (Qiskit Aer Simulation)
# =========================================================================

def test_qaoa_circuit_builder(sample_qubo_2var):
    ising = qubo_to_ising(sample_qubo_2var)
    builder = QAOACircuitBuilder(ising, depth_p=1)
    meta = builder.get_circuit_metadata()

    assert meta.num_qubits == 2
    assert meta.depth_p == 1
    assert meta.num_parameters == 2


def test_qaoa_engine_execution(sample_qubo_2var):
    engine = QAOAEngine(depth_p=1, shots=1000, maxiter=20, seed=42)
    res = engine.solve(sample_qubo_2var, known_ground_energy=1.0)

    assert res.depth_p == 1
    assert res.optimal_bitstring == "01"
    assert np.isclose(res.best_sampled_energy, 1.0)
    assert res.ground_state_probability > 0.0
    assert len(res.trajectory) > 0
    assert "No quantum physical device" in res.hardware_disclaimer


# =========================================================================
# 5. Problem Library Tests
# =========================================================================

def test_knapsack_problem():
    items = [
        KnapsackItem("1", "A", 10.0, 5.0),
        KnapsackItem("2", "B", 15.0, 10.0),
        KnapsackItem("3", "C", 20.0, 8.0),
    ]
    builder = KnapsackProblemBuilder(items, capacity=13.0)
    qubo = builder.to_qubo()

    assert qubo.num_variables > 3  # items + slack
    milp = HiGHSMILPSolver()
    sol = milp.solve_qubo(qubo)
    assert sol.success is True


def test_portfolio_problem():
    assets = [
        RealEstateAsset("h1", "Hinjewadi IT", 18.0, 4.0, 0.3, "Hinjewadi"),
        RealEstateAsset("w1", "Wakad Hub", 15.0, 3.0, 0.2, "Wakad"),
        RealEstateAsset("b1", "Baner Res", 14.0, 5.0, 0.2, "Baner"),
    ]
    builder = RealEstatePortfolioBuilder(assets, total_budget_cr=8.0)
    qubo = builder.to_qubo()

    milp = HiGHSMILPSolver()
    sol = milp.solve_qubo(qubo)
    assert sol.success is True


def test_facility_location_problem():
    sites = [
        CandidateSite("s1", "Site 1", 18.5, 73.8, 10.0, 50.0),
        CandidateSite("s2", "Site 2", 18.6, 73.9, 12.0, 50.0),
    ]
    demands = [
        DemandPoint("d1", "Demand 1", 18.55, 73.85, 1.0),
    ]
    builder = FacilityLocationBuilder(sites, demands, num_facilities_to_open=1)
    qubo = builder.to_qubo()

    milp = HiGHSMILPSolver()
    sol = milp.solve_qubo(qubo)
    assert sol.success is True


def test_resource_allocation_problem():
    jobs = [ConstructionSiteJob("j1", "Job 1", "crane", 2.0, 5, 1.0)]
    units = [EquipmentUnit("u1", "crane", 1.0, 1.0)]
    builder = ResourceAllocationBuilder(jobs, units)
    qubo = builder.to_qubo()

    milp = HiGHSMILPSolver()
    sol = milp.solve_qubo(qubo)
    assert sol.success is True


# =========================================================================
# 6. Hybrid & Benchmarking Tests
# =========================================================================

def test_hybrid_optimizer(sample_qubo_2var):
    opt = HybridOptimizer(depth_p=1, shots=500, seed=42)
    res = opt.solve(sample_qubo_2var)

    assert res.consensus_reached is True
    assert res.optimality_gap_pct == 0.0
    assert res.approximation_ratio == 1.0


def test_benchmark_runner(sample_qubo_2var):
    runner = BenchmarkRunner(seed=42)
    report = runner.run_benchmark(sample_qubo_2var, run_qaoa_p2=False, qaoa_shots=500, qaoa_maxiter=15)

    assert len(report.solvers) >= 4
    assert np.isclose(report.exact_ground_energy, 1.0)


# =========================================================================
# 7. FastAPI Endpoint Integration Tests
# =========================================================================

def test_api_optimization_health(client):
    res = client.get("/api/optimization/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert "Qiskit Aer" in data["simulation_backend"]


def test_api_problems_build(client):
    res = client.post("/api/optimization/problems/build", json={
        "problem_type": "portfolio",
        "parameters": {"budget_cr": 10.0}
    })
    assert res.status_code == 200
    data = res.json()
    assert data["problem_type"] == "portfolio"
    assert len(data["qubo"]["matrix"]) > 0


def test_api_qubo_validate(client, sample_qubo_2var):
    res = client.post("/api/optimization/qubo/validate", json={
        "matrix": sample_qubo_2var.matrix.tolist(),
        "offset": sample_qubo_2var.offset,
        "variable_names": sample_qubo_2var.variable_names,
        "problem_name": sample_qubo_2var.problem_name,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True


def test_api_solve_classical(client, sample_qubo_2var):
    res = client.post("/api/optimization/solve/classical", json={
        "qubo": {
            "matrix": sample_qubo_2var.matrix.tolist(),
            "offset": sample_qubo_2var.offset,
            "variable_names": sample_qubo_2var.variable_names,
            "problem_name": sample_qubo_2var.problem_name,
        },
        "solver": "milp"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["optimal_bitstring"] == "01"
    assert np.isclose(data["objective_value"], 1.0)


def test_api_solve_qaoa(client, sample_qubo_2var):
    res = client.post("/api/optimization/solve/qaoa", json={
        "qubo": {
            "matrix": sample_qubo_2var.matrix.tolist(),
            "offset": sample_qubo_2var.offset,
            "variable_names": sample_qubo_2var.variable_names,
            "problem_name": sample_qubo_2var.problem_name,
        },
        "depth_p": 1,
        "shots": 500,
        "maxiter": 15,
        "seed": 42
    })
    assert res.status_code == 200
    data = res.json()
    assert data["optimal_bitstring"] == "01"
    assert np.isclose(data["best_sampled_energy"], 1.0)
    assert len(data["top_measurements"]) > 0
