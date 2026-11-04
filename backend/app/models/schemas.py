"""
Pydantic v2 data models for Quantum Estate X.

All domain objects — land parcels, infrastructure reports, QUBO problems,
QAOA/classical results, benchmarks, and the full workflow response — are
defined here as strict, validated schemas.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════════
# 1. LAND & INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════

class LandParcel(BaseModel):
    """A single land parcel with infrastructure scores and financials."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique parcel identifier, e.g. 'PUNE-001'")
    name: str = Field(..., description="Human-readable location name")
    location_lat: float = Field(..., description="Latitude (WGS-84)")
    location_lng: float = Field(..., description="Longitude (WGS-84)")
    area_acres: float = Field(..., gt=0, description="Total area in acres")
    price_crore: float = Field(..., gt=0, description="Market price in ₹ Crore")

    # Infrastructure scores (0.0 – 1.0)
    water_score: float = Field(..., ge=0, le=1)
    electricity_score: float = Field(..., ge=0, le=1)
    sewage_score: float = Field(..., ge=0, le=1)
    road_score: float = Field(..., ge=0, le=1)

    projected_return_pct: float = Field(
        ..., description="Projected annual return (%)"
    )
    zone_type: str = Field(
        default="mixed", description="Zoning: residential, commercial, industrial, mixed"
    )
    data_provenance: str = Field(
        default="Pune Municipal Corporation / IGR Maharashtra",
        description="Source attribution for the parcel data",
    )


class InfrastructureReport(BaseModel):
    """Engineering-grade infrastructure assessment for a parcel."""

    model_config = ConfigDict(from_attributes=True)

    parcel_id: str
    parcel_name: str
    water_demand_lpd: float = Field(..., description="Water demand in litres per day")
    sewage_output_lpd: float = Field(..., description="Sewage output in litres per day")
    electricity_kva: float = Field(..., description="Electricity demand in kVA")
    infra_readiness_index: float = Field(
        ..., ge=0, le=1,
        description="Composite index: 0.25W + 0.25E + 0.20S + 0.30R",
    )


# ═══════════════════════════════════════════════════════════════════════
# 2. QUANTUM / QUBO
# ═══════════════════════════════════════════════════════════════════════

class QUBOProblem(BaseModel):
    """Quadratic Unconstrained Binary Optimization problem representation."""

    model_config = ConfigDict(from_attributes=True)

    Q_matrix: List[List[float]] = Field(
        ..., description="Upper-triangular QUBO matrix (n×n)"
    )
    offset: float = Field(default=0.0, description="Constant energy offset")
    num_variables: int = Field(..., gt=0)
    variable_names: List[str] = Field(
        ..., description="Maps variable index → parcel name"
    )


class QAOAResult(BaseModel):
    """Result of a QAOA optimization run."""

    model_config = ConfigDict(from_attributes=True)

    optimal_bitstring: str = Field(..., description="Best bitstring found, e.g. '10110'")
    optimal_value: float = Field(..., description="Objective value of best solution")
    top_bitstrings: List[str] = Field(
        ..., description="Top-k bitstrings by probability"
    )
    probabilities: Dict[str, float] = Field(
        ..., description="Mapping bitstring → measurement probability"
    )
    execution_time_ms: float = Field(..., ge=0)
    circuit_depth: int = Field(..., ge=0)
    num_qubits: int = Field(..., gt=0)


class ClassicalResult(BaseModel):
    """Result of a classical optimization baseline."""

    model_config = ConfigDict(from_attributes=True)

    method: str = Field(..., description="Algorithm name, e.g. 'brute_force'")
    optimal_value: float
    optimal_solution: str = Field(
        ..., description="Optimal bitstring, e.g. '10110'"
    )
    execution_time_ms: float = Field(..., ge=0)


# ═══════════════════════════════════════════════════════════════════════
# 3. BENCHMARKING & WORKFLOW
# ═══════════════════════════════════════════════════════════════════════

class SolutionDecoding(BaseModel):
    """Decoded solution mapping bitstring → selected parcels."""

    model_config = ConfigDict(from_attributes=True)

    selected_parcels: List[str]
    total_cost_crore: float
    total_utility: float
    budget_compliant: bool


class BenchmarkComparison(BaseModel):
    """Side-by-side QAOA vs classical comparison."""

    model_config = ConfigDict(from_attributes=True)

    qaoa_result: QAOAResult
    classical_results: List[ClassicalResult]
    qaoa_decoded: SolutionDecoding
    classical_decoded: SolutionDecoding
    approximation_ratio: float = Field(
        ..., ge=0, le=1.0 + 1e-9,
        description="E_qaoa / E_exact  (1.0 = optimal)",
    )
    budget_compliance: bool


class WorkflowResponse(BaseModel):
    """Full 9-step Pune development workflow output."""

    model_config = ConfigDict(from_attributes=True)

    parcels_evaluated: List[LandParcel]
    infrastructure_reports: List[InfrastructureReport]
    qubo_formulation: QUBOProblem
    benchmark: BenchmarkComparison
    recommendation: Dict[str, object] = Field(
        ..., description="Final recommendation summary"
    )


# ═══════════════════════════════════════════════════════════════════════
# 4. REQUEST BODIES
# ═══════════════════════════════════════════════════════════════════════

class OptimizeRequest(BaseModel):
    """Request body for the quantum optimization endpoint."""

    model_config = ConfigDict(from_attributes=True)

    budget_crore: float = Field(default=40.0, gt=0)
    max_parcels: Optional[int] = Field(default=None, gt=0)
    qaoa_p: int = Field(default=2, ge=1, le=10)
    qaoa_shots: int = Field(default=4096, ge=100)
    lambda_budget: float = Field(default=10.0, gt=0)
    lambda_risk: float = Field(default=1.0, ge=0)


class WorkflowRequest(BaseModel):
    """Request body for the full Pune development workflow."""

    model_config = ConfigDict(from_attributes=True)

    budget_crore: float = Field(default=40.0, gt=0)
    zone_filter: Optional[str] = Field(default=None)
    qaoa_p: int = Field(default=2, ge=1, le=10)
    qaoa_shots: int = Field(default=4096, ge=100)
