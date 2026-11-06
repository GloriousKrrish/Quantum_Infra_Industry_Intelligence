r"""
angle_encoding.py - Quantum Angle & Rotation Encoding.

Encodes continuous feature vectors x in R^d into rotation angles of single-qubit
Pauli rotation gates (RX, RY, RZ, or combined Euler rotations).

Mathematical Formulations:
  For one-to-one mapping (x_i -> Qubit i):
  1. RY Encoding:
     |ψ_x> = \bigotimes_{i=0}^{n-1} R_Y(x_i) |0>
           = \bigotimes_{i=0}^{n-1} [ cos(x_i / 2) |0> + sin(x_i / 2) |1> ]
     Produces real-valued statevectors with tunable amplitudes.
     
  2. RX Encoding:
     |ψ_x> = \bigotimes_{i=0}^{n-1} R_X(x_i) |0>
           = \bigotimes_{i=0}^{n-1} [ cos(x_i / 2) |0> - i sin(x_i / 2) |1> ]
           
  3. RZ Encoding:
     |ψ_x> = \bigotimes_{i=0}^{n-1} R_Z(x_i) |+>   (with initial Hadamard layer)
           = \bigotimes_{i=0}^{n-1} (1 / sqrt(2)) [ |0> + e^{i x_i} |1> ]
           
  4. Combined Euler Rotation Encoding (Dense 3:1 mapping):
     Encodes up to 3 features per qubit: U(θ_1, θ_2, θ_3) = R_Z(x_{3i+2}) R_Y(x_{3i+1}) R_X(x_{3i})
"""

from typing import Dict, List, Optional, Any, Union
import numpy as np

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from .base_encoder import BaseQuantumEncoder


