"""
portfolio.py - Real Estate Asset and Parcel Portfolio Optimization.

Models parcel investment selection under capital budget constraints,
expected ROI, risk variance, geographic correlation, and micro-market diversification.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from ..qubo.qubo_model import QUBOModel


@dataclass
class RealEstateAsset:
    id: str
    name: str
    expected_roi_pct: float
    cost_cr: float
    risk_score: float  # [0, 1] variance proxy
    micro_market: str  # e.g., "Hinjewadi", "Wakad", "Baner", "Chakan", "Kharadi"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    provenance_tier: str = "SYNTHETIC_BENCHMARK"


class RealEstatePortfolioBuilder:
    """
    Builds Markowitz-style mean-variance QUBO and MILP models for real estate parcel selection.
    """

    def __init__(
        self,
        assets: List[RealEstateAsset],
        total_budget_cr: float,
        risk_aversion: float = 0.5,
        diversification_penalty: float = 2.0,
        budget_penalty_multiplier: Optional[float] = None,
    ):
        if not assets:
            raise ValueError("Must provide at least one real estate asset.")
        if total_budget_cr <= 0:
            raise ValueError("Total budget must be positive.")

        self.assets = assets
        self.budget = float(total_budget_cr)
        self.risk_aversion = float(risk_aversion)
        self.diversification_penalty = float(diversification_penalty)
        self.n = len(assets)

        # Budget penalty
        max_ret = max(a.expected_roi_pct for a in assets)
        self.penalty = budget_penalty_multiplier if budget_penalty_multiplier is not None else (max_ret * 2.0)

    def to_milp_matrices(self) -> Dict[str, Any]:
        """
        Linearized approximation for SciPy HiGHS:
        min c^T x s.t. cost^T x <= Budget
        where c = -(expected_roi - risk_aversion * risk_score)
        """
        c = np.zeros(self.n, dtype=float)
        for i, a in enumerate(self.assets):
            c[i] = -(a.expected_roi_pct - self.risk_aversion * a.risk_score * 10.0)

        A_ub = np.array([[a.cost_cr for a in self.assets]], dtype=float)
        b_ub = np.array([self.budget], dtype=float)

        return {
            "c": c,
            "A_ub": A_ub,
            "b_ub": b_ub,
            "variable_names": [f"{a.name} ({a.micro_market})" for a in self.assets],
        }

    def to_qubo(self) -> QUBOModel:
        """
        Constructs quadratic portfolio QUBO:
          Objective = - sum mu_i x_i + lambda * sum sigma_i^2 x_i
                      + gamma * sum_{i < j, same zone} x_i x_j   (concentration penalty)
                      + P * (sum c_i x_i + slack - Budget)^2
        """
        n_assets = self.n
        B = self.budget
        costs = [a.cost_cr for a in self.assets]
        P = self.penalty

        # Generate binary slack variables for budget in increments
        # Slack represents unused budget in Cr
        max_cost = max(costs)
        # Power of 2 slack decomposition up to B
        slack_coeffs = []
        rem = B
        step = 1.0
        while step <= rem and len(slack_coeffs) < 6:
            slack_coeffs.append(step)
            rem -= step
            step *= 2.0
        if rem > 0.1 and len(slack_coeffs) < 6:
            slack_coeffs.append(round(rem, 2))

        n_slack = len(slack_coeffs)
        total_vars = n_assets + n_slack

        var_names = [f"asset_{i}_{self.assets[i].id}" for i in range(n_assets)]
        for s_idx in range(n_slack):
            var_names.append(f"budget_slack_{s_idx}")

        a = np.zeros(total_vars, dtype=float)
        a[:n_assets] = costs
        for s_idx, c_val in enumerate(slack_coeffs):
            a[n_assets + s_idx] = c_val

        Q = np.zeros((total_vars, total_vars), dtype=float)

        # 1. Asset returns and risk (diagonal)
        for i in range(n_assets):
            asset = self.assets[i]
            # Expected return reward (negative because we minimize)
            ret_term = -asset.expected_roi_pct
            # Risk variance penalty
            risk_term = self.risk_aversion * (asset.risk_score ** 2) * 10.0
            Q[i, i] += ret_term + risk_term

        # 2. Zone concentration penalty for pairs in the same micro_market
        for i in range(n_assets):
            for j in range(i + 1, n_assets):
                if self.assets[i].micro_market == self.assets[j].micro_market:
                    # Penalize selecting multiple assets in the identical micro-market
                    Q[i, j] += self.diversification_penalty

        # 3. Budget penalty expansion: P * (sum a_m x_m - B)^2
        # Diagonals: P * a_m^2 - 2 * P * B * a_m
        for m in range(total_vars):
            Q[m, m] += P * (a[m] ** 2) - 2.0 * P * B * a[m]

        # Off-diagonals: 2 * P * a_m * a_l
        for m in range(total_vars):
            for l in range(m + 1, total_vars):
                Q[m, l] += 2.0 * P * a[m] * a[l]

        c0 = P * (B ** 2)

        return QUBOModel(
            matrix=Q,
            offset=c0,
            variable_names=var_names,
            problem_name=f"Real Estate Portfolio (Budget={B}Cr)",
            metadata={
                "n_assets": n_assets,
                "n_slack": n_slack,
                "budget_cr": B,
                "risk_aversion": self.risk_aversion,
                "diversification_penalty": self.diversification_penalty,
                "provenance_tier": "SYNTHETIC_BENCHMARK",
                "data_provenance": "SYNTHETIC_BENCHMARK (Simulated indicative values for algorithmic research and benchmarking; not actual transactional registry data)",
            }
        )

