"""
Quantum Data Encoding Engine.
Milestone 5.1 of Quantum Estate X Phase 05.

Provides mathematically rigorous, reproducible quantum state encoders:
  - BasisEncoder: Binary feature encoding into computational basis states
  - AmplitudeEncoder: Normalized continuous feature encoding into state amplitudes
  - AngleEncoder: Continuous rotation encoding (RX, RY, RZ, Combined Euler)
  - IQPFeatureMap: Instantaneous Quantum Polynomial entangling feature maps
  - EncodingRegistry: Centralized factory, catalog, and resource comparator
  - EncodingResourceMetrics: Real circuit instruction complexity analyzer
"""

from .base_encoder import BaseQuantumEncoder, EncodingResult
from .encoding_metrics import EncodingResourceMetrics, calculate_circuit_metrics
from .basis_encoding import BasisEncoder
from .amplitude_encoding import AmplitudeEncoder
from .angle_encoding import AngleEncoder
from .feature_maps import IQPFeatureMap
from .encoding_registry import EncodingRegistry

__all__ = [
    "BaseQuantumEncoder",
    "EncodingResult",
    "EncodingResourceMetrics",
    "calculate_circuit_metrics",
    "BasisEncoder",
    "AmplitudeEncoder",
    "AngleEncoder",
    "IQPFeatureMap",
    "EncodingRegistry",
]
