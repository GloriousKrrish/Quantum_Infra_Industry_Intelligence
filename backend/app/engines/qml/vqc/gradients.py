"""
gradients.py - Analytical Parameter-Shift Rule & Finite-Difference Gradient Engine.

Implements exact analytical quantum gradients for variational circuits:
  Parameter-Shift Rule:
    For rotation generator G with eigenvalues ±1/2:
      d <M> / d θ_k = [ <M>(θ_k + s) - <M>(θ_k - s) ] / (2 * sin(s)), where s = π/2
      
    This yields the two-term analytical formula:
      d <M> / d θ_k = [ <M>(θ_k + π/2) - <M>(θ_k - π/2) ] / 2
      
  Chain Rule for Classification Loss:
    Since p = (1 - <Z_0>) / 2:
      dp / d <Z_0> = - 1/2
      dL / d θ_k = sum_i (dL / dp_i) * (dp_i / d <Z_0>) * (d <Z_0> / d θ_k)
                 = sum_i (dL / dp_i) * (-1/2) * (d <Z_0> / d θ_k)
"""

from typing import Dict, Any, Tuple, Optional, Callable
import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import Statevector, SparsePauliOp


class VQCGradientEngine:
    """
    Computes quantum circuit gradients via the Parameter-Shift Rule and Finite Differences.
    """

    SHIFT = np.pi / 2.0
    FD_EPSILON = 1e-5

    @classmethod
    def compute_single_sample_shift_gradient(
        cls,
        circuit: QuantumCircuit,
        param_vector: ParameterVector,
        current_params: np.ndarray,
        observable: SparsePauliOp,
    ) -> np.ndarray:
        """
        Computes analytical gradient vector d <M> / d θ of length P for a single circuit instance.
        Evaluates 2 * P shifted quantum states.
        """
        num_params = len(current_params)
        grad = np.zeros(num_params, dtype=float)
        shift = cls.SHIFT

        for k in range(num_params):
            # Forward shifted parameter vector: θ_k + π/2
            params_plus = current_params.copy()
            params_plus[k] += shift
            bind_plus = {param_vector[i]: float(params_plus[i]) for i in range(num_params)}
            qc_plus = circuit.assign_parameters(bind_plus)
            sv_plus = Statevector(qc_plus)
            exp_plus = float(sv_plus.expectation_value(observable).real)

            # Backward shifted parameter vector: θ_k - π/2
            params_minus = current_params.copy()
            params_minus[k] -= shift
            bind_minus = {param_vector[i]: float(params_minus[i]) for i in range(num_params)}
            qc_minus = circuit.assign_parameters(bind_minus)
            sv_minus = Statevector(qc_minus)
            exp_minus = float(sv_minus.expectation_value(observable).real)

            # Parameter-shift derivative
            grad[k] = (exp_plus - exp_minus) / 2.0

        return grad

    @classmethod
    def compute_single_sample_finite_difference(
        cls,
        circuit: QuantumCircuit,
        param_vector: ParameterVector,
        current_params: np.ndarray,
        observable: SparsePauliOp,
        epsilon: Optional[float] = None,
    ) -> np.ndarray:
        """
        Computes numerical two-sided finite-difference gradient vector d <M> / d θ.
        """
        num_params = len(current_params)
        grad = np.zeros(num_params, dtype=float)
        eps = epsilon or cls.FD_EPSILON

        for k in range(num_params):
            p_plus = current_params.copy()
            p_plus[k] += eps
            b_plus = {param_vector[i]: float(p_plus[i]) for i in range(num_params)}
            exp_plus = float(Statevector(circuit.assign_parameters(b_plus)).expectation_value(observable).real)

            p_minus = current_params.copy()
            p_minus[k] -= eps
            b_minus = {param_vector[i]: float(p_minus[i]) for i in range(num_params)}
            exp_minus = float(Statevector(circuit.assign_parameters(b_minus)).expectation_value(observable).real)

            grad[k] = (exp_plus - exp_minus) / (2.0 * eps)

        return grad

    @classmethod
    def verify_gradient_accuracy(
        cls,
        circuit: QuantumCircuit,
        param_vector: ParameterVector,
        current_params: np.ndarray,
        observable: SparsePauliOp,
        tolerance: float = 1e-4,
    ) -> Dict[str, Any]:
        """
        Cross-validates Parameter-Shift Rule against Finite Differences.
        Asserts absolute error || grad_shift - grad_fd ||_inf < tolerance.
        """
        grad_shift = cls.compute_single_sample_shift_gradient(
            circuit, param_vector, current_params, observable
        )
        grad_fd = cls.compute_single_sample_finite_difference(
            circuit, param_vector, current_params, observable
        )

        diff = np.abs(grad_shift - grad_fd)
        max_error = float(np.max(diff))
        is_consistent = bool(max_error < tolerance)

        return {
            "parameter_shift_gradient": grad_shift.tolist(),
            "finite_difference_gradient": grad_fd.tolist(),
            "max_absolute_error": max_error,
            "tolerance": tolerance,
            "is_consistent": is_consistent,
            "gradient_norm": float(np.linalg.norm(grad_shift)),
        }
