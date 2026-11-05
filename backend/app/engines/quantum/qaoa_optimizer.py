"""
QAOA-based QUBO Optimizer for Land Portfolio Selection.

This is the **core quantum engine** of Quantum Estate X.  It formulates
the land-parcel selection problem as a Quadratic Unconstrained Binary
Optimisation (QUBO) problem, converts it to an Ising Hamiltonian, and
solves it with the Quantum Approximate Optimization Algorithm (QAOA).

Mathematical formulation
────────────────────────
Binary variables:  x_i ∈ {0, 1}  for each parcel i ∈ {0, …, n-1}

Objective (maximise utility):
    max  Σ_i  u_i · x_i

Budget constraint (penalty form):
    min  λ₁ · (Σ_i c_i · x_i  −  B)²

Risk diversification penalty (discourages geographically clustered picks):
    min  λ₂ · Σ_{i<j}  r_{ij} · x_i · x_j

Combined QUBO (minimisation):
    min  x^T Q x
    Q_{ii}  = −u_i  +  λ₁·(c_i² − 2·B·c_i)
    Q_{ij}  =  λ₁·(2·c_i·c_j)  +  λ₂·r_{ij}      (i < j)
    offset  =  λ₁·B²

The QUBO matrix Q is converted to an Ising Hamiltonian via the
substitution  x_i = (1 − z_i) / 2  and passed to Qiskit's QAOA.

If Qiskit is unavailable the module falls back to a pure-NumPy
statevector simulation of a simplified QAOA ansatz.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

import numpy as np

from backend.app.engines.real_estate.land_intelligence import compute_utility_score
from backend.app.models.schemas import (
    LandParcel,
    QAOAResult,
    QUBOProblem,
    SolutionDecoding,
)

# ── Qiskit imports (with graceful fallback) ───────────────────────────
_QISKIT_AVAILABLE = False
try:
    from qiskit.quantum_info import SparsePauliOp
    from qiskit_aer import AerSimulator
    from qiskit.primitives import StatevectorEstimator
    from qiskit.circuit import QuantumCircuit, Parameter
    from scipy.optimize import minimize as scipy_minimize

    _QISKIT_AVAILABLE = True
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════════════════
# 1.  QUBO CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════


def _compute_risk_matrix(parcels: List[LandParcel]) -> np.ndarray:
    """
    Build a symmetric risk-coupling matrix based on geographic proximity.

    Parcels closer together receive a higher risk coupling (zone
    concentration risk).  Uses inverse-distance weighting normalised
    to [0, 1].
    """
    n = len(parcels)
    R = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            dlat = parcels[i].location_lat - parcels[j].location_lat
            dlng = parcels[i].location_lng - parcels[j].location_lng
            dist = np.sqrt(dlat ** 2 + dlng ** 2)
            # Inverse distance → higher coupling for nearby parcels
            # Cap minimum distance to avoid division by zero
            coupling = 1.0 / (1.0 + 50.0 * dist)
            # Boost coupling if same zone type
            if parcels[i].zone_type == parcels[j].zone_type:
                coupling *= 1.5
            R[i, j] = min(coupling, 1.0)
            R[j, i] = R[i, j]
    return R


def build_qubo_matrix(
    parcels: List[LandParcel],
    budget: float,
    lambda1: float = 10.0,
    lambda2: float = 1.0,
) -> Tuple[np.ndarray, float, List[str]]:
    """
    Construct the QUBO matrix Q for the land-portfolio optimisation.

    Args:
        parcels:  List of candidate parcels.
        budget:   Total budget in ₹ Crore.
        lambda1:  Penalty weight for the budget constraint.
        lambda2:  Penalty weight for risk diversification.

    Returns:
        (Q, offset, variable_names)
        - Q:  n×n upper-triangular QUBO matrix (numpy).
        - offset:  Constant energy offset λ₁·B².
        - variable_names:  Parcel names in variable order.
    """
    n = len(parcels)
    utilities = np.array([compute_utility_score(p) for p in parcels])
    costs = np.array([p.price_crore for p in parcels])
    risk_matrix = _compute_risk_matrix(parcels)

    Q = np.zeros((n, n), dtype=np.float64)

    # ── Diagonal terms ────────────────────────────────────────────────
    for i in range(n):
        # Negative utility (we minimise, so maximising utility = negative coeff)
        Q[i, i] = -utilities[i]
        # Budget constraint: λ₁·(c_i² − 2·B·c_i)
        Q[i, i] += lambda1 * (costs[i] ** 2 - 2.0 * budget * costs[i])

    # ── Off-diagonal terms (upper triangle only) ──────────────────────
    for i in range(n):
        for j in range(i + 1, n):
            # Budget constraint cross-term: λ₁·2·c_i·c_j
            Q[i, j] = lambda1 * 2.0 * costs[i] * costs[j]
            # Risk diversification penalty
            Q[i, j] += lambda2 * risk_matrix[i, j]

    offset = lambda1 * budget ** 2
    variable_names = [p.name for p in parcels]

    return Q, offset, variable_names


def qubo_to_qubo_problem(
    Q: np.ndarray,
    offset: float,
    variable_names: List[str],
) -> QUBOProblem:
    """Wrap raw QUBO arrays into a serialisable QUBOProblem model."""
    return QUBOProblem(
        Q_matrix=Q.tolist(),
        offset=offset,
        num_variables=Q.shape[0],
        variable_names=variable_names,
    )


# ═══════════════════════════════════════════════════════════════════════
# 2.  QUBO → ISING CONVERSION
# ═══════════════════════════════════════════════════════════════════════


def qubo_to_ising(Q: np.ndarray) -> Tuple:
    """
    Map a QUBO matrix to an Ising Hamiltonian.

    Substitution:  x_i = (1 − z_i) / 2

    Expanding  x^T Q x  under this substitution gives:

        H = const  +  Σ_i h_i·Z_i  +  Σ_{i<j} J_{ij}·Z_i·Z_j

    where:
        const = (1/4) Σ_{ij} Q_{ij}  −  (1/2) Σ_i Q_{ii}  +  Σ_i Q_{ii}/4
        h_i   = −(1/2) Q_{ii}  −  (1/4) Σ_{j≠i} (Q_{ij} + Q_{ji})
        J_{ij} = Q_{ij} / 4      (for i < j, with Q upper-triangular)

    Returns:
        If Qiskit is available: SparsePauliOp Hamiltonian
        Otherwise: (h_vec, J_matrix, const) as numpy arrays
    """
    n = Q.shape[0]
    # Symmetrise Q for the conversion
    Q_sym = (Q + Q.T) / 2.0

    # ── Compute Ising coefficients ────────────────────────────────────
    const = 0.0
    h = np.zeros(n, dtype=np.float64)
    J = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        const += Q_sym[i, i] / 4.0
        h[i] = -Q_sym[i, i] / 2.0
        for j in range(n):
            if i != j:
                h[i] -= Q_sym[i, j] / 4.0
                if i < j:
                    J[i, j] = Q_sym[i, j] / 4.0
                    const += Q_sym[i, j] / 4.0

    if not _QISKIT_AVAILABLE:
        return h, J, const

    # ── Build SparsePauliOp ───────────────────────────────────────────
    pauli_list = []

    # Identity (constant term)
    pauli_list.append(("I" * n, const))

    # Single-qubit Z terms
    for i in range(n):
        if abs(h[i]) > 1e-15:
            label = ["I"] * n
            label[n - 1 - i] = "Z"  # Qiskit uses big-endian ordering
            pauli_list.append(("".join(label), h[i]))

    # Two-qubit ZZ terms
    for i in range(n):
        for j in range(i + 1, n):
            if abs(J[i, j]) > 1e-15:
                label = ["I"] * n
                label[n - 1 - i] = "Z"
                label[n - 1 - j] = "Z"
                pauli_list.append(("".join(label), J[i, j]))

    hamiltonian = SparsePauliOp.from_list(pauli_list)
    return hamiltonian


# ═══════════════════════════════════════════════════════════════════════
# 3.  QAOA EXECUTION
# ═══════════════════════════════════════════════════════════════════════


def _build_qaoa_circuit(
    hamiltonian: "SparsePauliOp",
    num_qubits: int,
    p: int,
    gammas: np.ndarray,
    betas: np.ndarray,
) -> "QuantumCircuit":
    """
    Construct a parameterised QAOA circuit.

    |ψ(γ,β)⟩ = Π_{l=1}^{p}  e^{-iβ_l H_M}  e^{-iγ_l H_C}  |+⟩^n

    where H_C is the cost Hamiltonian and H_M = Σ X_i is the mixer.
    """
    qc = QuantumCircuit(num_qubits)

    # Initial state: |+⟩^n
    qc.h(range(num_qubits))

    for layer in range(p):
        # ── Cost unitary: e^{-iγ H_C} ────────────────────────────────
        # Decompose Hamiltonian into ZZ and Z gates
        for pauli_term in hamiltonian:
            label = pauli_term.paulis.to_labels()[0]
            coeff = float(np.real(pauli_term.coeffs[0]))

            z_qubits = [
                num_qubits - 1 - k
                for k, c in enumerate(label)
                if c == "Z"
            ]

            if len(z_qubits) == 0:
                # Identity — global phase, skip
                continue
            elif len(z_qubits) == 1:
                qc.rz(2.0 * gammas[layer] * coeff, z_qubits[0])
            elif len(z_qubits) == 2:
                q0, q1 = z_qubits
                qc.cx(q0, q1)
                qc.rz(2.0 * gammas[layer] * coeff, q1)
                qc.cx(q0, q1)

        # ── Mixer unitary: e^{-iβ H_M} = Π e^{-iβ X_i} ─────────────
        for q in range(num_qubits):
            qc.rx(2.0 * betas[layer], q)

    qc.measure_all()
    return qc


def _evaluate_qaoa_energy(
    params: np.ndarray,
    Q: np.ndarray,
    hamiltonian,
    num_qubits: int,
    p: int,
    shots: int,
) -> float:
    """
    Evaluate the expected QUBO energy for given QAOA parameters.

    Runs the QAOA circuit on AerSimulator and computes ⟨x|Q|x⟩
    weighted by measurement probabilities.
    """
    gammas = params[:p]
    betas = params[p:]

    qc = _build_qaoa_circuit(hamiltonian, num_qubits, p, gammas, betas)

    simulator = AerSimulator(method="statevector")
    qc_transpiled = qc
    result = simulator.run(qc_transpiled, shots=shots).result()
    counts = result.get_counts()

    # Compute expectation value
    total_shots = sum(counts.values())
    energy = 0.0
    for bitstring, count in counts.items():
        # Qiskit bitstrings are in big-endian; convert to variable vector
        bits = bitstring.replace(" ", "")
        x = np.array([int(b) for b in bits], dtype=np.float64)
        qubo_energy = x @ Q @ x
        energy += qubo_energy * (count / total_shots)

    return energy


def run_qaoa(
    Q: np.ndarray,
    p: int = 2,
    shots: int = 4096,
) -> QAOAResult:
    """
    Execute QAOA to solve the QUBO problem.

    Args:
        Q:      n×n QUBO matrix.
        p:      Number of QAOA layers (circuit depth parameter).
        shots:  Number of measurement shots.

    Returns:
        QAOAResult with optimal bitstring, top solutions, and timings.

    Raises:
        RuntimeError: If Qiskit is not installed and fallback fails.
    """
    num_qubits = Q.shape[0]
    t_start = time.perf_counter()

    if _QISKIT_AVAILABLE:
        return _run_qaoa_qiskit(Q, num_qubits, p, shots, t_start)
    else:
        return _run_qaoa_numpy_fallback(Q, num_qubits, p, shots, t_start)


def _run_qaoa_qiskit(
    Q: np.ndarray,
    num_qubits: int,
    p: int,
    shots: int,
    t_start: float,
) -> QAOAResult:
    """Full Qiskit-backed QAOA execution with COBYLA optimisation."""
    hamiltonian = qubo_to_ising(Q)

    # Initial parameters: random small values
    rng = np.random.default_rng(42)
    x0 = rng.uniform(-np.pi / 4, np.pi / 4, size=2 * p)

    # Optimise with COBYLA
    opt_result = scipy_minimize(
        _evaluate_qaoa_energy,
        x0,
        args=(Q, hamiltonian, num_qubits, p, shots),
        method="COBYLA",
        options={"maxiter": 200, "rhobeg": 0.5},
    )

    # Final evaluation with optimal parameters
    gammas_opt = opt_result.x[:p]
    betas_opt = opt_result.x[p:]

    qc = _build_qaoa_circuit(hamiltonian, num_qubits, p, gammas_opt, betas_opt)
    simulator = AerSimulator(method="statevector")
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts()

    t_elapsed = (time.perf_counter() - t_start) * 1000.0

    opt_params = {
        "gammas": [round(float(g), 4) for g in gammas_opt],
        "betas": [round(float(b), 4) for b in betas_opt],
    }

    return _process_counts(
        counts, Q, num_qubits, p, shots, t_elapsed, optimal_parameters=opt_params
    )


def _run_qaoa_numpy_fallback(
    Q: np.ndarray,
    num_qubits: int,
    p: int,
    shots: int,
    t_start: float,
) -> QAOAResult:
    """
    Pure-NumPy QAOA simulation for when Qiskit is unavailable.

    Uses exact statevector simulation with the QAOA ansatz applied
    as matrix exponentials.  Limited to ~16 qubits.
    """
    from scipy.optimize import minimize as sp_minimize

    N = 2 ** num_qubits

    # Pre-compute QUBO energies for all 2^n bitstrings
    energies = np.zeros(N, dtype=np.float64)
    for idx in range(N):
        x = np.array(
            [int(b) for b in format(idx, f"0{num_qubits}b")],
            dtype=np.float64,
        )
        energies[idx] = x @ Q @ x

    # Pre-compute mixer operator (sum of X_i) in computational basis
    # X_i flips bit i, so the mixer Hamiltonian connects states differing
    # by one bit flip.
    mixer_matrix = np.zeros((N, N), dtype=np.complex128)
    for idx in range(N):
        for q in range(num_qubits):
            flipped = idx ^ (1 << (num_qubits - 1 - q))
            mixer_matrix[idx, flipped] += 1.0

    def qaoa_expectation(params: np.ndarray) -> float:
        gammas = params[:p]
        betas = params[p:]

        # |+⟩^n = uniform superposition
        state = np.ones(N, dtype=np.complex128) / np.sqrt(N)

        for layer in range(p):
            # Cost unitary: e^{-iγ H_C}  (diagonal in computational basis)
            state *= np.exp(-1j * gammas[layer] * energies)

            # Mixer unitary: e^{-iβ H_M}
            # Use matrix exponentiation
            mixer_unitary = _matrix_exp(-1j * betas[layer] * mixer_matrix)
            state = mixer_unitary @ state

        # Probabilities
        probs = np.abs(state) ** 2
        return np.dot(probs, energies)

    rng = np.random.default_rng(42)
    x0 = rng.uniform(-np.pi / 4, np.pi / 4, size=2 * p)

    opt_result = sp_minimize(
        qaoa_expectation,
        x0,
        method="COBYLA",
        options={"maxiter": 200, "rhobeg": 0.5},
    )

    # Final state
    gammas_opt = opt_result.x[:p]
    betas_opt = opt_result.x[p:]
    state = np.ones(N, dtype=np.complex128) / np.sqrt(N)
    for layer in range(p):
        state *= np.exp(-1j * gammas_opt[layer] * energies)
        mixer_unitary = _matrix_exp(-1j * betas_opt[layer] * mixer_matrix)
        state = mixer_unitary @ state

    probs = np.abs(state) ** 2

    # Convert to counts-like dict
    counts: Dict[str, int] = {}
    for idx in range(N):
        if probs[idx] > 1e-8:
            bs = format(idx, f"0{num_qubits}b")
            counts[bs] = int(round(probs[idx] * shots))

    t_elapsed = (time.perf_counter() - t_start) * 1000.0
    opt_params = {
        "gammas": [round(float(g), 4) for g in gammas_opt],
        "betas": [round(float(b), 4) for b in betas_opt],
    }
    return _process_counts(
        counts, Q, num_qubits, p, shots, t_elapsed, optimal_parameters=opt_params
    )


def _matrix_exp(M: np.ndarray) -> np.ndarray:
    """
    Compute matrix exponential via eigendecomposition.

    For Hermitian M this is numerically stable and exact.
    """
    from scipy.linalg import expm

    return expm(M)


# ═══════════════════════════════════════════════════════════════════════
# 4.  RESULTS PROCESSING
# ═══════════════════════════════════════════════════════════════════════


def _process_counts(
    counts: Dict[str, int],
    Q: np.ndarray,
    num_qubits: int,
    p: int,
    shots: int,
    execution_time_ms: float,
    optimal_parameters: Optional[Dict[str, List[float]]] = None,
) -> QAOAResult:
    """Convert raw measurement counts into a structured QAOAResult."""
    total = sum(counts.values()) or 1

    # Evaluate QUBO energy for each measured bitstring
    evaluated: List[Tuple[str, float, float]] = []
    for bs, count in counts.items():
        bits = bs.replace(" ", "")
        x = np.array([int(b) for b in bits], dtype=np.float64)
        energy = float(x @ Q @ x)
        prob = count / total
        evaluated.append((bits, energy, prob))

    # Sort by energy (ascending — we minimise)
    evaluated.sort(key=lambda t: t[1])

    optimal_bs, optimal_val, _ = evaluated[0]

    # Top-10 bitstrings
    top_k = evaluated[:min(10, len(evaluated))]
    top_bitstrings = [t[0] for t in top_k]

    # Probability map (top 20 to keep payload small)
    probabilities = {t[0]: round(t[2], 6) for t in evaluated[:20]}

    return QAOAResult(
        optimal_bitstring=optimal_bs,
        optimal_value=round(optimal_val, 6),
        top_bitstrings=top_bitstrings,
        probabilities=probabilities,
        execution_time_ms=round(execution_time_ms, 2),
        circuit_depth=2 * p * (num_qubits + 1),  # Approximate depth
        num_qubits=num_qubits,
        optimal_parameters=optimal_parameters,
    )


# ═══════════════════════════════════════════════════════════════════════
# 5.  SOLUTION DECODING
# ═══════════════════════════════════════════════════════════════════════


def decode_solution(
    bitstring: str,
    parcels: List[LandParcel],
    budget: float,
) -> SolutionDecoding:
    """
    Decode a QUBO bitstring into a human-readable portfolio selection.

    Args:
        bitstring:  Binary string of length n, e.g. '10110011'.
        parcels:    Parcels in the same order as QUBO variables.
        budget:     Budget constraint in ₹ Crore.

    Returns:
        SolutionDecoding with selected parcels, costs, and compliance.
    """
    selected = []
    total_cost = 0.0
    total_utility = 0.0

    for i, bit in enumerate(bitstring):
        if bit == "1" and i < len(parcels):
            selected.append(parcels[i].name)
            total_cost += parcels[i].price_crore
            total_utility += compute_utility_score(parcels[i])

    return SolutionDecoding(
        selected_parcels=selected,
        total_cost_crore=round(total_cost, 2),
        total_utility=round(total_utility, 6),
        budget_compliant=total_cost <= budget,
    )
