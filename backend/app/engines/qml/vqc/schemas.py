"""
schemas.py - Pydantic Request & Response Schemas for VQC API Endpoints.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class VQCHealthResponse(BaseModel):
    status: str
    qiskit_version: str
    qiskit_aer_version: str
    scipy_version: str
    sklearn_version: str
    supported_ansatzes: List[str]
    supported_optimizers: List[str]
    supported_encoders: List[str]
    supported_datasets: List[str]
    simulation_backend: str
    hardware_disclaimer: str


class AnsatzItemSchema(BaseModel):
    identifier: str
    name: str
    description: str
    parameter_scaling: str
    entanglement_options: List[str]


class AnsatzListResponse(BaseModel):
    ansatzes: List[AnsatzItemSchema]


class CircuitBuildRequest(BaseModel):
    num_qubits: int = Field(4, ge=2, le=8)
    ansatz_type: str = Field("hardware_efficient", description="hardware_efficient, strongly_entangling, or two_local")
    num_layers: int = Field(2, ge=1, le=5)
    rotation_gates: List[str] = Field(default_factory=lambda: ["ry"])
    entanglement: str = Field("linear", description="linear, circular, or full")
    sample_features: Optional[List[float]] = None
    encoder_name: str = Field("angle_ry")


class CircuitBuildResponse(BaseModel):
    num_qubits: int
    num_parameters: int
    circuit_depth: int
    total_gates: int
    single_qubit_gates: int
    two_qubit_gates: int
    gate_breakdown: Dict[str, int]
    ansatz_type: str
    encoder_name: str


class VQCTrainRequest(BaseModel):
    dataset_name: str = Field("moons", description="linearly_separable, moons, circles, iris, land_suitability, infrastructure_risk")
    n_samples: int = Field(100, ge=30, le=250)
    encoder_name: str = Field("angle_ry")
    ansatz_type: str = Field("hardware_efficient")
    num_layers: int = Field(2, ge=1, le=4)
    optimizer: str = Field("COBYLA", description="COBYLA, L-BFGS-B, or Adam")
    max_iter: int = Field(35, ge=5, le=80)
    learning_rate: float = Field(0.05, ge=0.001, le=0.5)
    loss_function: str = Field("binary_cross_entropy")
    seed: int = Field(42)


class ConfusionMatrixSchema(BaseModel):
    tn: int
    fp: int
    fn: int
    tp: int


class ClassificationMetricsSchema(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    confusion_matrix: ConfusionMatrixSchema


class TrainingIterationRecord(BaseModel):
    iteration: int
    train_loss: float
    val_loss: Optional[float] = None
    train_accuracy: float
    val_accuracy: Optional[float] = None
    gradient_norm: Optional[float] = None
    step_time_ms: Optional[float] = None


class VQCTrainResponse(BaseModel):
    success: bool
    status: str
    experiment_id: str
    dataset_name: str
    provenance_tier: str
    num_qubits: int
    num_parameters: int
    iterations: int
    final_train_loss: float
    final_val_loss: Optional[float] = None
    test_metrics: ClassificationMetricsSchema
    weights: List[float]
    training_time_ms: float
    quantum_circuit_evaluations: int
    history: List[TrainingIterationRecord]
    hardware_disclaimer: str


class VQCPredictRequest(BaseModel):
    features: List[List[float]]
    weights: List[float]
    encoder_name: str = Field("angle_ry")
    ansatz_type: str = Field("hardware_efficient")
    num_layers: int = Field(2, ge=1, le=5)
    threshold: float = Field(0.5, ge=0.0, le=1.0)


class VQCPredictResponse(BaseModel):
    predictions: List[int]
    probabilities: List[List[float]]
    num_samples: int
    inference_time_ms: float


class BenchmarkModelEntrySchema(BaseModel):
    model_name: str
    is_quantum: bool
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    confusion_matrix: ConfusionMatrixSchema
    training_time_ms: float
    inference_latency_ms: float
    num_parameters: int
    circuit_depth: Optional[int] = None
    hardware_note: str


class VQCBenchmarkRequest(BaseModel):
    dataset_name: str = Field("moons")
    n_samples: int = Field(100, ge=30, le=200)
    encoder_name: str = Field("angle_ry")
    ansatz_type: str = Field("hardware_efficient")
    num_layers: int = Field(2, ge=1, le=4)
    max_iter: int = Field(30, ge=5, le=60)
    seed: int = Field(42)


class VQCBenchmarkResponse(BaseModel):
    dataset_name: str
    provenance_tier: str
    num_features: int
    train_samples: int
    test_samples: int
    models: List[BenchmarkModelEntrySchema]
    vqc_training_history: List[Dict[str, Any]]
    summary_findings: List[str]
    scientific_disclaimer: str
