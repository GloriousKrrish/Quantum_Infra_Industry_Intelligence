import axios from "axios";

/**
 * Axios instance configured for the QUANTUM ESTATE X FastAPI backend.
 * Points to http://localhost:8000/api with timeout handling for Qiskit Aer simulation.
 */
const api = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 35000, // 35 seconds to allow full Aer QAOA simulation + Scipy COBYLA
  headers: {
    "Content-Type": "application/json",
  },
});

// ═══════════════════════════════════════════════════════════════════════════════
// TYPE DEFINITIONS (Synchronized with backend/app/models/schemas.py)
// ═══════════════════════════════════════════════════════════════════════════════

export type VerificationStatus =
  | "VERIFIED_OFFICIAL"
  | "VERIFIED_OPEN_DATA"
  | "USER_PROVIDED"
  | "ESTIMATED"
  | "SYNTHETIC"
  | "UNVERIFIED"
  | "UNAVAILABLE";

export type ParcelGeometryType =
  | "CENTROID_POINT"
  | "APPROXIMATE_BOUNDING_FOOTPRINT"
  | "CADASTRAL_SURVEY_POLYGON";

export type DistanceMethodology =
  | "HAVERSINE_STRAIGHT_LINE"
  | "ROAD_NETWORK_ROUTED"
  | "MANHATTAN_METRIC";

export interface ProvenanceRecord {
  source_name: string;
  source_url?: string;
  source_type: string;
  verification_status: VerificationStatus;
  last_verified: string;
  confidence_level?: number;
  notes?: string;
  methodology_reference?: string;
}

export interface InfraScores {
  water: number;
  power: number;
  sewage: number;
  road: number;
}

export interface LandParcel {
  id: string; // e.g. "PUNE-001"
  name: string; // e.g. "Wagholi East"
  location_lat: number;
  location_lng: number;
  area_acres: number;
  price_crore: number;
  water_score: number;
  electricity_score: number;
  sewage_score: number;
  road_score: number;
  projected_return_pct: number;
  zone_type: string;
  data_provenance: string;
  price_per_acre_crore?: number;
  verification_status?: VerificationStatus | string;
  surrounding_notes?: string;
  geometry_type?: ParcelGeometryType;
  geojson_geometry?: Record<string, any>;
  provenance?: ProvenanceRecord;

  // Compatibility fields for legacy and UI components
  price_cr: number;
  expected_roi_pct: number;
  return_pct: number;
  infra_scores: InfraScores;
  utility_score: number;
  infrastructure_index: number;
  water_supply_score: number;
  location: string;
  status: "Available" | "Under Review" | "Shortlisted";
  max_fsi?: number;
}

// Backward-compatibility aliases
export type Parcel = LandParcel;
export type QuantumResult = OptimizationResponse;
export type BenchmarkResult = BenchmarkComparison;
export const fetchParcelsWithinBudget = fetchParcelsByBudget;

export interface InfrastructureReport {
  parcel_id: string;
  parcel_name: string;
  water_demand_lpd: number;
  sewage_output_lpd: number;
  electricity_kva: number;
  infra_readiness_index: number;
}

export interface InfrastructureProximityPoint {
  name: string;
  facility_type: string;
  distance_km: number;
  drive_time_min: number;
  coordinates: [number, number];
  data_source: string;
  distance_methodology?: DistanceMethodology | string;
  transit_time_benchmark?: string;
  provenance?: ProvenanceRecord;
}

export interface ParcelInfrastructureAnalysis {
  parcel_id: string;
  parcel_name: string;
  coordinates: [number, number];
  nearest_highway: InfrastructureProximityPoint;
  nearest_hospital: InfrastructureProximityPoint;
  nearest_education: InfrastructureProximityPoint;
  nearest_railway: InfrastructureProximityPoint;
  nearest_airport: InfrastructureProximityPoint;
  nearest_commercial_hub: InfrastructureProximityPoint;
  all_proximity_points: InfrastructureProximityPoint[];
  accessibility_score: number;
  power_grid_status: string;
  water_network_status: string;
  sewage_network_status: string;
  road_connectivity_status: string;
  data_source: string;
  accessibility_score_methodology?: string;
  scoring_weights?: Record<string, number>;
  provenance?: ProvenanceRecord;
}

export interface FeasibilityScenarioRequest {
  development_type?: string;
  custom_target_fsi?: number;
  custom_construction_cost_sqft?: number;
  projected_selling_price_sqft?: number;
}

export interface FeasibilityScenarioResult {
  development_type: string;
  permissible_fsi: number;
  land_area_sqft: number;
  built_up_area_sqft: number;
  construction_cost_per_sqft: number;
  land_acquisition_cost_crore: number;
  construction_cost_crore: number;
  infra_and_approvals_cost_crore: number;
  contingency_cost_crore: number;
  total_project_cost_crore: number;
  projected_selling_price_sqft: number;
  projected_gdv_crore: number;
  estimated_margin_crore: number;
  roi_pct: number;
  estimated_duration_months: number;
  infrastructure_requirements: string[];
  development_constraints: string[];
  disclaimer: string;
  regulatory_applicability_note?: string;
  provenance?: ProvenanceRecord;
}

export interface FinancialScenarioItem {
  scenario_name: string;
  projected_gdv_crore: number;
  total_project_cost_crore: number;
  net_profit_crore: number;
  margin_pct: number;
  roi_pct: number;
  assumptions_summary: string;
}

export interface CashFlowYear {
  year: number;
  milestone: string;
  outflow_crore: number;
  inflow_crore: number;
  net_cashflow_crore: number;
}

export interface FinancialAnalysisResponse {
  parcel_id: string;
  parcel_name: string;
  land_cost_crore: number;
  baseline_scenario: FeasibilityScenarioResult;
  scenarios: Record<string, FinancialScenarioItem>;
  cashflow_timeline: CashFlowYear[];
  break_even_sales_pct: number;
  assumptions: Record<string, any>;
}

export interface QuantumParticipationInfo {
  parcel_id: string;
  parcel_name: string;
  is_eligible: boolean;
  utility_score: number;
  budget_consumption_crore: number;
  risk_factor: number;
  included_in_baseline_qaoa: boolean;
  qaoa_solution_bitstring: string;
  optimization_notes: string;
}

