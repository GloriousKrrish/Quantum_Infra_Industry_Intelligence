"""
API routes for quantum optimization and benchmarking.
"""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np
from fastapi import APIRouter, HTTPException, Path

from backend.app.models.schemas import (
    BenchmarkComparison,
    CircuitSimulateRequest,
    CircuitSimulateResponse,
    DecoherenceSimulateRequest,
    DensityMatrixAnalyzeRequest,
    EntanglementAnalyzeRequest,
    ErrorCorrectionRequest,
    ExperimentTemplate,
    GateSpec,
    InterferenceSimulateRequest,
    MeasurementExperimentRequest,
    NoiseSimulateRequest,
    OptimizeRequest,
    QAOAResult,
    QuantumChannelRequest,
    QuantumInformationRequest,
    QUBOProblem,
    SolutionDecoding,
    StateEvolutionRequest,
    TomographyRequest,
)
from backend.app.engines.real_estate.land_intelligence import get_all_parcels
from backend.app.engines.quantum.qaoa_optimizer import (
    build_qubo_matrix,
    decode_solution,
    qubo_to_qubo_problem,
    run_qaoa,
)
from backend.app.engines.quantum.benchmarking import run_benchmark
from backend.app.engines.quantum.gate_library import (
    get_all_gate_specs,
    get_gate_spec,
)
from backend.app.engines.quantum.circuit_engine import CircuitValidationError
from backend.app.engines.quantum.simulation_engine import simulate_circuit
from backend.app.engines.quantum.experiment_library import (
    get_all_experiments,
    get_experiment_by_id,
)
from backend.app.engines.quantum.state_evolution import simulate_state_evolution
from backend.app.engines.quantum.density_matrix import analyze_density_matrix, DensityMatrixValidationError
from backend.app.engines.quantum.measurement_theory import execute_measurement_experiment
from backend.app.engines.quantum.interference import simulate_mach_zehnder
from backend.app.engines.quantum.quantum_information import analyze_quantum_information
from backend.app.engines.quantum.entanglement_analysis import analyze_entanglement_state
from backend.app.engines.quantum.noise_models import simulate_noisy_circuit
from backend.app.engines.quantum.decoherence import simulate_decoherence_trajectory
from backend.app.engines.quantum.error_correction import (
    simulate_3qubit_bit_flip_code,
    simulate_3qubit_phase_flip_code,
)
from backend.app.engines.quantum.quantum_channels import apply_quantum_channel
from backend.app.engines.quantum.tomography import perform_single_qubit_tomography

router = APIRouter(prefix="/api/quantum", tags=["Quantum Computing & Optimization"])


# ═══════════════════════════════════════════════════════════════════════
# 1. PHASE 02: QUANTUM COMPUTING FOUNDATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.get(
    "/gates",
    response_model=List[GateSpec],
    summary="Get library of supported quantum gates",
    description="Returns mathematical matrices, LaTeX representations, and metadata for single and multi-qubit gates.",
)
async def list_quantum_gates() -> List[Dict[str, Any]]:
    """Return all registered quantum gates."""
    return get_all_gate_specs()


@router.get(
    "/gates/{gate_id}",
    response_model=GateSpec,
    summary="Get specification for a single quantum gate",
    description="Returns unitary matrix and physical action for a single gate by ID (e.g. 'H', 'CX', 'RX').",
)
async def get_quantum_gate(
    gate_id: str = Path(..., description="Unique gate symbol (e.g. 'H', 'CX', 'RZ')"),
) -> Dict[str, Any]:
    """Return specification for a single gate."""
    spec = get_gate_spec(gate_id)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Quantum gate '{gate_id}' not found in gate library.")
    return spec


