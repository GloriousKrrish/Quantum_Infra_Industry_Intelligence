"""
loss_functions.py - Loss Functions and Gradient Derivatives for VQC.

Provides loss computation and analytical derivatives with respect to class probabilities:
  1. Binary Cross-Entropy (BCE)
  2. Mean Squared Error (MSE)
"""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np


class BaseLossFunction(ABC):
    """Abstract interface for classification loss functions."""

    @abstractmethod
    def compute(self, y_true: np.ndarray, y_pred_prob: np.ndarray) -> float:
        """Computes scalar loss over batch."""
        pass

    @abstractmethod
    def gradient_wrt_prob(self, y_true: np.ndarray, y_pred_prob: np.ndarray) -> np.ndarray:
        """Computes derivative dL/dp_1 for each sample."""
        pass


class BinaryCrossEntropyLoss(BaseLossFunction):
    """
    Binary Cross-Entropy Loss:
      L(y, p) = - 1/N sum [ y * ln(p + eps) + (1 - y) * ln(1 - p + eps) ]
      dL/dp = - y / (p + eps) + (1 - y) / (1 - p + eps)
    """

    def __init__(self, eps: float = 1e-12):
        self.eps = eps

    def compute(self, y_true: np.ndarray, y_pred_prob: np.ndarray) -> float:
        y_t = np.asarray(y_true, dtype=float)
        p = np.clip(np.asarray(y_pred_prob, dtype=float), self.eps, 1.0 - self.eps)
        loss = -np.mean(y_t * np.log(p) + (1.0 - y_t) * np.log(1.0 - p))
        return float(loss)

    def gradient_wrt_prob(self, y_true: np.ndarray, y_pred_prob: np.ndarray) -> np.ndarray:
        y_t = np.asarray(y_true, dtype=float)
        p = np.clip(np.asarray(y_pred_prob, dtype=float), self.eps, 1.0 - self.eps)
        # dL / dp_1
        grad = (-y_t / p) + ((1.0 - y_t) / (1.0 - p))
        return grad / len(y_t)


class MeanSquaredErrorLoss(BaseLossFunction):
    """
    Mean Squared Error Loss:
      L(y, p) = 1/N sum (p - y)^2
      dL/dp = 2 * (p - y) / N
    """

    def compute(self, y_true: np.ndarray, y_pred_prob: np.ndarray) -> float:
        y_t = np.asarray(y_true, dtype=float)
        p = np.asarray(y_pred_prob, dtype=float)
        return float(np.mean((p - y_t) ** 2))

    def gradient_wrt_prob(self, y_true: np.ndarray, y_pred_prob: np.ndarray) -> np.ndarray:
        y_t = np.asarray(y_true, dtype=float)
        p = np.asarray(y_pred_prob, dtype=float)
        return (2.0 * (p - y_t)) / len(y_t)


def get_loss_function(name: str) -> BaseLossFunction:
    """Factory helper to obtain loss function instance."""
    normalized = name.lower().replace("-", "_")
    if normalized in ("binary_cross_entropy", "bce", "cross_entropy"):
        return BinaryCrossEntropyLoss()
    elif normalized in ("mean_squared_error", "mse"):
        return MeanSquaredErrorLoss()
    else:
        return BinaryCrossEntropyLoss()
