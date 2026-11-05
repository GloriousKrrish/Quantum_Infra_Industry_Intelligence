/**
 * Fallback & Synthetic Demonstration Data for QUANTUM ESTATE X.
 * 
 * NOTE: Used strictly when the FastAPI backend on http://localhost:8000
 * is offline or unreachable. All data points mirror the real Pune dataset
 * in backend/app/engines/real_estate/land_intelligence.py.
 */

import { normalizeParcel, type LandParcel, type OptimizationResponse, type BenchmarkComparison } from "./api";

// ─── 8 Pune PMRDA Parcels (Standardized to Backend Schema) ────────────────────

export const MOCK_PARCELS: LandParcel[] = [
  normalizeParcel({
    id: "PUNE-001",
    name: "Wagholi East",
    location_lat: 18.5788,
    location_lng: 73.9787,
    area_acres: 6.5,
    price_crore: 11.5,
    water_score: 0.85,
    electricity_score: 0.80,
    sewage_score: 0.70,
    road_score: 0.90,
    projected_return_pct: 18.0,
    zone_type: "mixed",
    data_provenance: "Pune Municipal Corporation / IGR Maharashtra (Synthetic Fallback)",
    location: "Wagholi, Pune PMRDA",
  }),
  normalizeParcel({
    id: "PUNE-002",
    name: "Chakan Industrial",
    location_lat: 18.7609,
    location_lng: 73.8639,
    area_acres: 12.0,
    price_crore: 14.0,
    water_score: 0.60,
    electricity_score: 0.90,
    sewage_score: 0.55,
    road_score: 0.85,
    projected_return_pct: 15.0,
    zone_type: "industrial",
    data_provenance: "Pune Municipal Corporation / IGR Maharashtra (Synthetic Fallback)",
    location: "Chakan MIDC Phase II, Pune",
  }),
  normalizeParcel({
    id: "PUNE-003",
    name: "Hinjawadi Phase 3",
    location_lat: 18.5912,
    location_lng: 73.7380,
    area_acres: 4.2,
    price_crore: 13.8,
    water_score: 0.90,
    electricity_score: 0.95,
    sewage_score: 0.85,
    road_score: 0.95,
    projected_return_pct: 22.0,
    zone_type: "commercial",
    data_provenance: "Pune Municipal Corporation / IGR Maharashtra (Synthetic Fallback)",
    location: "Hinjawadi Infotech Park, Pune",
  }),
  normalizeParcel({
    id: "PUNE-004",
    name: "Talegaon Dabhade",
    location_lat: 18.7335,
    location_lng: 73.6757,
    area_acres: 9.0,
    price_crore: 9.2,
    water_score: 0.55,
    electricity_score: 0.65,
    sewage_score: 0.50,
    road_score: 0.75,
    projected_return_pct: 12.0,
    zone_type: "residential",
    data_provenance: "Pune Municipal Corporation / IGR Maharashtra (Synthetic Fallback)",
    location: "Talegaon Floriculture Corridor, Pune",
  }),
  normalizeParcel({
    id: "PUNE-005",
    name: "Hadapsar Extension",
    location_lat: 18.5089,
    location_lng: 73.9260,
    area_acres: 5.0,
    price_crore: 12.4,
    water_score: 0.90,
    electricity_score: 0.90,
    sewage_score: 0.80,
    road_score: 0.90,
    projected_return_pct: 20.0,
    zone_type: "mixed",
    data_provenance: "Pune Municipal Corporation / IGR Maharashtra (Synthetic Fallback)",
    location: "Hadapsar Magarpatta Growth Zone, Pune",
  }),
  normalizeParcel({
    id: "PUNE-006",
    name: "Pirangut Corridor",
    location_lat: 18.5164,
    location_lng: 73.6863,
    area_acres: 8.5,
    price_crore: 10.5,
    water_score: 0.65,
    electricity_score: 0.70,
    sewage_score: 0.55,
    road_score: 0.65,
    projected_return_pct: 14.0,
    zone_type: "residential",
    data_provenance: "Pune Municipal Corporation / IGR Maharashtra (Synthetic Fallback)",
    location: "Pirangut Industrial Valley, Pune",
  }),
  normalizeParcel({
    id: "PUNE-007",
    name: "Kharadi IT Hub",
    location_lat: 18.5535,
    location_lng: 73.9455,
    area_acres: 3.8,
    price_crore: 14.5,
    water_score: 0.95,
    electricity_score: 0.95,
    sewage_score: 0.90,
    road_score: 0.95,
    projected_return_pct: 24.0,
    zone_type: "commercial",
    data_provenance: "Pune Municipal Corporation / IGR Maharashtra (Synthetic Fallback)",
    location: "Kharadi EON Free Zone, Pune",
  }),
  normalizeParcel({
    id: "PUNE-008",
    name: "Mamurdi PCMC",
    location_lat: 18.6571,
    location_lng: 73.7889,
    area_acres: 7.2,
    price_crore: 8.8,
    water_score: 0.70,
    electricity_score: 0.75,
    sewage_score: 0.60,
    road_score: 0.80,
    projected_return_pct: 13.0,
    zone_type: "mixed",
    data_provenance: "Pune Municipal Corporation / IGR Maharashtra (Synthetic Fallback)",
    location: "Mamurdi Expressway Junction, PCMC",
  }),
];

