"""
High-Performance Energy Evaluation & Expectation Calculation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple, Union
import numpy as np

from backend.app.engines.optimization.qubo.qubo_model import QUBOModel


def evaluate_bitstring_energy(bitstring: str, qubo: QUBOModel) -> float:
    """Evaluate QUBO energy for a single bitstring (e.g. '10101')."""
    return qubo.evaluate_energy(bitstring)


def evaluate_batch_energies(bitstrings: Sequence[str], qubo: QUBOModel) -> List[float]:
    """Evaluate QUBO energy for an array of bitstrings."""
    return [qubo.evaluate_energy(bs) for bs in bitstrings]


def compute_expectation_value(
    counts: Dict[str, int],
    qubo: QUBOModel,
) -> Tuple[float, List[Tuple[str, float, float]]]:
    """
    Compute expectation value <x|Q|x> from measurement counts:
        <E> = sum_x P(x) * E(x)
    Returns:
        (expectation_value, evaluated_solutions_sorted_by_energy)
        where each solution is (bitstring, energy, probability).
    """
    total_shots = sum(counts.values()) or 1
    solutions: List[Tuple[str, float, float]] = []
    expectation = 0.0

    for bs, count in counts.items():
        clean_bs = bs.replace(" ", "")
        energy = qubo.evaluate_energy(clean_bs)
        prob = count / total_shots
        solutions.append((clean_bs, round(energy, 6), round(prob, 6)))
        expectation += energy * prob

    # Sort ascending (minimization)
    solutions.sort(key=lambda item: item[1])
    return round(float(expectation), 6), solutions


def get_ground_state_exact(qubo: QUBOModel) -> Tuple[str, float]:
    """
    Compute the exact global minimum by exhaustive enumeration for small n (n <= 20).
    """
    n = qubo.num_variables
    if n > 20:
        raise ValueError(f"Exhaustive ground state search infeasible for n={n} > 20.")

    best_energy = float("inf")
    best_bs = "0" * n

    for idx in range(2**n):
        bs = format(idx, f"0{n}b")
        e = qubo.evaluate_energy(bs)
        if e < best_energy:
            best_energy = e
            best_bs = bs

    return best_bs, round(best_energy, 6)

