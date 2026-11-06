"""
knapsack.py - 0/1 and Bounded Knapsack Formulation as QUBO and MILP.

Formulates:
    Maximize sum_{i=1}^n v_i x_i
    Subject to sum_{i=1}^n w_i x_i <= W, x_i in {0, 1}

Converts into an exact QUBO via binary expansion of slack variables:
    slack = sum_{k=0}^{K} 2^k s_k, where K = floor(log2(W))
    Penalty = P * (sum w_i x_i + sum 2^k s_k - W)^2
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import math

from ..core.binary_variables import VariableRegister
from ..core.problem_definition import OptimizationProblem, ProblemCategory, OptimizationSense
from ..qubo.qubo_model import QUBOModel


@dataclass
class KnapsackItem:
    id: str
    name: str
    value: float
    weight: float
    category: Optional[str] = None


class KnapsackProblemBuilder:
    """
    Builds MILP matrices and QUBO models for 0/1 Knapsack.
    """

    def __init__(
        self,
        items: List[KnapsackItem],
        capacity: float,
        penalty_multiplier: Optional[float] = None
    ):
        if capacity <= 0:
            raise ValueError(f"Knapsack capacity must be positive, got {capacity}")
        if not items:
            raise ValueError("Knapsack must have at least one item.")

        self.items = items
        self.capacity = float(capacity)
        self.n_items = len(items)

        # Automatic penalty factor P > max(v_i) to strictly enforce feasibility
        max_val = max(item.value for item in items)
        self.penalty = penalty_multiplier if penalty_multiplier is not None else (max_val * 1.5 + 1.0)

    def to_milp_matrices(self) -> Dict[str, Any]:
        """
        Standard MILP formulation for SciPy HiGHS:
        min c^T x s.t. A_ub x <= b_ub, x in {0, 1}^n
        where c = -values (since MILP minimizes).
        """
        c = np.array([-item.value for item in self.items], dtype=float)
        A_ub = np.array([[item.weight for item in self.items]], dtype=float)
        b_ub = np.array([self.capacity], dtype=float)

        return {
            "c": c,
            "A_ub": A_ub,
            "b_ub": b_ub,
            "variable_names": [item.name for item in self.items],
            "n_items": self.n_items,
        }

    def to_qubo(self) -> QUBOModel:
        """
        Exact QUBO with binary slack variable expansion.
        slack in [0, capacity]
        K = floor(log2(capacity))
        slack = sum_{k=0}^K 2^k s_k + (capacity - (2^{K+1} - 1)) s_{K+1}
        """
        W = self.capacity
        weights = [item.weight for item in self.items]
        values = [item.value for item in self.items]
        P = self.penalty

        # Compute power-of-2 slack coefficients
        slack_coeffs = []
        rem = W
        k = 0
        while 2**k <= rem:
            slack_coeffs.append(float(2**k))
            rem -= 2**k
            k += 1
        if rem > 0:
            slack_coeffs.append(float(rem))

        n_slack = len(slack_coeffs)
        total_vars = self.n_items + n_slack

        var_names = [f"item_{i}_{self.items[i].id}" for i in range(self.n_items)]
        for s_idx in range(n_slack):
            var_names.append(f"slack_{s_idx}")

        # Combined coefficients vector: a_i = weight_i for items, a_{n+k} = 2^k for slack
        a = np.zeros(total_vars, dtype=float)
        a[:self.n_items] = weights
        for s_idx, c_val in enumerate(slack_coeffs):
            a[self.n_items + s_idx] = c_val

        # QUBO expansion of P * (sum a_m x_m - W)^2 - sum v_i x_i:
        # P * [(sum a_m x_m)^2 - 2 W sum a_m x_m + W^2] - sum v_i x_i
        # (sum a_m x_m)^2 = sum a_m^2 x_m + 2 sum_{m < l} a_m a_l x_m x_l  (since x_m^2 = x_m)
        Q = np.zeros((total_vars, total_vars), dtype=float)

        # Diagonal terms: P * a_m^2 - 2 * P * W * a_m - (v_m if item else 0)
        for m in range(total_vars):
            diag = P * (a[m] ** 2) - 2.0 * P * W * a[m]
            if m < self.n_items:
                diag -= values[m]
            Q[m, m] = diag

        # Off-diagonal terms (upper triangular): 2 * P * a_m * a_l
        for m in range(total_vars):
            for l in range(m + 1, total_vars):
                Q[m, l] = 2.0 * P * a[m] * a[l]

        c0 = P * (W ** 2)

        return QUBOModel(
            matrix=Q,
            offset=c0,
            variable_names=var_names,
            problem_name=f"0/1 Knapsack (Cap={W})",
            metadata={
                "n_items": self.n_items,
                "n_slack": n_slack,
                "capacity": W,
                "penalty": P,
                "slack_coefficients": slack_coeffs,
            }
        )