@router.post(
    "/circuit/simulate",
    response_model=CircuitSimulateResponse,
    summary="Simulate quantum circuit on Qiskit Aer",
    description=(
        "Executes a user-defined circuit on Qiskit Aer. Returns full complex statevector amplitudes, "
        "shot-based measurement counts, and scientifically accurate per-qubit reduced density matrices & Bloch vectors."
    ),
)
async def simulate_user_circuit(
    req: CircuitSimulateRequest,
) -> Dict[str, Any]:
    """Execute quantum circuit and return statevector and measurements."""
    try:
        raw_ops = [op.model_dump() for op in req.operations]
        result = simulate_circuit(
            num_qubits=req.num_qubits,
            operations=raw_ops,
            shots=req.shots,
        )
        return result
    except CircuitValidationError as cve:
        raise HTTPException(status_code=422, detail=str(cve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Quantum simulation error: {str(exc)}")


@router.get(
    "/experiments",
    response_model=List[ExperimentTemplate],
    summary="List pre-loaded reproducible quantum experiments",
    description="Returns catalog of 10 verified experiments including Bell states, GHZ state, interference, and teleportation.",
)
async def list_quantum_experiments() -> List[Dict[str, Any]]:
    """Return catalog of pre-loaded experiments."""
    return get_all_experiments()


@router.get(
    "/experiments/{exp_id}",
    response_model=ExperimentTemplate,
    summary="Get single experiment details and circuit",
    description="Returns the circuit operations, mathematical formula, and expected state for a given experiment ID.",
)
async def get_quantum_experiment(
    exp_id: str = Path(..., description="Experiment identifier (e.g. 'exp_bell_phi_plus')"),
) -> Dict[str, Any]:
    """Return a single experiment by ID."""
    exp = get_experiment_by_id(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{exp_id}' not found.")
    return exp


# ═══════════════════════════════════════════════════════════════════════
# 2. PHASE 03: ADVANCED QUANTUM MECHANICS & RESEARCH LAB ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.post(
    "/evolution/simulate",
    summary="Simulate continuous Hamiltonian quantum state evolution",
    description="Calculates |ψ(t)⟩ = exp(-iHt/ℏ)|ψ(0)⟩ for Pauli, Ising, Exchange, and Heisenberg Hamiltonians.",
)
async def simulate_evolution_endpoint(req: StateEvolutionRequest) -> Dict[str, Any]:
    try:
        return simulate_state_evolution(
            hamiltonian_type=req.hamiltonian_type,
            initial_state_name=req.initial_state_name,
            omega=req.omega,
            b_field=req.b_field,
            j_coupling=req.j_coupling,
            total_time=req.total_time,
            num_steps=req.num_steps,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evolution simulation error: {str(exc)}")


@router.post(
    "/density/analyze",
    summary="Validate and analyze density matrix spectral properties",
    description="Checks Hermiticity, unit trace, positive semidefiniteness, purity Tr(ρ²), and subsystem partial trace.",
)
async def analyze_density_matrix_endpoint(req: DensityMatrixAnalyzeRequest) -> Dict[str, Any]:
    try:
        return analyze_density_matrix(matrix_data=req.matrix_data, preset=req.preset)
    except DensityMatrixValidationError as dve:
        raise HTTPException(status_code=422, detail=str(dve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Density matrix analysis error: {str(exc)}")


@router.post(
    "/measurement/execute",
    summary="Execute projective quantum measurement and state collapse",
    description="Simulates measurement in Z, X, or Y basis with theoretical Born probabilities and collapsed post-measurement state.",
)
async def execute_measurement_endpoint(req: MeasurementExperimentRequest) -> Dict[str, Any]:
    try:
        raw_ops = [op.model_dump() for op in req.operations]
        return execute_measurement_experiment(
            circuit_ops=raw_ops,
            num_qubits=req.num_qubits,
            basis=req.basis,
            shots=req.shots,
            simulate_collapse_outcome=req.simulate_collapse_outcome,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Measurement error: {str(exc)}")


@router.post(
    "/interference/simulate",
    summary="Simulate Mach-Zehnder wave interference",
    description="Calculates constructive/destructive wave interference, continuous phase sweep fringes, and classical contrast.",
)
async def simulate_interference_endpoint(req: InterferenceSimulateRequest) -> Dict[str, Any]:
    try:
        return simulate_mach_zehnder(
            phase_theta=req.phase_theta,
            shots=req.shots,
            include_sweep=req.include_sweep,
            sweep_steps=req.sweep_steps,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Interference simulation error: {str(exc)}")


@router.post(
    "/information/analyze",
    summary="Compute Von Neumann entropy, quantum fidelity, and trace distance",
    description="Calculates S(ρ), Tr(ρ²), classical Shannon entropy, Jozsa fidelity, and verifies Fuchs-van de Graaf inequality bounds.",
)
async def analyze_information_endpoint(req: QuantumInformationRequest) -> Dict[str, Any]:
    try:
        return analyze_quantum_information(
            state_a_preset=req.state_a_preset,
            state_b_preset=req.state_b_preset,
            custom_state_a=req.custom_state_a,
            custom_state_b=req.custom_state_b,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Quantum information error: {str(exc)}")


@router.post(
    "/entanglement/analyze",
    summary="Advanced entanglement analysis: Schmidt decomposition, concurrence, and PPT negativity",
    description="Calculates Schmidt rank/coefficients, Wootters' concurrence C(ρ), and Peres-Horodecki PPT negativity.",
)
async def analyze_entanglement_endpoint(req: EntanglementAnalyzeRequest) -> Dict[str, Any]:
    try:
        return analyze_entanglement_state(
            preset=req.preset,
            werner_parameter_p=req.werner_parameter_p,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Entanglement analysis error: {str(exc)}")


@router.post(
    "/noise/simulate",
    summary="Simulate quantum circuit under Qiskit Aer noise models",
    description="Compares ideal vs. noisy circuit execution side-by-side for depolarizing, amplitude damping, phase damping, and thermal noise.",
)
async def simulate_noise_endpoint(req: NoiseSimulateRequest) -> Dict[str, Any]:
    try:
        raw_ops = [op.model_dump() for op in req.operations]
        return simulate_noisy_circuit(
            circuit_ops=raw_ops,
            num_qubits=req.num_qubits,
            noise_type=req.noise_type,
            error_prob=req.error_prob,
            gamma=req.gamma,
            lambda_param=req.lambda_param,
            shots=req.shots,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Noise simulation error: {str(exc)}")


@router.post(
    "/decoherence/simulate",
    summary="Simulate T1 relaxation and T2 dephasing trajectory",
    description="Calculates continuous time-series evolution of the Bloch vector, purity decay, and von Neumann entropy.",
)
async def simulate_decoherence_endpoint(req: DecoherenceSimulateRequest) -> Dict[str, Any]:
    try:
        return simulate_decoherence_trajectory(
            initial_state_name=req.initial_state_name,
            t1_us=req.t1_us,
            t2_us=req.t2_us,
            total_time_us=req.total_time_us,
            num_steps=req.num_steps,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Decoherence simulation error: {str(exc)}")


@router.post(
    "/error-correction/execute",
    summary="Execute 3-qubit bit-flip or phase-flip quantum error correction",
    description="Demonstrates non-local stabilizer encoding, error injection, syndrome diagnosis, and coherent state recovery.",
)
async def execute_error_correction_endpoint(req: ErrorCorrectionRequest) -> Dict[str, Any]:
    try:
        if req.code_type.lower() == "phase_flip":
            return simulate_3qubit_phase_flip_code(
                initial_state_theta=req.initial_state_theta,
                error_qubit=req.error_qubit,
                shots=req.shots,
            )
        else:
            return simulate_3qubit_bit_flip_code(
                initial_state_theta=req.initial_state_theta,
                error_qubit=req.error_qubit,
                shots=req.shots,
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error correction error: {str(exc)}")


@router.post(
    "/channel/apply",
    summary="Apply completely positive trace-preserving (CPTP) quantum channel",
    description="Calculates Kraus representation output, verifies completeness Σ E_k† E_k = I, and calculates output purity and fidelity.",
)
async def apply_channel_endpoint(req: QuantumChannelRequest) -> Dict[str, Any]:
    try:
        return apply_quantum_channel(
            channel_type=req.channel_type,
            input_state_preset=req.input_state_preset,
            param_p=req.param_p,
            gamma=req.gamma,
            lambda_param=req.lambda_param,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Quantum channel error: {str(exc)}")


@router.post(
    "/tomography/reconstruct",
    summary="Reconstruct quantum state from Pauli basis measurements",
    description="Performs state tomography via ⟨σ_x⟩, ⟨σ_y⟩, ⟨σ_z⟩ measurements, reconstructs density matrix, and computes fidelity.",
)
async def reconstruct_tomography_endpoint(req: TomographyRequest) -> Dict[str, Any]:
    try:
        raw_ops = [op.model_dump() for op in req.operations]
        return perform_single_qubit_tomography(circuit_ops=raw_ops, shots=req.shots)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Tomography error: {str(exc)}")


# ═══════════════════════════════════════════════════════════════════════
# 3. EXISTING QAOA REAL ESTATE OPTIMIZATION ENDPOINTS (PRESERVED)
# ═══════════════════════════════════════════════════════════════════════


@router.post(
    "/optimize",
    summary="Run QAOA optimization on parcel portfolio",
    description=(
        "Formulates the parcel selection QUBO and solves it with QAOA. "
        "Returns optimal bitstring, decoded portfolio, and QUBO details."
    ),
)
async def optimize_portfolio(
    req: OptimizeRequest,
) -> dict:
    """
    Run QAOA-based portfolio optimization.

    Steps:
    1. Fetch parcels within budget
    2. Build QUBO matrix
    3. Run QAOA
    4. Decode solution
    """
    parcels = get_all_parcels()
    if req.max_parcels:
        parcels = parcels[: req.max_parcels]

    Q, offset, var_names = build_qubo_matrix(
        parcels,
        req.budget_crore,
        lambda1=req.lambda_budget,
        lambda2=req.lambda_risk,
    )
    qubo_problem = qubo_to_qubo_problem(Q, offset, var_names)
    qaoa_result = run_qaoa(Q, p=req.qaoa_p, shots=req.qaoa_shots)
    decoded = decode_solution(qaoa_result.optimal_bitstring, parcels, req.budget_crore)

    return {
        "qaoa_result": qaoa_result,
        "qubo_formulation": qubo_problem,
        "decoded_solution": decoded,
        "budget_crore": req.budget_crore,
    }


@router.get(
    "/benchmark/{budget_crore}",
    response_model=BenchmarkComparison,
    summary="Run full QAOA vs Classical benchmark",
    description=(
        "Runs QAOA, brute-force, and simulated annealing on the same "
        "QUBO instance and returns comparative metrics."
    ),
)
async def benchmark(
    budget_crore: float = Path(..., gt=0, description="Total budget in ₹ Crore"),
) -> BenchmarkComparison:
    """Run the full benchmark suite."""
    parcels = get_all_parcels()
    comparison, _ = run_benchmark(parcels, budget_crore)
    return comparison
