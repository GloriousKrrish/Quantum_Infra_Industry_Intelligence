"""
amplitude_encoding.py - Quantum Amplitude Encoding.

Encodes an arbitrary continuous feature vector x in C^d into the probability
amplitudes of an n-qubit quantum state |ψ_x>.

Mathematical Formulation:
  Given input vector x = [x_0, x_1, ..., x_{d-1}], compute the L2 norm:
    ||x||_2 = sqrt( sum_{i=0}^{d-1} |x_i|^2 )
  The normalized vector has components:
    c_i = x_i / ||x||_2   (for i < d)
    c_i = 0               (for d <= i < 2^n, zero-padded to power of 2)
  The prepared quantum state is:
    |ψ_x> = sum_{i=0}^{2^n - 1} c_i |i>
    
Resource & Complexity Analysis:
  - Qubit Scaling: O(log_2(d)) qubits. Exponentially compact space representation!
  - Gate & Depth Scaling: O(2^n) = O(d) CNOT gates and single-qubit rotations.
    Arbitrary state preparation without quantum RAM (qRAM) requires exponential
    gate synthesis via recursive Givens rotations / Mottonen isometries.
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import math

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from .base_encoder import BaseQuantumEncoder


class AmplitudeEncoder(BaseQuantumEncoder):
    """
    Encodes normalized continuous vectors into the amplitudes of an n-qubit state.
    """

    def __init__(
        self,
        num_qubits: Optional[int] = None,
        normalize: bool = True,
        pad_mode: str = "zeros",
    ):
        """
        Args:
            num_qubits: Optional fixed number of qubits. Must satisfy 2^num_qubits >= dimension.
            normalize: Automatically L2-normalize vectors if True.
            pad_mode: 'zeros' (pads with 0.0) to power-of-two dimension.
        """
        super().__init__(name="amplitude_encoding", num_qubits=num_qubits)
        self.normalize = normalize
        self.pad_mode = pad_mode

    def validate_input(self, data: Any) -> np.ndarray:
        """
        Validates continuous numeric data, checks finiteness and non-zero norm.
        """
        arr = np.asarray(data)
        if arr.ndim != 1:
            raise ValueError(f"Amplitude encoding requires 1D vector, got shape {arr.shape}")
        if arr.size == 0:
            raise ValueError("Input vector cannot be empty")

        if not np.issubdtype(arr.dtype, np.number):
            raise TypeError(f"Amplitude encoding requires numeric input, got dtype {arr.dtype}")

        if not np.all(np.isfinite(arr)):
            raise ValueError("Input vector contains NaN, Inf, or non-finite values")

        norm = float(np.linalg.norm(arr))
        if norm < 1e-12:
            raise ValueError(
                f"Zero-vector rejection: L2 norm is {norm:.2e} (< 1e-12). Cannot normalize the null vector."
            )

        # Cast to float or complex
        if np.iscomplexobj(arr):
            return arr.astype(complex)
        return arr.astype(float)

    def prepare_normalized_vector(self, data: Any) -> Tuple[np.ndarray, int]:
        """
        Validates, normalizes, and zero-pads the input vector to dimension 2^n.
        Returns: (padded_normalized_vector, num_qubits)
        """
        vec = self.validate_input(data)
        d = len(vec)

        # Determine required qubits
        min_qubits = max(1, math.ceil(math.log2(d)))
        if self._num_qubits is not None:
            if self._num_qubits < min_qubits:
                raise ValueError(
                    f"Configured num_qubits={self._num_qubits} is too small for vector of dimension {d}. "
                    f"Need at least {min_qubits} qubits (2^{min_qubits} = {2**min_qubits} >= {d})."
                )
            n_qubits = self._num_qubits
        else:
            n_qubits = min_qubits

        target_dim = 2 ** n_qubits

        # L2 Normalization
        if self.normalize:
            norm = np.linalg.norm(vec)
            norm_vec = vec / norm
        else:
            norm = np.linalg.norm(vec)
            if not np.isclose(norm, 1.0, atol=1e-5):
                raise ValueError(f"Vector is not normalized (norm = {norm:.6f}) and normalize=False")
            norm_vec = vec

        # Padding if d < target_dim
        if d < target_dim:
            padded = np.zeros(target_dim, dtype=norm_vec.dtype)
            padded[:d] = norm_vec
        else:
            padded = norm_vec

        # Re-verify unit norm on padded vector
        padded_norm = np.linalg.norm(padded)
        if not np.isclose(padded_norm, 1.0, atol=1e-7):
            padded = padded / padded_norm

        return padded, n_qubits

    def build_circuit(self, data: Any) -> QuantumCircuit:
        """
        Builds the Qiskit state preparation circuit via recursive isometry initialization.
        """
        padded_vec, n_qubits = self.prepare_normalized_vector(data)
        qc = QuantumCircuit(n_qubits, name="amp_enc")
        qc.initialize(padded_vec, list(range(n_qubits)))
        return qc

    def verify_state_preparation(self, data: Any) -> Dict[str, Any]:
        """
        Verifies that the statevector produced by Qiskit matches the theoretical target
        vector up to global phase.
        """
        padded_target, n_qubits = self.prepare_normalized_vector(data)
        qc = self.build_circuit(data)
        sv = Statevector(qc)
        sv_data = np.asarray(sv.data, dtype=complex)

        # Overlap <target | actual>
        overlap = np.vdot(padded_target, sv_data)
        fidelity = float(abs(overlap) ** 2)
        global_phase_rad = float(np.angle(overlap))

        is_valid = math.isclose(fidelity, 1.0, abs_tol=1e-4)

        return {
            "num_qubits": n_qubits,
            "target_dimension": len(padded_target),
            "statevector_fidelity": fidelity,
            "global_phase_rad": global_phase_rad,
            "is_valid": is_valid,
        }

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "encoding_type": "amplitude",
            "normalize": self.normalize,
            "pad_mode": self.pad_mode,
            "description": "Encodes vector x in R^d into state amplitudes |ψ> = sum c_i |i> on ceil(log2(d)) qubits",
            "qubit_scaling": "O(log_2(d)) qubits — logarithmic space compression",
            "gate_scaling": "O(d) = O(2^n) single-qubit rotations and CNOT gates",
            "depth_scaling": "O(d) circuit depth without specialized quantum RAM (qRAM)",
            "scientific_disclaimer": (
                "While amplitude encoding offers logarithmic qubit savings, preparing arbitrary "
                "states requires O(2^n) gate synthesis. It does not automatically guarantee "
                "computational advantage without efficient state preparation routines."
            ),
        }
