"""
qaoa_engine.py - Advanced Configurable QAOA Quantum-Classical Optimization Engine.

Implements parameterized Quantum Approximate Optimization Algorithm (QAOA)
with arbitrary depth p, multi-strategy parameter schedules, classical optimizer loops
(COBYLA, Nelder-Mead, SLSQP), full convergence history tracking, and Qiskit Aer simulation.

EXPLICIT SCIENTIFIC NOTE: All quantum computations run locally via classical CPU simulation
using Qiskit Aer. No quantum hardware execution or supremacy is claimed.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import time
from scipy.optimize import minimize

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from ..qubo.qubo_model import QUBOModel
from ..qubo.qubo_ising_converter import QUBOToIsingConverter, IsingModel
from .qaoa_circuit_builder import QAOACircuitBuilder, QAOACircuitMetadata
from .parameter_strategies import QAOAParameterInitializer, ParameterStrategy
from .measurement_decoder import MeasurementDecoder, QAOADecodedResult, BitstringMeasurement


@dataclass
class QAOAIterationPoint:
    iteration: int
    gammas: List[float]
    betas: List[float]
    energy: float


@dataclass
class QAOASolution:
    status: str
    success: bool
    depth_p: int
    shots: int
    optimizer_name: str
    iterations: int
    optimal_gammas: List[float]
    optimal_betas: List[float]
    optimal_bitstring: str  # Kept for backward compatibility (best sampled bitstring)
    best_sampled_bitstring: str
    most_frequent_bitstring: str
    optimal_vector: List[int]
    best_sampled_energy: float
    most_frequent_energy: float
    expected_energy: float
    ground_state_probability: float
    is_verified_ground_state: bool
    approximation_ratio: Optional[float]
    solve_time_ms: float
    circuit_metadata: Dict[str, Any]
    trajectory: List[QAOAIterationPoint]
    top_measurements: List[Dict[str, Any]]
    all_counts: Dict[str, int]
    solver_name: str = "QAOA (Qiskit Aer CPU Simulation)"
    hardware_disclaimer: str = (
        "Simulated locally on classical CPU via Qiskit Aer. "
        "No quantum physical device was accessed."
    )


class QAOAEngine:
    """
    Configurable QAOA Engine supporting arbitrary depth p and classical optimization.
    """

    def __init__(
        self,
        depth_p: int = 1,
        shots: int = 2048,
        optimizer_name: str = "COBYLA",
        maxiter: int = 50,
        strategy: ParameterStrategy = ParameterStrategy.LINEAR_RAMP,
        seed: Optional[int] = 42,
    ):
        if depth_p < 1 or depth_p > 5:
            raise ValueError(f"QAOA depth p must be between 1 and 5 for tractable CPU simulation, got {depth_p}")
        self.depth_p = depth_p
        self.shots = shots
        self.optimizer_name = optimizer_name.upper()
        self.maxiter = maxiter
        self.strategy = strategy
        self.seed = seed

    def solve(
        self,
        qubo: QUBOModel,
        known_ground_energy: Optional[float] = None
    ) -> QAOASolution:
        start_time = time.perf_counter()
        n = qubo.num_variables
        p = self.depth_p

        # Step 1: Convert QUBO to Ising model
        ising_model = QUBOToIsingConverter.convert(qubo)
        ising_hamiltonian = ising_model.to_qiskit_operator()
        c0 = ising_model.offset

        # Step 2: Initialize Circuit Builder
        circuit_builder = QAOACircuitBuilder(ising_model=ising_model, depth_p=p)
        qc_param, param_g, param_b = circuit_builder.build_parameterized_circuit()

        # Step 3: Parameter Initialization
        init_g, init_b = QAOAParameterInitializer.get_initial_parameters(
            depth_p=p,
            strategy=self.strategy,
            seed=self.seed
        )
        initial_params = np.array(init_g + init_b, dtype=float)

        # Step 4: Setup convergence tracking
        trajectory: List[QAOAIterationPoint] = []
        iteration_counter = [0]

        # Cost evaluation function using exact statevector
        def cost_function(params: np.ndarray) -> float:
            gammas = params[:p]
            betas = params[p:]

            param_dict = {}
            for l in range(p):
                param_dict[param_g[l]] = float(gammas[l])
                param_dict[param_b[l]] = float(betas[l])

            bound_qc = qc_param.assign_parameters(param_dict)
            sv = Statevector.from_instruction(bound_qc)
            # Expectation value: <psi | H_Ising | psi> (offset is already incorporated in SparsePauliOp identity term)
            energy = float(sv.expectation_value(ising_hamiltonian).real)

            iteration_counter[0] += 1
            if iteration_counter[0] <= 50 or iteration_counter[0] % 5 == 0:
                trajectory.append(
                    QAOAIterationPoint(
                        iteration=iteration_counter[0],
                        gammas=[round(float(g), 4) for g in gammas],
                        betas=[round(float(b), 4) for b in betas],
                        energy=round(energy, 6),
                    )
                )

            return energy

        # Step 5: Classical optimization loop
        optimizer_method = self.optimizer_name
        if optimizer_method not in ["COBYLA", "NELDER-MEAD", "SLSQP", "BFGS"]:
            optimizer_method = "COBYLA"

        res = minimize(
            fun=cost_function,
            x0=initial_params,
            method=optimizer_method,
            options={"maxiter": self.maxiter, "disp": False}
        )

        opt_gammas = res.x[:p].tolist()
        opt_betas = res.x[p:].tolist()
        expected_energy = float(res.fun)

        # Step 6: Sample from optimal circuit using AerSimulator
        bound_meas_qc = circuit_builder.build_bound_circuit(
            gammas=opt_gammas,
            betas=opt_betas,
            with_measurements=True
        )

        simulator = AerSimulator(seed_simulator=self.seed)
        sim_result = simulator.run(bound_meas_qc, shots=self.shots).result()
        raw_counts = sim_result.get_counts()

        # Step 7: Decode measurements
        decoder = MeasurementDecoder(qubo)
        decoded = decoder.decode_counts(
            raw_counts,
            ground_state_energy=known_ground_energy,
            top_k=15
        )

        # Step 8: Calculate approximation ratio if exact ground energy is available
        approx_ratio = None
        if known_ground_energy is not None:
            # For minimization: alpha = E_approx / E_optimal or standard definition
            if abs(known_ground_energy) > 1e-6:
                # If both are negative, ratio is E_min / E_sampled or similar;
                # standard definition when ground state is non-zero:
                approx_ratio = round(decoded.best_energy / known_ground_energy, 4)
            elif abs(decoded.best_energy - known_ground_energy) < 1e-4:
                approx_ratio = 1.0

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        circuit_meta = circuit_builder.get_circuit_metadata()

        most_freq_energy = qubo.evaluate_energy(decoded.most_probable_bitstring)
        is_ground = (
            known_ground_energy is not None
            and abs(decoded.best_energy - known_ground_energy) < 1e-4
        )

        return QAOASolution(
            status="OPTIMIZED" if res.success else "ITERATION_LIMIT_REACHED",
            success=bool(res.success),
            depth_p=p,
            shots=self.shots,
            optimizer_name=optimizer_method,
            iterations=int(iteration_counter[0]),
            optimal_gammas=[round(float(g), 6) for g in opt_gammas],
            optimal_betas=[round(float(b), 6) for b in opt_betas],
            optimal_bitstring=decoded.best_energy_bitstring,
            best_sampled_bitstring=decoded.best_energy_bitstring,
            most_frequent_bitstring=decoded.most_probable_bitstring,
            optimal_vector=[int(b) for b in decoded.best_energy_bitstring],
            best_sampled_energy=decoded.best_energy,
            most_frequent_energy=round(most_freq_energy, 6),
            expected_energy=round(expected_energy, 6),
            ground_state_probability=decoded.ground_state_probability,
            is_verified_ground_state=is_ground,
            approximation_ratio=approx_ratio,
            solve_time_ms=round(elapsed_ms, 2),
            circuit_metadata={
                "num_qubits": circuit_meta.num_qubits,
                "depth_p": circuit_meta.depth_p,
                "circuit_depth": circuit_meta.circuit_depth,
                "gate_counts": circuit_meta.gate_counts,
                "cx_count": circuit_meta.cx_count,
                "rzz_count": circuit_meta.rzz_count,
            },
            trajectory=trajectory[:40],  # keep compact for JSON response
            top_measurements=[
                {
                    "bitstring": m.bitstring,
                    "counts": m.counts,
                    "probability": round(m.probability, 4),
                    "energy": m.energy,
                    "is_ground_state": m.is_ground_state,
                }
                for m in decoded.top_measurements
            ],
            all_counts=raw_counts,
        )

