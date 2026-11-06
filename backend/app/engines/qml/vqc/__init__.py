"""
Variational Quantum Classifier (VQC) Engine.
Milestone 5.2 of Quantum Estate X Phase 05.
"""

from .config import AnsatzConfig, MeasurementConfig, TrainingConfig, VQCConfig
from .ansatz import ParameterizedAnsatz
from .measurement import VQCMeasurementEngine
from .loss_functions import (
    BaseLossFunction,
    BinaryCrossEntropyLoss,
    MeanSquaredErrorLoss,
    get_loss_function,
)
from .gradients import VQCGradientEngine
from .model import VariationalQuantumClassifier
from .trainer import VQCTrainer, VQCTrainingResult
from .datasets import DatasetPreprocessor, VQCDatasetLibrary
from .classical_baselines import ClassicalBaselineRunner
from .evaluation import evaluate_classifier_predictions, VQCBenchmarkSuite
from .experiment import VQCExperimentRecord, VQCExperimentRegistry

__all__ = [
    "AnsatzConfig",
    "MeasurementConfig",
    "TrainingConfig",
    "VQCConfig",
    "ParameterizedAnsatz",
    "VQCMeasurementEngine",
    "BaseLossFunction",
    "BinaryCrossEntropyLoss",
    "MeanSquaredErrorLoss",
    "get_loss_function",
    "VQCGradientEngine",
    "VariationalQuantumClassifier",
    "VQCTrainer",
    "VQCTrainingResult",
    "DatasetPreprocessor",
    "VQCDatasetLibrary",
    "ClassicalBaselineRunner",
    "evaluate_classifier_predictions",
    "VQCBenchmarkSuite",
    "VQCExperimentRecord",
    "VQCExperimentRegistry",
]
