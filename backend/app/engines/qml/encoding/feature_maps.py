r"""
feature_maps.py - Instantaneous Quantum Polynomial (IQP) Style Feature Maps.

Implements non-linear quantum feature maps that embed classical data vectors
into quantum Hilbert space using Hadamard superposition layers, single-qubit
Z-phase rotations, and two-qubit CNOT-entangled ZZ phase interactions.

Mathematical Formulation (Havlíček et al., Nature 567, 209-212 (2019)):
  For input vector x in R^d:
  1. Superposition:
     H^{⊗n}
  2. Single-qubit phase layer:
     U_1(x) = \prod_{i=0}^{n-1} R_Z(2 x_i)
  3. Pairwise entangling ZZ interaction layer:
     U_2(x) = \prod_{(i, j) \in E} exp(i * \phi_{ij}(x) * Z_i Z_j)
     where \phi_{ij}(x) = 2 * (π - x_i) * (π - x_j)
     Synthesized as:
       CNOT(i, j) -> R_Z(2 * \phi_{ij}(x)) -> CNOT(i, j)
  4. Repetitions:
     U_IQP(x) = [ U_2(x) U_1(x) H^{⊗n} ]^R
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from qiskit import QuantumCircuit
from .base_encoder import BaseQuantumEncoder


class IQPFeatureMap(BaseQuantumEncoder):
    """
    IQP-style non-linear quantum feature map with entangling ZZ interactions.
    """

    SUPPORTED_ENTANGLEMENT = ("linear", "circular", "full")

    def __init__(
        self,
        num_qubits: Optional[int] = None,
        repetitions: int = 1,
        entanglement: str = "full",
        interaction_type: str = "havlicek",  # 'havlicek' ((pi-x)(pi-y)) or 'product' (x*y)
        alpha: float = 1.0,
    ):
        """
        Args:
            num_qubits: Optional fixed number of qubits. If None, inferred from feature dimension.
            repetitions: Number of feature map layers R >= 1.
            entanglement: 'linear', 'circular', or 'full' (all-to-all).
            interaction_type: 'havlicek' for 2*(pi-x)*(pi-y) or 'product' for 2*x*y.
            alpha: Scaling multiplier applied to angles.
        """
        if repetitions < 1:
            raise ValueError(f"Repetitions must be >= 1, got {repetitions}")
        ent = entanglement.lower()
        if ent not in self.SUPPORTED_ENTANGLEMENT:
            raise ValueError(
                f"Unsupported entanglement: '{entanglement}'. Supported: {self.SUPPORTED_ENTANGLEMENT}"
            )

        super().__init__(name="iqp_feature_map", num_qubits=num_qubits)
        self.repetitions = repetitions
        self.entanglement = ent
        self.interaction_type = interaction_type
        self.alpha = float(alpha)

    def validate_input(self, data: Any) -> np.ndarray:
        """
        Validates continuous feature vector.
        """
        arr = np.asarray(data, dtype=float)
        if arr.ndim != 1:
            raise ValueError(f"IQP feature map requires 1D vector, got shape {arr.shape}")
        if arr.size == 0:
            raise ValueError("Input vector cannot be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("Input vector contains NaN, Inf, or non-finite values")
        return arr

    def get_entanglement_pairs(self, n: int) -> List[Tuple[int, int]]:
        """
        Generates pairs of qubits to entangle based on selected topology.
        """
        pairs = []
        if n < 2:
            return pairs

        if self.entanglement == "linear":
            for i in range(n - 1):
                pairs.append((i, i + 1))
        elif self.entanglement == "circular":
            for i in range(n - 1):
                pairs.append((i, i + 1))
            if n > 2:
                pairs.append((n - 1, 0))
        elif self.entanglement == "full":
            for i in range(n):
                for j in range(i + 1, n):
                    pairs.append((i, j))
        return pairs

    def compute_zz_interaction_angle(self, xi: float, xj: float) -> float:
        """
        Calculates the two-qubit rotation angle phi_ij(x).
        """
        if self.interaction_type == "havlicek":
            # Standard Havlicek et al. 2019 formula: 2 * (π - x_i) * (π - x_j)
            angle = 2.0 * (np.pi - xi) * (np.pi - xj)
        else:
            # Standard pairwise product: 2 * x_i * x_j
            angle = 2.0 * xi * xj
        return float(angle * self.alpha)

    def build_circuit(self, data: Any) -> QuantumCircuit:
        """
        Constructs the IQP feature map circuit.
        """
        features = self.validate_input(data)
        d = len(features)
        n = self._num_qubits if self._num_qubits is not None else d

        qc = QuantumCircuit(n, name=f"iqp_rep{self.repetitions}")
        pairs = self.get_entanglement_pairs(n)

        for rep in range(self.repetitions):
            # 1. Hadamard superposition layer
            for q in range(n):
                qc.h(q)

            # 2. Single-qubit non-linear phase rotations: R_Z(2 * alpha * x_i)
            for i in range(min(d, n)):
                angle = 2.0 * float(features[i]) * self.alpha
                qc.rz(angle, i)

            # 3. Two-qubit ZZ interaction layer
            for i, j in pairs:
                if i < d and j < d:
                    phi_ij = self.compute_zz_interaction_angle(features[i], features[j])
                    # Synthesize R_ZZ(theta): CNOT(i, j) -> R_Z(theta, j) -> CNOT(i, j)
                    qc.cx(i, j)
                    qc.rz(phi_ij, j)
                    qc.cx(i, j)

        return qc

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "encoding_type": "iqp_feature_map",
            "repetitions": self.repetitions,
            "entanglement": self.entanglement,
            "interaction_type": self.interaction_type,
            "alpha": self.alpha,
            "description": (
                "Instantaneous Quantum Polynomial (IQP) feature map mapping classical data "
                "into non-linear quantum Hilbert space via Hadamard, RZ, and entangling ZZ gates."
            ),
            "qubit_scaling": "O(d) qubits for d continuous features",
            "gate_scaling": f"O(R * (d + |E|)) where |E| is the number of {self.entanglement} edges",
            "depth_scaling": "O(R * d) with all-to-all; O(R) with parallel nearest-neighbor interactions",
        }
