"""
base_encoder.py - Abstract Base Class and Data Contracts for Quantum Data Encoders.

Defines the standard interface that all Quantum Machine Learning encoders must implement.
Guarantees consistent data ingestion, input validation, circuit construction,
statevector extraction, and resource metric analysis.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import numpy as np

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from .encoding_metrics import EncodingResourceMetrics, calculate_circuit_metrics


@dataclass
class EncodingResult:
    """
    Standardized result contract returned by any quantum data encoder.
    """
    circuit: QuantumCircuit
    input_data: np.ndarray
    statevector: np.ndarray
    probabilities: np.ndarray
    metrics: EncodingResourceMetrics
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_statevector_fidelity(self, target_statevector: np.ndarray) -> float:
        """
        Calculates quantum state fidelity F = |<target|statevector>|^2.
        """
        target = np.asarray(target_statevector, dtype=complex)
        actual = np.asarray(self.statevector, dtype=complex)
        if target.shape != actual.shape:
            raise ValueError(
                f"Dimension mismatch for fidelity: target {target.shape} vs actual {actual.shape}"
            )
        overlap = np.vdot(target, actual)
        return float(abs(overlap) ** 2)

    def get_dominant_state(self) -> Dict[str, Any]:
        """
        Returns the computational basis state with maximum probability.
        """
        max_idx = int(np.argmax(self.probabilities))
        n_qubits = self.circuit.num_qubits
        bitstring = format(max_idx, f"0{n_qubits}b")
        return {
            "index": max_idx,
            "bitstring": bitstring,
            "probability": float(self.probabilities[max_idx]),
            "amplitude": complex(self.statevector[max_idx]),
        }

    def to_dict(self) -> Dict[str, Any]:
        dom = self.get_dominant_state()
        return {
            "num_qubits": self.circuit.num_qubits,
            "input_dimension": len(self.input_data),
            "dominant_state": dom,
            "metrics": self.metrics.to_dict(),
            "metadata": self.metadata,
        }


class BaseQuantumEncoder(ABC):
    """
    Abstract interface for all Quantum Data Encoders.
    """

    def __init__(self, name: str, num_qubits: Optional[int] = None):
        self.name = name
        self._num_qubits = num_qubits

    @property
    def num_qubits(self) -> Optional[int]:
        return self._num_qubits

    @abstractmethod
    def validate_input(self, data: Any) -> np.ndarray:
        """
        Validates, sanitizes, and converts raw input data into a standardized numpy array.
        Raises ValueError or TypeError if input violates mathematical constraints.
        """
        pass

    @abstractmethod
    def build_circuit(self, data: Any) -> QuantumCircuit:
        """
        Constructs the Qiskit QuantumCircuit encoding the input data.
        """
        pass

    def encode(self, data: Any, transpile_metrics: bool = False) -> EncodingResult:
        """
        End-to-end encoding pipeline:
          1. Validates input
          2. Builds Qiskit QuantumCircuit
          3. Extracts Statevector & Born probabilities
          4. Inspects actual circuit instructions for resource metrics
        """
        cleaned_data = self.validate_input(data)
        circuit = self.build_circuit(cleaned_data)

        # Extract statevector via Qiskit Aer Statevector representation
        sv = Statevector(circuit)
        sv_data = np.asarray(sv.data, dtype=complex)
        probabilities = np.asarray(sv.probabilities(), dtype=float)

        metrics = calculate_circuit_metrics(circuit, transpile_to_basis=transpile_metrics)

        metadata = self.get_metadata()
        metadata["input_dimension"] = len(cleaned_data)
        metadata["encoder_name"] = self.name

        return EncodingResult(
            circuit=circuit,
            input_data=cleaned_data,
            statevector=sv_data,
            probabilities=probabilities,
            metrics=metrics,
            metadata=metadata,
        )

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns architectural specifications and hyperparameter details.
        """
        pass

    def get_resource_metrics(self, data: Any) -> EncodingResourceMetrics:
        """
        Returns resource metrics for a sample data vector without returning the full statevector.
        """
        cleaned_data = self.validate_input(data)
        circuit = self.build_circuit(cleaned_data)
        return calculate_circuit_metrics(circuit, transpile_to_basis=True)
