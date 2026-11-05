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
    price_per_acre_crore: Optional[float] = Field(
        default=None, description="Calculated asking price per acre in ₹ Crore"
    )
    verification_status: str = Field(
        default="PMRDA Public Cadastral Baseline",
        description="Data verification status (e.g. Cadastral Verified, Demonstration, Preliminary)",
    )
    surrounding_notes: Optional[str] = Field(
        default=None, description="Brief contextual summary of immediate surroundings"
    )


class InfrastructureProximityPoint(BaseModel):
    """Proximity measurement to a specific real-world infrastructure anchor."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Facility or infrastructure name")
    facility_type: str = Field(
        ...,
        description="Type: Highway, Hospital, Education, Railway, Airport, Commercial Hub",
    )
    distance_km: float = Field(..., ge=0, description="Haversine distance in kilometres")
    drive_time_min: int = Field(..., ge=0, description="Estimated drive time in minutes")
    coordinates: List[float] = Field(..., description="[Latitude, Longitude]")
    data_source: str = Field(
        default="OpenStreetMap GIS & PMRDA Regional Master Plan",
        description="Geographic verification source",
    )


class ParcelInfrastructureAnalysis(BaseModel):
    """Detailed multi-sector infrastructure proximity and readiness analysis."""

    model_config = ConfigDict(from_attributes=True)

    parcel_id: str
    parcel_name: str
    coordinates: List[float] = Field(..., description="[Latitude, Longitude]")
    nearest_highway: InfrastructureProximityPoint
    nearest_hospital: InfrastructureProximityPoint
    nearest_education: InfrastructureProximityPoint
    nearest_railway: InfrastructureProximityPoint
    nearest_airport: InfrastructureProximityPoint
    nearest_commercial_hub: InfrastructureProximityPoint
    all_proximity_points: List[InfrastructureProximityPoint] = Field(default_factory=list)
    accessibility_score: float = Field(..., ge=0, le=100, description="Composite score out of 100")
    power_grid_status: str
    water_network_status: str
    sewage_network_status: str
    road_connectivity_status: str
    data_source: str = Field(
        default="OpenStreetMap GIS & IS 1172/CPHEEO Engineering Standards",
        description="Attribution for infrastructure data",
    )


class FeasibilityScenarioRequest(BaseModel):
    """Configurable parameters for development feasibility evaluation."""

    model_config = ConfigDict(from_attributes=True)

    development_type: str = Field(
        default="mixed",
        description="Typology: residential, commercial, industrial, mixed",
    )
    custom_target_fsi: Optional[float] = Field(
        default=None, gt=0, le=5.0, description="Optional custom FSI/FAR"
    )
    custom_construction_cost_sqft: Optional[float] = Field(
        default=None, gt=0, description="Construction cost per sq.ft in ₹"
    )
    projected_selling_price_sqft: Optional[float] = Field(
        default=None, gt=0, description="Projected realization per sq.ft in ₹"
    )


class FeasibilityScenarioResult(BaseModel):
    """Comprehensive development feasibility metrics and preliminary cost estimation."""

    model_config = ConfigDict(from_attributes=True)

    development_type: str
    permissible_fsi: float
    land_area_sqft: float
    built_up_area_sqft: float
    construction_cost_per_sqft: float
    land_acquisition_cost_crore: float
    construction_cost_crore: float
    infra_and_approvals_cost_crore: float
    contingency_cost_crore: float
    total_project_cost_crore: float
    projected_selling_price_sqft: float
    projected_gdv_crore: float = Field(..., description="Gross Development Value in ₹ Crore")
    estimated_margin_crore: float
    roi_pct: float
    estimated_duration_months: int
    infrastructure_requirements: List[str]
    development_constraints: List[str]
    disclaimer: str = Field(
        default="Preliminary feasibility estimate based on typical PMRDA benchmarks. Does not constitute statutory FSI approval or sanctioned development permit.",
        description="Legal and regulatory disclaimer",
    )


class FinancialScenarioItem(BaseModel):
    """Single financial scenario (conservative, baseline, or optimistic)."""

    model_config = ConfigDict(from_attributes=True)

    scenario_name: str
    projected_gdv_crore: float
    total_project_cost_crore: float
    net_profit_crore: float
    margin_pct: float
    roi_pct: float
    assumptions_summary: str


class CashFlowYear(BaseModel):
    """Annual capital outflow and inflow projection."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    milestone: str
    outflow_crore: float
    inflow_crore: float
    net_cashflow_crore: float


class FinancialAnalysisResponse(BaseModel):
    """Comprehensive financial scenario modeling and cash flow timeline."""

    model_config = ConfigDict(from_attributes=True)

    parcel_id: str
    parcel_name: str
    land_cost_crore: float
    baseline_scenario: FeasibilityScenarioResult
    scenarios: Dict[str, FinancialScenarioItem]
    cashflow_timeline: List[CashFlowYear]
    break_even_sales_pct: float
    assumptions: Dict[str, object]


class QuantumParticipationInfo(BaseModel):
    """Status and metrics of parcel participation in quantum portfolio optimization."""

    model_config = ConfigDict(from_attributes=True)

    parcel_id: str
    parcel_name: str
    is_eligible: bool = Field(default=True)
    utility_score: float
    budget_consumption_crore: float
    risk_factor: float
    included_in_baseline_qaoa: bool
    qaoa_solution_bitstring: str
    optimization_notes: str = Field(
        default="Mathematical participation in QAOA QUBO Hamiltonian. Eligibility does not imply statutory or financial clearance."
    )


class ParcelDetailedProfile(BaseModel):
    """Master structured profile combining cadastral, geographic, infrastructure, feasibility, and quantum metadata."""

    model_config = ConfigDict(from_attributes=True)

    parcel: LandParcel
    price_per_acre_crore: float
    verification_status: str
    data_source: str
    geographic_summary: Dict[str, object]
    infrastructure_summary: InfrastructureReport
    infrastructure_analysis: ParcelInfrastructureAnalysis
    feasibility: FeasibilityScenarioResult
    financials: FinancialAnalysisResponse
    quantum_participation: QuantumParticipationInfo


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
    optimal_parameters: Optional[Dict[str, List[float]]] = Field(
        default=None, description="Optimal variational parameters: gammas and betas"
    )


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
