"""
Bidirectional QUBO ⇄ Ising Model Converter & Qiskit SparsePauliOp Mapping.

Mathematical Equivalence:
    x_i in {0, 1} <---> z_i in {-1, +1}
    x_i = (1 - z_i) / 2
    z_i = 1 - 2 x_i

    QUBO:  E(x) = x^T Q x + c_0
    Ising: H(z) = sum_i h_i Z_i + sum_{i<j} J_ij Z_i Z_j + c_Ising
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from backend.app.engines.optimization.qubo.qubo_model import QUBOModel

try:
    from qiskit.quantum_info import SparsePauliOp
    _QISKIT_AVAILABLE = True
except ImportError:
    _QISKIT_AVAILABLE = False


@dataclass
class IsingModel:
    """
    Mathematical representation of an Ising spin Hamiltonian:
    H(z) = sum_i h_i z_i + sum_{i<j} J_ij z_i z_j + offset
    where z_i in {-1, +1}.
    """
    h: np.ndarray  # (n,) single-spin linear fields
    J: np.ndarray  # (n, n) two-spin couplings (upper-triangular)
    offset: float = 0.0
    variable_names: List[str] = field(default_factory=list)
    problem_name: str = "Ising Hamiltonian"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.h = np.asarray(self.h, dtype=np.float64)
        self.J = np.asarray(self.J, dtype=np.float64)
        if self.h.ndim != 1:
            raise ValueError(f"Ising linear field h must be 1D array, got shape {self.h.shape}")
        if self.J.ndim != 2 or self.J.shape[0] != self.J.shape[1]:
            raise ValueError(f"Ising coupling J must be square 2D matrix, got shape {self.J.shape}")
        if len(self.h) != self.J.shape[0]:
            raise ValueError(f"Dimension mismatch between h ({len(self.h)}) and J ({self.J.shape[0]})")
        
        n = len(self.h)
        if not self.variable_names:
            self.variable_names = [f"z_{i}" for i in range(n)]

    @property
    def num_spins(self) -> int:
        return len(self.h)

    @property
    def n_qubits(self) -> int:
        return self.num_spins

    @property
    def linear_terms(self) -> Dict[int, float]:
        return {i: float(self.h[i]) for i in range(self.num_spins)}

    @property
    def quadratic_terms(self) -> Dict[Tuple[int, int], float]:
        couplings = {}
        for i in range(self.num_spins):
            for j in range(i + 1, self.num_spins):
                val = float(self.J[i, j] + self.J[j, i])
                if abs(val) > 1e-12:
                    couplings[(i, j)] = val
        return couplings

    def to_qiskit_operator(self) -> Any:
        return self.to_sparse_pauli_op()

    def evaluate_energy(self, z: Union[Sequence[int], np.ndarray]) -> float:
        """
        Evaluate Ising energy for spin state z in {-1, +1}^n.
        """
        z_arr = np.asarray(z, dtype=np.float64)
        if len(z_arr) != self.num_spins:
            raise ValueError(f"Spin vector length ({len(z_arr)}) must match spin count ({self.num_spins})")
        if not np.all((z_arr == -1) | (z_arr == 1)):
            raise ValueError(f"Spin elements must be strictly -1 or +1, got {z_arr}")

        # H = sum_i h_i z_i + sum_{i<j} J_ij z_i z_j + offset
        n = self.num_spins
        e_linear = float(np.dot(self.h, z_arr))
        e_quad = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                e_quad += float((self.J[i, j] + self.J[j, i]) * z_arr[i] * z_arr[j])

        return e_linear + e_quad + self.offset

    def to_sparse_pauli_op(self) -> Any:
        """
        Construct Qiskit SparsePauliOp Hamiltonian.
        Follows Qiskit big-endian convention: qubit 0 is the rightmost character in Pauli string.
        """
        if not _QISKIT_AVAILABLE:
            raise RuntimeError("Qiskit is not available in environment.")

        n = self.num_spins
        pauli_list = []

        # Constant identity term
        if abs(self.offset) > 1e-15:
            pauli_list.append(("I" * n, float(self.offset)))

        # Single-qubit Z fields: h_i Z_i
        for i in range(n):
            coeff = float(self.h[i])
            if abs(coeff) > 1e-15:
                label = ["I"] * n
                label[n - 1 - i] = "Z"  # Qiskit qubit 0 is rightmost
                pauli_list.append(("".join(label), coeff))

        # Two-qubit ZZ interactions: J_ij Z_i Z_j
        for i in range(n):
            for j in range(i + 1, n):
                coupling = float(self.J[i, j] + self.J[j, i])
                if abs(coupling) > 1e-15:
                    label = ["I"] * n
                    label[n - 1 - i] = "Z"
                    label[n - 1 - j] = "Z"
                    pauli_list.append(("".join(label), coupling))

        if not pauli_list:
            pauli_list.append(("I" * n, 0.0))

        return SparsePauliOp.from_list(pauli_list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_name": self.problem_name,
            "num_spins": self.num_spins,
            "variable_names": self.variable_names,
            "h": self.h.tolist(),
            "J": self.J.tolist(),
            "offset": round(self.offset, 6),
            "metadata": self.metadata,
        }


def qubo_to_ising(qubo: QUBOModel) -> IsingModel:
    """
    Convert a QUBOModel to an exact equivalent IsingModel:
    Substitute x_i = (1 - z_i) / 2 into x^T Q x + offset.

    Closed-form formulas:
        J_ij = (Q_ij + Q_ji) / 4   (represented as Q_sym[i, j] / 2 in upper triangle)
        h_i  = -Q_ii / 2 - sum_{j != i} (Q_ij + Q_ji) / 4
        c_Ising = offset + (1/2) sum_i Q_ii + sum_{i<j} (Q_ij + Q_ji) / 4
    """
    Q = qubo.matrix
    n = qubo.num_variables
    Q_sym = (Q + Q.T) / 2.0

    h = np.zeros(n, dtype=np.float64)
    J = np.zeros((n, n), dtype=np.float64)
    offset = float(qubo.offset) + 0.5 * float(np.sum(np.diag(Q_sym)))

    for i in range(n):
        h[i] = -Q_sym[i, i] / 2.0
        for j in range(n):
            if i != j:
                h[i] -= Q_sym[i, j] / 2.0
                if i < j:
                    J[i, j] = Q_sym[i, j] / 2.0  # since H has term (J_ij + J_ji) z_i z_j
                    offset += Q_sym[i, j] / 2.0

    return IsingModel(
        h=h,
        J=J,
        offset=offset,
        variable_names=list(qubo.variable_names),
        problem_name=f"Ising[{qubo.problem_name}]",
        metadata=dict(qubo.metadata, original_form="QUBO"),
    )


def ising_to_qubo(ising: IsingModel) -> QUBOModel:
    """
    Convert an IsingModel to an exact equivalent QUBOModel:
    Substitute z_i = 1 - 2 x_i into H(z).

    Closed-form formulas:
        Q_ii = -2 h_i - 2 sum_{j != i} (J_ij + J_ji)
        Q_ij = 4 (J_ij + J_ji)  (for i < j)
        offset = c_Ising + sum_i h_i + sum_{i<j} (J_ij + J_ji)
    """
    n = ising.num_spins
    h = ising.h

    Q = np.zeros((n, n), dtype=np.float64)
    offset = float(ising.offset)

    for i in range(n):
        Q[i, i] += -2.0 * h[i]
        offset += h[i]
        for j in range(i + 1, n):
            J_val = float(ising.J[i, j] + ising.J[j, i])
            Q[i, j] += 4.0 * J_val
            Q[i, i] += -2.0 * J_val
            Q[j, j] += -2.0 * J_val
            offset += J_val

    return QUBOModel(
        matrix=Q,
        offset=offset,
        variable_names=list(ising.variable_names),
        problem_name=f"QUBO[{ising.problem_name}]",
        metadata=dict(ising.metadata, original_form="Ising"),
    )


def verify_qubo_ising_equivalence(qubo: QUBOModel, ising: IsingModel, samples: int = 32) -> bool:
    """
    Mathematically prove that for random binary vectors x and their corresponding
    spin vectors z = 1 - 2x, E_QUBO(x) == E_Ising(z) within 1e-10 numerical tolerance.
    """
    n = qubo.num_variables
    if ising.num_spins != n:
        raise ValueError("QUBO and Ising dimension mismatch.")

    rng = np.random.default_rng(42)
    max_states = 2**n
    check_count = min(samples, max_states)

    for _ in range(check_count):
        x = rng.integers(0, 2, size=n)
        z = 1 - 2 * x

        e_qubo = qubo.evaluate_energy(x)
        e_ising = ising.evaluate_energy(z)

        if not np.isclose(e_qubo, e_ising, atol=1e-10):
            raise AssertionError(
                f"Equivalence failure: x={x}, z={z} -> E_QUBO={e_qubo}, E_Ising={e_ising}, diff={abs(e_qubo - e_ising)}"
            )

    return True


class QUBOToIsingConverter:
    """Wrapper class for QUBO to Ising conversion."""

    @staticmethod
    def convert(qubo: QUBOModel) -> IsingModel:
        return qubo_to_ising(qubo)

    @staticmethod
    def convert_inverse(ising: IsingModel) -> QUBOModel:
        return ising_to_qubo(ising)
