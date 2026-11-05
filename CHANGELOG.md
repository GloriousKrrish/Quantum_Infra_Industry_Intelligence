# CHANGELOG — QUANTUM ESTATE X

All notable changes to the Quantum Estate X platform are documented in this file.

---

## [Phase 02] — 2026-11-05
### Added: Quantum Computing Foundation & Scientific Visual Laboratory
- **Native Qiskit Aer C++ Engine Integration (`backend/app/engines/quantum/`)**:
  - Integrated `qiskit 2.6.1` and `qiskit-aer 0.18.2` native C++ AerSimulator on Python 3.14 without fallbacks.
  - Built `simulation_engine.py` delivering exact complex amplitudes ($\text{Re}, \text{Im}$, magnitude, phase $\phi \in [-\pi, \pi]$), probabilities $|\alpha_i|^2$, and shot-based measurement histograms ($N=1024, 2048, 4096$).
  - Derived per-qubit reduced density matrices $\rho_k = \text{Tr}_{\bar{k}}(\rho)$ via partial tracing over the register.
  - Calculated exact Bloch vector coordinates $\vec{r} = (2\text{Re}(\rho_{01}), 2\text{Im}(\rho_{10}), \rho_{00} - \rho_{11})$ and state purity $\gamma = \text{Tr}(\rho^2)$.
- **Comprehensive Quantum Gate Library (`gate_library.py`)**:
  - Implemented 14 unitary gates satisfying $U^\dagger U = I$:
    - Single-qubit: $I, X, Y, Z, H, S, T, R_x(\theta), R_y(\theta), R_z(\phi)$.
    - Multi-qubit: $CX, CZ, \text{SWAP}, \text{CCNOT}$ (Toffoli).
  - Attached exact $2\times 2, 4\times 4, 8\times 8$ complex unitary matrices and LaTeX expressions to every gate.
  - Published REST endpoints `GET /api/quantum/gates` and `GET /api/quantum/gates/{gate_id}`.
- **Circuit Engine & Simulation Endpoint (`circuit_engine.py`, `routes_quantum.py`)**:
  - Strict validation of 1–8 qubit circuits, operation order, control/target disjointness, and circuit depth calculations.
  - Published circuit simulation endpoint `POST /api/quantum/circuit/simulate`.
- **Pre-Loaded Reproducible Experiments (`experiment_library.py`)**:
  - Cataloged 10 canonical experiments: Single-Qubit Superposition, Pauli-X Inversion, S/T Phase Shifts, Mach-Zehnder Interference ($H \to Z \to H$), 4 Bell states ($|\Phi^+\rangle, |\Phi^-\rangle, |\Psi^+\rangle, |\Psi^-\rangle$), GHZ state, and Bennett et al. Quantum Teleportation.
  - Published endpoints `GET /api/quantum/experiments` and `GET /api/quantum/experiments/{id}`.
- **Frontend Quantum Research Laboratory (`frontend/src/components/quantum/`, `pages/QuantumLab.tsx`)**:
  - `BlochSphere3D.tsx`: Upgraded 3D Three.js sphere rendering pure states on the surface ($|\vec{r}|=1$), mixed states inside the sphere ($|\vec{r}|<1$), and maximally mixed states at the origin ($|\vec{r}|=0, \gamma=0.5$) with amber halo and scientific explanation.
  - `CircuitBuilder.tsx`: Visual 1–8 qubit circuit grid with gate selection, target/control/parameter sliders, preset loader, and execution trigger.
  - `EntanglementLab.tsx`: Interactive Bell & GHZ state generator with joint correlation histograms, measurement sampling, and individual qubit reduced state inspection.
  - `QuantumMathExplorer.tsx`: Dirac bra-ket statevector table ($|\psi\rangle = \sum \alpha_i |i\rangle$), complex number breakdown, and gate unitary matrix explorer.
  - `ExperimentLibraryModal.tsx`: Modal browser for 10 canonical experiments with one-click injection into the circuit builder.
  - Preserved QAOA real estate optimizer and classical benchmarking tabs intact.
- **Verification & Testing**:
  - Created `backend/tests/test_quantum_foundation.py` with 32 unit and API tests.
  - Complete backend test suite: **81 / 81 passed** in 11.95s.
  - Frontend production build: **0 errors** in 2.63s.

---

## [Phase 1.7] — 2026-11-05
### Added: Geospatial Data Integrity & Scientific Validation Framework
- **Data Trust Framework (`backend/app/data/provenance/`)**:
  - Implemented 7 formal data verification tiers: `VERIFIED_OFFICIAL`, `VERIFIED_OPEN_DATA`, `USER_PROVIDED`, `ESTIMATED`, `SYNTHETIC`, `UNVERIFIED`, `UNAVAILABLE`.
  - Added structured `ProvenanceRecord` metadata across all land parcels, infrastructure proximity points, feasibility scenarios, and financial forecasts.
  - Published platform-wide provenance audit endpoint (`GET /api/parcels/provenance/audit`).
- **OpenStreetMap Overpass API Integration (`backend/app/data/sources/osm_source.py`)**:
  - Integrated public Overpass API client with 1-hour in-memory TTL caching.
  - 3.5-second connection timeout and rate-limit handling with automatic offline fallback to verified local geodetic anchors.
  - Added live amenities query endpoint (`GET /api/parcels/{id}/overpass`).
