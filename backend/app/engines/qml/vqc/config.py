"""
config.py - Configuration Contracts for Variational Quantum Classifier (VQC).

Defines architectural, measurement, and optimization hyperparameters for the VQC engine.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class AnsatzConfig:
    """Configuration for parameterized quantum circuit ansatz."""
    ansatz_type: str = "hardware_efficient"  # 'hardware_efficient', 'strongly_entangling', 'two_local'
    num_qubits: int = 4
    num_layers: int = 2
    rotation_gates: List[str] = field(default_factory=lambda: ["ry"])
    entanglement: str = "linear"  # 'linear', 'circular', 'full'
    seed: Optional[int] = 42

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ansatz_type": self.ansatz_type,
            "num_qubits": self.num_qubits,
            "num_layers": self.num_layers,
            "rotation_gates": self.rotation_gates,
            "entanglement": self.entanglement,
            "seed": self.seed,
        }


@dataclass
class MeasurementConfig:
    """Configuration for quantum expectation value extraction."""
    observable_type: str = "z0"  # 'z0', 'parity_z'
    shots: Optional[int] = None  # None for exact statevector; int for shot sampling
    seed: Optional[int] = 42

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observable_type": self.observable_type,
            "shots": self.shots,
            "seed": self.seed,
        }


@dataclass
class TrainingConfig:
    """Hyperparameters for classical parameter optimization loop."""
    optimizer: str = "COBYLA"  # 'COBYLA', 'L-BFGS-B', 'Adam', 'SPSA'
    max_iter: int = 35
    learning_rate: float = 0.05
    tolerance: float = 1e-4
    loss_function: str = "binary_cross_entropy"  # 'binary_cross_entropy', 'mse'
    batch_size: Optional[int] = None  # None for full batch
    early_stopping_patience: int = 8
    seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return {
            "optimizer": self.optimizer,
            "max_iter": self.max_iter,
            "learning_rate": self.learning_rate,
            "tolerance": self.tolerance,
            "loss_function": self.loss_function,
            "batch_size": self.batch_size,
            "early_stopping_patience": self.early_stopping_patience,
            "seed": self.seed,
        }


@dataclass
class VQCConfig:
    """Master configuration for end-to-end Variational Quantum Classifier."""
    encoder_name: str = "angle_ry"
    encoder_kwargs: Dict[str, Any] = field(default_factory=dict)
    ansatz: AnsatzConfig = field(default_factory=AnsatzConfig)
    measurement: MeasurementConfig = field(default_factory=MeasurementConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "encoder_name": self.encoder_name,
            "encoder_kwargs": self.encoder_kwargs,
            "ansatz": self.ansatz.to_dict(),
            "measurement": self.measurement.to_dict(),
            "training": self.training.to_dict(),
        }