class AngleEncoder(BaseQuantumEncoder):
    """
    Encodes continuous features into single-qubit Pauli rotation angles.
    """

    SUPPORTED_ROTATIONS = ("rx", "ry", "rz", "combined")
    SUPPORTED_MAPPINGS = ("one_to_one", "dense", "cyclic")

    def __init__(
        self,
        rotation: str = "ry",
        mapping: str = "one_to_one",
        num_qubits: Optional[int] = None,
        scaling: float = 1.0,
        use_hadamard_for_rz: bool = True,
    ):
        """
        Args:
            rotation: 'rx', 'ry', 'rz', or 'combined'
            mapping: 'one_to_one' (1 feature per qubit), 'dense' (up to 3 per qubit), 'cyclic'
            num_qubits: Optional explicit qubit count
            scaling: Multiplier applied to input features (e.g., np.pi, 2*np.pi)
            use_hadamard_for_rz: If True, applies initial H gates for RZ encoding to create relative phase.
        """
        rot = rotation.lower()
        if rot not in self.SUPPORTED_ROTATIONS:
            raise ValueError(
                f"Unsupported rotation: '{rotation}'. Supported: {self.SUPPORTED_ROTATIONS}"
            )
        map_mode = mapping.lower()
        if map_mode not in self.SUPPORTED_MAPPINGS:
            raise ValueError(
                f"Unsupported mapping: '{mapping}'. Supported: {self.SUPPORTED_MAPPINGS}"
            )

        super().__init__(name=f"angle_encoding_{rot}", num_qubits=num_qubits)
        self.rotation = rot
        self.mapping = map_mode
        self.scaling = float(scaling)
        self.use_hadamard_for_rz = use_hadamard_for_rz

    def validate_input(self, data: Any) -> np.ndarray:
        """
        Validates continuous feature vector.
        """
        arr = np.asarray(data, dtype=float)
        if arr.ndim != 1:
            raise ValueError(f"Angle encoding requires 1D vector, got shape {arr.shape}")
        if arr.size == 0:
            raise ValueError("Input vector cannot be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("Input vector contains NaN, Inf, or non-finite values")
        return arr

    def determine_qubit_count(self, d: int) -> int:
        """
        Calculates required qubits given feature dimension d and mapping strategy.
        """
        if self._num_qubits is not None:
            return self._num_qubits

        if self.mapping == "one_to_one":
            return d
        elif self.mapping == "dense":
            # Up to 3 features per qubit in combined mode
            return max(1, (d + 2) // 3)
        elif self.mapping == "cyclic":
            return min(d, 8)  # Default bounded cyclic
        return d

    def build_circuit(self, data: Any) -> QuantumCircuit:
        """
        Builds the single-qubit angle rotation circuit.
        """
        features = self.validate_input(data) * self.scaling
        d = len(features)
        n_qubits = self.determine_qubit_count(d)

        qc = QuantumCircuit(n_qubits, name=f"angle_{self.rotation}")

        # If RZ encoding and hadamard requested, initialize in |+>
        if self.rotation == "rz" and self.use_hadamard_for_rz:
            for q in range(n_qubits):
                qc.h(q)

        if self.mapping == "one_to_one":
            limit = min(d, n_qubits)
            for i in range(limit):
                theta = float(features[i])
                if self.rotation == "rx":
                    qc.rx(theta, i)
                elif self.rotation == "ry":
                    qc.ry(theta, i)
                elif self.rotation == "rz":
                    qc.rz(theta, i)
                elif self.rotation == "combined":
                    # Single feature gets RY
                    qc.ry(theta, i)

        elif self.mapping == "dense":
            # 3 features per qubit: RZ(f3) RY(f2) RX(f1)
            for q in range(n_qubits):
                idx = q * 3
                f1 = float(features[idx]) if idx < d else 0.0
                f2 = float(features[idx + 1]) if (idx + 1) < d else 0.0
                f3 = float(features[idx + 2]) if (idx + 2) < d else 0.0

                if self.rotation == "combined":
                    if f1 != 0.0:
                        qc.rx(f1, q)
                    if f2 != 0.0:
                        qc.ry(f2, q)
                    if f3 != 0.0:
                        qc.rz(f3, q)
                else:
                    # Apply sum or selected rotation
                    if self.rotation == "rx":
                        qc.rx(f1, q)
                    elif self.rotation == "ry":
                        qc.ry(f1, q)
                    elif self.rotation == "rz":
                        qc.rz(f1, q)

        elif self.mapping == "cyclic":
            for i, feat in enumerate(features):
                q = i % n_qubits
                theta = float(feat)
                if self.rotation == "rx":
                    qc.rx(theta, q)
                elif self.rotation == "ry":
                    qc.ry(theta, q)
                elif self.rotation == "rz":
                    qc.rz(theta, q)
                elif self.rotation == "combined":
                    qc.ry(theta, q)

        return qc

    def compute_analytical_reference_state(self, data: Any) -> np.ndarray:
        """
        Independently constructs the theoretical statevector using direct Kronecker tensor products.
        Verifies that Qiskit's execution matches pure quantum mechanics.
        """
        features = self.validate_input(data) * self.scaling
        d = len(features)
        n = self.determine_qubit_count(d)

        # Single-qubit statevectors
        qubit_states = []
        for i in range(n):
            if i < d:
                theta = float(features[i])
            else:
                theta = 0.0

            if self.rotation == "ry":
                # R_y(θ)|0> = cos(θ/2)|0> + sin(θ/2)|1>
                state_1q = np.array([np.cos(theta / 2.0), np.sin(theta / 2.0)], dtype=complex)
            elif self.rotation == "rx":
                # R_x(θ)|0> = cos(θ/2)|0> - i sin(θ/2)|1>
                state_1q = np.array([np.cos(theta / 2.0), -1j * np.sin(theta / 2.0)], dtype=complex)
            elif self.rotation == "rz":
                if self.use_hadamard_for_rz:
                    # R_z(θ)|+> = 1/sqrt(2) [e^{-i θ/2}|0> + e^{i θ/2}|1>]
                    state_1q = np.array(
                        [np.exp(-1j * theta / 2.0) / np.sqrt(2.0), np.exp(1j * theta / 2.0) / np.sqrt(2.0)],
                        dtype=complex
                    )
                else:
                    # R_z(θ)|0> = e^{-i θ/2}|0>
                    state_1q = np.array([np.exp(-1j * theta / 2.0), 0.0], dtype=complex)
            else:
                # Combined Euler
                state_1q = np.array([np.cos(theta / 2.0), np.sin(theta / 2.0)], dtype=complex)

            qubit_states.append(state_1q)

        # Kronecker product for little-endian ordering: q_{n-1} \otimes ... \otimes q_0
        full_state = qubit_states[n - 1]
        for q_idx in range(n - 2, -1, -1):
            full_state = np.kron(full_state, qubit_states[q_idx])

        return full_state

    def verify_against_reference(self, data: Any) -> Dict[str, Any]:
        """
        Compares the actual Qiskit circuit Statevector against the independent Kronecker product.
        """
        ref_state = self.compute_analytical_reference_state(data)
        qc = self.build_circuit(data)
        sv = Statevector(qc)
        actual_state = np.asarray(sv.data, dtype=complex)

        overlap = np.vdot(ref_state, actual_state)
        fidelity = float(abs(overlap) ** 2)

        return {
            "fidelity": fidelity,
            "is_exact": bool(np.isclose(fidelity, 1.0, atol=1e-5)),
            "max_absolute_error": float(np.max(np.abs(ref_state - actual_state))),
        }

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "encoding_type": f"angle_{self.rotation}",
            "rotation": self.rotation,
            "mapping": self.mapping,
            "scaling": self.scaling,
            "description": f"Encodes features into single-qubit {self.rotation.upper()} rotation angles",
            "qubit_scaling": "O(d) qubits for one-to-one mapping; O(d/3) for dense mapping",
            "gate_scaling": "O(d) single-qubit rotation gates, 0 two-qubit gates",
            "depth_scaling": "O(1) circuit depth (parallel single-qubit rotations)",
        }
