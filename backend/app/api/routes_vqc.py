"""
routes_vqc.py - FastAPI Router for Variational Quantum Classifier (VQC).

Endpoints:
  GET  /api/qml/vqc/health
  GET  /api/qml/vqc/ansatz/list
  POST /api/qml/vqc/circuit/build
  POST /api/qml/vqc/model/train
  POST /api/qml/vqc/model/predict
  POST /api/qml/vqc/benchmark/run
  GET  /api/qml/vqc/experiments
  GET  /api/qml/vqc/experiments/{experiment_id}
"""

import time
import numpy as np
from fastapi import APIRouter, HTTPException, status
import qiskit
import qiskit_aer
import scipy
import sklearn

from backend.app.engines.qml.vqc import (
    AnsatzConfig,
    MeasurementConfig,
    TrainingConfig,
    VQCConfig,
    ParameterizedAnsatz,
    VariationalQuantumClassifier,
    VQCTrainer,
    VQCDatasetLibrary,
    VQCBenchmarkSuite,
    VQCExperimentRegistry,
    evaluate_classifier_predictions,
)
from backend.app.engines.qml.vqc.schemas import (
    VQCHealthResponse,
    AnsatzListResponse,
    AnsatzItemSchema,
    CircuitBuildRequest,
    CircuitBuildResponse,
    VQCTrainRequest,
    VQCTrainResponse,
    VQCPredictRequest,
    VQCPredictResponse,
    VQCBenchmarkRequest,
    VQCBenchmarkResponse,
    ClassificationMetricsSchema,
    ConfusionMatrixSchema,
    TrainingIterationRecord,
    BenchmarkModelEntrySchema,
)
from backend.app.engines.qml.encoding import EncodingRegistry, calculate_circuit_metrics

router = APIRouter(prefix="/api/qml/vqc", tags=["Quantum Machine Learning - VQC"])


@router.get("/health", response_model=VQCHealthResponse)
async def get_vqc_health():
    """Returns software versions, supported architectures, and hardware disclaimers."""
    return VQCHealthResponse(
        status="OPERATIONAL",
        qiskit_version=qiskit.__version__,
        qiskit_aer_version=qiskit_aer.__version__,
        scipy_version=scipy.__version__,
        sklearn_version=sklearn.__version__,
        supported_ansatzes=["hardware_efficient", "strongly_entangling", "two_local"],
        supported_optimizers=["COBYLA", "L-BFGS-B", "Adam"],
        supported_encoders=["angle_ry", "angle_rx", "angle_rz", "angle_combined", "iqp", "amplitude", "basis"],
        supported_datasets=["moons", "circles", "linearly_separable", "iris", "land_suitability", "infrastructure_risk"],
        simulation_backend="Qiskit Aer 0.18.2 Classical CPU Simulator",
        hardware_disclaimer=(
            "VQC training and inference are executed locally using classical CPU simulation "
            "via Qiskit Aer. No physical quantum device was accessed, and no quantum advantage is claimed."
        ),
    )


@router.get("/ansatz/list", response_model=AnsatzListResponse)
async def list_supported_ansatzes():
    """Lists supported parameterized quantum ansatz architectures."""
    return AnsatzListResponse(
        ansatzes=[
            AnsatzItemSchema(
                identifier="hardware_efficient",
                name="Hardware-Efficient Ansatz (HEA)",
                description="Alternating layers of single-qubit rotations (RY, RZ) and CNOT entangling gates.",
                parameter_scaling="(L + 1) * n * rot_gates",
                entanglement_options=["linear", "circular", "full"],
            ),
            AnsatzItemSchema(
                identifier="strongly_entangling",
                name="Strongly Entangling Ansatz (SEA)",
                description="Three-parameter Euler rotations (RZ-RY-RZ) on every qubit followed by range-shifted circular CNOTs.",
                parameter_scaling="3 * n * L",
                entanglement_options=["circular"],
            ),
            AnsatzItemSchema(
                identifier="two_local",
                name="Two-Local Variational Circuit",
                description="General alternating rotation and two-qubit entanglement blocks.",
                parameter_scaling="(L + 1) * n",
                entanglement_options=["linear", "circular", "full"],
            ),
        ]
    )


