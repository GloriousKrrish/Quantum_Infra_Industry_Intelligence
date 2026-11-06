r"""
basis_encoding.py - Computational Basis State Encoding.

Encodes an n-dimensional binary vector x in {0, 1}^n into the computational
basis state |x> = |x_{n-1} ... x_1 x_0> using single-qubit Pauli-X gates.

Mathematical Formulation:
  |ψ> = (X^{x_0} \otimes X^{x_1} \otimes ... \otimes X^{x_{n-1}}) |0>^{\otimes n}
  
Qubit Ordering Convention:
  Qiskit uses little-endian qubit indexing:
    Qubit 0 corresponds to the least-significant bit (2^0).
    Qubit n-1 corresponds to the most-significant bit (2^{n-1}).
  Under standard little-endian indexing (endianness='little'):
    x = [x_0, x_1, ..., x_{n-1}] maps x_i -> Qubit i.
    The resulting statevector has amplitude 1.0 at index k = sum_{i=0}^{n-1} x_i * 2^i.
"""

from typing import Dict, List, Optional, Any, Union
import numpy as np

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from .base_encoder import BaseQuantumEncoder


class BasisEncoder(BaseQuantumEncoder):
    """
    Encodes discrete binary vectors into quantum computational basis states.
    """

    def __init__(
        self,
        num_qubits: Optional[int] = None,
        endianness: str = "little",
    ):
        """
        Args:
            num_qubits: Optional fixed number of qubits. If None, inferred from input length.
            endianness: 'little' (default, x[0] -> Qubit 0, LSB) or 'big' (x[0] -> MSB).
        """
        super().__init__(name="basis_encoding", num_qubits=num_qubits)
        if endianness not in ("little", "big"):
            raise ValueError("endianness must be 'little' or 'big'")
        self.endianness = endianness

    def validate_input(self, data: Any) -> np.ndarray:
        """
        Validates binary data.
        Accepts:
          - List/ndarray of 0s and 1s, or booleans.
          - Binary string (e.g., '10101').
          - Non-negative integer if num_qubits is specified.
        Rejects:
          - Non-binary values (e.g. 2, -1, 0.5).
          - Non-numeric or invalid string formats.
          - Length mismatches if num_qubits is fixed.
        """
        if isinstance(data, str):
            # Parse bitstring
            cleaned = data.strip().replace(" ", "")
            if not all(c in ("0", "1") for c in cleaned):
                raise ValueError(f"String input contains non-binary characters: '{data}'")
            bits = np.array([int(c) for c in cleaned], dtype=int)
        elif isinstance(data, (int, np.integer)) and not isinstance(data, bool):
            if data < 0:
                raise ValueError(f"Integer input must be non-negative, got {data}")
            if self._num_qubits is None:
                raise ValueError("Must specify num_qubits when passing a bare integer to BasisEncoder")
            # Convert integer to bits
            bit_str = format(int(data), f"0{self._num_qubits}b")
            # If little-endian, reverse so index 0 is LSB
            bits = np.array([int(c) for c in reversed(bit_str)], dtype=int)
        else:
            arr = np.asarray(data)
            if arr.ndim != 1:
                raise ValueError(f"Basis encoding requires 1D vector, got shape {arr.shape}")
            if arr.size == 0:
                raise ValueError("Basis encoding input vector cannot be empty")
            
            # Check for non-finite or non-integer values
            if not np.issubdtype(arr.dtype, np.number) and not np.issubdtype(arr.dtype, np.bool_):
                raise TypeError(f"Invalid dtype for basis encoding: {arr.dtype}")
            
            if np.issubdtype(arr.dtype, np.floating):
                # Verify floats are exactly 0.0 or 1.0
                if not np.all(np.isin(arr, [0.0, 1.0])):
                    raise ValueError(f"Floating-point input must only contain 0.0 and 1.0. Found: {arr}")
            else:
                if not np.all(np.isin(arr, [0, 1])):
                    raise ValueError(f"Integer input must only contain 0 and 1. Found: {arr}")
            
            bits = arr.astype(int)

        if self._num_qubits is not None and len(bits) != self._num_qubits:
            raise ValueError(
                f"Input length {len(bits)} does not match configured num_qubits {self._num_qubits}"
            )

        return bits

    def build_circuit(self, data: Any) -> QuantumCircuit:
        """
        Builds the computational basis state preparation circuit.
        """
        bits = self.validate_input(data)
        n = len(bits)
        qc = QuantumCircuit(n, name="basis_enc")

        for idx, bit in enumerate(bits):
            if bit == 1:
                qubit_target = idx if self.endianness == "little" else (n - 1 - idx)
                qc.x(qubit_target)

        return qc

    def get_basis_index(self, data: Any) -> int:
        """
        Calculates the exact integer index in the statevector where amplitude should be 1.0.
        """
        bits = self.validate_input(data)
        n = len(bits)
        if self.endianness == "little":
            # x[i] is at 2^i
            return int(sum(int(bits[i]) * (2 ** i) for i in range(n)))
        else:
            # x[0] is MSB: 2^(n - 1 - i)
            return int(sum(int(bits[i]) * (2 ** (n - 1 - i)) for i in range(n)))

    def verify_measurement(self, data: Any, shots: int = 1024, seed: int = 42) -> Dict[str, Any]:
        """
        Simulates shot measurement on AerSimulator to verify 100% deterministic collapse to |x>.
        """
        bits = self.validate_input(data)
        n = len(bits)
        qc = self.build_circuit(bits)
        qc.measure_all()

        backend = AerSimulator(seed_simulator=seed)
        result = backend.run(qc, shots=shots).result()
        counts = result.get_counts()

        expected_idx = self.get_basis_index(bits)
        expected_bitstring = format(expected_idx, f"0{n}b")

        measured_bitstring = max(counts, key=counts.get)
        accuracy = counts.get(expected_bitstring, 0) / shots

        return {
            "expected_bitstring": expected_bitstring,
            "measured_counts": counts,
            "is_deterministic": len(counts) == 1 and measured_bitstring == expected_bitstring,
            "accuracy": accuracy,
        }

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "encoding_type": "basis",
            "endianness": self.endianness,
            "description": "Encodes binary vector x in {0,1}^n into computational basis state |x> using X gates",
            "qubit_scaling": "O(n) qubits for n binary features",
            "gate_scaling": "O(n) single-qubit X gates, 0 two-qubit gates",
            "depth_scaling": "O(1) circuit depth (all X gates execute in parallel)",
        }
