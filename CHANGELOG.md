# CHANGELOG — QUANTUM ESTATE X

All notable changes to the Quantum Estate X platform are documented in this file.

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
