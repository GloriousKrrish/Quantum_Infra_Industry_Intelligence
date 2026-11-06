"""
qaoa_circuit_builder.py - Parameterized QAOA Quantum Circuit Generator.

Constructs depth-p QAOA quantum circuits for Ising Hamiltonians:
  H_C = sum_{i < j} J_{ij} Z_i Z_j + sum_i h_i Z_i + c_0
  H_B = sum_i X_i

Supports arbitrary layer depth p, parameter binding, and circuit metric extraction.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector

from ..qubo.qubo_ising_converter import IsingModel


@dataclass
class QAOACircuitMetadata:
    num_qubits: int
    depth_p: int
    num_parameters: int
    circuit_depth: int
    gate_counts: Dict[str, int]
    cx_count: int
    rzz_count: int
    rz_count: int
    rx_count: int


class QAOACircuitBuilder:
    """
    Builds parameterized and bound QAOA quantum circuits using native Qiskit primitives.
    """

    def __init__(self, ising_model: IsingModel, depth_p: int = 1):
        if depth_p < 1:
            raise ValueError(f"QAOA depth p must be >= 1, got {depth_p}")
        self.ising_model = ising_model
        self.depth_p = depth_p
        self.n_qubits = ising_model.n_qubits

    def build_parameterized_circuit(self) -> Tuple[QuantumCircuit, ParameterVector, ParameterVector]:
        """
        Builds QAOA circuit with symbolic ParameterVectors for gammas and betas.
        Returns:
            (circuit, gammas_param_vec, betas_param_vec)
        """
        n = self.n_qubits
        p = self.depth_p

        gammas = ParameterVector("γ", p)
        betas = ParameterVector("β", p)

        qc = QuantumCircuit(n, name=f"QAOA_p{p}")

        # Initial state: Uniform superposition |+>^n
        for q in range(n):
            qc.h(q)

        # Apply p alternating problem and mixer layers
        for layer in range(p):
            gamma = gammas[layer]
            beta = betas[layer]

            # Cost Hamiltonian Unitary U(C, gamma) = exp(-i * gamma * H_C)
            # Quadratic terms: exp(-i * gamma * J_ij * Z_i * Z_j)
            for (i, j), J_ij in self.ising_model.quadratic_terms.items():
                if abs(J_ij) > 1e-12:
                    # Angle in RZZ is 2 * gamma * J_ij
                    qc.rzz(2.0 * float(J_ij) * gamma, i, j)

            # Linear terms: exp(-i * gamma * h_i * Z_i)
            for i, h_i in self.ising_model.linear_terms.items():
                if abs(h_i) > 1e-12:
                    # Angle in RZ is 2 * gamma * h_i
                    qc.rz(2.0 * float(h_i) * gamma, i)

            # Mixer Hamiltonian Unitary U(B, beta) = exp(-i * beta * H_B)
            # exp(-i * beta * sum X_i) = prod_i RX(2 * beta)
            for q in range(n):
                qc.rx(2.0 * beta, q)

        return qc, gammas, betas

    def build_bound_circuit(
        self,
        gammas: List[float],
        betas: List[float],
        with_measurements: bool = True
    ) -> QuantumCircuit:
        """
        Builds QAOA circuit with concrete numerical parameter values bound.
        """
        if len(gammas) != self.depth_p or len(betas) != self.depth_p:
            raise ValueError(
                f"Parameter lengths ({len(gammas)}, {len(betas)}) must match depth p={self.depth_p}"
            )

        qc_param, param_g, param_b = self.build_parameterized_circuit()

        param_dict = {}
        for l in range(self.depth_p):
            param_dict[param_g[l]] = float(gammas[l])
            param_dict[param_b[l]] = float(betas[l])

        bound_qc = qc_param.assign_parameters(param_dict)

        if with_measurements:
            meas_qc = QuantumCircuit(self.n_qubits, self.n_qubits, name=f"QAOA_p{self.depth_p}_meas")
            meas_qc.compose(bound_qc, inplace=True)
            meas_qc.measure(range(self.n_qubits), range(self.n_qubits))
            return meas_qc

        return bound_qc

    def get_circuit_metadata(self) -> QAOACircuitMetadata:
        """Extracts gate counts and structural properties of the circuit."""
        # Build bound with dummy 0 parameters to inspect concrete unrolled structure
        qc = self.build_bound_circuit([0.0] * self.depth_p, [0.0] * self.depth_p, with_measurements=False)
        decomp_qc = qc.decompose()

        counts = dict(decomp_qc.count_ops())
        return QAOACircuitMetadata(
            num_qubits=self.n_qubits,
            depth_p=self.depth_p,
            num_parameters=2 * self.depth_p,
            circuit_depth=decomp_qc.depth(),
            gate_counts=counts,
            cx_count=counts.get("cx", 0),
            rzz_count=counts.get("rzz", 0),
            rz_count=counts.get("rz", 0),
            rx_count=counts.get("rx", 0),
        )

