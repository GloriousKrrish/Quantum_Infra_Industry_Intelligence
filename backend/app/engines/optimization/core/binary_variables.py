"""
Binary Decision Variables Specification.

Manages binary variables x_i in {0, 1} for combinatorial and QUBO optimization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence


@dataclass(frozen=True)
class BinaryVariable:
    """Represents a single binary decision variable x_i in {0, 1}."""
    index: int
    name: str
    description: Optional[str] = None
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError(f"Variable index must be non-negative, got {self.index}")
        if not self.name or not self.name.strip():
            raise ValueError("Variable name cannot be empty")


class VariableRegister:
    """Ordered register of binary decision variables with fast lookup by name or index."""

    def __init__(self, variable_names: Optional[Sequence[str]] = None) -> None:
        self._variables: List[BinaryVariable] = []
        self._name_to_index: Dict[str, int] = {}

        if variable_names:
            for name in variable_names:
                self.add_variable(name)

    def add_variable(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> BinaryVariable:
        if name in self._name_to_index:
            raise ValueError(f"Duplicate variable name '{name}' in register.")
        idx = len(self._variables)
        var = BinaryVariable(
            index=idx,
            name=name,
            description=description,
            metadata=metadata or {},
        )
        self._variables.append(var)
        self._name_to_index[name] = idx
        return var

    def get_by_index(self, index: int) -> BinaryVariable:
        if 0 <= index < len(self._variables):
            return self._variables[index]
        raise IndexError(f"Variable index {index} out of range [0, {len(self._variables) - 1}].")

    def get_by_name(self, name: str) -> BinaryVariable:
        if name in self._name_to_index:
            return self._variables[self._name_to_index[name]]
        raise KeyError(f"Variable name '{name}' not found in register.")

    @property
    def names(self) -> List[str]:
        return [v.name for v in self._variables]

    @property
    def size(self) -> int:
        return len(self._variables)

    def __len__(self) -> int:
        return len(self._variables)

    def __iter__(self):
        return iter(self._variables)
