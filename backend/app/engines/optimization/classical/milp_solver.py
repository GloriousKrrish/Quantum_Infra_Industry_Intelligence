"""
milp_solver.py - Exact Mixed-Integer Linear Programming Solver via SciPy HiGHS.

Provides mathematically verified exact solving for 0/1 integer linear programs
and linearized QUBO models using scipy.optimize.milp (HiGHS backend).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import time
from scipy.optimize import milp, LinearConstraint, Bounds

from ..qubo.qubo_model import QUBOModel


@dataclass
class MILPSolution:
    """Structured result from SciPy HiGHS MILP solver."""
    status: str
    success: bool
    optimal_bitstring: str
    optimal_vector: List[int]
    objective_value: float
    optimality_gap: float
    iterations: int
    nodes_explored: int
    solve_time_ms: float
    solver_name: str = "SciPy HiGHS (Branch and Bound)"
    extra_metadata: Dict[str, Any] = field(default_factory=dict)


class HiGHSMILPSolver:
    """
    Exact classical solver utilizing SciPy's HiGHS branch-and-bound solver.
    Solves 0/1 integer programs and linearized QUBO models.
    """

    def __init__(self, time_limit_sec: float = 30.0, mip_rel_gap: float = 1e-6):
        self.time_limit_sec = time_limit_sec
        self.mip_rel_gap = mip_rel_gap

    def solve_linear_problem(
        self,
        c: np.ndarray,
        A_ub: Optional[np.ndarray] = None,
        b_ub: Optional[np.ndarray] = None,
        A_eq: Optional[np.ndarray] = None,
        b_eq: Optional[np.ndarray] = None,
        variable_names: Optional[List[str]] = None,
    ) -> MILPSolution:
        """
        Solve min c^T x subject to:
          A_ub x <= b_ub
          A_eq x == b_eq
          x_i in {0, 1}
        """
        start_time = time.perf_counter()
        n = len(c)
        c = np.asarray(c, dtype=float)

        # 0/1 binary integrality: 1 indicates integer variable
        integrality = np.ones(n, dtype=int)
        bounds = Bounds(lb=np.zeros(n), ub=np.ones(n))

        constraints = []
        if A_ub is not None and b_ub is not None and len(b_ub) > 0:
            A_ub = np.asarray(A_ub, dtype=float)
            b_ub = np.asarray(b_ub, dtype=float)
            # -inf <= A_ub x <= b_ub
            constraints.append(LinearConstraint(A_ub, -np.inf, b_ub))

        if A_eq is not None and b_eq is not None and len(b_eq) > 0:
            A_eq = np.asarray(A_eq, dtype=float)
            b_eq = np.asarray(b_eq, dtype=float)
            # b_eq <= A_eq x <= b_eq
            constraints.append(LinearConstraint(A_eq, b_eq, b_eq))

        options = {
            "time_limit": self.time_limit_sec,
            "mip_rel_gap": self.mip_rel_gap,
            "disp": False
        }

        try:
            res = milp(
                c=c,
                integrality=integrality,
                bounds=bounds,
                constraints=constraints if constraints else None,
                options=options
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if res.success and res.x is not None:
                x_rounded = np.round(res.x[:n]).astype(int).tolist()
                bitstring = "".join(str(b) for b in x_rounded)
                gap = float(getattr(res, "mip_gap", 0.0) or 0.0)
                iterations = int(getattr(res, "mip_node_count", 0) or 0)

                return MILPSolution(
                    status="OPTIMAL" if res.status == 0 else f"STATUS_{res.status}",
                    success=True,
                    optimal_bitstring=bitstring,
                    optimal_vector=x_rounded,
                    objective_value=float(res.fun),
                    optimality_gap=gap,
                    iterations=int(getattr(res, "simplex_nit", 0) or 0),
                    nodes_explored=iterations,
                    solve_time_ms=elapsed_ms,
                    extra_metadata={"highs_message": res.message}
                )
            else:
                return MILPSolution(
                    status=f"FAILED_{res.status}",
                    success=False,
                    optimal_bitstring="",
                    optimal_vector=[],
                    objective_value=float("inf"),
                    optimality_gap=1.0,
                    iterations=0,
                    nodes_explored=0,
                    solve_time_ms=elapsed_ms,
                    extra_metadata={"highs_message": getattr(res, "message", "Solver failed")}
                )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return MILPSolution(
                status=f"ERROR: {str(e)}",
                success=False,
                optimal_bitstring="",
                optimal_vector=[],
                objective_value=float("inf"),
                optimality_gap=1.0,
                iterations=0,
                nodes_explored=0,
                solve_time_ms=elapsed_ms,
                extra_metadata={"exception": str(e)}
            )

    def solve_qubo(self, qubo: QUBOModel) -> MILPSolution:
        """
        Solve QUBO: min x^T Q x + c_0 for x in {0, 1}^n by exact linearization.
        Uses McCormick envelopes:
          For each pair i < j with Q_ij != 0:
            Introduce y_ij in [0, 1]
            y_ij <= x_i
            y_ij <= x_j
            y_ij >= x_i + x_j - 1
            replace Q_ij * x_i * x_j with Q_ij * y_ij
        """
        start_time = time.perf_counter()
        n = qubo.n_variables
        Q_sym = qubo.to_symmetric_matrix()
        c0 = qubo.constant_offset

        # Find off-diagonal terms
        pair_terms: List[Tuple[int, int, float]] = []
        for i in range(n):
            for j in range(i + 1, n):
                val = float(Q_sym[i, j] + Q_sym[j, i])
                if abs(val) > 1e-9:
                    pair_terms.append((i, j, val))

        m = len(pair_terms)
        total_vars = n + m

        # Objective vector
        # First n variables are x_i with linear weights Q_ii
        # Next m variables are y_ij with weights 2 * Q_ij
        c_obj = np.zeros(total_vars, dtype=float)
        for i in range(n):
            c_obj[i] = float(Q_sym[i, i])
        for idx, (i, j, val) in enumerate(pair_terms):
            c_obj[n + idx] = val

        # Integrality:
        # x_i are binary {0, 1}
        # y_ij can be continuous [0, 1] because at binary x_i, x_j the McCormick envelope is exact!
        integrality = np.zeros(total_vars, dtype=int)
        integrality[:n] = 1

        bounds = Bounds(lb=np.zeros(total_vars), ub=np.ones(total_vars))

        # McCormick constraints:
        # 1) y_ij - x_i <= 0
        # 2) y_ij - x_j <= 0
        # 3) -y_ij + x_i + x_j <= 1
        num_constraints = 3 * m
        if num_constraints > 0:
            A_ub = np.zeros((num_constraints, total_vars), dtype=float)
            b_ub = np.zeros(num_constraints, dtype=float)

            for k, (i, j, _) in enumerate(pair_terms):
                y_idx = n + k
                # 1) y_ij - x_i <= 0
                A_ub[3 * k + 0, y_idx] = 1.0
                A_ub[3 * k + 0, i] = -1.0
                b_ub[3 * k + 0] = 0.0

                # 2) y_ij - x_j <= 0
                A_ub[3 * k + 1, y_idx] = 1.0
                A_ub[3 * k + 1, j] = -1.0
                b_ub[3 * k + 1] = 0.0

                # 3) x_i + x_j - y_ij <= 1
                A_ub[3 * k + 2, i] = 1.0
                A_ub[3 * k + 2, j] = 1.0
                A_ub[3 * k + 2, y_idx] = -1.0
                b_ub[3 * k + 2] = 1.0

            constraints = [LinearConstraint(A_ub, -np.inf, b_ub)]
        else:
            constraints = None

        options = {
            "time_limit": self.time_limit_sec,
            "mip_rel_gap": self.mip_rel_gap,
            "disp": False
        }

        try:
            res = milp(
                c=c_obj,
                integrality=integrality,
                bounds=bounds,
                constraints=constraints,
                options=options
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if res.success and res.x is not None:
                x_bits = np.round(res.x[:n]).astype(int).tolist()
                bitstring = "".join(str(b) for b in x_bits)
                raw_obj = float(res.fun) + c0

                # Verify exact energy with qubo evaluate
                exact_energy = qubo.evaluate(bitstring)

                return MILPSolution(
                    status="OPTIMAL" if res.status == 0 else f"STATUS_{res.status}",
                    success=True,
                    optimal_bitstring=bitstring,
                    optimal_vector=x_bits,
                    objective_value=exact_energy,
                    optimality_gap=float(getattr(res, "mip_gap", 0.0) or 0.0),
                    iterations=int(getattr(res, "simplex_nit", 0) or 0),
                    nodes_explored=int(getattr(res, "mip_node_count", 0) or 0),
                    solve_time_ms=elapsed_ms,
                    extra_metadata={
                        "linearized_auxiliary_vars": m,
                        "highs_message": res.message
                    }
                )
            else:
                return MILPSolution(
                    status=f"FAILED_{res.status}",
                    success=False,
                    optimal_bitstring="",
                    optimal_vector=[],
                    objective_value=float("inf"),
                    optimality_gap=1.0,
                    iterations=0,
                    nodes_explored=0,
                    solve_time_ms=elapsed_ms,
                    extra_metadata={"highs_message": getattr(res, "message", "Solver failed")}
                )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return MILPSolution(
                status=f"ERROR: {str(e)}",
                success=False,
                optimal_bitstring="",
                optimal_vector=[],
                objective_value=float("inf"),
                optimality_gap=1.0,
                iterations=0,
                nodes_explored=0,
                solve_time_ms=elapsed_ms,
                extra_metadata={"exception": str(e)}
            )