@router.post("/circuit/build", response_model=CircuitBuildResponse)
async def build_vqc_circuit(req: CircuitBuildRequest):
    """Constructs and analyzes a sample VQC circuit combining encoding and ansatz."""
    try:
        sample_x = req.sample_features
        if sample_x is None:
            sample_x = [0.5] * req.num_qubits
        elif len(sample_x) != req.num_qubits:
            # Pad or truncate to match num_qubits
            if len(sample_x) < req.num_qubits:
                sample_x = sample_x + [0.0] * (req.num_qubits - len(sample_x))
            else:
                sample_x = sample_x[:req.num_qubits]

        cfg = VQCConfig(
            encoder_name=req.encoder_name,
            ansatz=AnsatzConfig(
                ansatz_type=req.ansatz_type,
                num_qubits=req.num_qubits,
                num_layers=req.num_layers,
                rotation_gates=req.rotation_gates,
                entanglement=req.entanglement,
            ),
        )
        model = VariationalQuantumClassifier(cfg)
        full_qc = model.build_full_circuit(np.array(sample_x), bind_ansatz=True)
        metrics = calculate_circuit_metrics(full_qc, transpile_to_basis=False)

        return CircuitBuildResponse(
            num_qubits=full_qc.num_qubits,
            num_parameters=model.num_parameters,
            circuit_depth=metrics.circuit_depth,
            total_gates=metrics.total_gates,
            single_qubit_gates=metrics.single_qubit_gates,
            two_qubit_gates=metrics.two_qubit_gates,
            gate_breakdown=metrics.gate_breakdown,
            ansatz_type=req.ansatz_type,
            encoder_name=req.encoder_name,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Circuit construction failed: {str(e)}",
        )


@router.post("/model/train", response_model=VQCTrainResponse)
async def train_vqc_model(req: VQCTrainRequest):
    """Trains a VQC model on a specified dataset and records training history."""
    try:
        # 1. Load dataset with leakage-free preprocessing
        data_bundle = VQCDatasetLibrary.load_dataset(
            dataset_name=req.dataset_name,
            n_samples=req.n_samples,
            test_size=0.25,
            seed=req.seed,
        )
        X_train = data_bundle["X_train"]
        X_test = data_bundle["X_test"]
        y_train = data_bundle["y_train"]
        y_test = data_bundle["y_test"]
        meta = data_bundle["metadata"]
        num_features = X_train.shape[1]

        # 2. Build VQC
        cfg = VQCConfig(
            encoder_name=req.encoder_name,
            ansatz=AnsatzConfig(
                ansatz_type=req.ansatz_type,
                num_qubits=num_features,
                num_layers=req.num_layers,
                seed=req.seed,
            ),
            training=TrainingConfig(
                optimizer=req.optimizer,
                max_iter=req.max_iter,
                learning_rate=req.learning_rate,
                loss_function=req.loss_function,
                seed=req.seed,
            ),
        )
        model = VariationalQuantumClassifier(cfg)
        trainer = VQCTrainer(model, cfg.training)

        # 3. Fit model
        train_result = trainer.fit(X_train, y_train, X_val=X_test, y_val=y_test)

        # 4. Evaluate on test split
        test_preds = model.predict(X_test)
        test_probs = model.predict_proba(X_test)[:, 1]
        metrics = evaluate_classifier_predictions(y_test, test_preds, test_probs)

        # 5. Persist experiment record
        exp_id = VQCExperimentRegistry.save(
            dataset_name=meta["dataset_name"],
            provenance_tier=meta.get("provenance_tier", "BENCHMARK"),
            model_config=cfg.to_dict(),
            training_metrics={
                "final_train_loss": train_result.final_train_loss,
                "final_val_loss": train_result.final_val_loss,
                "training_time_ms": train_result.total_training_time_ms,
                "quantum_evaluations": train_result.quantum_evaluations,
            },
            evaluation_metrics=metrics,
            history=train_result.history,
        )

        return VQCTrainResponse(
            success=train_result.success,
            status=train_result.status,
            experiment_id=exp_id,
            dataset_name=meta["dataset_name"],
            provenance_tier=meta.get("provenance_tier", "BENCHMARK"),
            num_qubits=model.num_qubits,
            num_parameters=model.num_parameters,
            iterations=train_result.iterations,
            final_train_loss=train_result.final_train_loss,
            final_val_loss=train_result.final_val_loss,
            test_metrics=ClassificationMetricsSchema(
                accuracy=metrics["accuracy"],
                precision=metrics["precision"],
                recall=metrics["recall"],
                f1_score=metrics["f1_score"],
                roc_auc=metrics["roc_auc"],
                confusion_matrix=ConfusionMatrixSchema(
                    tn=metrics["confusion_matrix"]["tn"],
                    fp=metrics["confusion_matrix"]["fp"],
                    fn=metrics["confusion_matrix"]["fn"],
                    tp=metrics["confusion_matrix"]["tp"],
                ),
            ),
            weights=train_result.best_weights.tolist(),
            training_time_ms=train_result.total_training_time_ms,
            quantum_circuit_evaluations=train_result.quantum_evaluations,
            history=[
                TrainingIterationRecord(
                    iteration=h["iteration"],
                    train_loss=h["train_loss"],
                    val_loss=h.get("val_loss"),
                    train_accuracy=h["train_accuracy"],
                    val_accuracy=h.get("val_accuracy"),
                    gradient_norm=h.get("gradient_norm"),
                    step_time_ms=h.get("step_time_ms"),
                )
                for h in train_result.history
            ],
            hardware_disclaimer="Executed via Qiskit Aer classical CPU simulation.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"VQC training failed: {str(e)}",
        )


