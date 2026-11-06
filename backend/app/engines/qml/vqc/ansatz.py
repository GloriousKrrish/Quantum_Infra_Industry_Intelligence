"""
ansatz.py - Parameterized Quantum Circuit (PQC) Ansatz Architectures.

Provides configurable variational quantum circuit architectures for QML:
  1. Hardware-Efficient Ansatz (HEA):
     Alternating layers of single-qubit rotations (RY, RZ) and CNOT entanglers.
  2. Strongly Entangling Ansatz (SEA):
     Universal single-qubit Euler rotations followed by range-shifted circular CNOTs.
  3. TwoLocal Ansatz:
     Alternating rotation blocks and entanglement layers.

All parameters are bound via Qiskit's ParameterVector mechanism.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector

from .config import AnsatzConfig


class ParameterizedAnsatz:
    """
    Constructs and manages parameterized variational quantum circuits.
    """

    def __init__(self, config: Optional[AnsatzConfig] = None):
        self.config = config or AnsatzConfig()
        self.n = self.config.num_qubits
        self.layers = self.config.num_layers
        self.ansatz_type = self.config.ansatz_type.lower()
        self.entanglement = self.config.entanglement.lower()
        self.rotation_gates = [g.lower() for g in self.config.rotation_gates]

        self._num_params = self._calculate_num_parameters()
        self._param_vector = ParameterVector("θ", self._num_params)
        self._circuit = self._build_ansatz_circuit()

    @property
    def num_parameters(self) -> int:
        return self._num_params

    @property
    def parameter_vector(self) -> ParameterVector:
        return self._param_vector

    @property
    def circuit(self) -> QuantumCircuit:
        return self._circuit

    def _calculate_num_parameters(self) -> int:
        """Computes exact parameter count based on architecture and layers."""
        n = self.n
        L = self.layers
        rot_count = len(self.rotation_gates)

        if self.ansatz_type in ("hardware_efficient", "two_local"):
            # (L + 1) rotation layers, each having n * rot_count parameters
            return (L + 1) * n * rot_count
        elif self.ansatz_type == "strongly_entangling":
            # 3 Euler rotation parameters per qubit per layer (Z-Y-Z)
            return 3 * n * L
        else:
            # Default to HEA count
            return (L + 1) * n * rot_count

    def _get_entanglement_pairs(self, layer_idx: int = 0) -> List[Tuple[int, int]]:
        """Generates entangling CNOT qubit pairs."""
        n = self.n
        if n < 2:
            return []

        if self.ansatz_type == "strongly_entangling":
            # Range-shifted circular entanglement
            shift = (layer_idx % (n - 1)) + 1
            return [(i, (i + shift) % n) for i in range(n)]

        # HEA and TwoLocal topologies
        if self.entanglement == "linear":
            return [(i, i + 1) for i in range(n - 1)]
        elif self.entanglement == "circular":
            pairs = [(i, i + 1) for i in range(n - 1)]
            if n > 2:
                pairs.append((n - 1, 0))
            return pairs
        elif self.entanglement == "full":
            return [(i, j) for i in range(n) for j in range(i + 1, n)]
        return [(i, i + 1) for i in range(n - 1)]

    def _build_ansatz_circuit(self) -> QuantumCircuit:
        """Constructs unassigned Parameterized Quantum Circuit."""
        n = self.n
        L = self.layers
        qc = QuantumCircuit(n, name=f"ansatz_{self.ansatz_type}")
        params = self._param_vector
        p_idx = 0

        if self.ansatz_type == "strongly_entangling":
            for l in range(L):
                # 3 parameters per qubit: RZ(θ1) -> RY(θ2) -> RZ(θ3)
                for q in range(n):
                    qc.rz(params[p_idx], q)
                    qc.ry(params[p_idx + 1], q)
                    qc.rz(params[p_idx + 2], q)
                    p_idx += 3

                # Entanglement
                for ctrl, tgt in self._get_entanglement_pairs(layer_idx=l):
                    qc.cx(ctrl, tgt)

        else:
            # Hardware-Efficient Ansatz & TwoLocal
            for l in range(L):
                # Rotation layer
                for q in range(n):
                    for r_gate in self.rotation_gates:
                        if r_gate == "ry":
                            qc.ry(params[p_idx], q)
                        elif r_gate == "rz":
                            qc.rz(params[p_idx], q)
                        elif r_gate == "rx":
                            qc.rx(params[p_idx], q)
                        p_idx += 1

                # Entanglement layer
                for ctrl, tgt in self._get_entanglement_pairs(layer_idx=l):
                    qc.cx(ctrl, tgt)

            # Final rotation layer
            for q in range(n):
                for r_gate in self.rotation_gates:
                    if r_gate == "ry":
                        qc.ry(params[p_idx], q)
                    elif r_gate == "rz":
                        qc.rz(params[p_idx], q)
                    elif r_gate == "rx":
                        qc.rx(params[p_idx], q)
                    p_idx += 1

        return qc

    def initialize_parameters(
        self,
        strategy: str = "uniform_random",
        seed: Optional[int] = None,
    ) -> np.ndarray:
        """
        Initializes parameter vector weights.
        Strategies:
          - 'uniform_random': uniform in [-pi, pi]
          - 'normal_small': normal with std 0.1 around 0
          - 'zeros': all zeros
        """
        rng = np.random.default_rng(seed if seed is not None else self.config.seed)
        num_p = self._num_params

        if strategy == "uniform_random":
            return rng.uniform(-np.pi, np.pi, size=num_p)
        elif strategy == "normal_small":
            return rng.normal(0.0, 0.1, size=num_p)
        elif strategy == "zeros":
            return np.zeros(num_p, dtype=float)
        else:
            return rng.uniform(-np.pi, np.pi, size=num_p)

    def bind_parameters(self, param_values: np.ndarray) -> QuantumCircuit:
        """Binds numeric parameter array to circuit, returning bound QuantumCircuit."""
        arr = np.asarray(param_values, dtype=float)
        if len(arr) != self._num_params:
            raise ValueError(
                f"Expected {self._num_params} parameter values, got {len(arr)}"
            )
        param_dict = {self._param_vector[i]: float(arr[i]) for i in range(self._num_params)}
        return self._circuit.assign_parameters(param_dict)
