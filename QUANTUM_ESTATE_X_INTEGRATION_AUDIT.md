# QUANTUM ESTATE X — 3D CITY TWIN & QUANTUM INTEGRATION AUDIT

**Audit Date:** November 5, 2026  
**Status:** Verification & Architectural Assessment  
**Build & Test Health:** 
- Frontend Build: **100% Pass** (`vite v8.3.5` + `tsc -b`, 0 errors)
- Backend Test Suite: **100% Pass** (14 / 14 tests passing on `pytest-9.1.1` in 103s)

---

## Executive Summary

This audit evaluates the end-to-end integration between the **Three.js 3D City Twin**, the **FastAPI Real Estate/Infrastructure Engine**, and the **Qiskit Aer Quantum Optimization Pipeline**.

**Key Finding:**  
The **FastAPI backend contains genuine, functioning scientific engines** (real IS 1172 infrastructure calculations, authentic QUBO formulation, and true Qiskit Aer QAOA execution with Scipy COBYLA parameter optimization). However, **the React frontend is currently decoupled from the backend**. The frontend operates exclusively on static mock objects (`mockData.ts`), uses a client-side toy formula for QUBO matrix cells, and renders synthetic/illustrative geometry in the 3D viewers.

---

## 1. Existing Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React 19 + Vite)                            │
│  Port 8080                                                                      │
│                                                                                 │
│  ┌───────────────────────┐  ┌─────────────────────────┐  ┌───────────────────┐  │
│  │     CityTwin3D.tsx    │  │     BlochSphere3D.tsx   │  │QuantumLandscape3D │  │
│  │ (Synthetic 3D Blocks) │  │(Single-Qubit SU(2) Model│  │(Synthetic Wave Mesh│  │
│  └───────────▲───────────┘  └────────────▲────────────┘  └─────────▲─────────┘  │
│              │                           │                         │            │
│  ┌───────────┴───────────────────────────┴─────────────────────────┴─────────┐  │
│  │                          Pages: Dashboard / QuantumLab                    │  │
│  │                     (Reads from static mockData.ts)                       │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │  [DISCONNECTED IN PRODUCTION]
                                         │  api.ts defined but uninvoked in pages
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI + Qiskit Aer)                        │
│  Port 8000                                                                      │
│                                                                                 │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌───────────────────┐  │
│  │   land_intelligence    │  │  infrastructure_calc   │  │   qaoa_optimizer  │  │
│  │ (8 Pune PMRDA Parcels) │  │  (IS 1172 Water/Power)  │  │ (Qiskit Aer CPU)  │  │
│  └───────────┬────────────┘  └───────────┬────────────┘  └─────────┬─────────┘  │
│              │                           │                         │            │
│              └───────────────────────────┼─────────────────────────┘            │
│                                          ▼                                      │
│                             routes_workflow.py (Full 9-Step)                    │
│                        POST /api/workflow/pune-development                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Working Functionality vs. Disconnections

| Module | Sub-Component | Status | Operational Details |
| :--- | :--- | :--- | :--- |
| **Backend Engine** | Land Intelligence | **Working** | 8 Pune parcels with GIS coordinates, prices, and IS scores. |
| **Backend Engine** | Infrastructure Sizing | **Working** | Deterministic IS 1172 water, sewage, and substation kVA math. |
| **Backend Engine** | QUBO Formulation | **Working** | Objective utility $+ \lambda_1$ budget penalty $+ \lambda_2$ proximity risk. |
| **Backend Engine** | QAOA Optimization | **Working** | Qiskit Aer simulator runs parameterised ansatz + Scipy COBYLA. |
| **Backend Engine** | Classical Benchmarks | **Working** | Exact Branch-and-Bound MILP ($2^n$) + Simulated Annealing. |
| **Backend API** | Endpoints | **Working** | `/api/parcels`, `/api/quantum/optimize`, `/api/workflow/pune-development`. |
| **Frontend UI** | 3D Viewport Controls | **Working** | Three.js orbit controls, camera lerp, presets, hover raycasting. |
| **Integration** | Frontend $\rightarrow$ Backend | **FAILED** | Frontend pages do not call API; they read from `mockData.ts`. |
| **Data Fidelity** | 3D Parcel Coordinates | **Synthetic** | Local grid coordinates, not projected GIS polygons. |
| **Quantum Fidelity** | 3D Energy Landscape | **Illustrative**| Synthetic trigonometric mesh, not actual Hamiltonian eigenvalues. |

---

## 3. TASK 1 Audit — 3D City Twin (`CityTwin3D.tsx`)

### 1.1 Parcel Generation
- Parcels are mapped by name to hardcoded positions in `PUNE_3D_LAYOUT`:
  ```ts
  "Hinjewadi Phase III": { x: -6.5, z: -3.0, height: 4.2, type: "tech", color: 0x2563eb }
  "Wakad Central": { x: -3.2, z: -1.2, height: 3.5, type: "residential", color: 0x0284c7 }
  "Kharadi IT Park": { x: 5.8, z: -1.5, height: 4.6, type: "tech", color: 0x1d4ed8 }
  ```
- Geometry: Box primitives (`BoxGeometry(1.6, bHeight, 1.6)`) sitting on uniform foundation slabs (`BoxGeometry(2.8, 0.16, 2.8)`).
- Fallback: Unmapped parcels fall back to procedural linear layout `x = (parcel.id - 4) * 3`.

### 1.2 Coordinate Realism
- **Synthetic**: Coordinates are abstract units in Three.js scene space ($[-8, +8]$), oriented loosely to Pune geography (Hinjewadi in NW, Kharadi in E, Chakan in N).
- They do **not** use real GIS projections (EPSG:4326 WGS84 lat/long or EPSG:32643 UTM Zone 43N).

### 1.3 Parcel Boundaries
- **Synthetic / Illustrative**: Boundaries are uniform $2.8 \times 2.8$ meter/unit square wireframes. They do not represent cadastral survey boundaries (7/12 extract plots, PMRDA town planning scheme polygons).

### 1.4 Infrastructure Networks
- **Illustrative**:
  - **Water Supply Pipeline**: A single hardcoded `CatmullRomCurve3` spline connecting 6 arbitrary 3D points.
  - **Power Transmission Grid**: A static line connecting 5 parcel locations to a synthetic central hub `(0, 3.2, 0)`.
  - Neither is linked to actual municipal hydraulic distribution models (EPANET) or Maharashtra State Electricity Distribution (MSEDCL) GIS feeder lines.

### 1.5 Parcel Selection & Raycasting
- **Working Correctly**:
  - `mousemove` events raycast against `interactiveObjects` to set `hoveredParcel`.
  - `click` events trigger `onSelectParcel(hitData)` and update `targetLookAt` and `targetCamPos`.
  - External parcel selection highlights the active 3D massing with royal blue emissive shading.

### 1.6 Camera Controls
- **Working Correctly**:
  - Uses `OrbitControls` with damping (`dampingFactor: 0.05`).
  - Smooth animation loop using camera lerp (`camera.position.lerp(targetCamPos, 0.04)`).
  - Presets (`PMRDA Wide`, `QAOA Winners`, `Selected Plot Focus`) function smoothly.

---

## 4. TASK 2 Audit — Land Data Integration

### 2.1 Backend vs. Frontend Data Discrepancy

A fundamental mismatch exists between backend parcels and frontend mock data:

| Attribute | Backend (`land_intelligence.py`) | Frontend Mock (`mockData.ts`) |
| :--- | :--- | :--- |
| **ID Format** | String (`"PUNE-001"` to `"PUNE-008"`) | Number (`1` to `8`) |
| **Parcel 1** | Wagholi East (₹11.5 Cr, 6.5 Acres) | Hinjewadi Phase III (₹3.8 Cr, 5.2 Acres) |
| **Parcel 2** | Chakan Industrial (₹14.0 Cr, 12.0 Acres) | Wakad Central (₹2.5 Cr, 3.1 Acres) |
| **Parcel 3** | Hinjawadi Phase 3 (₹13.8 Cr, 4.2 Acres) | Baner Hilltop (₹4.2 Cr, 4.7 Acres) |
| **Parcel 4** | Talegaon Dabhade (₹9.2 Cr, 9.0 Acres) | Kharadi IT Park (₹5.1 Cr, 6.0 Acres) |
| **Price Range** | **₹8.8 Cr — ₹14.5 Cr per parcel** | **₹1.8 Cr — ₹5.1 Cr per parcel** |
| **Design Budget** | Requires **₹40.0 Cr** for multi-parcel selection | Requires **₹15.0 Cr** for multi-parcel selection |

### 2.2 API Client vs. Backend Schema Mismatch
In [`frontend/src/lib/api.ts`](file:///c:/Users/admin/OneDrive/Desktop/PROJECTS/Infra%20Industry%20Quantum%20Mechanics/frontend/src/lib/api.ts):
- `runQuantumOptimization(budget)` sends `{ budget }`.  
  **Mismatch:** Backend expects `{ budget_crore: float }`.
- `fetchParcelsWithinBudget(budget)` calls `GET /parcels?budget=${budget}`.  
  **Mismatch:** Backend route is `GET /api/parcels/budget/{budget_crore}`.
- `runBenchmark(budget)` sends `POST /quantum/benchmark`.  
  **Mismatch:** Backend route is `GET /api/quantum/benchmark/{budget_crore}`.
- `runPuneWorkflow(budget)` calls `POST /workflow/pune`.  
  **Mismatch:** Backend route is `POST /api/workflow/pune-development`.

### 2.3 Budget Slider Behavior
- In `Dashboard.tsx` and `LandStudio.tsx`, the budget slider (`budgetCap`) only mutates local component state (`useState`).
- It triggers no API fetch or recalculation. The QAOA button triggers a simulated timer:
  ```ts
  const handleRunQAOA = () => {
    setIsOptimizing(true);
    setTimeout(() => {
      setIsOptimizing(false);
      setShowNotification(true);
    }, 900);
  };
  ```

---

## 5. TASK 3 Audit — QAOA Engine & Integration

### 3.1 Actual Quantum Execution
- **QAOA ACTUALLY RUNS ON BACKEND:**
  When invoked via `POST /api/quantum/optimize` or `POST /api/workflow/pune-development`, Qiskit Aer executes the variational circuit on CPU:
  - Cost Hamiltonian: $\sum h_i Z_i + \sum J_{ij} Z_i Z_j$
  - Mixer Hamiltonian: $\sum X_i$
  - Optimizer: Scipy `COBYLA` with up to 200 iterations
  - Measurement: `AerSimulator(method="statevector")` with 4,096 shots
  - Execution Time: ~1.8 — 2.2 seconds for 8 qubits
- **Empirical Execution Log:**
  Invoking `POST /api/quantum/optimize` with `budget_crore: 40.0` produced:
  ```json
  {
    "selected_parcels": ["Wagholi East", "Talegaon Dabhade", "Pirangut Corridor", "Mamurdi PCMC"],
    "total_cost_crore": 40.0,
    "total_utility": 2.4475,
    "budget_compliant": true
  }
  ```

### 3.2 Frontend Optimization Disconnection
- In `Dashboard.tsx`:
  - Selected parcels are hardcoded to `MOCK_QUANTUM_RESULT.selected_parcels`:
    `["Hinjewadi Phase III", "Wakad Central", "Kharadi IT Park", "Hadapsar Growth Zone"]`
  - Cost is hardcoded to `₹14.6 Cr` / Reserve `₹0.40 Cr`.
  - Bitstring is hardcoded to `|11010010⟩`.
  - None of this data originates from the executed QAOA backend.

---

## 6. TASK 4 Audit — Quantum Visualizations

### 4.1 3D Bloch Sphere (`BlochSphere3D.tsx`)
- **Mathematical Accuracy:** Correct for a **single 2-level qubit**:
  $$|\psi\rangle = \cos(\theta/2)|0\rangle + e^{i\phi}\sin(\theta/2)|1\rangle$$
  Amplitudes and probability readouts ($P(|0\rangle) = \cos^2(\theta/2)$, $P(|1\rangle) = \sin^2(\theta/2)$) are mathematically correct.
- **Limitation / Disconnection:** It represents an isolated 1-qubit system. It does not (and mathematically cannot) represent the 8-qubit entangled QAOA statevector in $\mathbb{C}^{256}$. It serves an educational/illustrative role.

### 4.2 Quantum Circuit Viewer (`CircuitViewer.tsx`)
- **Structural Accuracy:** Represents the canonical QAOA layer structure:
  - Hadamard barrier on all 8 wires: $H^{\otimes 8}$
  - Parameterised Cost Unitaries: $e^{-i\gamma H_P}$
  - Parameterised Mixer Rotations: $R_X(2\beta)$
  - Final measurement barriers $[M]$
- **Limitation:** Gate parameters $\gamma, \beta$ are hardcoded defaults (`gamma = 0.785`, `beta = 0.392`) and do not update dynamically from the backend's Scipy COBYLA optimal angles (`gammas_opt`, `betas_opt`).

### 4.3 QUBO Heatmap (`QUBOHeatmap.tsx`)
- **Critical Finding — Toy Calculation:**
  The frontend computes the $8 \times 8$ matrix using a client-side toy formula:
  ```ts
  if (i === j) val = Math.round(-15 * utility + 0.1 * price ** 2);
  else if (j > i) val = Math.round(0.15 * price_i * price_j + (i + j) * 1.2);
  ```
- **Disconnection:** It completely ignores the backend's real $Q$ matrix returned by `qubo_to_qubo_problem(Q, offset, var_names)`.

### 4.4 3D Quantum Energy Landscape (`QuantumLandscape3D.tsx`)
- **Critical Finding — Synthetic Metaphor:**
  The 3D surface is generated using a synthetic procedural function:
  $$y = \sin(0.7x)\cos(0.7z)\cdot 1.2 + 0.5(\cos(1.4x) + \sin(1.4z)) - 3.2e^{-0.7 d} + 0.8$$
- **Particle Tunneling:** The animated sphere interpolates between arbitrary coordinates $(-3.5, 1.8, -3.0)$ and $(2.2, -1.8, 1.8)$ using `Math.sin(time * 0.8)`.
- It does **not** plot actual bitstring state energies $x^T Q x$ for the 256 computational basis configurations.

---

## 7. Integration Failures Summary

1. **Payload Key Mismatch:** Frontend sends `{ budget }`, backend requires `{ budget_crore }`.
2. **HTTP Method Mismatches:** Frontend calls `POST` on `/quantum/benchmark`, backend exposes `GET /benchmark/{budget_crore}`.
3. **Dataset Inconsistency:**
   - Backend parcel prices total ₹8.8 — ₹14.5 Cr each (meaningful at ₹40 Cr budget).
   - Frontend mock data parcel prices total ₹1.8 — ₹5.1 Cr each (meaningful at ₹15 Cr budget).
   - Names and IDs do not match (`"PUNE-001"` vs `1`).
4. **Mock Bypass:** Neither `Dashboard.tsx` nor `QuantumLab.tsx` makes any network calls. All buttons use `setTimeout` dummy timers.
5. **Decoupled Visualizations:** QUBO Heatmap, Bloch Sphere, and Energy Landscape compute internal synthetic visuals rather than consuming backend API payloads.

---

## 8. Recommended Corrections & Next Milestone

### Immediate Remediation Plan (Awaiting User Approval):

1. **Synchronize Data Model:**
   - Decide on a canonical budget baseline:
     - **Option A:** Align backend parcel prices to the ₹15 Cr cap study (parcels at ₹1.8 — ₹5.1 Cr).
     - **Option B:** Align frontend budget controls to ₹40 Cr to match current backend dataset.
   - Standardize parcel IDs across frontend and backend.

2. **Fix API Client (`api.ts`):**
   - Correct endpoint paths, methods, and payload parameter names (`budget_crore`).
   - Add React Query hooks (`useParcels`, `useQAOAOptimize`, `useWorkflow`).

3. **Wire Frontend Pages to Live Endpoints:**
   - In `Dashboard.tsx`: Replace `MOCK_PARCELS` with `useQuery(['parcels'])`.
   - Wire `handleRunQAOA` to call `POST /api/quantum/optimize` with actual slider `budgetCap`.
   - Update `winningParcels` dynamically from `response.data.decoded_solution.selected_parcels`.

4. **Connect Quantum Visualizations to Real Calculations:**
   - Pass backend `qubo_formulation.Q_matrix` into `QUBOHeatmap.tsx`.
   - Pass backend `qaoa_result.probabilities` into `QuantumLab.tsx` bar chart.
   - Pass optimal angles $\gamma^*, \beta^*$ into `CircuitViewer.tsx`.

---

*Report prepared for user review. No breaking code modifications have been made. Awaiting authorization to proceed with live integration wiring.*