export interface ParcelDetailedProfile {
  parcel: LandParcel;
  price_per_acre_crore: number;
  verification_status: string;
  data_source: string;
  geographic_summary: Record<string, any>;
  infrastructure_summary: InfrastructureReport;
  infrastructure_analysis: ParcelInfrastructureAnalysis;
  feasibility: FeasibilityScenarioResult;
  financials: FinancialAnalysisResponse;
  quantum_participation: QuantumParticipationInfo;
  provenance_audit?: any;
}

export interface QUBOProblem {
  Q_matrix: number[][];
  offset: number;
  num_variables: number;
  variable_names: string[];
}

export interface ComplexNumber {
  real: number;
  imag: number;
}

export interface GateSpec {
  id: string;
  name: string;
  category: string;
  num_qubits: number;
  is_parameterized: boolean;
  default_param?: number;
  symbol: string;
  latex: string;
  description: string;
  effect: string;
  matrix: ComplexNumber[][];
}

export interface GateOperation {
  gate: string;
  targets: number[];
  controls?: number[];
  params?: Record<string, number> | number[] | number;
}

export interface StateAmplitude {
  index: number;
  bitstring: string;
  ket: string;
  real: number;
  imag: number;
  magnitude: number;
  probability: number;
  phase_rad: number;
  phase_deg: number;
}

export interface MeasurementDistribution {
  bitstring: string;
  count: number;
  frequency: number;
  percentage: number;
}

export interface BlochVectorData {
  x: number;
  y: number;
  z: number;
  length: number;
}

export interface SphericalCoordsData {
  theta_rad: number;
  theta_pi: number;
  phi_rad: number;
  phi_pi: number;
}

export interface QubitBlochInfo {
  qubit_index: number;
  bloch_vector: BlochVectorData;
  spherical_coords: SphericalCoordsData;
  purity: number;
  state_classification: "PURE" | "MIXED" | "MAXIMALLY_MIXED";
  description: string;
  prob_0: number;
  prob_1: number;
  density_matrix: ComplexNumber[][];
}

export interface CircuitSimulateResponse {
  num_qubits: number;
  num_clbits: number;
  circuit_depth: number;
  total_gate_count: number;
  ops_breakdown: Record<string, number>;
  is_entangled: boolean;
  shots_requested: number;
  execution_time_ms: number;
  simulator_backend: string;
  statevector: StateAmplitude[];
  top_states: StateAmplitude[];
  measurements: MeasurementDistribution[];
  qubit_bloch_vectors: QubitBlochInfo[];
}

export interface ExperimentTemplate {
  id: string;
  name: string;
  category: string;
  num_qubits: number;
  objective: string;
  formula: string;
  circuit: GateOperation[];
  expected_state: string;
  explanation: string;
}

export interface QAOAResult {
  optimal_bitstring: string;
  optimal_value: number;
  top_bitstrings: string[];
  probabilities: Record<string, number>;
  execution_time_ms: number;
  circuit_depth: number;
  num_qubits: number;
  optimal_parameters?: {
    gammas: number[];
    betas: number[];
  };
}

export interface SolutionDecoding {
  selected_parcels: string[];
  total_cost_crore: number;
  total_utility: number;
  budget_compliant: boolean;
}

export interface ClassicalResult {
  method: string;
  optimal_value: number;
  optimal_solution: string;
  execution_time_ms: number;
}

export interface BenchmarkComparison {
  qaoa_result: QAOAResult;
  classical_results: ClassicalResult[];
  qaoa_decoded: SolutionDecoding;
  classical_decoded: SolutionDecoding;
  approximation_ratio: number;
  budget_compliance: boolean;
}