@router.post("/model/predict", response_model=VQCPredictResponse)
async def predict_vqc_model(req: VQCPredictRequest):
    """Executes forward-pass prediction for input features using pre-trained weights."""
    try:
        t0 = time.perf_counter()
        X_arr = np.asarray(req.features, dtype=float)
        num_qubits = X_arr.shape[1]

        cfg = VQCConfig(
            encoder_name=req.encoder_name,
            ansatz=AnsatzConfig(
                ansatz_type=req.ansatz_type,
                num_qubits=num_qubits,
                num_layers=req.num_layers,
            ),
        )
        model = VariationalQuantumClassifier(cfg)
        model.set_parameters(np.array(req.weights, dtype=float))

        probs = model.predict_proba(X_arr)
        preds = model.predict(X_arr, threshold=req.threshold)
        inf_time_ms = (time.perf_counter() - t0) * 1000.0

        return VQCPredictResponse(
            predictions=preds.tolist(),
            probabilities=probs.tolist(),
            num_samples=len(X_arr),
            inference_time_ms=round(inf_time_ms, 2),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prediction failed: {str(e)}",
        )


@router.post("/benchmark/run", response_model=VQCBenchmarkResponse)
async def run_vqc_benchmark(req: VQCBenchmarkRequest):
    """Runs head-to-head benchmark comparing VQC against 6 Classical ML Baselines."""
    try:
        report = VQCBenchmarkSuite.run_benchmark(
            dataset_name=req.dataset_name,
            n_samples=req.n_samples,
            encoder_name=req.encoder_name,
            ansatz_type=req.ansatz_type,
            num_layers=req.num_layers,
            max_iter=req.max_iter,
            seed=req.seed,
        )

        return VQCBenchmarkResponse(
            dataset_name=report["dataset_name"],
            provenance_tier=report["provenance_tier"],
            num_features=report["num_features"],
            train_samples=report["train_samples"],
            test_samples=report["test_samples"],
            models=[
                BenchmarkModelEntrySchema(
                    model_name=m["model_name"],
                    is_quantum=m["is_quantum"],
                    accuracy=m["accuracy"],
                    precision=m["precision"],
                    recall=m["recall"],
                    f1_score=m["f1_score"],
                    roc_auc=m["roc_auc"],
                    confusion_matrix=ConfusionMatrixSchema(
                        tn=m["confusion_matrix"]["tn"],
                        fp=m["confusion_matrix"]["fp"],
                        fn=m["confusion_matrix"]["fn"],
                        tp=m["confusion_matrix"]["tp"],
                    ),
                    training_time_ms=m["training_time_ms"],
                    inference_latency_ms=m["inference_latency_ms"],
                    num_parameters=m["num_parameters"],
                    circuit_depth=m.get("circuit_depth"),
                    hardware_note=m["hardware_note"],
                )
                for m in report["models"]
            ],
            vqc_training_history=report["vqc_training_history"],
            summary_findings=report["summary_findings"],
            scientific_disclaimer=report["scientific_disclaimer"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Benchmark execution failed: {str(e)}",
        )


@router.get("/experiments")
async def list_vqc_experiments():
    """Returns catalog of historical VQC training runs and benchmarks."""
    return VQCExperimentRegistry.list_all(limit=25)


@router.get("/experiments/{experiment_id}")
async def get_vqc_experiment(experiment_id: str):
    """Retrieves specific historical experiment details."""
    exp = VQCExperimentRegistry.get(experiment_id)
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found",
        )
    return exp
