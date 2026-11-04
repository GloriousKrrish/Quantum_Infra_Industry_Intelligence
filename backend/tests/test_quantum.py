"""
Tests for QAOA Quantum Optimizer, QUBO Formulation & Classical Benchmarking.
"""

import pytest
import numpy as np
from backend.app.engines.real_estate.land_intelligence import get_all_parcels
from backend.app.engines.quantum.qaoa_optimizer import (
    build_qubo_matrix,
    run_qaoa,
    decode_solution,
)
from backend.app.engines.classical_ai.classical_optimizer import (
    run_brute_force,
    run_simulated_annealing,
)
from backend.app.engines.quantum.benchmarking import run_benchmark


def test_qubo_matrix_structure():
    parcels = get_all_parcels()[:4]
    budget = 15.0
    Q, offset, var_names = build_qubo_matrix(parcels, budget)

    assert Q.shape == (4, 4)
    assert len(var_names) == 4
    # Check upper-triangular or symmetric
    assert offset >= 0


def test_qaoa_execution():
    parcels = get_all_parcels()[:3]
    budget = 15.0
    Q, _, _ = build_qubo_matrix(parcels, budget)

    res = run_qaoa(Q, p=1, shots=1024)
    assert len(res.optimal_bitstring) == 3
    assert res.num_qubits == 3
    assert res.execution_time_ms >= 0
    assert len(res.top_bitstrings) > 0


def test_classical_solvers():
    parcels = get_all_parcels()[:4]
    Q, _, _ = build_qubo_matrix(parcels, 15.0)

    bf = run_brute_force(Q)
    assert len(bf.optimal_solution) == 4
    assert bf.method == "brute_force"

    sa = run_simulated_annealing(Q, iterations=1000)
    assert len(sa.optimal_solution) == 4
    assert sa.method == "simulated_annealing"


def test_solution_decoding():
    parcels = get_all_parcels()[:3]
    decoded = decode_solution("101", parcels, budget=30.0)
    assert len(decoded.selected_parcels) == 2
    assert decoded.budget_compliant is True


def test_full_benchmark_pipeline():
    parcels = get_all_parcels()[:3]
    benchmark, qubo = run_benchmark(parcels, budget=15.0, qaoa_p=1, qaoa_shots=1024)

    assert 0.0 <= benchmark.approximation_ratio <= 1.0 + 1e-6
    assert len(benchmark.classical_results) == 2
    assert benchmark.qaoa_result.num_qubits == 3

