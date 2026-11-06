"""
measurement.py - Quantum Measurement & Expectation Value Operator.

Computes Hermitian observable expectation values <M> and maps them to
calibrated class probabilities P(y) for binary classification.

Mathematical Formulations:
  Observable Z_0 (Qubit 0 Pauli-Z):
    M = I^{⊗(n-1)} ⊗ Z
    In Qiskit little-endian Pauli string: 'I...IZ'
    
  Expectation Value:
    <Z_0> = <ψ| Z_0 |ψ> = P(q_0 = 0) - P(q_0 = 1) ∈ [-1, +1]
    
  Binary Probability Calibration:
    P(y = 0) = (1 + <Z_0>) / 2
    P(y = 1) = (1 - <Z_0>) / 2
    
  Decision Rule:
    y_pred = 1 if P(y=1) >= threshold (default 0.5, i.e. <Z_0> <= 0) else 0
"""

from typing import Dict, Any, Optional, Tuple
import numpy as np

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_aer import AerSimulator

from .config import MeasurementConfig


class VQCMeasurementEngine:
    """
    Evaluates quantum observables and extracts class probabilities.
    """

    def __init__(self, num_qubits: int, config: Optional[MeasurementConfig] = None):
        self.num_qubits = num_qubits
        self.config = config or MeasurementConfig()
        self.observable_type = self.config.observable_type.lower()
        self.shots = self.config.shots
        self.seed = self.config.seed

        self._observable = self._build_observable()

    @property
    def observable(self) -> SparsePauliOp:
        return self._observable

    def _build_observable(self) -> SparsePauliOp:
        """Constructs Qiskit SparsePauliOp observable."""
        n = self.num_qubits
        if self.observable_type == "parity_z":
            # Z on every qubit: 'ZZ...Z'
            return SparsePauliOp("Z" * n)
        else:
            # Default 'z0': Qubit 0 has Z, all others I.
            # Qiskit endianness: Qubit 0 is rightmost char
            pauli_str = ("I" * (n - 1)) + "Z"
            return SparsePauliOp(pauli_str)

    def evaluate_circuit(self, circuit: QuantumCircuit) -> Tuple[float, np.ndarray]:
        """
        Executes circuit and returns (expectation_value, probabilities_array [P(0), P(1)]).
        """
        if self.shots is None or self.shots <= 0:
            # Mode 1: Exact Statevector evaluation (fast, deterministic, zero shot-noise)
            sv = Statevector(circuit)
            exp_val = float(sv.expectation_value(self._observable).real)
        else:
            # Mode 2: Finite shot measurement on AerSimulator
            meas_qc = circuit.copy()
            meas_qc.measure_all()
            backend = AerSimulator(seed_simulator=self.seed)
            result = backend.run(meas_qc, shots=self.shots).result()
            counts = result.get_counts()

            # For z0 observable: compare counts where qubit 0 is '0' vs '1'
            # In Qiskit bitstring 'b_{n-1}...b_1 b_0', qubit 0 is bitstring[-1]
            p0_counts = sum(cnt for bstr, cnt in counts.items() if bstr[-1] == "0")
            p1_counts = sum(cnt for bstr, cnt in counts.items() if bstr[-1] == "1")
            exp_val = float((p0_counts - p1_counts) / self.shots)

        # Numerical clamp to valid expectation range [-1.0, 1.0]
        exp_val = max(-1.0, min(1.0, exp_val))

        # Probability derivation
        p0 = (1.0 + exp_val) / 2.0
        p1 = (1.0 - exp_val) / 2.0

        # Strict normalization
        p0 = max(0.0, min(1.0, p0))
        p1 = max(0.0, min(1.0, p1))
        total_p = p0 + p1
        if total_p > 0:
            p0 /= total_p
            p1 /= total_p

        return exp_val, np.array([p0, p1], dtype=float)

    def expectation_to_probability(self, exp_val: float) -> Tuple[float, float]:
        """Converts raw expectation value <Z> to (P(0), P(1))."""
        clamped = max(-1.0, min(1.0, exp_val))
        p0 = (1.0 + clamped) / 2.0
        p1 = (1.0 - clamped) / 2.0
        return float(p0), float(p1)
