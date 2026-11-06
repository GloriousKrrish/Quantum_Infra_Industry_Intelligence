"""
resource_allocation.py - Construction Equipment & Resource Scheduling Optimization.

Models allocation of specialized capital machinery (tower cranes, piling rigs,
concrete transit mixers) across active construction sites under capacity limits
and temporal collision penalties.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from ..qubo.qubo_model import QUBOModel


@dataclass
class ConstructionSiteJob:
    id: str
    site_name: str
    required_equipment: str
    priority_weight: float
    duration_days: int
    cost_per_day: float


@dataclass
class EquipmentUnit:
    id: str
    equipment_type: str
    efficiency_multiplier: float
    daily_lease_cost: float


class ResourceAllocationBuilder:
    """
    Formulates bipartite matching and resource scheduling QUBO models.
    """

    def __init__(
        self,
        jobs: List[ConstructionSiteJob],
        equipment_units: List[EquipmentUnit],
        one_to_one_penalty: float = 150.0,
    ):
        if not jobs or not equipment_units:
            raise ValueError("Must provide at least one job and one equipment unit.")

        self.jobs = jobs
        self.units = equipment_units
        self.penalty = one_to_one_penalty
        self.n_jobs = len(jobs)
        self.n_units = len(equipment_units)
        # Binary variables: x_{j, u} = 1 if equipment u assigned to job j
        self.total_vars = self.n_jobs * self.n_units

    def _var_index(self, job_idx: int, unit_idx: int) -> int:
        return job_idx * self.n_units + unit_idx

    def to_qubo(self) -> QUBOModel:
        """
        QUBO formulation:
          Objective: Minimize total cost = sum_{j, u} (JobCost - PriorityBenefit) * x_{j, u}
          Constraints:
            Each job should have exactly one equipment: P * (sum_u x_{j, u} - 1)^2
            Each equipment unit can serve at most one job: P * sum_{j < k} x_{j, u} * x_{k, u}
        """
        N = self.total_vars
        P = self.penalty
        Q = np.zeros((N, N), dtype=float)
        offset = 0.0

        var_names = []
        for j in range(self.n_jobs):
            for u in range(self.n_units):
                var_names.append(f"assign_J{self.jobs[j].id}_U{self.units[u].id}")

        # 1. Base costs and job assignment penalties
        for j in range(self.n_jobs):
            job = self.jobs[j]
            # Each job j has constraint: (sum_u x_{j, u} - 1)^2 = sum_u x_{j, u} + 2 sum_{u < v} x_{j, u} x_{j, v} - 2 sum_u x_{j, u} + 1
            # Diag: P * (1 - 2) = -P
            offset += P * 1.0

            for u in range(self.n_units):
                unit = self.units[u]
                idx = self._var_index(j, u)

                # Cost term: lease cost adjusted by priority
                type_match = (1.0 if job.required_equipment == unit.equipment_type else 5.0)
                cost = (job.cost_per_day + unit.daily_lease_cost) * type_match - job.priority_weight * 20.0

                Q[idx, idx] += cost - P  # diagonal includes -P from constraint expansion

            # Job constraint off-diagonals: 2 * P * x_{j, u} * x_{j, v}
            for u in range(self.n_units):
                for v in range(u + 1, self.n_units):
                    idx1 = self._var_index(j, u)
                    idx2 = self._var_index(j, v)
                    Q[idx1, idx2] += 2.0 * P

        # 2. Equipment unit exclusivity: at most one job per unit
        # P * sum_{j < k} x_{j, u} * x_{k, u}
        for u in range(self.n_units):
            for j in range(self.n_jobs):
                for k in range(j + 1, self.n_jobs):
                    idx1 = self._var_index(j, u)
                    idx2 = self._var_index(k, u)
                    Q[idx1, idx2] += P

        return QUBOModel(
            matrix=Q,
            offset=offset,
            variable_names=var_names,
            problem_name=f"Construction Resource Allocation ({self.n_jobs} jobs, {self.n_units} units)",
            metadata={
                "n_jobs": self.n_jobs,
                "n_units": self.n_units,
                "penalty": P,
            }
        )
