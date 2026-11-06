"""
facility_location.py - P-Median Spatial Facility Location & Infrastructure Optimization.

Models optimal site selection for regional infrastructure (logistics depots,
emergency medical hubs, EV superchargers) to minimize demand-weighted travel distances
while avoiding redundant spatial proximity.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from ..qubo.qubo_model import QUBOModel


@dataclass
class CandidateSite:
    id: str
    name: str
    lat: float
    lng: float
    setup_cost: float
    capacity: float


@dataclass
class DemandPoint:
    id: str
    name: str
    lat: float
    lng: float
    demand_weight: float


class FacilityLocationBuilder:
    """
    Builds P-Median / Spatial Coverage QUBO and MILP models.
    """

    def __init__(
        self,
        candidate_sites: List[CandidateSite],
        demand_points: List[DemandPoint],
        num_facilities_to_open: int = 2,
        redundancy_penalty_radius_km: float = 3.0,
        cardinality_penalty: float = 100.0,
    ):
        if not candidate_sites:
            raise ValueError("Must provide candidate sites.")
        if not demand_points:
            raise ValueError("Must provide demand points.")
        if num_facilities_to_open <= 0 or num_facilities_to_open > len(candidate_sites):
            raise ValueError(
                f"Number of facilities to open ({num_facilities_to_open}) must be between 1 and {len(candidate_sites)}"
            )

        self.sites = candidate_sites
        self.demands = demand_points
        self.k = num_facilities_to_open
        self.radius_km = redundancy_penalty_radius_km
        self.penalty = cardinality_penalty
        self.m = len(candidate_sites)

    def _haversine_km(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        r = 6371.0  # Earth radius in km
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlam = np.radians(lng2 - lng1)
        a = np.sin(dphi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2.0)**2
        return 2.0 * r * np.arcsin(np.sqrt(a))

    def to_milp_matrices(self) -> Dict[str, Any]:
        """
        Exact MILP for site selection:
        min c^T x s.t. sum x_j == k
        where c_j = setup_cost + sum_i w_i * dist(i, j)
        """
        c = np.zeros(self.m, dtype=float)
        for j, site in enumerate(self.sites):
            demand_dist = sum(
                d.demand_weight * self._haversine_km(d.lat, d.lng, site.lat, site.lng)
                for d in self.demands
            )
            c[j] = site.setup_cost + demand_dist

        A_eq = np.ones((1, self.m), dtype=float)
        b_eq = np.array([self.k], dtype=float)

        return {
            "c": c,
            "A_eq": A_eq,
            "b_eq": b_eq,
            "variable_names": [s.name for s in self.sites],
        }

    def to_qubo(self) -> QUBOModel:
        """
        QUBO formulation:
          Objective = sum_j c_j x_j + sum_{i < j, dist < R} RedundancyPenalty * x_i x_j
                      + P * (sum x_j - k)^2
        """
        m = self.m
        k = self.k
        P = self.penalty

        # Compute single-site costs
        c = np.zeros(m, dtype=float)
        for j, site in enumerate(self.sites):
            demand_dist = sum(
                d.demand_weight * self._haversine_km(d.lat, d.lng, site.lat, site.lng)
                for d in self.demands
            )
            c[j] = site.setup_cost + demand_dist

        Q = np.zeros((m, m), dtype=float)

        # 1. Linear costs and cardinality diagonal expansion
        # P * (sum x_j - k)^2 = P * [sum x_j + 2 sum_{i<j} x_i x_j - 2 k sum x_j + k^2]
        # Diagonal: c_j + P * (1 - 2*k)
        for j in range(m):
            Q[j, j] = c[j] + P * (1.0 - 2.0 * k)

        # 2. Pairwise terms
        for i in range(m):
            for j in range(i + 1, m):
                # Cardinality interaction: 2 * P
                coupling = 2.0 * P

                # Redundancy penalty if sites are closer than radius
                dist_km = self._haversine_km(
                    self.sites[i].lat, self.sites[i].lng,
                    self.sites[j].lat, self.sites[j].lng
                )
                if dist_km < self.radius_km:
                    coupling += 50.0 * (1.0 - dist_km / max(self.radius_km, 1e-3))

                Q[i, j] = coupling

        c0 = P * (k ** 2)

        return QUBOModel(
            matrix=Q,
            offset=c0,
            variable_names=[f"site_{s.id}_{s.name}" for s in self.sites],
            problem_name=f"Spatial Facility Location (Select {k} of {m})",
            metadata={
                "n_sites": m,
                "n_demands": len(self.demands),
                "k_facilities": k,
                "radius_km": self.radius_km,
                "cardinality_penalty": P,
            }
        )

