"""
parameter_strategies.py - Parameter Initialization Strategies for QAOA.

Provides scientific parameter initialization schedules:
  - RANDOM: Uniform random exploration
  - LINEAR_RAMP: Linear quantum annealing heuristic
  - FOURIER: Fourier parameterized smooth schedules
  - LAYER_TRANSFER: Parameter extrapolation from depth p to p+1
"""

from enum import Enum
from typing import List, Optional, Tuple
import numpy as np


class ParameterStrategy(str, Enum):
    RANDOM = "random"
    LINEAR_RAMP = "linear_ramp"
    FOURIER = "fourier"
    LAYER_TRANSFER = "layer_transfer"


class QAOAParameterInitializer:
    """
    Computes initial variational parameters (gammas, betas) for QAOA depth p.
    """

    @staticmethod
    def get_initial_parameters(
        depth_p: int,
        strategy: ParameterStrategy = ParameterStrategy.LINEAR_RAMP,
        seed: Optional[int] = 42,
        prev_gammas: Optional[List[float]] = None,
        prev_betas: Optional[List[float]] = None,
    ) -> Tuple[List[float], List[float]]:
        rng = np.random.default_rng(seed)

        if strategy == ParameterStrategy.RANDOM:
            # Gammas typically in [0, 2*pi), Betas in [0, pi)
            gammas = rng.uniform(0.0, np.pi, size=depth_p).tolist()
            betas = rng.uniform(0.0, np.pi / 2.0, size=depth_p).tolist()
            return gammas, betas

        elif strategy == ParameterStrategy.LINEAR_RAMP:
            # Linear ramp inspired by adiabatic quantum computation:
            # Gammas increase with layer, Betas decrease with layer
            # t_k = (k + 0.5) / p
            # gamma_k = (k / p) * Delta t
            # beta_k = (1 - k / p) * Delta t
            gammas = [0.1 + 0.5 * (k + 1) / depth_p for k in range(depth_p)]
            betas = [0.5 * (1.0 - k / depth_p) for k in range(depth_p)]
            return gammas, betas

        elif strategy == ParameterStrategy.FOURIER:
            # Discrete cosine / sine transform parameterization
            # Good standard starting point
            gammas = [0.2 * np.sin((k + 0.5) * np.pi / depth_p) for k in range(depth_p)]
            betas = [0.2 * np.cos((k + 0.5) * np.pi / depth_p) for k in range(depth_p)]
            return gammas, betas

        elif strategy == ParameterStrategy.LAYER_TRANSFER:
            # Extrapolate from p-1 to p
            if prev_gammas is not None and prev_betas is not None and len(prev_gammas) == depth_p - 1:
                # Standard linear interpolation extrapolation to depth p
                x_old = np.linspace(0, 1, len(prev_gammas))
                x_new = np.linspace(0, 1, depth_p)
                new_gammas = np.interp(x_new, x_old, prev_gammas).tolist()
                new_betas = np.interp(x_new, x_old, prev_betas).tolist()
                return new_gammas, new_betas
            else:
                # Fallback to linear ramp if previous parameters not provided
                return QAOAParameterInitializer.get_initial_parameters(
                    depth_p, strategy=ParameterStrategy.LINEAR_RAMP, seed=seed
                )

        # Default fallback
        return [0.2] * depth_p, [0.2] * depth_p

