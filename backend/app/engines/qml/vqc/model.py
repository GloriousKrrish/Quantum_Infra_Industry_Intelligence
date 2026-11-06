"""
model.py - Variational Quantum Classifier (VQC) Core Model.

Integrates:
  1. Quantum Data Encoding (Phase 05.1)
  2. Parameterized Quantum Ansatz
  3. Observable Measurement & Expectation Value Operator
  4. Binary Probability Inference
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector

from ..encoding import EncodingRegistry, BaseQuantumEncoder
from .config import VQCConfig
from .ansatz import ParameterizedAnsatz
from .measurement import VQCMeasurementEngine


class VariationalQuantumClassifier:
    """
    Trainable Variational Quantum Classifier for binary classification.
    """

    def __init__(self, config: Optional[VQCConfig] = None):
        self.config = config or VQCConfig()

        # 1. Initialize Encoder from Phase 05.1
        self.encoder_name = self.config.encoder_name
        enc_kwargs = dict(self.config.encoder_kwargs)
        if "num_qubits" not in enc_kwargs:
            enc_kwargs["num_qubits"] = self.config.ansatz.num_qubits
        self.encoder: BaseQuantumEncoder = EncodingRegistry.get_encoder(
            self.encoder_name, **enc_kwargs
        )

        # 2. Initialize Parameterized Ansatz
        self.ansatz = ParameterizedAnsatz(self.config.ansatz)
        self.num_qubits = self.config.ansatz.num_qubits

        # 3. Initialize Measurement Engine
        self.measurement = VQCMeasurementEngine(
            num_qubits=self.num_qubits,
            config=self.config.measurement,
        )

        # 4. Trainable Parameter Weights Vector
        self.weights = self.ansatz.initialize_parameters(
            strategy="uniform_random",
            seed=self.config.ansatz.seed,
        )

        self._training_history: List[Dict[str, Any]] = []

    @property
    def num_parameters(self) -> int:
        return self.ansatz.num_parameters

    @property
    def parameter_vector(self) -> ParameterVector:
        return self.ansatz.parameter_vector

    def get_parameters(self) -> np.ndarray:
        return self.weights.copy()

    def set_parameters(self, new_weights: np.ndarray) -> None:
        arr = np.asarray(new_weights, dtype=float)
        if len(arr) != self.num_parameters:
            raise ValueError(
                f"Weight dimension mismatch: expected {self.num_parameters}, got {len(arr)}"
            )
        self.weights = arr.copy()

    def build_full_circuit(
        self,
        x: np.ndarray,
        params: Optional[np.ndarray] = None,
        bind_ansatz: bool = True,
    ) -> QuantumCircuit:
        """
        Builds the unified circuit: Encoding Circuit U_enc(x) + Parameterized Ansatz W(θ).
        """
        enc_qc = self.encoder.build_circuit(x)
        ansatz_qc = self.ansatz.circuit

        # Compose encoding and ansatz
        full_qc = enc_qc.compose(ansatz_qc)

        if bind_ansatz:
            weights_to_bind = params if params is not None else self.weights
            param_dict = {
                self.ansatz.parameter_vector[i]: float(weights_to_bind[i])
                for i in range(self.num_parameters)
            }
            return full_qc.assign_parameters(param_dict)

        return full_qc

    def forward_single(
        self,
        x: np.ndarray,
        params: Optional[np.ndarray] = None,
    ) -> Tuple[float, float]:
        """
        Executes quantum forward pass for a single feature vector.
        Returns: (expectation_val <Z_0>, prob_class_1)
        """
        circuit = self.build_full_circuit(x, params=params, bind_ansatz=True)
        exp_val, probs = self.measurement.evaluate_circuit(circuit)
        # probs[0] is P(y=0), probs[1] is P(y=1)
        return exp_val, float(probs[1])

    def forward_batch(
        self,
        X: np.ndarray,
        params: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Executes quantum forward pass across an entire dataset or mini-batch.
        Returns: (expectations_array, probabilities_class_1)
        """
        X_arr = np.asarray(X, dtype=float)
        n_samples = len(X_arr)
        expectations = np.zeros(n_samples, dtype=float)
        probs_class1 = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            exp_val, p1 = self.forward_single(X_arr[i], params=params)
            expectations[i] = exp_val
            probs_class1[i] = p1

        return expectations, probs_class1

    def predict_proba(
        self,
        X: np.ndarray,
        params: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Calculates class probabilities [P(y=0), P(y=1)] for each sample in X.
        Returns array of shape (N, 2).
        """
        _, p1 = self.forward_batch(X, params=params)
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])

    def predict(
        self,
        X: np.ndarray,
        threshold: float = 0.5,
        params: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Returns hard binary predictions y_hat in {0, 1}.
        """
        _, p1 = self.forward_batch(X, params=params)
        return (p1 >= threshold).astype(int)

    def get_model_info(self) -> Dict[str, Any]:
        """Returns architectural summary of the VQC model."""
        sample_x = np.zeros(self.num_qubits, dtype=float)
        sample_qc = self.build_full_circuit(sample_x, bind_ansatz=True)

        return {
            "model_type": "VariationalQuantumClassifier",
            "num_qubits": self.num_qubits,
            "num_parameters": self.num_parameters,
            "encoder": self.encoder_name,
            "ansatz_type": self.ansatz.ansatz_type,
            "ansatz_layers": self.ansatz.layers,
            "entanglement": self.ansatz.entanglement,
            "observable": self.measurement.observable_type,
            "circuit_depth": sample_qc.depth(),
            "total_gates": len(sample_qc.data),
            "current_weights_norm": float(np.linalg.norm(self.weights)),
        }
