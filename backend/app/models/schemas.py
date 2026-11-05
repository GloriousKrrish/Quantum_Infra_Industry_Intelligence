"""
Pydantic v2 data models for Quantum Estate X.

All domain objects — land parcels, infrastructure reports, QUBO problems,
QAOA/classical results, benchmarks, and the full workflow response — are
defined here as strict, validated schemas.

Phase 1.7 Data Trust Framework:
Enforces rigorous data provenance tracking, verification tiers, coordinate
validation, and explicit methodological labeling across all geospatial and
financial entities.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════
# 0. DATA TRUST & PROVENANCE FRAMEWORK (PHASE 1.7)
# ═══════════════════════════════════════════════════════════════════════

class VerificationStatus(str, Enum):
    """Formal verification tiers for all platform data points."""

    VERIFIED_OFFICIAL = "VERIFIED_OFFICIAL"          # Authoritative government or cadastral survey record
    VERIFIED_OPEN_DATA = "VERIFIED_OPEN_DATA"        # Externally verified open geodata (e.g. OpenStreetMap geodetic nodes)
    USER_PROVIDED = "USER_PROVIDED"                  # Supplied directly by client or developer input
    ESTIMATED = "ESTIMATED"                          # Derived mathematically or via standard engineering models
    SYNTHETIC = "SYNTHETIC"                          # Calibrated demonstration data for algorithmic simulation
    UNVERIFIED = "UNVERIFIED"                        # Field data pending ground-truthing
    UNAVAILABLE = "UNAVAILABLE"                      # Data field unavailable or sensor offline


class ParcelGeometryType(str, Enum):
    """Classification of parcel boundary spatial representation."""

    POINT_CENTROID = "POINT_CENTROID"                         # WGS-84 coordinate centroid only
    APPROXIMATE_BOUND = "APPROXIMATE_BOUND"                   # Indicative bounding perimeter
    VERIFIED_CADASTRAL_POLYGON = "VERIFIED_CADASTRAL_POLYGON" # Surveyor-certified cadastral polygon
    ILLUSTRATIVE_3D_MASSING = "ILLUSTRATIVE_3D_MASSING"       # Volumetric spatial visualization envelope


class DistanceMethodology(str, Enum):
    """Methodology used for geographic proximity calculation."""

    HAVERSINE_STRAIGHT_LINE = "HAVERSINE_STRAIGHT_LINE" # Great-circle spherical distance
    ROAD_NETWORK_ROUTING = "ROAD_NETWORK_ROUTING"       # Actual turn-by-turn road network routing
    ESTIMATED_PROXIMITY = "ESTIMATED_PROXIMITY"         # Regional zone proximity heuristic


class ProvenanceRecord(BaseModel):
    """Immutable provenance tracking record documenting the origin and trust level of data."""

    model_config = ConfigDict(from_attributes=True)

    source_name: str = Field(..., description="Organization, portal, or standard providing the data")
    source_url: Optional[str] = Field(default=None, description="Direct URL, API endpoint, or publication link")
    source_type: str = Field(
        default="Open Data",
        description="Type: Government Cadastre, OpenStreetMap Geodata, Engineering Code, Empirical Benchmark, User Input",
    )
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.ESTIMATED,
        description="Formal validation tier",
    )
    last_verified: Optional[str] = Field(
        default="2026-11-05", description="ISO-8601 date of verification or data capture"
    )
    confidence_level: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Methodologically supported confidence index (0.0 to 1.0)"
    )
    methodology_notes: Optional[str] = Field(
        default=None, description="Documentation of estimation, calculation, or survey rules"
    )


# ═══════════════════════════════════════════════════════════════════════
# 1. LAND & INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════

class LandParcel(BaseModel):
    """A single land parcel with infrastructure scores, financials, and provenance."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique parcel identifier, e.g. 'PUNE-001'")
    name: str = Field(..., description="Human-readable location name")
    location_lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude (WGS-84)")
    location_lng: float = Field(..., ge=-180.0, le=180.0, description="Longitude (WGS-84)")
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

    # Phase 1.7 Data Trust Framework Extensions
    geometry_type: ParcelGeometryType = Field(
        default=ParcelGeometryType.POINT_CENTROID,
        description="Spatial boundary classification (Point, Bound, Verified Polygon, Illustrative Massing)",
    )
    geojson_geometry: Optional[Dict[str, Any]] = Field(
        default=None,
        description="RFC 7946 GeoJSON Geometry object representing parcel coordinates or approximate polygon",
    )
    provenance: Optional[ProvenanceRecord] = Field(
        default=None,
        description="Complete data lineage and verification audit record",
    )

    @field_validator("location_lat")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError(f"Latitude must be in [-90.0, 90.0], got {v}")
        return round(v, 6)

    @field_validator("location_lng")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError(f"Longitude must be in [-180.0, 180.0], got {v}")
        return round(v, 6)


