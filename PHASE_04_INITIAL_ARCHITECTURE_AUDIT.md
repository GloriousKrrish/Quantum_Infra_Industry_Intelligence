# QUANTUM ESTATE X
# PHASE 04 — ADVANCED QUANTUM OPTIMIZATION & QUANTUM-CLASSICAL HYBRID COMPUTING
## INITIAL ARCHITECTURE AUDIT & FORENSIC BLUEPRINT

**Platform**: QUANTUM ESTATE X — Real Estate, Infrastructure, AI & Quantum Computing Intelligence Ecosystem  
**Repository**: `GloriousKrrish/Quantum_Infra_Industry_Intelligence`  
**Branch**: `master`  
**Phase**: Phase 04 — Advanced Quantum Optimization & Quantum-Classical Hybrid Computing  
**Author**: Antigravity Senior Quantum Computing & Operations Research Architect  
**Date**: November 6, 2026  
**Document Status**: **APPROVED ARCHITECTURAL BLUEPRINT**  

---

## 1. EXECUTIVE SUMMARY & MISSION STATEMENT

Phase 04 transforms the existing embryonic QAOA prototype of QUANTUM ESTATE X into a **scientifically rigorous, modular, and extensible Quantum-Classical Optimization Research Engine**.

Prior to Phase 04, the platform featured an initial demonstration of QAOA ($p=2$) applied exclusively to a single, hardcoded land-parcel selection problem. While mathematically sound as an initial prototype, the existing implementation suffered from several architectural and computational limitations:
1. **Monolithic Coupling**: QUBO matrix construction was tightly coupled to specific `LandParcel` models rather than operating as a general-purpose combinatorial optimization engine.
2. **Missing Solvers**: Classical benchmarking was labeled as "MILP" in certain API responses, but was actually implemented via exhaustive $O(2^n)$ brute-force enumeration. True Mixed-Integer Linear Programming (MILP) with modern branch-and-bound and simplex backends (e.g., SciPy's HiGHS solver) was absent.
3. **Restricted Problem Scope**: The platform only supported a single quadratic penalty knapsack variant; facility location, construction resource allocation, multi-constraint knapsack, and risk-diversified portfolio selection were not implemented.
4. **Fixed QAOA Circuit Depth**: QAOA was restricted to $p \le 2$ without convergence trajectory tracking, parameter transfer heuristics, or multi-start optimization.
5. **One-Way Conversion**: Conversion from QUBO to Ising existed, but bidirectional transformation (Ising $\to$ QUBO) and rigorous coefficient validation were missing.

### Phase 04 Objective
Establish a clean, decoupled optimization pipeline where any business or urban planning problem can be formulated, converted to QUBO/Ising, validated, solved independently across classical (MILP, Brute-Force, Greedy, Simulated Annealing) and quantum (Qiskit Aer QAOA) solvers, benchmarked with reproducible metrics, and rendered across both research dashboards and the real-world MapLibre digital twin.

---

## 2. AUDIT OF THE EXISTING SYSTEM

### 2.1 Quantum Computing Foundation (Phase 02 Baseline)
- **Location**: `backend/app/engines/quantum/circuit_engine.py`, `gate_library.py`, `simulation_engine.py`, `experiment_library.py`
- **Capabilities**:
  - 14 unitary gates ($H, X, Y, Z, S, S^\dagger, T, T^\dagger, CX, CZ, SWAP, RX, RY, RZ$) with exact $2\times 2$ and $4\times 4$ complex unitary matrices.
  - Circuit validation verifying qubit index bounds, parameter finiteness, and gate applicability.
  - Qiskit Aer simulation engine producing exact statevector amplitudes, measurement shot counts, reduced density matrices, and 3D Bloch vectors.
  - Catalog of 10 pre-built canonical experiments (Superposition, Bell states $\Phi^\pm, \Psi^\pm$, GHZ state, Quantum Teleportation with feedforward, W-state).
- **Audit Assessment**: **STABLE & PRESERVED**. This foundation remains untouched and serves as the lower-level execution harness.

### 2.2 Quantum Mechanics Research Laboratory (Phase 03 Baseline)
- **Location**: `density_matrix.py`, `state_evolution.py`, `interference.py`, `entanglement_analysis.py`, `noise_models.py`, `decoherence.py`, `error_correction.py`, `tomography.py`
- **Capabilities**:
  - Multi-qubit density operator analysis (Hermiticity, trace, positive semi-definiteness, purity $\text{Tr}(\rho^2)$).
  - Continuous Schrödinger/Liouville-von Neumann state evolution under Heisenberg, Ising, and XY Hamiltonians.
  - Mach-Zehnder wave interference and phase fringe shifts.
  - Entanglement characterization: Schmidt decomposition, Wootters concurrence $C(\rho)$, Peres-Horodecki PPT negativity, Werner state entanglement boundaries.
  - Open system decoherence ($T_1$ relaxation, $T_2$ dephasing) and Qiskit Aer noise models.
  - 3-qubit bit-flip and phase-flip stabilizer quantum error correction.
  - Quantum state tomography via multi-basis Pauli matrix inversion.
- **Audit Assessment**: **STABLE & PRESERVED**. 84 tests in Phase 03 continue to pass; these advanced quantum physics tools are independent of combinatorial optimization.

### 2.3 Existing QAOA Implementation (`qaoa_optimizer.py`)
- **Location**: `backend/app/engines/quantum/qaoa_optimizer.py`
- **Current Logic**:
  - `build_qubo_matrix(parcels, budget, lambda1, lambda2)` constructs an $n \times n$ upper-triangular matrix $Q$ where diagonal terms combine negative utility and quadratic budget expansion: $Q_{ii} = -u_i + \lambda_1(c_i^2 - 2Bc_i)$ and off-diagonals combine cross-budget penalties $\lambda_1(2 c_i c_j)$ and proximity risk $\lambda_2 r_{ij}$.
  - `qubo_to_ising(Q)` substitutes $x_i = \frac{1 - z_i}{2}$ to produce a `SparsePauliOp` Hamiltonian with $I$, single-qubit $Z$, and two-qubit $ZZ$ couplings.
  - `_build_qaoa_circuit` constructs alternating cost $e^{-i\gamma H_C}$ (using $RZ$ and $CX-RZ-CX$ gadgets) and mixer $e^{-i\beta \sum X_i}$ (using $RX$) layers.
  - `_evaluate_qaoa_energy` executes `AerSimulator(method="statevector")` for given $(\gamma, \beta)$ and computes expectation $\langle x | Q | x \rangle$.
  - Optimization is performed via `scipy.optimize.minimize` using `method="COBYLA"`.
  - Fallback pure-NumPy matrix exponential simulation exists for environments without Qiskit.
- **Deficiencies Identified**:
  1. *Coupling to Parcel Data*: Can only optimize arrays of `LandParcel` instances. It cannot accept an arbitrary QUBO problem from external data or different business domains.
  2. *Inefficient Optimization Loop*: In `_evaluate_qaoa_energy`, every iteration re-transpiles and runs `AerSimulator.run(qc, shots=shots)`. For 200 COBYLA iterations, this causes hundreds of separate simulation calls.
  3. *No Convergence Tracking*: The intermediate optimizer steps $(\gamma_k, \beta_k, E_k)$ are discarded, preventing the frontend from displaying optimization convergence curves.
  4. *Fixed Layer Structure*: Limited to small $p$; no parameter transfer (e.g. using $p=1$ optimal angles to warm-start $p=2$) or Fourier parameterization.

### 2.4 Existing Classical Solvers (`classical_optimizer.py` & `benchmarking.py`)
- **Location**: `backend/app/engines/classical_ai/classical_optimizer.py`
- **Current Logic**:
  - `run_brute_force(Q)` exhaustively checks all $2^n$ bitstrings for $n \le 20$.
  - `run_simulated_annealing(Q)` performs single-bit-flip Metropolis sampling with geometric cooling.
- **Deficiencies Identified**:
  1. *False MILP Attribution*: In `routes_map.py` line 544, the method name is surfaced as `"Exact Classical MILP"`, but the underlying execution was actually `run_brute_force`. If $n > 20$, it crashes with `ValueError: If n > 20 (would require > 1M evaluations)`.
  2. *Missing SciPy MILP Solver*: True Mixed-Integer Linear Programming via `scipy.optimize.milp` using modern branch-and-bound with the HiGHS backend was never implemented!
  3. *Missing Greedy Baseline*: No greedy approximation solver ($O(n \log n)$ value-to-cost heuristic) existed for standard knapsack comparison.

### 2.5 Optimization in Map Digital Twin (`routes_map.py`)
- **Location**: `backend/app/api/routes_map.py` (`POST /api/map/optimization/workflow`)
- **Current Logic**:
  - Accepts `budget_crore`, optional `candidate_parcel_ids`, `qaoa_p`, and `qaoa_shots`.
  - Calls `run_benchmark(selected_candidates, req.budget_crore, qaoa_p, qaoa_shots)`.
  - Extracts winning parcel coordinates and returns them for 3D MapLibre emerald glow visualization.
- **Audit Assessment**: **MUST BE PRESERVED**. The MapLibre digital twin relies on this endpoint for the interactive land allocation demonstration. The new optimization engine must back this endpoint seamlessly.

### 2.6 Environment & Dependencies
- **Qiskit**: `2.6.1` (Confirmed installed and operational)
- **Qiskit Aer**: `0.18.2` (Confirmed installed and operational)
- **SciPy**: `1.18.1` (Includes `scipy.optimize.milp`, `scipy.optimize.minimize`, `scipy.spatial.KDTree`)
- **NumPy**: `2.4.6`
- **FastAPI**: `0.115+`
- **React**: `19.0.0`
- **TypeScript**: `5.8+`
- **Vite**: `8.3.5`

---

## 3. CORE ARCHITECTURAL BLUEPRINT (PHASE 04)

Phase 04 organizes the optimization capabilities into a decoupled, layered package: `backend/app/engines/optimization/`.

```
backend/app/engines/optimization/
├── __init__.py                     # Package export of core classes
├── core/
│   ├── __init__.py
│   ├── problem_definition.py       # OptimizationProblem base class & metadata
│   ├── binary_variables.py         # Binary variable vector specification
│   ├── objective_functions.py      # Linear, quadratic, and interaction terms
│   └── constraint_manager.py       # Equality, inequality, and penalty encoders
├── qubo/
│   ├── __init__.py
│   ├── qubo_model.py               # QUBOModel dataclass (Q matrix, offset, names)
│   ├── qubo_builder.py             # General-purpose QUBO matrix builder
│   ├── qubo_validator.py           # Matrix symmetry, dimensions, and numerical checks
│   ├── qubo_ising_converter.py     # Bidirectional QUBO ⇄ Ising Hamiltonian translation
│   └── energy_evaluator.py         # Exact and expectation energy calculations
├── classical/
│   ├── __init__.py
│   ├── milp_solver.py              # Genuine scipy.optimize.milp solver (HiGHS backend)
│   ├── brute_force_solver.py       # Exact exhaustive search for small instances (n <= 20)
│   ├── greedy_solver.py            # High-speed O(n log n) heuristic baseline
│   └── simulated_annealing.py      # Single & multi-flip Metropolis metaheuristic
├── quantum/
│   ├── __init__.py
│   ├── qaoa_circuit_builder.py     # Parameterized Qiskit quantum circuit generator
│   ├── qaoa_engine.py              # Configurable QAOA engine (p=1..5, shots, seeds)
│   ├── parameter_strategies.py     # Random, linear ramp, warm-start, parameter transfer
│   └── measurement_decoder.py      # Bitstring frequency sorting, feasibility validation
├── problems/
│   ├── __init__.py
│   ├── knapsack.py                 # 0/1 Knapsack & multi-constraint knapsack
│   ├── portfolio.py                # Real Estate Portfolio with risk diversification & ROI
│   ├── facility_location.py        # P-median / p-center infrastructure & hospital siting
│   └── resource_allocation.py      # Construction equipment & capital distribution
└── hybrid/
    ├── __init__.py
    ├── hybrid_optimizer.py         # Unified quantum-classical execution orchestrator
    ├── benchmark_runner.py         # Head-to-head solver comparative performance runner
    └── performance_metrics.py      # Approximation ratio, optimality gap, runtime, energy
```

---

## 4. MATHEMATICAL FOUNDATIONS

### 4.1 General QUBO Formulation
A Quadratic Unconstrained Binary Optimization problem is defined over an $n$-dimensional binary vector $x \in \{0, 1\}^n$:
$$E(x) = x^T Q x + c_0 = \sum_{i=1}^n Q_{ii} x_i + \sum_{i < j} (Q_{ij} + Q_{ji}) x_i x_j + c_0$$
Because $x_i \in \{0, 1\}$, we have $x_i^2 = x_i$. Any linear term $c_i x_i$ is absorbed directly into the diagonal entry $Q_{ii}$.

To avoid double-counting and maintain mathematical rigor, the matrix $Q$ can be expressed in either:
1. **Upper-Triangular Convention**: $Q_{ij} = 0$ for $i > j$, with interaction coefficients placed entirely on $Q_{ij}$ ($i < j$).
2. **Symmetric Convention**: $Q_{\text{sym}} = \frac{Q + Q^T}{2}$, where off-diagonal couplings are distributed equally: $Q_{\text{sym}, ij} = Q_{\text{sym}, ji} = \frac{Q_{ij}}{2}$.

The Phase 04 engine supports **both conventions** and provides automated validation and canonicalization.

### 4.2 Exact Bidirectional QUBO $\longleftrightarrow$ Ising Conversion

#### A. QUBO $\longrightarrow$ Ising
We apply the canonical affine mapping from binary variables $x_i \in \{0, 1\}$ to Pauli spin eigenvalues $z_i \in \{-1, +1\}$:
$$x_i = \frac{1 - z_i}{2}$$

Substituting into $x^T Q x$ with symmetric matrix $Q$:
$$\begin{aligned}
x_i x_j &= \frac{1 - z_i - z_j + z_i z_j}{4} \\
x_i &= \frac{1 - z_i}{2}
\end{aligned}$$

The resulting Ising Hamiltonian takes the standard spin-glass form:
$$H_{\text{Ising}} = c_{\text{Ising}} \cdot I + \sum_{i=1}^n h_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j$$

Where the coefficients are given by exact closed-form expressions:
$$\begin{aligned}
J_{ij} &= \frac{Q_{ij} + Q_{ji}}{4} = \frac{Q_{\text{sym}, ij}}{2} \\
h_i &= -\frac{Q_{ii}}{2} - \sum_{j \ne i} \frac{Q_{ij} + Q_{ji}}{4} = -\frac{Q_{ii}}{2} - \sum_{j \ne i} \frac{Q_{\text{sym}, ij}}{2} \\
c_{\text{Ising}} &= \frac{1}{2} \sum_{i=1}^n Q_{ii} + \sum_{i < j} \frac{Q_{ij} + Q_{ji}}{4} + c_0
\end{aligned}$$

#### B. Ising $\longrightarrow$ QUBO
The inverse transformation maps spin variables $z_i \in \{-1, +1\}$ back to binary decisions $x_i \in \{0, 1\}$:
$$z_i = 1 - 2x_i$$

Substituting into the Ising Hamiltonian yields:
$$\begin{aligned}
Q_{ii} &= -2 h_i - 2 \sum_{j \ne i} J_{ij} \\
Q_{ij} &= 4 J_{ij} \quad (i < j) \\
c_0 &= c_{\text{Ising}} + \sum_{i=1}^n h_i + \sum_{i < j} J_{ij}
\end{aligned}$$

The Phase 04 engine implements both transformations and mathematically proves $E_{\text{QUBO}}(x) \equiv \langle x | H_{\text{Ising}} | x \rangle$ with test assertions enforcing $|E_{\text{QUBO}} - E_{\text{Ising}}| < 10^{-12}$.

---

## 5. OPTIMIZATION PROBLEM LIBRARY (MATHEMATICAL MODELS)

### 5.1 Knapsack Optimization

#### 0/1 Single-Constraint Knapsack
Given $n$ items with values $v_i > 0$ and weights $w_i > 0$, maximize total value subject to weight capacity $W$:
$$\max \sum_{i=1}^n v_i x_i \quad \text{subject to} \quad \sum_{i=1}^n w_i x_i \le W$$

In QUBO penalty formulation, we convert inequality to equality using slack binary variables $y_k \in \{0, 1\}$:
$$\sum_{i=1}^n w_i x_i + \sum_{k=0}^{K-1} 2^k y_k = W \quad \text{where } K = \lceil \log_2(W + 1) \rceil$$
$$H(x, y) = -\sum_{i=1}^n v_i x_i + \lambda \left( \sum_{i=1}^n w_i x_i + \sum_{k=0}^{K-1} 2^k y_k - W \right)^2$$

### 5.2 Real Estate Portfolio Selection
Given $n$ candidate development parcels with:
- Utility score $u_i \in [0, 1]$
- Acquisition cost $c_i > 0$ in ₹ Crore
- Expected Return on Investment $r_i > 0$ (percentage)
- Geographic location $(\text{lat}_i, \text{lng}_i)$ and zone concentration risk matrix $R_{ij} \in [0, 1]$
- Total capital budget $B$ in ₹ Crore

Objective function to minimize:
$$E(x) = -\sum_{i=1}^n (\alpha u_i + \beta r_i) x_i + \lambda_1 \left( \sum_{i=1}^n c_i x_i - B \right)^2 + \lambda_2 \sum_{i < j} R_{ij} x_i x_j$$

Expansion into quadratic matrix entries:
$$\begin{aligned}
Q_{ii} &= -(\alpha u_i + \beta r_i) + \lambda_1 (c_i^2 - 2 B c_i) \\
Q_{ij} &= 2 \lambda_1 c_i c_j + \lambda_2 R_{ij} \quad (i < j) \\
\text{offset} &= \lambda_1 B^2
\end{aligned}$$

### 5.3 Facility Location Optimization (Infrastructure & Hospital Siting)
Given $M$ customer demand centers (e.g. residential wards) and $N$ candidate facility sites (e.g. multi-specialty hospitals, logistics warehouses):
- $f_j$: Fixed capital cost to open facility at site $j$.
- $d_{ij}$: Metric distance / transport cost between demand center $i$ and candidate facility $j$.
- $p$: Target number of facilities to open.
- $y_j \in \{0, 1\}$: Binary variable indicating if facility $j$ is opened.
- $x_{ij} \in \{0, 1\}$: Binary variable indicating if demand center $i$ is serviced by facility $j$.

Formulation:
$$\min \sum_{j=1}^N f_j y_j + \sum_{i=1}^M \sum_{j=1}^N d_{ij} x_{ij}$$
$$\text{s.t.} \quad \sum_{j=1}^N x_{ij} = 1 \quad \forall i, \quad x_{ij} \le y_j \quad \forall i, j, \quad \sum_{j=1}^N y_j = p$$

Converted into a structured quadratic penalty Hamiltonian for QUBO/QAOA benchmarks.

### 5.4 Construction Resource Allocation & Scheduling
Given $T$ time slots and $K$ tasks requiring specialized machinery (cranes, excavators, batching plants) with capacity limits $C_t$:
- $x_{kt} \in \{0, 1\}$: Task $k$ scheduled at time $t$.
- Penalties enforce:
  1. Each task scheduled exactly once: $\sum_t x_{kt} = 1$.
  2. Resource limit at each time step: $\sum_k r_k x_{kt} \le C_t$.
  3. Precedence constraints: Task $A$ must complete before Task $B$ begins.

---

## 6. ADVANCED QAOA ENGINE ARCHITECTURE

### 6.1 Configurable Depth & Circuit Parameterization
The Quantum Approximate Optimization Algorithm evolves an initial equal superposition state under $p$ alternating layers of the problem Hamiltonian $H_C$ and the transverse-field mixer Hamiltonian $H_M = \sum_{i=1}^n X_i$:
$$|\psi(\boldsymbol{\gamma}, \boldsymbol{\beta})\rangle = \prod_{l=1}^p \left( e^{-i \beta_l \sum_{j=1}^n X_j} e^{-i \gamma_l H_C} \right) |+\rangle^{\otimes n}$$

```
|0⟩ ─ H ──■── RZ(2γ₁J₁₂) ──■── RZ(2γ₁h₁) ──── RX(2β₁) ── ... ──■── RZ(2γ_p J₁₂) ──■── RX(2β_p) ── M
          │                │                                    │                 │
|0⟩ ─ H ──X────────────────X── RZ(2γ₁h₂) ──── RX(2β₁) ── ... ──X─────────────────X── RX(2β_p) ── M
```

### 6.2 Parameter Initialization Strategies
1. **Random Small Perturbation**: $\gamma_l \in [-\frac{\pi}{4}, \frac{\pi}{4}]$, $\beta_l \in [-\frac{\pi}{4}, \frac{\pi}{4}]$.
2. **Linear Ramp Schedule (Annealing Heuristic)**:
   $$\gamma_l = \frac{l}{p} \Delta t, \quad \beta_l = \left(1 - \frac{l}{p}\right) \Delta t$$
3. **Layer Parameter Transfer (Warm-Start Depth)**: Optimal angles $(\boldsymbol{\gamma}^*, \boldsymbol{\beta}^*)$ obtained from a rapid $p=1$ simulation are interpolated to initialize $p=2$ and $p=3$ layers, drastically accelerating convergence.

### 6.3 Statevector vs Shot-Based Simulation
- **Statevector Execution**: Computes exact matrix expectation values $\langle \psi | H_C | \psi \rangle = \psi^\dagger H_C \psi$. Fast and deterministic for parameter optimization without statistical shot noise.
- **Shot-Based Sampling**: Samples $N_{\text{shots}} \in [512, 8192]$ from the final optimized statevector $|\psi(\boldsymbol{\gamma}^*, \boldsymbol{\beta}^*)\rangle$, reconstructing the actual empirical measurement probability distribution $P(x) = \frac{\text{count}(x)}{N_{\text{shots}}}$.

### 6.4 Convergence History Tracking
During classical optimization (COBYLA / Nelder-Mead / L-BFGS-B), the engine logs the optimization trajectory at every evaluation:
$$\text{Trajectory} = [ (\text{step}_k, \boldsymbol{\gamma}_k, \boldsymbol{\beta}_k, E_k) ]$$
This trajectory is returned to the frontend to render actual convergence curves in the research laboratory.

---

## 7. CLASSICAL BENCHMARKING ENGINE

| Classical Solver | Algorithmic Mechanism | Target Scale | Optimality Guarantee |
| :--- | :--- | :--- | :--- |
| **Exact Brute-Force** | Exhaustive enumeration of all $2^n$ state vectors | $n \le 20$ | **Global Optimum** |
| **SciPy MILP (HiGHS)** | Branch-and-bound with simplex and interior-point relaxations | $n \le 10,000$ | **Global Optimum** (within $\epsilon_{\text{tol}}$) |
| **Greedy Heuristic** | Sorts by value-to-cost density $v_i / c_i$ and greedily packs | Arbitrary $n$ | **Polynomial Approximation** |
| **Simulated Annealing** | Metropolis acceptance criterion with geometric temperature decay | $n \le 500$ | **Metaheuristic Near-Optimum** |
| **Random Baseline** | Uniform random sampling of feasible binary bitstrings | Arbitrary $n$ | **Statistical Baseline** |

### 7.1 True SciPy MILP Implementation
Phase 04 implements a genuine Mixed-Integer Linear Programming solver using `scipy.optimize.milp`:
$$\min c^T x \quad \text{subject to} \quad A_{\text{ub}} x \le b_{\text{ub}}, \quad A_{\text{eq}} x = b_{\text{eq}}, \quad x_i \in \{0, 1\}$$
For knapsack and portfolio problems, this provides sub-millisecond exact solutions that serve as the mathematically uncompromised ground truth for calculating QAOA approximation ratios.

### 7.2 Strict Approximation Ratio Definition
For an optimization problem with exact global optimum $E_{\text{MILP}}$ and QAOA expectation / best measured solution $E_{\text{QAOA}}$:
$$\alpha = \begin{cases} \frac{E_{\text{QAOA}}}{E_{\text{MILP}}} & \text{for maximization } (E > 0) \\ \frac{E_{\text{MILP}}}{E_{\text{QAOA}}} & \text{for minimization } (E < 0) \end{cases}$$
The engine enforces mathematical bounds: $\alpha \in [0.0, 1.0]$. If objectives are incomparable or sign conventions differ, the engine flags an error rather than outputting misleading ratios.

---

## 8. PROPOSED API ENDPOINTS (`/api/optimization/*`)

```
POST /api/optimization/problems/validate
     Validates problem parameters, variable bounds, and constraint feasibility.

POST /api/optimization/qubo/build
     Constructs upper-triangular and symmetric QUBO matrices for Knapsack, Portfolio,
     Facility Location, or Resource Allocation problems.

POST /api/optimization/qubo/validate
     Verifies matrix symmetry, diagonal absorption, and finite numerical values.

POST /api/optimization/qubo/convert
     Performs bidirectional QUBO ⇄ Ising conversion with exact Pauli operators.

POST /api/optimization/solve/classical
     Executes selected classical solver (MILP, Brute-Force, Greedy, Annealing).

POST /api/optimization/solve/qaoa
     Executes QAOA on Qiskit Aer with configurable depth (p=1..5), shots, and seed.
     Returns optimal bitstring, top solutions, and convergence history.

POST /api/optimization/solve/hybrid
     Executes hybrid comparative pipeline: Solves via MILP and QAOA simultaneously,
     computes approximation ratio, optimality gap, and solution feasibility.

POST /api/optimization/benchmark
     Runs complete comparative benchmark suite across all classical solvers and QAOA.

GET  /api/optimization/health
     Returns optimization engine health, solver availability (Qiskit Aer, SciPy HiGHS),
     and supported problem catalog.
```

---

## 9. FRONTEND RESEARCH LABORATORY SPECIFICATION

The frontend (`QuantumLab.tsx`) will be expanded with a dedicated **Quantum Optimization Laboratory** (`QuantumOptimizationLab.tsx`):

### 1. Problem Configuration Drawer
- Select problem domain: *Real Estate Portfolio*, *0/1 Knapsack*, *Facility Location (Hospital/Hub)*, *Resource Allocation*.
- Sliders for budget, risk penalty weight ($\lambda_2$), constraint penalty ($\lambda_1$).
- Pre-loaded sample instances and CSV dataset uploader.

### 2. QUBO & Ising Explorer
- Heatmap visualizer displaying $Q_{ij}$ coupling coefficients (`QUBOHeatmap.tsx`).
- Tabular breakdown of linear diagonal weights vs off-diagonal interaction couplings.
- Closed-form Ising spin-glass Hamiltonian representation with LaTeX notation ($h_i Z_i + J_{ij} Z_i Z_j$).

### 3. QAOA Experimenter
- Circuit depth selector: $p=1, 2, 3$.
- Shot count selector: $1024, 2048, 4096, 8192$.
- Optimizer selection: `COBYLA`, `Nelder-Mead`.
- Live convergence curve displaying energy $E_k$ vs optimizer iteration.
- Measurement distribution histogram showing probability of top observed bitstrings.

### 4. Head-to-Head Benchmarking Matrix
- Comparative table: Exact MILP vs QAOA vs Simulated Annealing vs Greedy.
- Key metrics: Objective value, execution runtime (ms), feasibility status, approximation ratio $\alpha$.
- Explicit scientific disclaimer: *"Qiskit Aer CPU classical simulation — Zero quantum hardware advantage claimed"*.

---

## 10. PRESERVATION GUARANTEES & NON-NEGOTIABLE PRINCIPLES

1. **No Regressions**: All 176 existing backend tests must continue to pass without failure or deprecation errors.
2. **Phase 02 & Phase 03 Preservation**: Gate library, circuit simulation, Bloch sphere, state evolution, density matrix, and quantum error correction modules remain untouched.
3. **MapLibre Digital Twin Continuity**: The existing map optimization workflow (`POST /api/map/optimization/workflow`) will be routed through the new engine without altering its external contract, preserving 3D building emerald glows.
4. **Honest Scientific Claims**: Explicit disclosure that Qiskit Aer simulation executes classically on workstation CPU cores. Zero claims of quantum advantage or quantum supremacy.
5. **Clean Phased Implementation**: Implementation will proceed strictly in milestones with continuous automated test verification at each step.

---

## 11. IMPLEMENTATION MILESTONES & ROADMAP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 04 IMPLEMENTATION ROADMAP                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  [M4.1] Core QUBO & Ising Engine (Models, Builders, Converters, Energy)     │
│  [M4.2] Classical Solver Suite (SciPy MILP, Brute-Force, Greedy, Annealing) │
│  [M4.3] Advanced QAOA Engine (Configurable p=1..5, Convergence, Strategies) │
│  [M4.4] Optimization Problem Library (Knapsack, Portfolio, Facility, Res)   │
│  [M4.5] Hybrid Execution Orchestrator & Benchmarking Runner                 │
│  [M4.6] FastAPI Optimization Router (/api/optimization/*) & Schemas         │
│  [M4.7] Frontend Quantum Optimization Laboratory & Interactive UI           │
│  [M4.8] Full Test Suite Verification, Audit Report & Documentation Updates   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Forensic Architecture Audit Completed & Certified for Implementation*  
*Date: November 6, 2026*
