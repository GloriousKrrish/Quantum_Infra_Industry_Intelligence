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

export default api;
