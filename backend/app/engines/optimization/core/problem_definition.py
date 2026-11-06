"""
Optimization Problem Definition Base Class & Categorization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from backend.app.engines.optimization.core.binary_variables import VariableRegister


class OptimizationSense(str, Enum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class ProblemCategory(str, Enum):
    KNAPSACK = "knapsack"
    PORTFOLIO = "portfolio"
    FACILITY_LOCATION = "facility_location"
    RESOURCE_ALLOCATION = "resource_allocation"
    GENERAL_QUBO = "general_qubo"


@dataclass
class OptimizationProblem:
    """
    Abstract base definition of a combinatorial binary optimization problem.
    """
    name: str
    category: ProblemCategory
    sense: OptimizationSense = OptimizationSense.MINIMIZE
    description: Optional[str] = None
    variable_names: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Problem name cannot be empty")
        self.register = VariableRegister(self.variable_names)

    @property
    def num_variables(self) -> int:
        return self.register.size

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "sense": self.sense.value,
            "description": self.description,
            "num_variables": self.num_variables,
            "variable_names": self.variable_names,
            "parameters": self.parameters,
            "metadata": self.metadata,
        }