class InfrastructureProximityPoint(BaseModel):
    """Proximity measurement to a specific real-world infrastructure anchor."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Facility or infrastructure name")
    facility_type: str = Field(
        ...,
        description="Type: Highway, Hospital, Education, Railway, Airport, Commercial Hub",
    )
    distance_km: float = Field(..., ge=0, description="Calculated distance in kilometres")
    drive_time_min: int = Field(..., ge=0, description="Estimated drive time in minutes")
    coordinates: List[float] = Field(..., description="[Latitude, Longitude]")
    data_source: str = Field(
        default="OpenStreetMap GIS & PMRDA Regional Master Plan",
        description="Geographic verification source",
    )

    # Phase 1.7 Data Trust Framework Extensions
    distance_methodology: DistanceMethodology = Field(
        default=DistanceMethodology.HAVERSINE_STRAIGHT_LINE,
        description="Calculation methodology: Straight-line Haversine or Road Network Routing",
    )
    distance_label: str = Field(
        default="Straight-line distance estimate (Haversine)",
        description="Human-readable methodology disclaimer",
    )
    drive_time_label: str = Field(
        default="Estimated transit time at benchmark road speed (IRC SP-73 / IRC-106)",
        description="Methodological basis for transit time",
    )
    provenance: Optional[ProvenanceRecord] = Field(
        default=None,
        description="Audit record documenting geospatial node origin",
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

    # Phase 1.7 Methodology Disclosures
    accessibility_score_methodology: str = Field(
        default="Weighted proximity decay formula (Highway 25%, Hospital 20%, Commercial 20%, Rail 15%, Edu 10%, Air 10%)",
        description="Documented mathematical formulation for the accessibility index",
    )
    is_official_rating: bool = Field(
        default=False,
        description="Explicit disclaimer: estimated heuristic index, not an official municipal or statutory rating",
    )
    provenance: Optional[ProvenanceRecord] = Field(
        default=None,
        description="Audit record documenting infrastructure dataset lineage",
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
    regulatory_applicability_note: str = Field(
        default="FSI and permissible built-up allowances depend on road width, plot frontage, and TDR eligibility under Maharashtra Unified DCPR 2020. Parameters are configurable estimates.",
        description="Statutory context for building potential",
    )
    provenance: Optional[ProvenanceRecord] = Field(
        default=None,
        description="Audit record documenting feasibility benchmark lineage",
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
    provenance: Optional[ProvenanceRecord] = Field(
        default=None,
        description="Lineage of scenario escalation assumptions",
    )


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
    provenance: Optional[ProvenanceRecord] = Field(
        default=None,
        description="Audit record documenting financial model assumptions",
    )


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
    provenance_audit: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed audit summary of verified, estimated, and synthetic data fields",
    )
    data_trust_tier: VerificationStatus = Field(
        default=VerificationStatus.ESTIMATED,
        description="Overall trust tier of the composite dossier",
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


# ═══════════════════════════════════════════════════════════════════════
# 5. PHASE 02 QUANTUM FOUNDATION SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class GateOperationSchema(BaseModel):
    """Single quantum gate operation in a user-designed circuit."""

    model_config = ConfigDict(from_attributes=True)

    gate: str = Field(..., description="Gate identifier: H, X, Y, Z, S, T, RX, RY, RZ, CX, CZ, SWAP, CCX")
    targets: List[int] = Field(default_factory=list, description="Target qubit indices (0-indexed)")
    controls: List[int] = Field(default_factory=list, description="Control qubit indices (for controlled gates)")
    params: Optional[Union[Dict[str, float], List[float], float]] = Field(
        default=None, description="Angle parameter for rotation gates (Rx, Ry, Rz)"
    )


class CircuitSimulateRequest(BaseModel):
    """Request to execute a quantum circuit on the Qiskit Aer simulator."""

    model_config = ConfigDict(from_attributes=True)

    num_qubits: int = Field(default=2, ge=1, le=8, description="Number of qubits (1 to 8)")
    operations: List[GateOperationSchema] = Field(
        default_factory=list, description="Sequential gate operations to execute"
    )
    shots: int = Field(default=1024, ge=100, le=10000, description="Measurement sampling shots")


class ComplexNumber(BaseModel):
    """Real and imaginary parts of a complex number."""
    real: float
    imag: float


class StateAmplitude(BaseModel):
    """Statevector computational basis amplitude element."""
    index: int
    bitstring: str
    ket: str
    real: float
    imag: float
    magnitude: float
    probability: float
    phase_rad: float
    phase_deg: float


class MeasurementDistribution(BaseModel):
    """Shot-based measurement outcome count and frequency."""
    bitstring: str
    count: int
    frequency: float
    percentage: float


class BlochVectorData(BaseModel):
    """3D coordinates and magnitude of a Bloch vector."""
    x: float
    y: float
    z: float
    length: float


class SphericalCoordsData(BaseModel):
    """Spherical angles on the Bloch sphere."""
    theta_rad: float
    theta_pi: float
    phi_rad: float
    phi_pi: float


class QubitBlochInfo(BaseModel):
    """Bloch vector, purity, and reduced density matrix for an individual qubit."""
    qubit_index: int
    bloch_vector: BlochVectorData
    spherical_coords: SphericalCoordsData
    purity: float = Field(..., description="Tr(rho^2) in [0.5, 1.0]. 1.0=pure, 0.5=maximally mixed")
    state_classification: str = Field(..., description="'PURE', 'MIXED', or 'MAXIMALLY_MIXED'")
    description: str
    prob_0: float
    prob_1: float
    density_matrix: List[List[ComplexNumber]]


class CircuitSimulateResponse(BaseModel):
    """Comprehensive quantum simulation results from Qiskit Aer."""

    model_config = ConfigDict(from_attributes=True)

    num_qubits: int
    num_clbits: int
    circuit_depth: int
    total_gate_count: int
    ops_breakdown: Dict[str, int]
    is_entangled: bool
    shots_requested: int
    execution_time_ms: float
    simulator_backend: str
    statevector: List[StateAmplitude]
    top_states: List[StateAmplitude]
    measurements: List[MeasurementDistribution]
    qubit_bloch_vectors: List[QubitBlochInfo]


class GateSpec(BaseModel):
    """Metadata specification for a registered quantum gate."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    num_qubits: int
    is_parameterized: bool
    default_param: Optional[float] = None
    symbol: str
    latex: str
    description: str
    effect: str
    matrix: List[List[ComplexNumber]]


class ExperimentTemplate(BaseModel):
    """Pre-loaded reproducible quantum experiment template."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    num_qubits: int
    objective: str
    formula: str
    circuit: List[Dict[str, Any]]
    expected_state: str
    explanation: str

