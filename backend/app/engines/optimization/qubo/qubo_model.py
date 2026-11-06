"""
QUBO Model Dataclass & Matrix Canonicalization.

Represents Quadratic Unconstrained Binary Optimization problems:
    E(x) = x^T Q x + c_0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union
import numpy as np


@dataclass
class QUBOModel:
    """
    Mathematical representation of a QUBO problem:
    E(x) = x^T Q x + offset
    """
    matrix: np.ndarray
    offset: float = 0.0
    variable_names: List[str] = field(default_factory=list)
    problem_name: str = "QUBO Problem"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.matrix = np.asarray(self.matrix, dtype=np.float64)
        if self.matrix.ndim != 2 or self.matrix.shape[0] != self.matrix.shape[1]:
            raise ValueError(f"QUBO matrix must be square 2D array, got shape {self.matrix.shape}")
        
        n = self.matrix.shape[0]
        if not self.variable_names:
            self.variable_names = [f"x_{i}" for i in range(n)]
        elif len(self.variable_names) != n:
            raise ValueError(
                f"Variable names count ({len(self.variable_names)}) must match matrix dimension ({n})"
            )

    @property
    def num_variables(self) -> int:
        return self.matrix.shape[0]

    @property
    def n_variables(self) -> int:
        return self.num_variables

    @property
    def constant_offset(self) -> float:
        return self.offset

    @constant_offset.setter
    def constant_offset(self, value: float) -> None:
        self.offset = float(value)

    def to_symmetric_matrix(self) -> np.ndarray:
        return (self.matrix + self.matrix.T) / 2.0

    def evaluate(self, x: Union[Sequence[int], np.ndarray, str]) -> float:
        return self.evaluate_energy(x)

    def to_upper_triangular(self) -> QUBOModel:
        """
        Return equivalent QUBO with upper-triangular matrix:
        For i < j: Q_ij' = Q_ij + Q_ji; Q_ji' = 0.
        """
        n = self.num_variables
        Q_upper = np.zeros((n, n), dtype=np.float64)
        for i in range(n):
            Q_upper[i, i] = self.matrix[i, i]
            for j in range(i + 1, n):
                Q_upper[i, j] = self.matrix[i, j] + self.matrix[j, i]
        return QUBOModel(
            matrix=Q_upper,
            offset=self.offset,
            variable_names=list(self.variable_names),
            problem_name=self.problem_name,
            metadata=dict(self.metadata, matrix_convention="upper_triangular"),
        )

    def to_symmetric(self) -> QUBOModel:
        """
        Return equivalent QUBO with symmetric matrix:
        Q_sym = (Q + Q^T) / 2.
        """
        Q_sym = (self.matrix + self.matrix.T) / 2.0
        return QUBOModel(
            matrix=Q_sym,
            offset=self.offset,
            variable_names=list(self.variable_names),
            problem_name=self.problem_name,
            metadata=dict(self.metadata, matrix_convention="symmetric"),
        )

    def evaluate_energy(self, x: Union[Sequence[int], np.ndarray, str]) -> float:
        """
        Evaluate objective energy for binary assignment x in {0, 1}^n:
        E(x) = x^T Q x + offset
        """
        if isinstance(x, str):
            x_arr = np.array([int(b) for b in x.replace(" ", "")], dtype=np.float64)
        else:
            x_arr = np.asarray(x, dtype=np.float64)

        if len(x_arr) != self.num_variables:
            raise ValueError(
                f"Binary vector length ({len(x_arr)}) does not match variable count ({self.num_variables})"
            )
        if not np.all((x_arr == 0) | (x_arr == 1)):
            raise ValueError(f"Vector elements must be strictly binary (0 or 1), got {x_arr}")

        return float(x_arr @ self.matrix @ x_arr + self.offset)

    def get_linear_coefficients(self) -> Dict[str, float]:
        """Return diagonal terms Q_ii associated with linear decisions x_i."""
        return {
            self.variable_names[i]: float(self.matrix[i, i])
            for i in range(self.num_variables)
        }

    def get_quadratic_interactions(self) -> List[Dict[str, Any]]:
        """Return non-zero pair couplings (i < j) with variable names."""
        interactions = []
        n = self.num_variables
        for i in range(n):
            for j in range(i + 1, n):
                coupling = float(self.matrix[i, j] + self.matrix[j, i])
                if abs(coupling) > 1e-12:
                    interactions.append({
                        "var1": self.variable_names[i],
                        "var2": self.variable_names[j],
                        "index1": i,
                        "index2": j,
                        "coupling": round(coupling, 6),
                    })
        return interactions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_name": self.problem_name,
            "num_variables": self.num_variables,
            "variable_names": self.variable_names,
            "offset": round(self.offset, 6),
            "matrix": self.matrix.tolist(),
            "linear_coefficients": self.get_linear_coefficients(),
            "quadratic_interactions": self.get_quadratic_interactions(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QUBOModel:
        return cls(
            matrix=np.array(data["matrix"], dtype=np.float64),
            offset=data.get("offset", 0.0),
            variable_names=data.get("variable_names", []),
            problem_name=data.get("problem_name", "QUBO Problem"),
            metadata=data.get("metadata", {}),
        )