// ─── Standardized Demonstration Baseline: ₹40.0 Cr ───────────────────────────
// Optimal combination under ₹40 Cr: Wagholi (11.5) + Talegaon (9.2) + Pirangut (10.5) + Mamurdi (8.8) = ₹40.0 Cr
export const MOCK_QUANTUM_RESULT: OptimizationResponse = {
  budget_crore: 40.0,
  qaoa_result: {
    optimal_bitstring: "10010101",
    optimal_value: -2.4475,
    top_bitstrings: ["10010101", "10001100", "00110100", "01010001"],
    probabilities: {
      "10010101": 0.284,
      "10001100": 0.142,
      "00110100": 0.098,
      "01010001": 0.076,
      "11000001": 0.052,
    },
    execution_time_ms: 1840.5,
    circuit_depth: 36,
    num_qubits: 8,
    optimal_parameters: {
      gammas: [0.6827, 0.3415],
      betas: [0.4179, 0.2089],
    },
  },
  qubo_formulation: {
    Q_matrix: [
      [-12.4, 4.2, 5.1, 3.8, 4.6, 3.2, 5.4, 2.9],
      [0, -8.6, 6.2, 4.1, 5.8, 3.9, 6.7, 3.4],
      [0, 0, -15.2, 3.9, 5.2, 3.5, 7.1, 3.1],
      [0, 0, 0, -9.1, 4.0, 2.8, 4.9, 2.6],
      [0, 0, 0, 0, -13.5, 4.4, 6.0, 3.7],
      [0, 0, 0, 0, 0, -7.9, 5.1, 2.7],
      [0, 0, 0, 0, 0, 0, -16.4, 3.8],
      [0, 0, 0, 0, 0, 0, 0, -8.2],
    ],
    offset: 1600.0,
    num_variables: 8,
    variable_names: [
      "Wagholi East",
      "Chakan Industrial",
      "Hinjawadi Phase 3",
      "Talegaon Dabhade",
      "Hadapsar Extension",
      "Pirangut Corridor",
      "Kharadi IT Hub",
      "Mamurdi PCMC",
    ],
  },
  decoded_solution: {
    selected_parcels: [
      "Wagholi East",
      "Talegaon Dabhade",
      "Pirangut Corridor",
      "Mamurdi PCMC",
    ],
    total_cost_crore: 40.0,
    total_utility: 2.4475,
    budget_compliant: true,
  },
};

// ─── Classical Benchmark Mock ─────────────────────────────────────────────────

export const MOCK_BENCHMARK: BenchmarkComparison = {
  qaoa_result: MOCK_QUANTUM_RESULT.qaoa_result,
  classical_results: [
    {
      method: "brute_force",
      optimal_value: -2.4475,
      optimal_solution: "10010101",
      execution_time_ms: 18.4,
    },
    {
      method: "simulated_annealing",
      optimal_value: -2.4475,
      optimal_solution: "10010101",
      execution_time_ms: 45.2,
    },
  ],
  qaoa_decoded: MOCK_QUANTUM_RESULT.decoded_solution,
  classical_decoded: MOCK_QUANTUM_RESULT.decoded_solution,
  approximation_ratio: 0.999,
  budget_compliance: true,
};

export const MOCK_BENCHMARK_CHART = [
  { metric: "Approximation Ratio (α)", exact_milp: 1.0, qaoa: 0.999, simulated_annealing: 0.985 },
  { metric: "Portfolio Utility Score", exact_milp: 2.448, qaoa: 2.448, simulated_annealing: 2.412 },
  { metric: "Budget Feasibility", exact_milp: 1.0, qaoa: 1.0, simulated_annealing: 1.0 },
];