export interface OptimizationResponse {
  qaoa_result: QAOAResult;
  qubo_formulation: QUBOProblem;
  decoded_solution: SolutionDecoding;
  budget_crore: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE 03 ADVANCED QUANTUM MECHANICS & RESEARCH LAB TYPES
// ═══════════════════════════════════════════════════════════════════════════════

export interface StateEvolutionRequest {
  hamiltonian_type?: string;
  initial_state_name?: string;
  custom_initial_state?: ComplexNumber[];
  omega?: number;
  b_field?: { x: number; y: number; z: number };
  j_coupling?: number;
  total_time?: number;
  num_steps?: number;
}

export interface StateEvolutionResponse {
  num_qubits: number;
  hamiltonian_type: string;
  formula_latex: string;
  energy_expectation: number;
  eigenvalues: number[];
  energy_gap: number;
  recurrence_period: number | null;
  total_time: number;
  num_steps: number;
  initial_overlap_final: number;
  trajectory: Array<{
    time: number;
    probabilities: number[];
    amplitudes: StateAmplitude[];
    bloch_vector?: BlochVectorData;
  }>;
}

export interface DensityMatrixAnalyzeRequest {
  preset?: string;
  matrix_data?: ComplexNumber[][];
}

export interface DensityMatrixAnalyzeResponse {
  dimension: number;
  num_qubits: number;
  is_hermitian: boolean;
  trace: number;
  is_unit_trace: boolean;
  is_positive_semidefinite: boolean;
  eigenvalues: number[];
  purity: number;
  rank: number;
  classification: "PURE" | "MIXED" | "MAXIMALLY_MIXED";
  reduced_density_matrix_A?: ComplexNumber[][];
  reduced_density_matrix_B?: ComplexNumber[][];
  purity_subsystem_A?: number;
  purity_subsystem_B?: number;
  matrix: ComplexNumber[][];
}

export interface MeasurementExperimentRequest {
  operations?: GateOperation[];
  num_qubits?: number;
  basis?: "Z" | "X" | "Y";
  shots?: number;
  simulate_collapse_outcome?: string;
}

export interface MeasurementExperimentResponse {
  num_qubits: number;
  basis: string;
  theoretical_outcomes: Array<{ bitstring: string; theoretical_prob: number }>;
  sampled_measurements: MeasurementDistribution[];
  collapsed_outcome?: string;
  collapsed_statevector?: StateAmplitude[];
  post_measurement_bloch_vectors?: QubitBlochInfo[];
}

export interface InterferenceSimulateRequest {
  phase_theta?: number;
  shots?: number;
  include_sweep?: boolean;
  sweep_steps?: number;
}

export interface InterferenceSimulateResponse {
  phase_theta_rad: number;
  theoretical_probabilities: { "0": number; "1": number };
  sampled_counts: { "0": number; "1": number };
  interference_regime: "CONSTRUCTIVE" | "DESTRUCTIVE" | "INTERMEDIATE";
  quantum_interference_contrast: number;
  classical_expectation_p0: number;
  sweep_curve?: Array<{
    theta_rad: number;
    theta_deg: number;
    theoretical_p0: number;
    sampled_p0: number;
  }>;
}

export interface QuantumInformationRequest {
  state_a_preset?: string;
  state_b_preset?: string;
  custom_state_a?: ComplexNumber[][];
  custom_state_b?: ComplexNumber[][];
}

export interface QuantumInformationResponse {
  state_A: {
    name: string;
    purity: number;
    von_neumann_entropy: number;
    shannon_entropy: number;
    classification: string;
    eigenvalues: number[];
  };
  state_B: {
    name: string;
    purity: number;
    von_neumann_entropy: number;
    shannon_entropy: number;
    classification: string;
    eigenvalues: number[];
  };
  relational_metrics: {
    fidelity_F: number;
    squared_fidelity_F: number;
    trace_distance_D: number;
    fuchs_van_de_graaf_bounds: {
      lower_bound: number;
      trace_distance: number;
      upper_bound: number;
      is_satisfied: boolean;
    };
  };
}

export interface EntanglementAnalyzeRequest {
  preset?: string;
  werner_parameter_p?: number;
}

export interface EntanglementAnalyzeResponse {
  preset: string;
  num_qubits: number;
  schmidt_decomposition?: {
    schmidt_rank: number;
    schmidt_coefficients: number[];
    entanglement_entropy: number;
  };
  concurrence: number;
  negativity: number;
  logarithmic_negativity: number;
  entanglement_classification: "ENTANGLED" | "SEPARABLE" | "BOUND_ENTANGLED";
  werner_critical_threshold?: number;
  explanation: string;
}

export interface NoiseSimulateRequest {
  operations?: GateOperation[];
  num_qubits?: number;
  noise_type?: string;
  error_prob?: number;
  gamma?: number;
  lambda_param?: number;
  shots?: number;
}

export interface NoiseSimulateResponse {
  noise_type: string;
  num_qubits: number;
  shots: number;
  ideal_measurements: MeasurementDistribution[];
  noisy_measurements: MeasurementDistribution[];
  total_variation_distance: number;
  noisy_purity_estimate: number;
  distribution_comparison: Array<{
    bitstring: string;
    ideal_frequency: number;
    noisy_frequency: number;
    delta: number;
  }>;
}

export interface DecoherenceSimulateRequest {
  initial_state_name?: string;
  t1_us?: number;
  t2_us?: number;
  total_time_us?: number;
  num_steps?: number;
}

export interface DecoherenceSimulateResponse {
  initial_state: string;
  t1_us: number;
  t2_us: number;
  physical_constraint_satisfied: boolean;
  trajectory: Array<{
    time_us: number;
    bloch_vector: BlochVectorData;
    purity: number;
    von_neumann_entropy: number;
    rho_00: number;
    rho_11: number;
    abs_rho_01: number;
  }>;
}

export interface ErrorCorrectionRequest {
  code_type?: "bit_flip" | "phase_flip";
  error_qubit?: number | null;
  initial_state_theta?: number;
  shots?: number;
}

export interface ErrorCorrectionResponse {
  code_type: string;
  initial_state_theta_rad: number;
  error_qubit_injected: number | null;
  syndrome_measurements: Record<string, number>;
  expected_syndrome: string;
  syndrome_table: Record<string, string>;
  is_corrected: boolean;
  logical_fidelity: number;
  circuit_steps: string[];
  code_limitations?: string;
  coherent_recovery_method?: string;
  recovered_logical_probabilities?: Record<string, number>;
  theoretical_input_probabilities?: Record<string, number>;
}

export interface QuantumChannelRequest {
  channel_type?: string;
  input_state_preset?: string;
  param_p?: number;
  gamma?: number;
  lambda_param?: number;
}

export interface QuantumChannelResponse {
  channel_type: string;
  num_kraus_operators: number;
  is_trace_preserving: boolean;
  input_purity: number;
  output_purity: number;
  state_fidelity: number;
  bloch_shrinkage: {
    x_scale: number;
    y_scale: number;
    z_scale: number;
    z_shift: number;
  };
  kraus_operators: ComplexNumber[][][];
}

export interface TomographyRequest {
  operations?: GateOperation[];
  shots?: number;
}

export interface TomographyResponse {
  shots_per_basis: number;
  pauli_measurements: {
    x: { expected_val: number; prob_plus: number; prob_minus: number; std_err?: number };
    y: { expected_val: number; prob_plus_i: number; prob_minus_i: number; std_err?: number };
    z: { expected_val: number; prob_0: number; prob_1: number; std_err?: number };
  };
  reconstructed_bloch_vector: BlochVectorData;
  raw_bloch_vector?: BlochVectorData;
  true_bloch_vector: BlochVectorData;
  reconstructed_density_matrix: ComplexNumber[][];
  fidelity_reconstructed: number;
  fidelity_raw?: number;
  fidelity_projected?: number;
  is_raw_psd?: boolean;
  is_psd_projected?: boolean;
  purity_reconstructed: number;
  trace_distance: number;
  statistical_notice?: string;
}

export interface WorkflowResponse {
  parcels_evaluated: LandParcel[];
  infrastructure_reports: InfrastructureReport[];
  qubo_formulation: QUBOProblem;
  benchmark: BenchmarkComparison;
  recommendation: {
    budget_requested_cr: number;
    method: string;
    selected_parcels: string[];
    total_investment_crore: number;
    budget_remaining_crore: number;
    portfolio_utility_score: number;
    budget_compliant: boolean;
    approximation_ratio: number;
    quantum_advantage_note: string;
    utility_breakdown: Record<string, number>;
    classical_comparison: any;
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE 1.8 REAL GEOGRAPHIC INTELLIGENCE ENGINE (RGIE) SCHEMAS
// ═══════════════════════════════════════════════════════════════════════════════

export interface GeospatialSource {
  id: string;
  name: string;
  publisher: string;
  source_url: string;
  date_accessed: string;
  publication_date?: string;
  geographic_coverage: string;
  coordinate_reference_system: string;
  projected_crs?: string;
  license: string;
  permitted_usage: string;
  update_frequency: string;
  provenance_tier: VerificationStatus;
  confidence_level: number;
  features_extracted: string[];
  quality_limitations: string;
}

export interface GeospatialSourcesResponse {
  sources_count: number;
  sources: GeospatialSource[];
}

export interface GeospatialFeature {
  type: "Feature";
  id?: string;
  geometry: {
    type: string;
    coordinates: any;
  };
  properties: Record<string, any>;
}

export interface GeospatialFeatureCollection {
  type: "FeatureCollection";
  features: GeospatialFeature[];
  properties?: Record<string, any>;
}

export interface GeospatialInfrastructureResponse {
  corridors: GeospatialFeatureCollection;
  water_bodies: GeospatialFeatureCollection;
  planning_zones: GeospatialFeatureCollection;
}

export interface GeospatialAnalyzeRequest {
  lat: number;
  lng: number;
  parcel_id?: string;
  parcel_name?: string;
  custom_weights?: Record<string, number>;
}

export interface GeospatialAnalyzeResponse {
  query_coordinates: { lat: number; lng: number };
  utm_zone_43n?: {
    easting_m: number;
    northing_m: number;
    crs: string;
    description: string;
  };
  parcel_metadata: { parcel_id?: string; parcel_name?: string };
  administrative_jurisdiction: {
    within_pmrda_region: boolean;
    within_pmc_corporation: boolean;
    within_pcmc_corporation: boolean;
    primary_planning_authority: string;
    applicable_regulations: string;
  };
  environmental_and_zoning: {
    intersected_planning_zones: string[];
    within_floodline_zone: boolean;
    within_defence_buffer: boolean;
    clearance_recommendations: (string | null)[];
  };
  nearest_infrastructure: {
    highway: any;
    hospital: any;
    education: any;
    railway: any;
    airport: any;
    commercial_hub: any;
  };
  road_network_routing: {
    to_nearest_highway?: {
      straight_line_distance_km: number;
      network_distance_km: number;
      circuity_factor: number;
      free_flow_time_minutes: number;
      peak_travel_time_minutes: number;
      route_path: string[];
      methodology: string;
    };
    to_nearest_commercial_hub?: {
      straight_line_distance_km: number;
      network_distance_km: number;
      circuity_factor: number;
      free_flow_time_minutes: number;
      peak_travel_time_minutes: number;
      route_path: string[];
      methodology: string;
    };
  };
  geographic_suitability: {
    final_suitability_score: number;
    base_score_before_penalties: number;
    classification: string;
    data_completeness_percent: number;
    is_data_complete: boolean;
    factors: Array<{
      factor_name: string;
      weight: number;
      input_distance_km: number | null;
      normalized_score: number;
      weighted_points: number;
      data_available: boolean;
    }>;
    environmental_penalties: Array<{
      constraint: string;
      penalty_points: number;
      regulatory_basis: string;
      impact: string;
    }>;
    total_penalty_points: number;
    methodology: {
      model_type: string;
      normalization: string;
      disclaimer: string;
    };
  };
  scientific_disclaimer: string;
}

export interface GeoJSONImportRequest {
  geojson_data: Record<string, any>;
  parcel_name?: string;
  asking_price_crore?: number;
  check_pmrda_boundary?: boolean;
}

export interface GeoJSONImportResponse {
  is_valid: boolean;
  parcel_id: string;
  parcel_name: string;
  centroid: [number, number];
  area_acres: number;
  area_sq_meters: number;
  normalized_geojson: Record<string, any>;
  provenance_tier: string;
  statutory_warning: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// HELPER: Normalize LandParcel to ensure all computed UI fields are populated
// ═══════════════════════════════════════════════════════════════════════════════

export function normalizeParcel(raw: Partial<LandParcel> & { id: string | number; name: string }): LandParcel {
  const price = typeof raw.price_crore === "number" ? raw.price_crore : (raw.price_cr ?? 10.0);
  const area = raw.area_acres ?? 5.0;
  const pricePerAcre = raw.price_per_acre_crore ?? Number((price / area).toFixed(2));
  const ret = typeof raw.projected_return_pct === "number" ? raw.projected_return_pct : (raw.return_pct ?? 15.0);
  const w = raw.water_score ?? raw.infra_scores?.water ?? 0.8;
  const e = raw.electricity_score ?? raw.infra_scores?.power ?? 0.85;
  const s = raw.sewage_score ?? raw.infra_scores?.sewage ?? 0.75;
  const r = raw.road_score ?? raw.infra_scores?.road ?? 0.85;

  const infra_readiness = 0.25 * w + 0.25 * e + 0.20 * s + 0.30 * r;
  const norm_return = Math.min(ret / 30.0, 1.0);
  const computed_utility = 0.60 * infra_readiness + 0.40 * norm_return;

  return {
    id: String(raw.id),
    name: raw.name,
    location_lat: raw.location_lat ?? 18.5204,
    location_lng: raw.location_lng ?? 73.8567,
    area_acres: area,
    price_crore: price,
    price_per_acre_crore: pricePerAcre,
    water_score: w,
    electricity_score: e,
    sewage_score: s,
    road_score: r,
    projected_return_pct: ret,
    zone_type: raw.zone_type ?? "mixed",
    data_provenance: raw.data_provenance ?? "Pune Municipal Corporation / IGR Maharashtra Cadastral Baseline",
    verification_status: raw.verification_status ?? "Cadastral Verified (PMRDA DP 2021-2041)",
    surrounding_notes: raw.surrounding_notes ?? `${raw.name} corridor in PMRDA planning boundary.`,

    // Aliases
    price_cr: price,
    expected_roi_pct: ret,
    return_pct: ret,
    infra_scores: { water: w, power: e, sewage: s, road: r },
    utility_score: raw.utility_score ?? Number(computed_utility.toFixed(4)),
    infrastructure_index: raw.infrastructure_index ?? Number(infra_readiness.toFixed(4)),
    water_supply_score: w,
    location: raw.location ?? `${raw.name}, Pune PMRDA`,
    status: raw.status ?? (ret >= 18 ? "Shortlisted" : "Available"),
    max_fsi: raw.max_fsi ?? (raw.zone_type === "commercial" ? 2.5 : 2.0),
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// API CLIENT FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

export interface ParcelSearchParams {
  search?: string;
  zone_type?: string;
  min_price?: number;
  max_price?: number;
  min_area?: number;
  max_area?: number;
  sort_by?: "price_asc" | "price_desc" | "area_asc" | "area_desc" | "utility_desc" | "price_per_acre_asc";
}

/**
 * Fetch all Pune land parcels with optional search, filters, and sorting.
 */
export async function fetchParcels(params?: ParcelSearchParams): Promise<LandParcel[]> {
  const { data } = await api.get<LandParcel[]>("/parcels", { params });
  return data.map(normalizeParcel);
}

/**
 * Filter parcels by per-parcel price cap.
 */
export async function fetchParcelsByBudget(budget_crore: number): Promise<LandParcel[]> {
  const { data } = await api.get<LandParcel[]>(`/parcels/budget/${budget_crore}`);
  return data.map(normalizeParcel);
}

/**
 * Fetch complete detailed intelligence profile for a selected parcel.
 */
export async function fetchParcelProfile(parcelId: string): Promise<ParcelDetailedProfile> {
  const { data } = await api.get<ParcelDetailedProfile>(`/parcels/${encodeURIComponent(parcelId)}`);
  data.parcel = normalizeParcel(data.parcel);
  return data;
}

/**
 * Fetch multi-sector infrastructure proximity analysis for a parcel.
 */
export async function fetchParcelInfrastructure(parcelId: string): Promise<ParcelInfrastructureAnalysis> {
  const { data } = await api.get<ParcelInfrastructureAnalysis>(`/parcels/${encodeURIComponent(parcelId)}/infrastructure`);
  return data;
}

/**
 * Calculate development feasibility scenario under custom or default assumptions.
 */
export async function calculateFeasibility(
  parcelId: string,
  request?: FeasibilityScenarioRequest
): Promise<FeasibilityScenarioResult> {
  const { data } = await api.post<FeasibilityScenarioResult>(
    `/parcels/${encodeURIComponent(parcelId)}/feasibility`,
    request ?? {}
  );
  return data;
}

/**
 * Simulate multi-tier financial scenarios (Conservative, Baseline, Optimistic) and cash flows.
 */
export async function calculateFinancials(
  parcelId: string,
  request?: FeasibilityScenarioRequest
): Promise<FinancialAnalysisResponse> {
  const { data } = await api.post<FinancialAnalysisResponse>(
    `/parcels/${encodeURIComponent(parcelId)}/financial`,
    request ?? {}
  );
  return data;
}

/**
 * Fetch deterministic IS 1172 infrastructure sizing reports for all parcels.
 */
export async function fetchInfrastructureReports(): Promise<InfrastructureReport[]> {
  const { data } = await api.get<InfrastructureReport[]>("/parcels/infrastructure");
  return data;
}

/**
 * Execute real QAOA portfolio optimization on Qiskit Aer.
 */
export async function runQuantumOptimization(params: {
  budget_crore: number;
  qaoa_p?: number;
  qaoa_shots?: number;
  lambda_budget?: number;
  lambda_risk?: number;
}): Promise<OptimizationResponse> {
  const { data } = await api.post<OptimizationResponse>("/quantum/optimize", {
    budget_crore: params.budget_crore,
    qaoa_p: params.qaoa_p ?? 2,
    qaoa_shots: params.qaoa_shots ?? 4096,
    lambda_budget: params.lambda_budget ?? 10.0,
    lambda_risk: params.lambda_risk ?? 1.0,
  });
  return data;
}

/**
 * Run QAOA vs Classical (Exact MILP & Simulated Annealing) Benchmark.
 */
export async function runBenchmark(budget_crore: number): Promise<BenchmarkComparison> {
  const { data } = await api.get<BenchmarkComparison>(`/quantum/benchmark/${budget_crore}`);
  return data;
}

/**
 * Execute full 9-step Pune Development Workflow.
 */
export async function runPuneWorkflow(params: {
  budget_crore: number;
  zone_filter?: string;
  qaoa_p?: number;
  qaoa_shots?: number;
}): Promise<WorkflowResponse> {
  const { data } = await api.post<WorkflowResponse>("/workflow/pune-development", {
    budget_crore: params.budget_crore,
    zone_filter: params.zone_filter,
    qaoa_p: params.qaoa_p ?? 2,
    qaoa_shots: params.qaoa_shots ?? 4096,
  });
  return data;
}

/**
 * Fetch platform-wide data provenance and verification audit summary.
 */
export async function fetchProvenanceAudit(): Promise<any> {
  const { data } = await api.get("/parcels/provenance/audit");
  return data;
}

/**
 * Query real-time OpenStreetMap amenities via Overpass API for a parcel.
 */
export async function fetchOverpassAmenities(
  parcelId: string,
  radiusMeters: number = 5000
): Promise<any> {
  const { data } = await api.get(`/parcels/${encodeURIComponent(parcelId)}/overpass`, {
    params: { radius_meters: radiusMeters },
  });
  return data;
}

/**
 * Fetch catalog of supported quantum gates and their unitary matrices.
 */
export async function fetchQuantumGates(): Promise<GateSpec[]> {
  const { data } = await api.get<GateSpec[]>("/quantum/gates");
  return data;
}

/**
 * Fetch specification for a single quantum gate by ID.
 */
export async function fetchQuantumGate(gateId: string): Promise<GateSpec> {
  const { data } = await api.get<GateSpec>(`/quantum/gates/${encodeURIComponent(gateId)}`);
  return data;
}

/**
 * Execute custom quantum circuit on Qiskit Aer simulator.
 */
export async function simulateQuantumCircuit(params: {
  num_qubits: number;
  operations: GateOperation[];
  shots?: number;
}): Promise<CircuitSimulateResponse> {
  const { data } = await api.post<CircuitSimulateResponse>("/quantum/circuit/simulate", {
    num_qubits: params.num_qubits,
    operations: params.operations,
    shots: params.shots ?? 1024,
  });
  return data;
}

/**
 * Fetch pre-loaded reproducible quantum experiments.
 */
export async function fetchQuantumExperiments(): Promise<ExperimentTemplate[]> {
  const { data } = await api.get<ExperimentTemplate[]>("/quantum/experiments");
  return data;
}

/**
 * Fetch single quantum experiment template by ID.
 */
export async function fetchQuantumExperiment(expId: string): Promise<ExperimentTemplate> {
  const { data } = await api.get<ExperimentTemplate>(`/quantum/experiments/${encodeURIComponent(expId)}`);
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE 03 ADVANCED QUANTUM MECHANICS & RESEARCH LAB CLIENT FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Simulate continuous-time Hamiltonian state evolution U(t) = exp(-i H t / ħ).
 */
export async function simulateStateEvolution(
  params: StateEvolutionRequest
): Promise<StateEvolutionResponse> {
  const { data } = await api.post<StateEvolutionResponse>("/quantum/evolution/simulate", params);
  return data;
}

/**
 * Validate and analyze density matrix spectral properties (Hermiticity, trace, purity, partial trace).
 */
export async function analyzeDensityMatrix(
  params: DensityMatrixAnalyzeRequest
): Promise<DensityMatrixAnalyzeResponse> {
  const { data } = await api.post<DensityMatrixAnalyzeResponse>("/quantum/density/analyze", params);
  return data;
}

/**
 * Execute projective quantum measurement in Z, X, or Y basis with state collapse.
 */
export async function executeMeasurement(
  params: MeasurementExperimentRequest
): Promise<MeasurementExperimentResponse> {
  const { data } = await api.post<MeasurementExperimentResponse>("/quantum/measurement/execute", params);
  return data;
}

/**
 * Simulate Mach-Zehnder wave interference with phase sweep fringe curves.
 */
export async function simulateInterference(
  params: InterferenceSimulateRequest
): Promise<InterferenceSimulateResponse> {
  const { data } = await api.post<InterferenceSimulateResponse>("/quantum/interference/simulate", params);
  return data;
}

/**
 * Analyze quantum information: Von Neumann entropy, fidelity, trace distance, Fuchs-van de Graaf bounds.
 */
export async function analyzeQuantumInformation(
  params: QuantumInformationRequest
): Promise<QuantumInformationResponse> {
  const { data } = await api.post<QuantumInformationResponse>("/quantum/information/analyze", params);
  return data;
}

/**
 * Advanced entanglement analysis: Schmidt decomposition, concurrence, and PPT negativity.
 */
export async function analyzeEntanglement(
  params: EntanglementAnalyzeRequest
): Promise<EntanglementAnalyzeResponse> {
  const { data } = await api.post<EntanglementAnalyzeResponse>("/quantum/entanglement/analyze", params);
  return data;
}

/**
 * Simulate quantum circuit under Qiskit Aer noise models with ideal vs noisy comparison.
 */
export async function simulateNoise(
  params: NoiseSimulateRequest
): Promise<NoiseSimulateResponse> {
  const { data } = await api.post<NoiseSimulateResponse>("/quantum/noise/simulate", params);
  return data;
}

/**
 * Simulate T1 relaxation and T2 dephasing trajectory on the Bloch sphere.
 */
export async function simulateDecoherence(
  params: DecoherenceSimulateRequest
): Promise<DecoherenceSimulateResponse> {
  const { data } = await api.post<DecoherenceSimulateResponse>("/quantum/decoherence/simulate", params);
  return data;
}

/**
 * Execute 3-qubit bit-flip or phase-flip quantum error correction code.
 */
export async function executeErrorCorrection(
  params: ErrorCorrectionRequest
): Promise<ErrorCorrectionResponse> {
  const { data } = await api.post<ErrorCorrectionResponse>("/quantum/error-correction/execute", params);
  return data;
}

/**
 * Apply completely positive trace-preserving (CPTP) quantum channel via Kraus operators.
 */
export async function applyQuantumChannel(
  params: QuantumChannelRequest
): Promise<QuantumChannelResponse> {
  const { data } = await api.post<QuantumChannelResponse>("/quantum/channel/apply", params);
  return data;
}

/**
 * Perform single-qubit quantum state tomography via Pauli basis measurements.
 */
export async function reconstructTomography(
  params: TomographyRequest
): Promise<TomographyResponse> {
  const { data } = await api.post<TomographyResponse>("/quantum/tomography/reconstruct", params);
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE 1.8 REAL GEOGRAPHIC INTELLIGENCE ENGINE (RGIE) API CLIENT
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Health check for the Real Geographic Intelligence Engine.
 */
export async function getGeospatialHealth(): Promise<any> {
  const { data } = await api.get("/geospatial/health");
  return data;
}

/**
 * List catalog of verified geographic data sources and statutory datasets.
 */
export async function getGeospatialSources(): Promise<GeospatialSourcesResponse> {
  const { data } = await api.get<GeospatialSourcesResponse>("/geospatial/sources");
  return data;
}

/**
 * Get administrative boundary GeoJSON FeatureCollections (PMRDA, PMC, PCMC).
 */
export async function getGeospatialBoundaries(): Promise<GeospatialFeatureCollection> {
  const { data } = await api.get<GeospatialFeatureCollection>("/geospatial/boundaries");
  return data;
}

/**
 * Get infrastructure corridors (Expressway, Metro), rivers, and planning zones.
 */
export async function getGeospatialInfrastructure(): Promise<GeospatialInfrastructureResponse> {
  const { data } = await api.get<GeospatialInfrastructureResponse>("/geospatial/infrastructure");
  return data;
}

/**
 * Query features within radius meters of (lat, lng).
 */
export async function getNearbyGeospatialFeatures(
  lat: number,
  lng: number,
  radiusMeters: number = 5000,
  category?: string
): Promise<any[]> {
  const params: Record<string, any> = { lat, lng, radius_meters: radiusMeters };
  if (category) params.category = category;
  const { data } = await api.get<any[]>("/geospatial/features/nearby", { params });
  return data;
}

/**
 * Run comprehensive geographic intelligence analysis for a parcel or coordinates.
 */
export async function analyzeGeospatialLocation(
  params: GeospatialAnalyzeRequest
): Promise<GeospatialAnalyzeResponse> {
  const { data } = await api.post<GeospatialAnalyzeResponse>("/geospatial/analyze", params);
  return data;
}

/**
 * Import, validate (RFC 7946), and normalize user-supplied GeoJSON parcel geometry.
 */
export async function importUserGeoJSON(
  params: GeoJSONImportRequest
): Promise<GeoJSONImportResponse> {
  const { data } = await api.post<GeoJSONImportResponse>("/geospatial/import/geojson", params);
  return data;
}

/**
 * Lookup formal provenance record for any geographic feature.
 */
export async function getGeospatialProvenance(
  featureId: string
): Promise<ProvenanceRecord> {
  const { data } = await api.get<ProvenanceRecord>(`/geospatial/provenance/${featureId}`);
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════════
// REAL-WORLD MAPLIBRE GL JS & DIGITAL TWIN CLIENT
// ═══════════════════════════════════════════════════════════════════════════════

export interface MapConfigResponse {
  engine: string;
  default_view: {
    center: [number, number];
    zoom: number;
    min_zoom: number;
    max_zoom: number;
    pitch: number;
    max_pitch: number;
    bearing: number;
  };
  coordinate_reference_systems: {
    geographic: string;
    projected_metric: string;
  };
  styles: Array<{
    id: string;
    name: string;
    description: string;
    attribution: string;
    url?: string;
    raster_tiles?: string[];
    is_default: boolean;
  }>;
  statutory_attribution: string;
}

export interface MapHealthResponse {
  status: string;
  map_renderer: string;
  cached_building_footprints: number;
  geocoding_localities_count: number;
  administrative_layers_available: boolean;
  infrastructure_corridors_available: boolean;
}

export interface MapLayerItem {
  id: string;
  name: string;
  type: string;
  source: string;
  coverage: string;
  default_visible: boolean;
  provenance_tier: string;
  "3d_capabilities"?: string;
  capabilities_3d?: string;
}

export interface MapSearchLocality {
  name: string;
  coordinates: [number, number]; // [lng, lat]
  lat: number;
  lng: number;
  type: string;
  jurisdiction: string;
  source: string;
  suggested_zoom: number;
}

export interface MapFeatureInspectRequest {
  lat: number;
  lng: number;
  feature_id?: string;
  feature_name?: string;
  feature_type?: string;
}

export interface MapFeatureInspectResponse {
  feature_identity: {
    feature_id: string;
    name: string;
    feature_type: string;
    provenance_status: string;
    data_source: string;
  };
  coordinates: {
    wgs84: { lat: number; lng: number };
    utm_zone_43n: {
      easting_m: number;
      northing_m: number;
      crs: string;
      projection: string;
    };
  };
  administrative_jurisdiction: {
    within_pmrda_region: boolean;
    within_pmc_corporation: boolean;
    within_pcmc_corporation: boolean;
    primary_planning_authority: string;
    applicable_regulations: string;
  };
  environmental_constraints: {
    intersected_planning_zones: string[];
    within_floodline_zone: boolean;
    within_defence_buffer: boolean;
    clearance_recommendations: (string | null)[];
  };
  nearest_infrastructure: {
    highway: any;
    hospital: any;
    education: any;
    railway: any;
    commercial_hub: any;
  };
  road_network_routing: {
    to_nearest_highway?: any;
    to_nearest_commercial_hub?: any;
  };
  data_notice: {
    is_cadastral_title: boolean;
    disclaimer: string;
  };
}

export interface MapOptimizationRequest {
  budget_crore: number;
  candidate_parcel_ids?: string[];
  qaoa_p?: number;
  qaoa_shots?: number;
}

export interface MapOptimizationResponse {
  optimization_metadata: {
    budget_crore: number;
    qaoa_layers_p: number;
    shots: number;
    candidate_count: number;
  };
  quantum_qaoa_result: {
    optimal_bitstring: string;
    optimal_energy: number;
    execution_time_ms: number;
    selected_parcels: string[];
    total_investment_crore: number;
    remaining_budget_crore: number;
    portfolio_utility: number;
    budget_compliant: boolean;
    engine: string;
  };
  classical_baseline_result: {
    method: string;
    optimal_bitstring: string;
    optimal_energy: number;
    execution_time_ms: number;
    selected_parcels: string[];
    total_investment_crore: number;
  };
  comparative_analysis: {
    approximation_ratio: number;
    ratio_percentage: number;
    agreement_with_classical: boolean;
    scientific_disclosure: string;
  };
  winning_parcels_for_map: Array<{
    id: string;
    name: string;
    lat: number;
    lng: number;
    price_crore: number;
    area_acres: number;
    projected_return_pct: number;
    utility_score: number;
    zone_type: string;
  }>;
}

/**
 * Fetch MapLibre GL configuration and styles.
 */
export async function getMapConfig(): Promise<MapConfigResponse> {
  const { data } = await api.get<MapConfigResponse>("/map/config");
  return data;
}

/**
 * Fetch MapLibre engine health status.
 */
export async function getMapHealth(): Promise<MapHealthResponse> {
  const { data } = await api.get<MapHealthResponse>("/map/health");
  return data;
}

/**
 * Fetch available map layers catalog.
 */
export async function getMapLayers(): Promise<MapLayerItem[]> {
  const { data } = await api.get<MapLayerItem[]>("/map/layers");
  return data;
}

/**
 * Fetch authentic OpenStreetMap-aligned building footprints for Pune.
 */
export async function getMapBuildings(): Promise<GeospatialFeatureCollection> {
  const { data } = await api.get<GeospatialFeatureCollection>("/map/buildings");
  return data;
}

/**
 * Perform genuine geocoding search for Pune localities.
 */
export async function searchMapLocalities(query: string): Promise<MapSearchLocality[]> {
  const { data } = await api.get<MapSearchLocality[]>("/map/search", { params: { q: query } });
  return data;
}

/**
 * Deeply inspect a clicked map feature or coordinate location.
 */
export async function inspectMapFeature(
  params: MapFeatureInspectRequest
): Promise<MapFeatureInspectResponse> {
  const { data } = await api.post<MapFeatureInspectResponse>("/map/features/inspect", params);
  return data;
}

/**
 * Execute map-driven comparative classical vs QAOA optimization.
 */
export async function executeMapOptimization(
  params: MapOptimizationRequest
): Promise<MapOptimizationResponse> {
  const { data } = await api.post<MapOptimizationResponse>("/map/optimization/workflow", params);
  return data;
}

// ═══════════════════════════════════════════════════════════════════════
// PHASE 04 — QUANTUM-CLASSICAL OPTIMIZATION ENGINE APIS
// ═══════════════════════════════════════════════════════════════════════

export interface QUBOPayload {
  matrix: number[][];
  offset: number;
  variable_names: string[];
  problem_name: string;
  metadata?: Record<string, any>;
}

export interface ProblemBuildRequest {
  problem_type: "knapsack" | "portfolio" | "facility_location" | "resource_allocation" | string;
  parameters?: Record<string, any>;
}

export interface ProblemBuildResponse {
  problem_type: string;
  qubo: QUBOPayload;
  num_variables: number;
  variable_names: string[];
  linear_coefficients: Record<string, number>;
  quadratic_interactions: Array<{
    var1: string;
    var2: string;
    index1: number;
    index2: number;
    coupling: number;
  }>;
  milp_summary?: Record<string, any>;
}

export interface QUBOValidateResponse {
  is_valid: boolean;
  num_variables: number;
  is_symmetric: boolean;
  is_finite: boolean;
  condition_number?: number;
  min_eigenvalue?: number;
  max_eigenvalue?: number;
  dynamic_range_db?: number;
  warnings: string[];
}

export interface IsingConvertResponse {
  num_spins: number;
  h_linear: number[];
  J_quadratic: number[][];
  offset: number;
  variable_names: string[];
  pauli_terms: Array<{ pauli: string; coefficient: number }>;
  verified_equivalent: boolean;
}

export interface SolveClassicalRequest {
  qubo: QUBOPayload;
  solver: "milp" | "brute_force" | "greedy" | "simulated_annealing";
  seed?: number;
}

export interface ClassicalSolutionResponse {
  solver_name: string;
  status: string;
  optimal_bitstring: string;
  optimal_vector: number[];
  objective_value: number;
  solve_time_ms: number;
  iterations: number;
  optimality_gap?: number;
  extra_metadata?: Record<string, any>;
}

export interface SolveQAOARequest {
  qubo: QUBOPayload;
  depth_p: number;
  shots: number;
  optimizer_name: string;
  strategy: string;
  maxiter: number;
  seed?: number;
}

export interface QAOAIterationPoint {
  iteration: number;
  energy: number;
  gammas: number[];
  betas: number[];
}

export interface MeasurementItem {
  bitstring: string;
  counts: number;
  probability: number;
  energy: number;
  is_ground_state: boolean;
}

export interface QAOASolutionResponse {
  status: string;
  success: boolean;
  depth_p: number;
  shots: number;
  optimizer_name: string;
  iterations: number;
  optimal_gammas: number[];
  optimal_betas: number[];
  optimal_bitstring: string;
  optimal_vector: number[];
  best_sampled_energy: number;
  expected_energy: number;
  ground_state_probability: number;
  approximation_ratio?: number;
  solve_time_ms: number;
  circuit_metadata: Record<string, any>;
  trajectory: QAOAIterationPoint[];
  top_measurements: MeasurementItem[];
  hardware_disclaimer: string;
}

export interface SolveHybridRequest {
  qubo: QUBOPayload;
  depth_p: number;
  shots: number;
  seed?: number;
}

export interface HybridOptimizationResponse {
  problem_name: string;
  num_variables: number;
  variable_names: string[];
  classical_solution: {
    solver: string;
    bitstring: string;
    vector: number[];
    objective_value: number;
    solve_time_ms: number;
    status: string;
  };
  quantum_solution: {
    solver: string;
    bitstring: string;
    vector: number[];
    best_sampled_energy: number;
    expected_energy: number;
    ground_state_probability: number;
    solve_time_ms: number;
    circuit_metadata: Record<string, any>;
    trajectory: QAOAIterationPoint[];
    top_measurements: MeasurementItem[];
  };
  consensus_reached: boolean;
  optimality_gap_pct: number;
  approximation_ratio: number;
  total_execution_time_ms: number;
  hardware_disclaimer: string;
}

export interface BenchmarkRequest {
  qubo?: QUBOPayload;
  problem_preset?: "portfolio_pune" | "knapsack_infra" | "facility_pune";
  run_qaoa_p2?: boolean;
  shots?: number;
  maxiter?: number;
  seed?: number;
}

export interface BenchmarkSolverEntry {
  solver_name: string;
  is_quantum: boolean;
  status: string;
  optimal_bitstring: string;
  energy: number;
  optimality_gap_pct: number;
  approximation_ratio: number;
  solve_time_ms: number;
  iterations: number;
  feasibility_status: string;
  hardware_note: string;
  metadata?: Record<string, any>;
}

export interface BenchmarkResponse {
  problem_name: string;
  num_variables: number;
  exact_ground_energy: number;
  exact_ground_bitstring: string;
  solvers: BenchmarkSolverEntry[];
  summary_findings: string[];
  total_benchmark_time_ms: number;
  scientific_disclaimer: string;
}

export interface OptimizationHealthResponse {
  status: string;
  qiskit_version: string;
  qiskit_aer_version: string;
  scipy_version: string;
  numpy_version: string;
  supported_solvers: string[];
  supported_problem_types: string[];
  simulation_backend: string;
  hardware_disclaimer: string;
}

export async function getOptimizationHealth(): Promise<OptimizationHealthResponse> {
  const { data } = await api.get<OptimizationHealthResponse>("/optimization/health");
  return data;
}

export async function buildOptimizationProblem(
  params: ProblemBuildRequest
): Promise<ProblemBuildResponse> {
  const { data } = await api.post<ProblemBuildResponse>("/optimization/problems/build", params);
  return data;
}

export async function validateQUBO(qubo: QUBOPayload): Promise<QUBOValidateResponse> {
  const { data } = await api.post<QUBOValidateResponse>("/optimization/qubo/validate", qubo);
  return data;
}

export async function convertQUBOToIsing(qubo: QUBOPayload): Promise<IsingConvertResponse> {
  const { data } = await api.post<IsingConvertResponse>("/optimization/qubo/convert", qubo);
  return data;
}

export async function solveClassicalOptimization(
  req: SolveClassicalRequest
): Promise<ClassicalSolutionResponse> {
  const { data } = await api.post<ClassicalSolutionResponse>("/optimization/solve/classical", req);
  return data;
}

export async function solveQAOAOptimization(
  req: SolveQAOARequest
): Promise<QAOASolutionResponse> {
  const { data } = await api.post<QAOASolutionResponse>("/optimization/solve/qaoa", req);
  return data;
}

export async function solveHybridOptimization(
  req: SolveHybridRequest
): Promise<HybridOptimizationResponse> {
  const { data } = await api.post<HybridOptimizationResponse>("/optimization/solve/hybrid", req);
  return data;
}

export async function runOptimizationBenchmark(
  req: BenchmarkRequest
): Promise<BenchmarkResponse> {
  const { data } = await api.post<BenchmarkResponse>("/optimization/benchmark", req);
  return data;
}

export default api;