- **Geodetic & Geospatial Accuracy**:
  - Implemented WGS-84 coordinate range checks and PMRDA bounding box validation.
  - Hardened Haversine formula against floating-point antipodal domain errors.
  - Explicitly labeled all straight-line calculations as "Straight-line distance estimate (Haversine WGS-84)" and distinguished from actual road network routing.
  - Added Indian Road Congress (IRC) transit benchmarks (30–45 km/h) for urban drive-time estimation.
  - Added RFC 7946 GeoJSON approximate bounding footprint generation for parcel geometries.
  - Supported configurable accessibility scoring weights via API query parameters with automated normalization.
- **Feasibility & Financial Mathematical Safeguards**:
  - Enforced input boundary guards: non-positive area ($\le 0$) and negative price ($< 0$) raise HTTP 422.
  - Added zero-division protections across all GDV, margin, and ROI formulas.
  - Attached statutory regulatory notes citing Maharashtra UDCPR 2020 and ROW road width dependencies.
- **Documentation & Verification**:
  - Published `PHASE_1_7_DATA_INTEGRITY_REPORT.md` and `SCIENTIFIC_VALIDATION.md`.
  - Added `backend/tests/test_geospatial_integrity.py` with 22 rigorous tests.
  - Total test suite expanded to 49 tests (100% pass rate).
  - Production frontend build validated with 0 errors.

---

## [Phase 1.6] — 2026-11-05
### Added: Land Intelligence Studio & Geospatial Proximity Engine
- **Dedicated Real Estate Intelligence Experience**:
  - Built comprehensive `ParcelProfileModal.tsx` organized into 6 professional sections:
    - **A. Overview & Cadastre**: Asking price, price per acre, area (acres & sq.ft), classification, PMRDA cadastral attribution.
    - **B. Geographic Intelligence**: WGS-84 survey coordinates, elevation (560m MSL), arterial frontage, OpenStreetMap geospatial grounding.
    - **C. Infrastructure Intelligence**: Multi-sector Haversine distance analysis and drive-time calculations to nearest Highways, Hospitals, Universities, Railway Stations, Airports, and Commercial Hubs.
    - **D. Development Feasibility**: Modular typology scenarios (Residential, Commercial, Mixed, Industrial), configurable FSI and construction cost sliders, BUA calculations, infrastructure requirements, and regulatory constraints.
    - **E. Financial Intelligence**: 3-tier financial scenarios (Conservative, Baseline, Optimistic), 3-year phased cash flow schedule, and break-even sales absorption percentage.
    - **F. Quantum Intelligence**: QAOA QUBO Hamiltonian eligibility, utility and risk contributions, ground state selection status, and anti-quantum-washing disclaimers.
- **Geospatial & Map Intelligence (`PuneMap.tsx`)**:
  - Integrated OpenStreetMap raster tiles without watermarks.
  - Added toggleable Regional Infrastructure Anchors (Highways, Hospitals, Educational Institutions, Railway Stations, Airports, IT Clusters).
  - Synchronized selection across GIS Map, 3D City Twin, and Land Studio card list.
  - Added interactive popup with "Open Detailed Profile" trigger.
- **Backend Infrastructure & Feasibility Engines**:
  - `backend/app/engines/real_estate/infrastructure_analysis.py`: Haversine great-circle distance math and verified Pune regional anchor dictionary.
  - `backend/app/engines/real_estate/development_feasibility.py`: Deterministic BUA, construction hard cost, soft cost, contingency, GDV, and preliminary ROI calculations conforming to NBC 2016 and PMRDA benchmarks.
  - `backend/app/engines/real_estate/financial_analysis.py`: Multi-scenario sensitivity modeling and 3-year annual cash flow schedules.
  - `backend/app/api/routes_land.py`: New endpoints for parcel search/filter, full master profiles (`GET /api/parcels/{id}`), infrastructure proximity (`GET /api/parcels/{id}/infrastructure`), feasibility simulation (`POST /api/parcels/{id}/feasibility`), and financial scenario modeling (`POST /api/parcels/{id}/financial`).
- **Automated Testing Suite**:
  - Added `backend/tests/test_real_estate_studio.py` covering 13 unit and integration test cases with 100% pass rate. Total test suite expanded to 27 tests.

---

## [Phase 1.5] — 2026-11-05
### Added: Live Backend-Frontend & Quantum Execution Integration
- Replaced synthetic mock timeouts with live FastAPI network calls.
- Connected Qiskit Aer QAOA simulator returning real variational rotation angles ($\gamma^*, \beta^*$) via SciPy COBYLA.
- Integrated live $8 \times 8$ QUBO Hamiltonian matrix into `QUBOHeatmap.tsx`.
- Standardized demonstration budget baseline to ₹40.0 Crore.
- Published `PHASE_1_5_INTEGRATION_REPORT.md` and `QUANTUM_ESTATE_X_INTEGRATION_AUDIT.md`.

---

## [Phase 1.0] — 2026-11-04
### Initial Release: Architectural Foundation
- FastAPI backend scaffold with Pune land dataset (`_PUNE_PARCELS`).
- Qiskit Aer QAOA formulation with Classical baselines (MILP, Simulated Annealing, Greedy).
- React 19 + Three.js 3D City Twin and Leaflet GIS mapping scaffold.
