"""
trainer.py - Hybrid Classical-Quantum Optimization Training Engine for VQC.

Coordinates:
  1. Parameter initialization
  2. Quantum circuit execution over mini-batches
  3. Loss evaluation (BCE or MSE)
  4. Gradient calculation (Parameter-Shift or Finite Difference)
  5. Parameter updates via COBYLA, L-BFGS-B, SPSA, or Adam
  6. Real-time telemetry tracking & early stopping
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import time
import numpy as np
from scipy.optimize import minimize

from .config import TrainingConfig
from .model import VariationalQuantumClassifier
from .loss_functions import get_loss_function, BaseLossFunction
from .gradients import VQCGradientEngine


@dataclass
class VQCTrainingResult:
    """Telemetry and outcome returned by the VQC training process."""
    success: bool
    status: str
    iterations: int
    final_train_loss: float
    final_val_loss: Optional[float]
    final_train_accuracy: float
    final_val_accuracy: Optional[float]
    best_weights: np.ndarray
    total_training_time_ms: float
    quantum_evaluations: int
    history: List[Dict[str, Any]] = field(default_factory=list)


class VQCTrainer:
    """
    Orchestrates the hybrid classical-quantum training loop for VQC.
    """

    def __init__(
        self,
        model: VariationalQuantumClassifier,
        config: Optional[TrainingConfig] = None,
    ):
        self.model = model
        self.config = config or model.config.training
        self.loss_fn: BaseLossFunction = get_loss_function(self.config.loss_function)
        self.quantum_evaluations = 0

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> VQCTrainingResult:
        """
        Executes the hybrid classical-quantum optimization loop.
        """
        t_start = time.perf_counter()
        X_tr = np.asarray(X_train, dtype=float)
        y_tr = np.asarray(y_train, dtype=int)
        has_val = X_val is not None and y_val is not None
        if has_val:
            X_v = np.asarray(X_val, dtype=float)
            y_v = np.asarray(y_val, dtype=int)

        opt_name = self.config.optimizer.upper()
        history: List[Dict[str, Any]] = []
        best_loss = float("inf")
        best_weights = self.model.get_parameters().copy()
        patience_counter = 0

        current_weights = self.model.get_parameters().copy()
        self.quantum_evaluations = 0

        # Objective function for optimizers
        def objective(weights: np.ndarray) -> float:
            self.quantum_evaluations += len(X_tr)
            _, p1 = self.model.forward_batch(X_tr, params=weights)
            loss = self.loss_fn.compute(y_tr, p1)
            return float(loss)

        # Gradient function for gradient-based optimizers (Parameter-Shift)
        def gradient(weights: np.ndarray) -> np.ndarray:
            _, p1 = self.model.forward_batch(X_tr, params=weights)
            dL_dp = self.loss_fn.gradient_wrt_prob(y_tr, p1)

            num_params = len(weights)
            total_grad = np.zeros(num_params, dtype=float)

            # Compute parameter-shift gradient per sample and accumulate via chain rule
            # dp_i / dθ = (-1/2) * d<Z_0>/dθ
            for i, x_sample in enumerate(X_tr):
                unbound_qc = self.model.build_full_circuit(x_sample, bind_ansatz=False)
                dZ_dtheta = VQCGradientEngine.compute_single_sample_shift_gradient(
                    unbound_qc,
                    self.model.parameter_vector,
                    weights,
                    self.model.measurement.observable,
                )
                self.quantum_evaluations += 2 * num_params
                dp_dtheta = -0.5 * dZ_dtheta
                total_grad += dL_dp[i] * dp_dtheta

            return total_grad

        # ── Optimization Loop Dispatch ─────────────────────────────────────
        if opt_name in ("COBYLA", "NELDER-MEAD"):
            iteration_counter = 0

            def callback(intermediate_weights: np.ndarray):
                nonlocal iteration_counter, best_loss, best_weights, patience_counter
                iteration_counter += 1
                step_t0 = time.perf_counter()

                # Train metrics
                _, tr_p1 = self.model.forward_batch(X_tr, params=intermediate_weights)
                tr_loss = self.loss_fn.compute(y_tr, tr_p1)
                tr_acc = float(np.mean((tr_p1 >= 0.5).astype(int) == y_tr))

                # Val metrics
                val_loss = None
                val_acc = None
                if has_val:
                    _, v_p1 = self.model.forward_batch(X_v, params=intermediate_weights)
                    val_loss = self.loss_fn.compute(y_v, v_p1)
                    val_acc = float(np.mean((v_p1 >= 0.5).astype(int) == y_v))
                    current_metric = val_loss
                else:
                    current_metric = tr_loss

                step_time = (time.perf_counter() - step_t0) * 1000.0

                record = {
                    "iteration": iteration_counter,
                    "train_loss": round(tr_loss, 5),
                    "val_loss": round(val_loss, 5) if val_loss is not None else None,
                    "train_accuracy": round(tr_acc, 4),
                    "val_accuracy": round(val_acc, 4) if val_acc is not None else None,
                    "step_time_ms": round(step_time, 2),
                }
                history.append(record)

                if current_metric < best_loss - self.config.tolerance:
                    best_loss = current_metric
                    best_weights = intermediate_weights.copy()
                    patience_counter = 0
                else:
                    patience_counter += 1

            opt_res = minimize(
                fun=objective,
                x0=current_weights,
                method="COBYLA",
                callback=callback,
                options={
                    "maxiter": self.config.max_iter,
                    "tol": self.config.tolerance,
                },
            )
            final_weights = best_weights if best_loss < float("inf") else opt_res.x

        elif opt_name in ("L-BFGS-B", "BFGS"):
            iteration_counter = 0

            def lbfgs_callback(intermediate_weights: np.ndarray):
                nonlocal iteration_counter, best_loss, best_weights
                iteration_counter += 1
                _, tr_p1 = self.model.forward_batch(X_tr, params=intermediate_weights)
                tr_loss = self.loss_fn.compute(y_tr, tr_p1)
                tr_acc = float(np.mean((tr_p1 >= 0.5).astype(int) == y_tr))

                val_loss = None
                val_acc = None
                if has_val:
                    _, v_p1 = self.model.forward_batch(X_v, params=intermediate_weights)
                    val_loss = self.loss_fn.compute(y_v, v_p1)
                    val_acc = float(np.mean((v_p1 >= 0.5).astype(int) == y_v))

                history.append({
                    "iteration": iteration_counter,
                    "train_loss": round(tr_loss, 5),
                    "val_loss": round(val_loss, 5) if val_loss is not None else None,
                    "train_accuracy": round(tr_acc, 4),
                    "val_accuracy": round(val_acc, 4) if val_acc is not None else None,
                })
                if tr_loss < best_loss:
                    best_loss = tr_loss
                    best_weights = intermediate_weights.copy()

            opt_res = minimize(
                fun=objective,
                x0=current_weights,
                method="L-BFGS-B",
                jac=gradient,
                callback=lbfgs_callback,
                options={
                    "maxiter": min(self.config.max_iter, 25),
                    "ftol": self.config.tolerance,
                },
            )
            final_weights = best_weights if best_loss < float("inf") else opt_res.x

        else:
            # Native Adam / Gradient Descent Loop
            weights = current_weights.copy()
            lr = self.config.learning_rate
            m = np.zeros_like(weights)
            v = np.zeros_like(weights)
            beta1, beta2, eps_adam = 0.9, 0.999, 1e-8

            for epoch in range(1, self.config.max_iter + 1):
                t_ep = time.perf_counter()
                grad = gradient(weights)

                # Adam updates
                m = beta1 * m + (1.0 - beta1) * grad
                v = beta2 * v + (1.0 - beta2) * (grad ** 2)
                m_hat = m / (1.0 - beta1 ** epoch)
                v_hat = v / (1.0 - beta2 ** epoch)
                weights -= lr * m_hat / (np.sqrt(v_hat) + eps_adam)

                # Evaluate progress
                _, tr_p1 = self.model.forward_batch(X_tr, params=weights)
                tr_loss = self.loss_fn.compute(y_tr, tr_p1)
                tr_acc = float(np.mean((tr_p1 >= 0.5).astype(int) == y_tr))

                val_loss, val_acc = None, None
                if has_val:
                    _, v_p1 = self.model.forward_batch(X_v, params=weights)
                    val_loss = self.loss_fn.compute(y_v, v_p1)
                    val_acc = float(np.mean((v_p1 >= 0.5).astype(int) == y_v))
                    current_loss = val_loss
                else:
                    current_loss = tr_loss

                step_time = (time.perf_counter() - t_ep) * 1000.0

                history.append({
                    "iteration": epoch,
                    "train_loss": round(tr_loss, 5),
                    "val_loss": round(val_loss, 5) if val_loss is not None else None,
                    "train_accuracy": round(tr_acc, 4),
                    "val_accuracy": round(val_acc, 4) if val_acc is not None else None,
                    "gradient_norm": round(float(np.linalg.norm(grad)), 6),
                    "step_time_ms": round(step_time, 2),
                })

                if current_loss < best_loss - self.config.tolerance:
                    best_loss = current_loss
                    best_weights = weights.copy()
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= self.config.early_stopping_patience:
                        break

            final_weights = best_weights

        # Update model with optimal weights
        self.model.set_parameters(final_weights)

        # Final evaluation
        _, final_tr_p1 = self.model.forward_batch(X_tr)
        final_tr_loss = self.loss_fn.compute(y_tr, final_tr_p1)
        final_tr_acc = float(np.mean((final_tr_p1 >= 0.5).astype(int) == y_tr))

        final_val_loss, final_val_acc = None, None
        if has_val:
            _, final_v_p1 = self.model.forward_batch(X_v)
            final_val_loss = self.loss_fn.compute(y_v, final_v_p1)
            final_val_acc = float(np.mean((final_v_p1 >= 0.5).astype(int) == y_v))

        total_time_ms = (time.perf_counter() - t_start) * 1000.0

        return VQCTrainingResult(
            success=True,
            status="CONVERGED" if len(history) < self.config.max_iter else "MAX_ITER_REACHED",
            iterations=len(history),
            final_train_loss=float(final_tr_loss),
            final_val_loss=float(final_val_loss) if final_val_loss is not None else None,
            final_train_accuracy=float(final_tr_acc),
            final_val_accuracy=float(final_val_acc) if final_val_acc is not None else None,
            best_weights=final_weights,
            total_training_time_ms=round(total_time_ms, 2),
            quantum_evaluations=self.quantum_evaluations,
            history=history,
        )
